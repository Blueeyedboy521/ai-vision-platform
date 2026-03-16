# -*- coding: utf-8 -*-
"""
区域 API Controller

- 只负责路由、参数与权限校验
- 具体业务逻辑委托给 area_service
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.schemas.area import AreaCreate, AreaUpdate
from app.schemas.common import success_response
from app.services.area_service import (
    list_areas,
    get_area_tree_data,
    get_area_detail,
    create_area_record,
    update_area_record,
    delete_area_record,
)


router = APIRouter()


@router.get("", summary="获取区域列表")
async def get_areas_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取区域列表 (平铺)
    """
    data = await list_areas(db)
    return success_response(data)


@router.get("/tree", summary="获取区域树")
async def get_area_tree_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取区域树形结构
    """
    tree = await get_area_tree_data(db)
    return success_response(tree)


@router.get("/{area_id}", summary="获取区域详情")
async def get_area_api(
    area_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取区域详情
    """
    detail = await get_area_detail(db, area_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="区域不存在",
        )
    return success_response(detail)


@router.post("", summary="创建区域")
async def create_area_api(
    area_data: AreaCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建区域
    """
    try:
        area_id = await create_area_record(db, area_data, current_user)
    except ValueError as e:
        if str(e) == "AREA_CODE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域编码已存在",
            )
        if str(e) == "PARENT_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父区域不存在",
            )
        raise

    return success_response({"id": area_id}, "创建成功")


@router.put("/{area_id}", summary="更新区域")
async def update_area_api(
    area_id: str,
    area_data: AreaUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新区域
    """
    ok, reason = await update_area_record(db, area_id, area_data, current_user)
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="区域不存在",
            )
        if reason == "SELF_PARENT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父区域不能是自己",
            )
    return success_response(None, "更新成功")


@router.delete("/{area_id}", summary="删除区域")
async def delete_area_api(
    area_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除区域

    如果有子区域或摄像头，则无法删除
    """
    ok, reason = await delete_area_record(db, area_id)
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="区域不存在",
            )
        if reason == "HAS_CHILDREN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="存在子区域，无法删除",
            )
        if reason == "HAS_CAMERAS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="存在关联的摄像头，无法删除",
            )
    return success_response(None, "删除成功")

