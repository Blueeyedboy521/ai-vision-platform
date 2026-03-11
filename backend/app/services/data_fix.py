# -*- coding: utf-8 -*-
"""
启动期数据修复（幂等）

用于补齐：
- areas.level / areas.hierarchy_path
- alarms.camera_name / alarms.algorithm_name / alarms.area_name(层级路径)

注意：
- 该修复可重复运行，适合作为启动期一次性补丁；
- 若数据库缺少相关字段会捕获异常并记录日志，不影响应用启动（但你仍应执行 DDL）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Area
from common.logging import logger


async def fix_area_hierarchy(session: AsyncSession) -> int:
    """
    计算并回填所有 Area 的 level/hierarchy_path。
    返回更新的记录数（估算）。
    """
    result = await session.execute(select(Area))
    areas: List[Area] = result.scalars().all()
    if not areas:
        return 0

    by_id: Dict[str, Area] = {a.id: a for a in areas}
    children: Dict[Optional[str], List[Area]] = {}
    for a in areas:
        children.setdefault(a.parent_id, []).append(a)

    updated = 0

    def dfs(node: Area) -> None:
        nonlocal updated
        for ch in children.get(node.id, []):
            before_level = getattr(ch, "level", None)
            before_path = getattr(ch, "hierarchy_path", None)
            ch.compute_hierarchy(node)
            if before_level != ch.level or before_path != ch.hierarchy_path:
                updated += 1
            dfs(ch)

    # roots
    roots = children.get(None, [])
    for r in roots:
        before_level = getattr(r, "level", None)
        before_path = getattr(r, "hierarchy_path", None)
        r.compute_hierarchy(None)
        if before_level != r.level or before_path != r.hierarchy_path:
            updated += 1
        dfs(r)

    await session.commit()
    return updated


async def fix_alarm_denormalized_fields(session: AsyncSession) -> None:
    """
    批量回填 alarms 的冗余字段。
    使用 SQL JOIN 更新（MySQL），失败则仅记录日志（不影响启动）。
    """
    # 1) camera_name
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                SET a.camera_name = c.name
                WHERE (a.camera_name IS NULL OR a.camera_name = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.camera_name 失败(可忽略): {e}")

    # 2) algorithm_name
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN algorithms ag ON a.algorithm_id = ag.id
                SET a.algorithm_name = ag.name
                WHERE (a.algorithm_name IS NULL OR a.algorithm_name = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.algorithm_name 失败(可忽略): {e}")

    # 3) area_id（冗余存储）
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                SET a.area_id = c.area_id
                WHERE (a.area_id IS NULL OR a.area_id = '')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.area_id 失败(可忽略): {e}")

    # 4) area_name（层级路径）
    try:
        await session.execute(
            text(
                """
                UPDATE alarms a
                LEFT JOIN cameras c ON a.camera_id = c.id
                LEFT JOIN areas ar ON c.area_id = ar.id
                SET a.area_name = COALESCE(ar.hierarchy_path, ar.name)
                WHERE (a.area_name IS NULL OR a.area_name = '' OR a.area_name NOT LIKE '%/%')
                """
            )
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.warning(f"[data_fix] 回填 alarms.area_name 失败(可忽略): {e}")


async def run_startup_data_fix(session: AsyncSession) -> None:
    """
    启动期数据修复入口（幂等）。
    """
    try:
        updated = await fix_area_hierarchy(session)
        if updated:
            logger.info(f"[data_fix] areas 层级字段已回填/更新: {updated} 条")
    except Exception as e:
        logger.warning(f"[data_fix] 回填 areas 层级字段失败(可忽略): {e}")

    try:
        await fix_alarm_denormalized_fields(session)
        logger.info("[data_fix] alarms 冗余字段回填完成")
    except Exception as e:
        logger.warning(f"[data_fix] 回填 alarms 冗余字段失败(可忽略): {e}")

