# -*- coding: utf-8 -*-
"""
模型 API

提供 AI 模型 CRUD 接口
"""
from typing import Optional
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user, get_current_admin
from app.models import User, Model, Algorithm
from app.models.base import generate_uuid
from app.services.model_sync import sync_model_classes_from_algorithms
from app.schemas.model import ModelCreate, ModelUpdate, ModelResponse
from app.schemas.common import success_response, page_response
from app.services.config_publisher import get_config_publisher
from common.logging import logger
from common.redis import RedisKeys
from common.storage import get_storage


router = APIRouter()


async def _migrate_model_file_if_needed(model: Model, db: AsyncSession) -> None:
    """
    如模型文件仍在临时存储（tmp/ 前缀），则迁移到正式路径 models/{model_id}/...。
    """
    if not model.model_path or not model.model_path.startswith("tmp/"):
        return
    
    storage = get_storage()
    temp_key = model.model_path
    data = storage.get_file(temp_key)
    if data is None:
        logger.error(f"模型文件不存在于临时存储: {temp_key}")
        return
    
    filename = temp_key.split("/")[-1]
    final_key = f"models/{model.id}/{filename}"
    
    try:
        storage.save_file(data, final_key, content_type=None)
        model.model_path = final_key
        await db.commit()
        storage.delete_file(temp_key)
        logger.info(f"模型文件已从临时存储迁移到正式路径: {final_key}")
    except Exception as e:
        logger.error(f"迁移模型文件到正式存储失败: {e}")


async def _write_model_to_redis(model: Model) -> None:
    """
    将模型配置写入 Redis，供引擎读取。
    """
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.model_config(model.id),
            json.dumps(
                {
                    "id": model.id,
                    "code": model.code,
                    "name": model.name,
                    "model_type": model.model_type,
                    "model_path": model.model_path,
                    "classes": list(model.classes or []),
                    "is_enabled": model.is_enabled,
                },
                ensure_ascii=False,
            ),
        )
    except Exception as e:
        logger.error(f"写入模型配置到 Redis 失败: {e}")


async def _publish_model_event(action: str, model: Model) -> None:
    """
    发布模型相关的配置变更事件到引擎。
    """
    config_publisher = get_config_publisher()
    payload = {
        "model_id": model.id,
        "code": model.code,
        "model_type": model.model_type,
        "model_path": model.model_path,
    }
    if action == "add":
        await config_publisher.publish_model_add(payload)
    elif action == "update":
        await config_publisher.publish_model_update(payload)
    elif action == "delete":
        await config_publisher.publish_model_delete(model.id)


@router.get("", summary="获取模型列表")
async def get_models(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取模型列表
    """
    query = select(Model)
    count_query = select(func.count(Model.id))
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Model.name.ilike(keyword_filter)) |
            (Model.code.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Model.name.ilike(keyword_filter)) |
            (Model.code.ilike(keyword_filter))
        )
    
    if is_enabled is not None:
        query = query.where(Model.is_enabled == is_enabled)
        count_query = count_query.where(Model.is_enabled == is_enabled)
    
    # 统计总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(Model.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    data = []
    for model in models:
        # 统计关联算法数量
        algo_count_result = await db.execute(
            select(func.count(Algorithm.id))
            .where(Algorithm.model_id == model.id)
        )
        algo_count = algo_count_result.scalar() or 0
        
        data.append({
            "id": model.id,
            "name": model.name,
            "code": model.code,
            "description": model.description,
            "model_type": model.model_type,
            "model_path": model.model_path,
            "version": model.version,
            "classes": model.classes,
            "gpu_memory_mb": model.gpu_memory_mb,
            "inference_ms": model.inference_ms,
            "input_width": model.input_width,
            "input_height": model.input_height,
            "is_enabled": model.is_enabled,
            "algorithm_count": algo_count,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat()
        })
    
    return page_response(data, page, page_size, total)


@router.get("/{model_id}", summary="获取模型详情")
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取模型详情
    """
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 统计关联算法数量
    algo_count_result = await db.execute(
        select(func.count(Algorithm.id))
        .where(Algorithm.model_id == model.id)
    )
    algo_count = algo_count_result.scalar() or 0
    
    return success_response({
        "id": model.id,
        "name": model.name,
        "code": model.code,
        "description": model.description,
        "model_type": model.model_type,
        "model_path": model.model_path,
        "version": model.version,
        "classes": model.classes,
        "gpu_memory_mb": model.gpu_memory_mb,
        "inference_ms": model.inference_ms,
        "input_width": model.input_width,
        "input_height": model.input_height,
        "is_enabled": model.is_enabled,
        "algorithm_count": algo_count,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat()
    })


@router.post("", summary="创建模型")
async def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    创建模型 (仅管理员)
    """
    # 检查编码是否重复
    existing = await db.execute(
        select(Model).where(Model.code == model_data.code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="模型编码已存在"
        )
    
    # 创建模型
    model = Model(
        id=generate_uuid(),
        name=model_data.name,
        code=model_data.code,
        description=model_data.description,
        model_type=model_data.model_type,
        model_path=model_data.model_path,
        version=model_data.version,
        classes=model_data.classes,
        gpu_memory_mb=model_data.gpu_memory_mb,
        inference_ms=model_data.inference_ms,
        input_width=model_data.input_width,
        input_height=model_data.input_height,
        is_enabled=model_data.is_enabled,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    db.add(model)
    await db.commit()
    # 无需 refresh：id 为 generate_uuid，后续仅用 model.id 等已赋值字段

    # 如有临时文件则迁移到正式路径
    await _migrate_model_file_if_needed(model, db)

    # 根据检测类别自动生成算法列表（每个类别一条算法能力，去重）
    raw_classes = model_data.classes or []
    classes = sorted({c for c in raw_classes if c and isinstance(c, str)})
    for cls in classes:
        code = f"{model.code}_{cls}".strip()
        name = f"检测-{cls}"
        algo = Algorithm(
            id=generate_uuid(),
            name=name,
            code=code,
            model_id=model.id,
            default_confidence=0.5,
            is_enabled=True,
            created_by=current_user.id,
            updated_by=current_user.id,
        )
        algo.target_classes = [cls]
        algo.alert_config = {
            "trigger_type": "instant",
            "duration_seconds": 0,
            "count_threshold": 0,
            "cooldown_seconds": 30,
            "alert_level": "warning",
        }
        db.add(algo)
    if classes:
        await db.commit()

    # 同步到 Redis 并通知引擎
    await _write_model_to_redis(model)
    await _publish_model_event("add", model)
    
    logger.info(f"模型已创建: {model.id} - {model.name}，已自动生成 {len(classes)} 条算法")
    
    return success_response({"id": model.id}, "创建成功")


@router.put("/{model_id}", summary="更新模型")
async def update_model(
    model_id: str,
    model_data: ModelUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    更新模型 (仅管理员)
    """
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 更新字段
    update_data = model_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "classes":
            model._classes = value
        else:
            setattr(model, field, value)
    
    model.updated_by = current_user.id
    
    await db.commit()

    # 如果本次更新中上传了新的模型文件（tmp/ 前缀），则迁移到正式路径
    await _migrate_model_file_if_needed(model, db)

    # 同步到 Redis 并通知引擎
    await _write_model_to_redis(model)
    await _publish_model_event("update", model)
    
    logger.info(f"模型已更新: {model_id}")
    
    return success_response(None, "更新成功")


@router.delete("/{model_id}", summary="删除模型")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    删除模型 (仅管理员)
    
    如果有关联算法，则无法删除
    """
    result = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模型不存在"
        )
    
    # 检查是否有关联算法
    algo_count_result = await db.execute(
        select(func.count(Algorithm.id))
        .where(Algorithm.model_id == model_id)
    )
    if (algo_count_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存在关联的算法，无法删除"
        )
    
    await db.delete(model)
    await db.commit()
    
    # 从 Redis 中删除模型配置
    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.model_config(model_id))
    except Exception as e:
        logger.error(f"从 Redis 删除模型配置失败: {e}")
    
    # 发布配置变更到引擎
    config_publisher = get_config_publisher()
    await config_publisher.publish_model_delete(model_id)
    
    logger.info(f"模型已删除: {model_id}")
    
    return success_response(None, "删除成功")
