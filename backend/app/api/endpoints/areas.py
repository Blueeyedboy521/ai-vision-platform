# -*- coding: utf-8 -*-
"""
区域 API

提供区域 CRUD 和树形结构接口
"""
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import delete_camera_area_paths_for_cameras
from app.api.deps import get_current_user
from app.models import User, Area, Camera
from app.models.base import generate_uuid
from app.schemas.area import (
    AreaCreate,
    AreaUpdate,
    AreaResponse,
    AreaTreeNode,
    AreaTreeResponse,
    AreaListResponse
)
from app.schemas.common import success_response
from common.logging import logger


router = APIRouter()

async def _refresh_subtree_hierarchy(db: AsyncSession, root_id: str) -> None:
    """
    当某个区域的 name/parent_id 变化时，需要级联更新其子树的 level/hierarchy_path。
    这里通过一次性加载全量 areas，构建 children 映射后，从 root_id 向下 DFS 更新。
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

    # root 自己已经 compute_hierarchy 过，这里只更新子树
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


@router.get("", summary="获取区域列表")
async def get_areas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取区域列表 (平铺)
    """
    result = await db.execute(
        select(Area).order_by(Area.sort_order, Area.created_at)
    )
    areas = result.scalars().all()
    
    data = []
    for area in areas:
        # 统计摄像头数量
        camera_count_result = await db.execute(
            select(func.count(Camera.id)).where(Camera.area_id == area.id)
        )
        camera_count = camera_count_result.scalar() or 0
        
        data.append({
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "description": area.description,
            "parent_id": area.parent_id,
            "sort_order": area.sort_order,
            "camera_count": camera_count,
            "created_at": area.created_at.isoformat(),
            "updated_at": area.updated_at.isoformat()
        })
    
    return success_response(data)


@router.get("/tree", summary="获取区域树")
async def get_area_tree(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取区域树形结构
    """
    result = await db.execute(
        select(Area).order_by(Area.sort_order, Area.created_at)
    )
    areas = result.scalars().all()
    
    # 构建ID到区域的映射
    area_map = {}
    for area in areas:
        # 统计摄像头数量
        camera_count_result = await db.execute(
            select(func.count(Camera.id)).where(Camera.area_id == area.id)
        )
        camera_count = camera_count_result.scalar() or 0
        
        area_map[area.id] = {
            "id": area.id,
            "name": area.name,
            "code": area.code,
            "parent_id": area.parent_id,
            "sort_order": area.sort_order,
            "camera_count": camera_count,
            "children": []
        }
    
    # 构建树形结构
    tree = []
    for area_id, area_data in area_map.items():
        parent_id = area_data["parent_id"]
        if parent_id and parent_id in area_map:
            area_map[parent_id]["children"].append(area_data)
        else:
            tree.append(area_data)
    
    return success_response(tree)


@router.get("/{area_id}", summary="获取区域详情")
async def get_area(
    area_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取区域详情
    """
    result = await db.execute(
        select(Area).where(Area.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    
    # 统计摄像头数量
    camera_count_result = await db.execute(
        select(func.count(Camera.id)).where(Camera.area_id == area.id)
    )
    camera_count = camera_count_result.scalar() or 0
    
    return success_response({
        "id": area.id,
        "name": area.name,
        "code": area.code,
        "description": area.description,
        "parent_id": area.parent_id,
        "sort_order": area.sort_order,
        "camera_count": camera_count,
        "created_at": area.created_at.isoformat(),
        "updated_at": area.updated_at.isoformat()
    })


@router.post("", summary="创建区域")
async def create_area(
    area_data: AreaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建区域
    """
    # 检查编码是否重复
    if area_data.code:
        existing = await db.execute(
            select(Area).where(Area.code == area_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域编码已存在"
            )
    
    # 检查父区域是否存在
    if area_data.parent_id:
        parent_result = await db.execute(
            select(Area).where(Area.id == area_data.parent_id)
        )
        if parent_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父区域不存在"
            )
    
    # 创建区域
    area = Area(
        id=generate_uuid(),
        name=area_data.name,
        code=area_data.code,
        description=area_data.description,
        parent_id=area_data.parent_id,
        sort_order=area_data.sort_order,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    # 计算层级冗余字段
    parent = None
    if area_data.parent_id:
        parent_result = await db.execute(select(Area).where(Area.id == area_data.parent_id))
        parent = parent_result.scalar_one_or_none()
    area.compute_hierarchy(parent)
    
    db.add(area)
    await db.commit()
    # 无需 refresh：id 为 generate_uuid，返回仅用 id

    logger.info(f"区域已创建: {area.id} - {area.name}")
    
    return success_response({"id": area.id}, "创建成功")


@router.put("/{area_id}", summary="更新区域")
async def update_area(
    area_id: str,
    area_data: AreaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新区域
    """
    result = await db.execute(
        select(Area).where(Area.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    
    # 防止循环引用
    if area_data.parent_id and area_data.parent_id == area_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="父区域不能是自己"
        )
    
    # 更新字段
    update_data = area_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(area, field, value)
    
    area.updated_by = current_user.id

    # 若 name/parent_id 发生变化，重新计算自身层级字段，并级联更新子树
    if "name" in update_data or "parent_id" in update_data:
        parent = None
        if area.parent_id:
            parent_result = await db.execute(select(Area).where(Area.id == area.parent_id))
            parent = parent_result.scalar_one_or_none()
        area.compute_hierarchy(parent)
        await _refresh_subtree_hierarchy(db, area.id)
    await db.commit()

    # 区域树变更时，使该节点及子树下所有摄像头的区域路径缓存失效
    if "name" in update_data or "parent_id" in update_data:
        subtree_ids = await _get_subtree_area_ids(db, area_id)
        if subtree_ids:
            cam_result = await db.execute(
                select(Camera.id).where(Camera.area_id.in_(subtree_ids))
            )
            camera_ids = [r[0] for r in cam_result.all()]
            if camera_ids:
                delete_camera_area_paths_for_cameras(camera_ids)
    
    logger.info(f"区域已更新: {area_id}")
    
    return success_response(None, "更新成功")


@router.delete("/{area_id}", summary="删除区域")
async def delete_area(
    area_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除区域
    
    如果有子区域或摄像头，则无法删除
    """
    result = await db.execute(
        select(Area).where(Area.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在"
        )
    
    # 检查是否有子区域
    child_count_result = await db.execute(
        select(func.count(Area.id)).where(Area.parent_id == area_id)
    )
    if (child_count_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存在子区域，无法删除"
        )
    
    # 检查是否有摄像头
    camera_count_result = await db.execute(
        select(func.count(Camera.id)).where(Camera.area_id == area_id)
    )
    if (camera_count_result.scalar() or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="存在关联的摄像头，无法删除"
        )
    
    await db.delete(area)
    await db.commit()
    
    logger.info(f"区域已删除: {area_id}")
    
    return success_response(None, "删除成功")
