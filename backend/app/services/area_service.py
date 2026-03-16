# -*- coding: utf-8 -*-
"""
区域相关业务逻辑：
- 区域列表 / 树 / 详情
- 区域创建 / 更新 / 删除
- 维护层级冗余字段与相关摄像头区域路径缓存
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import delete_camera_area_paths_for_cameras
from app.models import Area, Camera, User
from app.models.base import generate_uuid
from common.logging import logger


async def _refresh_subtree_hierarchy(db: AsyncSession, root_id: str) -> None:
    """
    当某个区域的 name/parent_id 变化时，需要级联更新其子树的 level/hierarchy_path。
    一次性加载全量 areas，构建 children 映射后，从 root_id 向下 DFS 更新。
    """
    result = await db.execute(select(Area))
    areas = result.scalars().all()
    area_by_id: Dict[str, Area] = {a.id: a for a in areas}
    children: Dict[Optional[str], List[Area]] = {}
    for a in areas:
        children.setdefault(a.parent_id, []).append(a)

    root = area_by_id.get(root_id)
    if root is None:
        return

    def dfs(node: Area) -> None:
        for ch in children.get(node.id, []):
            ch.compute_hierarchy(node)
            dfs(ch)

    dfs(root)


async def _get_subtree_area_ids(db: AsyncSession, root_id: str) -> List[str]:
    """返回以 root_id 为根的子树（含自身）的所有区域 id 列表。"""
    result = await db.execute(select(Area))
    areas = result.scalars().all()
    area_by_id: Dict[str, Area] = {a.id: a for a in areas}
    children: Dict[Optional[str], List[Area]] = {}
    for a in areas:
        children.setdefault(a.parent_id, []).append(a)
    root = area_by_id.get(root_id)
    if root is None:
        return []
    ids: List[str] = []

    def collect(node: Area) -> None:
        ids.append(node.id)
        for ch in children.get(node.id, []):
            collect(ch)

    collect(root)
    return ids


async def list_areas(db: AsyncSession) -> List[Dict]:
    """
    获取区域列表（平铺），带摄像头数量。
    """
    result = await db.execute(
        select(Area).order_by(Area.sort_order, Area.created_at)
    )
    areas = result.scalars().all()

    data: List[Dict] = []
    for area in areas:
        camera_count_result = await db.execute(
            select(func.count(Camera.id)).where(Camera.area_id == area.id)
        )
        camera_count = camera_count_result.scalar() or 0

        data.append(
            {
                "id": area.id,
                "name": area.name,
                "code": area.code,
                "description": area.description,
                "parent_id": area.parent_id,
                "sort_order": area.sort_order,
                "camera_count": camera_count,
                "created_at": area.created_at.isoformat(),
                "updated_at": area.updated_at.isoformat(),
            }
        )
    return data


async def get_area_tree_data(db: AsyncSession) -> List[Dict]:
    """
    获取区域树形结构数据。
    """
    result = await db.execute(
        select(Area).order_by(Area.sort_order, Area.created_at)
    )
    areas = result.scalars().all()

    area_map: Dict[str, Dict] = {}
    for area in areas:
        camera_count_result = await db.execute(
            select(func.count(Camera.id)).where(Camera.area_id == area.id)
        )
        camera_count = camera_count_result.scalar() or 0

        area_map[area.id] = {
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "description": area.description,
            "parent_id": area.parent_id,
            "sort_order": area.sort_order,
            "camera_count": camera_count,
            "children": [],
        }

    tree: List[Dict] = []
    for area_id, area_data in area_map.items():
        parent_id = area_data["parent_id"]
        if parent_id and parent_id in area_map:
            area_map[parent_id]["children"].append(area_data)
        else:
            tree.append(area_data)

    return tree


async def get_area_detail(db: AsyncSession, area_id: str) -> Optional[Dict]:
    """
    获取单个区域详情。
    """
    result = await db.execute(select(Area).where(Area.id == area_id))
    area = result.scalar_one_or_none()
    if area is None:
        return None

    camera_count_result = await db.execute(
        select(func.count(Camera.id)).where(Camera.area_id == area.id)
    )
    camera_count = camera_count_result.scalar() or 0

    return {
        "id": area.id,
        "name": area.name,
        "code": area.code,
        "description": area.description,
        "parent_id": area.parent_id,
        "sort_order": area.sort_order,
        "camera_count": camera_count,
        "created_at": area.created_at.isoformat(),
        "updated_at": area.updated_at.isoformat(),
    }


async def create_area_record(
    db: AsyncSession,
    area_data,
    current_user: User,
) -> str:
    """
    创建区域，返回区域 ID。
    业务校验：
    - code 不重复
    - parent 存在
    - 维护层级字段
    """
    if area_data.code:
        existing = await db.execute(
            select(Area).where(Area.code == area_data.code)
        )
        if existing.scalar_one_or_none():
            raise ValueError("AREA_CODE_EXISTS")

    parent = None
    if area_data.parent_id:
        parent_result = await db.execute(
            select(Area).where(Area.id == area_data.parent_id)
        )
        parent = parent_result.scalar_one_or_none()
        if parent is None:
            raise ValueError("PARENT_NOT_FOUND")

    area = Area(
        id=generate_uuid(),
        name=area_data.name,
        code=area_data.code,
        description=area_data.description,
        parent_id=area_data.parent_id,
        sort_order=area_data.sort_order,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    area.compute_hierarchy(parent)

    db.add(area)
    await db.commit()

    logger.info(f"区域已创建: {area.id} - {area.name}")
    return area.id


async def update_area_record(
    db: AsyncSession,
    area_id: str,
    area_data,
    current_user: User,
) -> Tuple[bool, Optional[str]]:
    """
    更新区域。
    返回 (ok, error_code)：
    - ok=False, error_code="NOT_FOUND" 区域不存在
    - ok=False, error_code="SELF_PARENT" 父区域是自己
    - 其它错误抛异常
    """
    result = await db.execute(select(Area).where(Area.id == area_id))
    area = result.scalar_one_or_none()
    if area is None:
        return False, "NOT_FOUND"

    if area_data.parent_id and area_data.parent_id == area_id:
        return False, "SELF_PARENT"

    update_data = area_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(area, field, value)

    area.updated_by = current_user.id

    name_changed = "name" in update_data
    parent_changed = "parent_id" in update_data

    if name_changed or parent_changed:
        parent = None
        if area.parent_id:
            parent_result = await db.execute(
                select(Area).where(Area.id == area.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
        area.compute_hierarchy(parent)
        await _refresh_subtree_hierarchy(db, area.id)

    await db.commit()

    if name_changed or parent_changed:
        subtree_ids = await _get_subtree_area_ids(db, area_id)
        if subtree_ids:
            cam_result = await db.execute(
                select(Camera.id).where(Camera.area_id.in_(subtree_ids))
            )
            camera_ids = [r[0] for r in cam_result.all()]
            if camera_ids:
                delete_camera_area_paths_for_cameras(camera_ids)

    logger.info(f"区域已更新: {area_id}")
    return True, None


async def delete_area_record(
    db: AsyncSession,
    area_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    删除区域。
    返回 (ok, error_code)：
    - ok=False, "NOT_FOUND" 区域不存在
    - ok=False, "HAS_CHILDREN" 有子区域
    - ok=False, "HAS_CAMERAS" 有摄像头
    """
    result = await db.execute(select(Area).where(Area.id == area_id))
    area = result.scalar_one_or_none()
    if area is None:
        return False, "NOT_FOUND"

    child_count_result = await db.execute(
        select(func.count(Area.id)).where(Area.parent_id == area_id)
    )
    if (child_count_result.scalar() or 0) > 0:
        return False, "HAS_CHILDREN"

    camera_count_result = await db.execute(
        select(func.count(Camera.id)).where(Camera.area_id == area_id)
    )
    if (camera_count_result.scalar() or 0) > 0:
        return False, "HAS_CAMERAS"

    await db.delete(area)
    await db.commit()

    logger.info(f"区域已删除: {area_id}")
    return True, None

