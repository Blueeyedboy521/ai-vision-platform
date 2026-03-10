# -*- coding: utf-8 -*-
"""
算法 API

提供算法 CRUD 和摄像头-算法配置接口
"""
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_current_admin
from app.models import User, Algorithm, Model, CameraAlgorithm, Camera
from app.models.base import generate_uuid
from app.schemas.algorithm import (
    AlgorithmCreate,
    AlgorithmUpdate,
    CameraAlgorithmCreate,
    CameraAlgorithmUpdate
)
from app.schemas.common import success_response, page_response
from app.services.config_publisher import get_config_publisher
from common.logging import logger
from common.redis import RedisKeys
from app.core.redis import (
    write_model_to_redis,
    write_algorithm_to_redis,
    delete_algorithm_from_redis,
)


router = APIRouter()


@router.get("", summary="获取算法列表")
async def get_algorithms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_id: Optional[str] = Query(None, description="模型ID"),
    keyword: Optional[str] = Query(None, description="关键词"),
    is_enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取算法列表
    """
    query = select(Algorithm).options(selectinload(Algorithm.model))
    count_query = select(func.count(Algorithm.id))
    
    if model_id:
        query = query.where(Algorithm.model_id == model_id)
        count_query = count_query.where(Algorithm.model_id == model_id)
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Algorithm.name.ilike(keyword_filter)) |
            (Algorithm.code.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Algorithm.name.ilike(keyword_filter)) |
            (Algorithm.code.ilike(keyword_filter))
        )
    
    if is_enabled is not None:
        query = query.where(Algorithm.is_enabled == is_enabled)
        count_query = count_query.where(Algorithm.is_enabled == is_enabled)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(Algorithm.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    algorithms = result.scalars().all()
    
    data = []
    for algo in algorithms:
        # 统计关联摄像头数量
        cam_count_result = await db.execute(
            select(func.count(CameraAlgorithm.id))
            .where(CameraAlgorithm.algorithm_id == algo.id)
        )
        cam_count = cam_count_result.scalar() or 0
        
        data.append({
            "id": algo.id,
            "name": algo.name,
            "code": algo.code,
            "description": algo.description,
            "model_id": algo.model_id,
            "model_name": algo.model.name if algo.model else None,
            "target_classes": algo.target_classes,
            "default_confidence": algo.default_confidence,
            "alert_config": algo.alert_config,
            "is_enabled": algo.is_enabled,
            "camera_count": cam_count,
            "created_at": algo.created_at.isoformat(),
            "updated_at": algo.updated_at.isoformat()
        })
    
    return page_response(data, page, page_size, total)


@router.get("/{algorithm_id}", summary="获取算法详情")
async def get_algorithm(
    algorithm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取算法详情
    """
    result = await db.execute(
        select(Algorithm)
        .options(selectinload(Algorithm.model))
        .where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    
    if algo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    cam_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id))
        .where(CameraAlgorithm.algorithm_id == algo.id)
    )
    cam_count = cam_count_result.scalar() or 0
    
    return success_response({
        "id": algo.id,
        "name": algo.name,
        "code": algo.code,
        "description": algo.description,
        "model_id": algo.model_id,
        "model_name": algo.model.name if algo.model else None,
        "target_classes": algo.target_classes,
        "default_confidence": algo.default_confidence,
        "alert_config": algo.alert_config,
        "is_enabled": algo.is_enabled,
        "camera_count": cam_count,
        "created_at": algo.created_at.isoformat(),
        "updated_at": algo.updated_at.isoformat()
    })


@router.post("", summary="创建算法")
async def create_algorithm(
    algo_data: AlgorithmCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建算法 (仅管理员)
    """
    # 检查编码,条件应该是model_id,code
    existing = await db.execute(
        select(Algorithm).where(Algorithm.model_id == algo_data.model_id, Algorithm.code == algo_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="算法编码已存在"
        )
    
    # 检查模型
    model_result = await db.execute(
        select(Model).where(Model.id == algo_data.model_id)
    )
    if model_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模型不存在"
        )
    
    # 创建算法
    algo = Algorithm(
        id=generate_uuid(),
        name=algo_data.name,
        code=algo_data.code,
        description=algo_data.description,
        model_id=algo_data.model_id,
        default_confidence=algo_data.default_confidence,
        is_enabled=algo_data.is_enabled,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    algo.target_classes = algo_data.target_classes
    algo.alert_config = algo_data.alert_config
    
    db.add(algo)
    await db.commit()
    # 无需 refresh：id 等均为 Python 侧赋值，无 DB 端默认值需回读

    # 写入算法配置到 Redis（统一封装）
    await write_algorithm_to_redis(algo)
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_add({
        "algorithm_id": algo.id,
        "code": algo.code,
        "model_id": algo.model_id
    })
    
    logger.info(f"算法已创建: {algo.id} - {algo.name}")
    
    # 更新关联模型的 Redis 配置（包含算法列表）
    await write_model_to_redis(algo.model_id, db)
    return success_response({"id": algo.id}, "创建成功")


@router.put("/{algorithm_id}", summary="更新算法")
async def update_algorithm(
    algorithm_id: str,
    algo_data: AlgorithmUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新算法 (仅管理员)
    """
    result = await db.execute(
        select(Algorithm).where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    
    if algo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    update_data = algo_data.model_dump(exclude_unset=True)

    # 若修改了 code，需保证全局唯一（Algorithm.code 有 unique 约束）
    new_code = update_data.get("code")
    if new_code and new_code != algo.code:
        existing = await db.execute(
            select(Algorithm).where(Algorithm.code == new_code, Algorithm.id != algorithm_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="算法编码已存在"
            )
    
    for field, value in update_data.items():
        if field == "target_classes":
            algo.target_classes = value
        elif field == "alert_config":
            algo.alert_config = value
        else:
            setattr(algo, field, value)
    
    algo.updated_by = current_user.id
    
    await db.commit()
    
    # 更新 Redis 中的算法配置（统一封装）
    await write_algorithm_to_redis(algo)
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_update({
        "algorithm_id": algo.id,
        "code": algo.code,
        "model_id": algo.model_id
    })
    
    logger.info(f"算法已更新: {algorithm_id}")
    
    # 更新关联模型的 Redis 配置（包含算法列表）
    await write_model_to_redis(algo.model_id, db)
    return success_response(None, "更新成功")


@router.delete("/{algorithm_id}", summary="删除算法")
async def delete_algorithm(
    algorithm_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除算法 (仅管理员)
    """
    result = await db.execute(
        select(Algorithm).where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    
    if algo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在"
        )
    
    # 检查关联
    cam_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id))
        .where(CameraAlgorithm.algorithm_id == algorithm_id)
    )
    if (cam_count_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存在关联的摄像头配置，无法删除"
        )
    
    model_id = algo.model_id
    await db.delete(algo)
    await db.commit()
    
    # 从 Redis 中删除算法配置（统一封装）
    await delete_algorithm_from_redis(algorithm_id)
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_delete(algorithm_id)
    
    logger.info(f"算法已删除: {algorithm_id}")
    
    # 更新关联模型的 Redis 配置（包含算法列表）
    await write_model_to_redis(model_id, db)
    return success_response(None, "删除成功")


# ==================== 摄像头-算法配置 ====================

@router.get("/camera/{camera_id}/configs", summary="获取摄像头算法配置")
async def get_camera_algorithm_configs(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取摄像头的算法配置列表
    """
    result = await db.execute(
        select(CameraAlgorithm)
        .options(
            selectinload(CameraAlgorithm.algorithm),
            selectinload(CameraAlgorithm.camera)
        )
        .where(CameraAlgorithm.camera_id == camera_id)
    )
    configs = result.scalars().all()
    
    data = []
    for config in configs:
        data.append({
            "id": config.id,
            "camera_id": config.camera_id,
            "camera_name": config.camera.name if config.camera else None,
            "algorithm_id": config.algorithm_id,
            "algorithm_name": config.algorithm.name if config.algorithm else None,
            "model_id": config.model_id,
            "confidence": config.confidence,
            "effective_confidence": config.get_effective_confidence(),
            "alert_config": config.alert_config,
            "effective_alert_config": config.get_effective_alert_config(),
            "regions": config.regions,
            "inference_interval_sec": getattr(config, "inference_interval_sec", 5),
            "alarm_interval_sec": getattr(config, "alarm_interval_sec", 30),
            "is_enabled": config.is_enabled,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        })
    
    return success_response(data)


@router.post("/camera/{camera_id}/configs", summary="添加摄像头算法配置")
async def create_camera_algorithm_config(
    camera_id: str,
    config_data: CameraAlgorithmCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为摄像头添加算法配置
    """
    # 检查摄像头
    cam_result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    if cam_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 检查是否已存在
    existing = await db.execute(
        select(CameraAlgorithm)
        .where(
            CameraAlgorithm.camera_id == camera_id,
            CameraAlgorithm.algorithm_id == config_data.algorithm_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该摄像头已配置此算法"
        )
    
    # 创建配置
    config = CameraAlgorithm(
        id=generate_uuid(),
        camera_id=camera_id,
        algorithm_id=config_data.algorithm_id,
        model_id=config_data.model_id,
        confidence=config_data.confidence,
        is_enabled=config_data.is_enabled,
        inference_interval_sec=getattr(config_data, "inference_interval_sec", None) or 5,
        alarm_interval_sec=getattr(config_data, "alarm_interval_sec", None) or 30,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    config.alert_config = config_data.alert_config
    config.regions = config_data.regions
    
    db.add(config)
    await db.commit()
    
    # 计算生效配置（此处避免访问懒加载关系，只使用当前覆盖值）
    effective_confidence = config.confidence if config.confidence is not None else 0.5
    effective_alert_config = config.alert_config or {}
    regions = config.regions
    
    # 写入摄像头-算法配置到 Redis
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.camera_algorithm_config(camera_id, config_data.algorithm_id),
            json.dumps(
                {
                    "camera_id": camera_id,
                    "algorithm_id": config_data.algorithm_id,
                    "model_id": config.model_id,
                    "confidence": effective_confidence,
                    "alert_config": effective_alert_config,
                    "regions": regions,
                    "inference_interval_sec": config.inference_interval_sec,
                    "alarm_interval_sec": config.alarm_interval_sec,
                    "is_enabled": config.is_enabled,
                },
                ensure_ascii=False,
            ),
        )
    except Exception as e:
        logger.error(f"写入摄像头算法配置到 Redis 失败: {e}")
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_algorithm_add(
        camera_id,
        config_data.algorithm_id,
        {
            "confidence": effective_confidence,
            "regions": regions,
            "alert_config": effective_alert_config
        }
    )
    
    logger.info(f"摄像头算法配置已添加: {camera_id} - {config_data.algorithm_id}")
    
    return success_response({"id": config.id}, "添加成功")


@router.put("/camera/{camera_id}/configs/{config_id}", summary="更新摄像头算法配置")
async def update_camera_algorithm_config(
    camera_id: str,
    config_id: str,
    config_data: CameraAlgorithmUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新摄像头算法配置（置信度 / 区域 / 启用状态等）
    """
    result = await db.execute(
        select(CameraAlgorithm)
        .options(
            selectinload(CameraAlgorithm.algorithm),
            selectinload(CameraAlgorithm.camera),
        )
        .where(
            CameraAlgorithm.id == config_id,
            CameraAlgorithm.camera_id == camera_id
        )
    )
    config = result.scalar_one_or_none()
    
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    update_data = config_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "regions":
            config.regions = value
        else:
            setattr(config, field, value)
    
    config.updated_by = current_user.id

    await db.commit()
    # 无需 refresh：下面用 config 自身属性即可，避免懒加载

    # 更新 Redis 中的摄像头-算法配置（alert_config 用合并后的生效配置，空覆盖时回退算法默认）
    effective_confidence = config.confidence if config.confidence is not None else 0.5
    effective_alert_config = config.get_effective_alert_config()
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.camera_algorithm_config(camera_id, config.algorithm_id),
            json.dumps(
                {
                    "camera_id": camera_id,
                    "algorithm_id": config.algorithm_id,
                    "model_id": config.model_id,
                    "confidence": effective_confidence,
                    "alert_config": effective_alert_config,
                    "regions": config.regions,
                    "inference_interval_sec": getattr(config, "inference_interval_sec", 5),
                    "alarm_interval_sec": getattr(config, "alarm_interval_sec", 30),
                    "is_enabled": config.is_enabled,
                },
                ensure_ascii=False,
            ),
        )
    except Exception as e:
        logger.error(f"更新摄像头算法配置到 Redis 失败: {e}")
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_algorithm_update(
        camera_id,
        config.algorithm_id,
        {
            "confidence": config.get_effective_confidence(),
            "regions": config.regions,
            "alert_config": config.get_effective_alert_config(),
            "is_enabled": config.is_enabled,
        },
    )
    
    logger.info(f"摄像头算法配置已更新: {camera_id} - {config.algorithm_id}")
    
    return success_response(None, "更新成功")


@router.delete("/camera/{camera_id}/configs/{config_id}", summary="删除摄像头算法配置")
async def delete_camera_algorithm_config(
    camera_id: str,
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除摄像头算法配置
    """
    result = await db.execute(
        select(CameraAlgorithm)
        .where(
            CameraAlgorithm.id == config_id,
            CameraAlgorithm.camera_id == camera_id
        )
    )
    config = result.scalar_one_or_none()
    
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="配置不存在"
        )
    
    algorithm_id = config.algorithm_id
    
    await db.delete(config)
    await db.commit()
    
    # 从 Redis 中删除摄像头-算法配置
    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.camera_algorithm_config(camera_id, algorithm_id))
    except Exception as e:
        logger.error(f"从 Redis 删除摄像头算法配置失败: {e}")
    
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_algorithm_delete(camera_id, algorithm_id)
    
    logger.info(f"摄像头算法配置已删除: {camera_id} - {algorithm_id}")
    
    return success_response(None, "删除成功")
