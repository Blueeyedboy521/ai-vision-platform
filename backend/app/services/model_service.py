# -*- coding: utf-8 -*-
"""
模型相关业务逻辑：
- 模型列表 / 详情
- 模型创建 / 更新 / 删除
- 模型文件从 tmp 迁移到正式路径
- 写入 / 删除 Redis 模型配置并通知引擎
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis, write_model_to_redis
from app.models import Model, Algorithm, User
from app.models.base import generate_uuid
from app.schemas.model import ModelCreate, ModelUpdate
from app.services.config_publisher import get_config_publisher
from common.logging import logger
from common.redis import RedisKeys
from common.storage import get_storage


async def migrate_model_file_if_needed(model: Model, db: AsyncSession) -> None:
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


async def publish_model_event(action: str, model: Model) -> None:
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


async def list_models(
    db: AsyncSession,
    page: int,
    page_size: int,
    keyword: Optional[str],
    is_enabled: Optional[bool],
) -> Tuple[List[Dict[str, Any]], int]:
    query = select(Model)
    count_query = select(func.count(Model.id))

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Model.name.ilike(keyword_filter))
            | (Model.code.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Model.name.ilike(keyword_filter))
            | (Model.code.ilike(keyword_filter))
        )

    if is_enabled is not None:
        query = query.where(Model.is_enabled == is_enabled)
        count_query = count_query.where(Model.is_enabled == is_enabled)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Model.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    models = result.scalars().all()

    data: List[Dict[str, Any]] = []
    for model in models:
        algo_count_result = await db.execute(
            select(func.count(Algorithm.id)).where(Algorithm.model_id == model.id)
        )
        algo_count = algo_count_result.scalar() or 0

        data.append(
            {
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
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            }
        )

    return data, total


async def get_model_detail(db: AsyncSession, model_id: str) -> Optional[Dict[str, Any]]:
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        return None

    algo_count_result = await db.execute(
        select(func.count(Algorithm.id)).where(Algorithm.model_id == model.id)
    )
    algo_count = algo_count_result.scalar() or 0

    return {
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
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


async def create_model_with_algorithms(
    db: AsyncSession,
    model_data: ModelCreate,
    current_user: User,
) -> Tuple[str, int]:
    existing = await db.execute(select(Model).where(Model.code == model_data.code))
    if existing.scalar_one_or_none():
        raise ValueError("MODEL_CODE_EXISTS")

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
        updated_by=current_user.id,
    )

    db.add(model)
    await db.commit()

    await migrate_model_file_if_needed(model, db)

    import re

    def _normalize_code_part(s: str) -> str:
        t = (s or "").strip().lower()
        t = re.sub(r"[^a-z0-9]+", "_", t)
        t = re.sub(r"_+", "_", t).strip("_")
        return t

    raw_classes = model_data.classes or []
    classes = sorted({c for c in raw_classes if c and isinstance(c, str)})
    used_codes: set[str] = set()
    created_algos = 0
    for idx, cls in enumerate(classes):
        code_part = _normalize_code_part(cls) or f"class_{idx+1}"
        base_code = f"{(model.code or '').strip()}_{code_part}".strip("_")
        base_code = base_code[:50]
        code = base_code
        suffix = 2
        while code in used_codes:
            suffix_str = f"_{suffix}"
            code = (base_code[: max(0, 50 - len(suffix_str))] + suffix_str)[:50]
            suffix += 1
        used_codes.add(code)
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
        created_algos += 1
    if classes:
        await db.commit()

    await write_model_to_redis(model.id, db)
    await publish_model_event("add", model)

    logger.info(f"模型已创建: {model.id} - {model.name}，已自动生成 {created_algos} 条算法")
    return model.id, created_algos


async def update_model_data(
    db: AsyncSession,
    model_id: str,
    model_data: ModelUpdate,
    current_user: User,
) -> bool:
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        return False

    update_data = model_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "classes":
            model._classes = value
        else:
            setattr(model, field, value)

    model.updated_by = current_user.id
    await db.commit()

    await migrate_model_file_if_needed(model, db)
    await write_model_to_redis(model.id, db)
    await publish_model_event("update", model)
    logger.info(f"模型已更新: {model_id}")
    return True


async def delete_model_data(
    db: AsyncSession,
    model_id: str,
) -> Tuple[bool, str]:
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        return False, "NOT_FOUND"

    algo_count_result = await db.execute(
        select(func.count(Algorithm.id)).where(Algorithm.model_id == model_id)
    )
    if (algo_count_result.scalar() or 0) > 0:
        return False, "HAS_ALGORITHMS"

    await db.delete(model)
    await db.commit()

    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.model_config(model_id))
    except Exception as e:
        logger.error(f"从 Redis 删除模型配置失败: {e}")

    config_publisher = get_config_publisher()
    await config_publisher.publish_model_delete(model_id)
    logger.info(f"模型已删除: {model_id}")
    return True, ""

