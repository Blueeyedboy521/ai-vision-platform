# -*- coding: utf-8 -*-
"""
算法及摄像头-算法配置业务逻辑：
- 算法列表 / 详情 / CRUD
- 摄像头算法配置列表 / 创建 / 更新 / 删除（含 Redis 写入）
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import json

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis, write_model_to_redis, write_algorithm_to_redis, delete_algorithm_from_redis
from app.models import Algorithm, Model, CameraAlgorithm, Camera, User
from app.models.base import generate_uuid
from app.schemas.algorithm import AlgorithmCreate, AlgorithmUpdate, CameraAlgorithmCreate, CameraAlgorithmUpdate
from app.services.config_publisher import get_config_publisher
from app.schemas.common import page_response, success_response
from common.redis import RedisKeys
from common.logging import logger


async def list_algorithms(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    model_id: Optional[str],
    keyword: Optional[str],
    is_enabled: Optional[bool],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取算法列表及总数。
    """
    query = select(Algorithm).options(selectinload(Algorithm.model))
    count_query = select(func.count(Algorithm.id))

    if model_id:
        query = query.where(Algorithm.model_id == model_id)
        count_query = count_query.where(Algorithm.model_id == model_id)

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Algorithm.name.ilike(keyword_filter))
            | (Algorithm.code.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Algorithm.name.ilike(keyword_filter))
            | (Algorithm.code.ilike(keyword_filter))
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

    data: List[Dict[str, Any]] = []
    for algo in algorithms:
        cam_count_result = await db.execute(
            select(func.count(CameraAlgorithm.id)).where(
                CameraAlgorithm.algorithm_id == algo.id
            )
        )
        cam_count = cam_count_result.scalar() or 0

        data.append(
            {
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
                "updated_at": algo.updated_at.isoformat(),
            }
        )

    return data, total


async def get_algorithm_detail(
    db: AsyncSession,
    algorithm_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取单个算法详情。
    """
    result = await db.execute(
        select(Algorithm)
        .options(selectinload(Algorithm.model))
        .where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    if algo is None:
        return None

    cam_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id)).where(
            CameraAlgorithm.algorithm_id == algo.id
        )
    )
    cam_count = cam_count_result.scalar() or 0

    return {
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
        "updated_at": algo.updated_at.isoformat(),
    }


async def create_algorithm_record(
    db: AsyncSession,
    algo_data: AlgorithmCreate,
    current_user: User,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    创建算法。
    返回 (ok, error_code, algorithm_id)
    error_code:
    - "ALGO_CODE_EXISTS"
    - "MODEL_NOT_FOUND"
    """
    existing = await db.execute(
        select(Algorithm).where(
            Algorithm.model_id == algo_data.model_id,
            Algorithm.code == algo_data.code,
        )
    )
    if existing.scalar_one_or_none():
        return False, "ALGO_CODE_EXISTS", None

    model_result = await db.execute(
        select(Model).where(Model.id == algo_data.model_id)
    )
    if model_result.scalar_one_or_none() is None:
        return False, "MODEL_NOT_FOUND", None

    algo = Algorithm(
        id=generate_uuid(),
        name=algo_data.name,
        code=algo_data.code,
        description=algo_data.description,
        model_id=algo_data.model_id,
        default_confidence=algo_data.default_confidence,
        is_enabled=algo_data.is_enabled,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    algo.target_classes = algo_data.target_classes
    algo.alert_config = algo_data.alert_config

    db.add(algo)
    await db.commit()

    await write_algorithm_to_redis(algo)

    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_add(
        {
            "algorithm_id": algo.id,
            "code": algo.code,
            "model_id": algo.model_id,
        }
    )

    await write_model_to_redis(algo.model_id, db)
    logger.info(f"算法已创建: {algo.id} - {algo.name}")

    return True, None, algo.id


async def update_algorithm_record(
    db: AsyncSession,
    algorithm_id: str,
    algo_data: AlgorithmUpdate,
    current_user: User,
) -> Tuple[bool, Optional[str]]:
    """
    更新算法。
    返回 (ok, error_code)
    - "NOT_FOUND"
    - "ALGO_CODE_EXISTS"
    """
    result = await db.execute(
        select(Algorithm).where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    if algo is None:
        return False, "NOT_FOUND"

    update_data = algo_data.model_dump(exclude_unset=True)

    new_code = update_data.get("code")
    if new_code and new_code != algo.code:
        existing = await db.execute(
            select(Algorithm).where(
                Algorithm.code == new_code, Algorithm.id != algorithm_id
            )
        )
        if existing.scalar_one_or_none():
            return False, "ALGO_CODE_EXISTS"

    for field, value in update_data.items():
        if field == "target_classes":
            algo.target_classes = value
        elif field == "alert_config":
            algo.alert_config = value
        else:
            setattr(algo, field, value)

    algo.updated_by = current_user.id
    await db.commit()

    await write_algorithm_to_redis(algo)

    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_update(
        {
            "algorithm_id": algo.id,
            "code": algo.code,
            "model_id": algo.model_id,
        }
    )

    await write_model_to_redis(algo.model_id, db)
    logger.info(f"算法已更新: {algorithm_id}")
    return True, None


async def delete_algorithm_record(
    db: AsyncSession,
    algorithm_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    删除算法。
    返回 (ok, error_code)
    - "NOT_FOUND"
    - "HAS_CAMERA_CONFIGS"
    """
    result = await db.execute(
        select(Algorithm).where(Algorithm.id == algorithm_id)
    )
    algo = result.scalar_one_or_none()
    if algo is None:
        return False, "NOT_FOUND"

    cam_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id)).where(
            CameraAlgorithm.algorithm_id == algorithm_id
        )
    )
    if (cam_count_result.scalar() or 0) > 0:
        return False, "HAS_CAMERA_CONFIGS"

    model_id = algo.model_id
    await db.delete(algo)
    await db.commit()

    await delete_algorithm_from_redis(algorithm_id)

    config_publisher = get_config_publisher()
    await config_publisher.publish_algorithm_delete(algorithm_id)

    await write_model_to_redis(model_id, db)
    logger.info(f"算法已删除: {algorithm_id}")
    return True, None


async def list_camera_algorithm_configs(
    db: AsyncSession,
    camera_id: str,
) -> List[Dict[str, Any]]:
    """
    获取摄像头算法配置列表。
    """
    result = await db.execute(
        select(CameraAlgorithm)
        .options(
            selectinload(CameraAlgorithm.algorithm),
            selectinload(CameraAlgorithm.camera),
        )
        .where(CameraAlgorithm.camera_id == camera_id)
    )
    configs = result.scalars().all()

    data: List[Dict[str, Any]] = []
    for config in configs:
        data.append(
            {
                "id": config.id,
                "camera_id": config.camera_id,
                "camera_name": config.camera.name if config.camera else None,
                "algorithm_id": config.algorithm_id,
                "algorithm_name": config.algorithm.name
                if config.algorithm
                else None,
                "model_id": config.model_id,
                "confidence": config.confidence,
                "effective_confidence": config.get_effective_confidence(),
                "alert_config": config.alert_config,
                "effective_alert_config": config.get_effective_alert_config(),
                "regions": config.regions,
                "inference_interval_sec": getattr(
                    config, "inference_interval_sec", 5
                ),
                "alarm_interval_sec": getattr(config, "alarm_interval_sec", 30),
                "is_enabled": config.is_enabled,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat(),
            }
        )

    return data


async def create_camera_algorithm_config_record(
    db: AsyncSession,
    *,
    camera_id: str,
    config_data: CameraAlgorithmCreate,
    current_user: User,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    创建摄像头算法配置。
    返回 (ok, error_code, config_id)
    - "CAMERA_NOT_FOUND"
    - "ALREADY_EXISTS"
    """
    cam_result = await db.execute(select(Camera).where(Camera.id == camera_id))
    if cam_result.scalar_one_or_none() is None:
        return False, "CAMERA_NOT_FOUND", None

    existing = await db.execute(
        select(CameraAlgorithm).where(
            CameraAlgorithm.camera_id == camera_id,
            CameraAlgorithm.algorithm_id == config_data.algorithm_id,
        )
    )
    if existing.scalar_one_or_none():
        return False, "ALREADY_EXISTS", None

    config = CameraAlgorithm(
        id=generate_uuid(),
        camera_id=camera_id,
        algorithm_id=config_data.algorithm_id,
        model_id=config_data.model_id,
        confidence=config_data.confidence,
        is_enabled=config_data.is_enabled,
        inference_interval_sec=getattr(config_data, "inference_interval_sec", None)
        or 5,
        alarm_interval_sec=getattr(config_data, "alarm_interval_sec", None)
        or 30,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    config.alert_config = config_data.alert_config
    config.regions = config_data.regions

    db.add(config)
    await db.commit()

    effective_confidence = (
        config.confidence if config.confidence is not None else 0.5
    )
    effective_alert_config = config.alert_config or {}
    regions = config.regions

    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.camera_algorithm_config(
                camera_id, config_data.algorithm_id
            ),
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
    config_publisher_task_payload = {
        "confidence": effective_confidence,
        "regions": regions,
        "alert_config": effective_alert_config,
    }
    await config_publisher.publish_camera_algorithm_add(
        camera_id, config_data.algorithm_id, config_publisher_task_payload
    )

    logger.info(
        f"摄像头算法配置已添加: {camera_id} - {config_data.algorithm_id}"
    )

    return True, None, config.id


async def update_camera_algorithm_config_record(
    db: AsyncSession,
    *,
    camera_id: str,
    config_id: str,
    config_data: CameraAlgorithmUpdate,
    current_user: User,
) -> Tuple[bool, Optional[str]]:
    """
    更新摄像头算法配置。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(
        select(CameraAlgorithm)
        .options(
            selectinload(CameraAlgorithm.algorithm),
            selectinload(CameraAlgorithm.camera),
        )
        .where(
            CameraAlgorithm.id == config_id,
            CameraAlgorithm.camera_id == camera_id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        return False, "NOT_FOUND"

    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "regions":
            config.regions = value
        else:
            setattr(config, field, value)

    config.updated_by = current_user.id
    await db.commit()

    effective_confidence = (
        config.confidence if config.confidence is not None else 0.5
    )
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
                    "inference_interval_sec": getattr(
                        config, "inference_interval_sec", 5
                    ),
                    "alarm_interval_sec": getattr(
                        config, "alarm_interval_sec", 30
                    ),
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
    return True, None


async def delete_camera_algorithm_config_record(
    db: AsyncSession,
    *,
    camera_id: str,
    config_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    删除摄像头算法配置。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(
        select(CameraAlgorithm).where(
            CameraAlgorithm.id == config_id,
            CameraAlgorithm.camera_id == camera_id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        return False, "NOT_FOUND"

    algorithm_id = config.algorithm_id

    await db.delete(config)
    await db.commit()

    try:
        redis = get_redis()
        await redis.client.delete(
            RedisKeys.camera_algorithm_config(camera_id, algorithm_id)
        )
    except Exception as e:
        logger.error(f"从 Redis 删除摄像头算法配置失败: {e}")

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_algorithm_delete(
        camera_id, algorithm_id
    )

    logger.info(f"摄像头算法配置已删除: {camera_id} - {algorithm_id}")
    return True, None

