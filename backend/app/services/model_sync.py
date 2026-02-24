# -*- coding: utf-8 -*-
"""
模型与算法同步服务

保证模型主表的检测类别（classes）与子表算法列表的 target_classes 一致
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Model, Algorithm
from common.logging import logger


async def sync_model_classes_from_algorithms(db: AsyncSession, model_id: str) -> None:
    """
    根据该模型下所有算法的 target_classes 汇总，更新模型主表的 classes 字段。
    保证模型.classes = 所有算法 target_classes 的并集（去重排序）。
    """
    result = await db.execute(
        select(Algorithm).where(Algorithm.model_id == model_id)
    )
    algos = result.scalars().all()
    all_classes = set()
    for a in algos:
        if a.target_classes:
            all_classes.update(a.target_classes)
    model_result = await db.execute(select(Model).where(Model.id == model_id))
    model = model_result.scalar_one_or_none()
    if model is not None:
        model.classes = sorted(all_classes)
        await db.commit()
        logger.info(f"已同步模型 {model_id} 的检测类别: {model.classes}")
