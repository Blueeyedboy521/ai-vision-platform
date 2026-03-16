# -*- coding: utf-8 -*-
"""
算法 API Controller

- 负责路由、权限和参数校验
- 业务逻辑委托给 algorithm_service
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_admin
from app.core.database import get_db
from app.models import User
from app.schemas.algorithm import (
    AlgorithmCreate,
    AlgorithmUpdate,
    CameraAlgorithmCreate,
    CameraAlgorithmUpdate,
)
from app.schemas.common import success_response, page_response
from app.services.algorithm_service import (
    list_algorithms,
    get_algorithm_detail,
    create_algorithm_record,
    update_algorithm_record,
    delete_algorithm_record,
    list_camera_algorithm_configs,
    create_camera_algorithm_config_record,
    update_camera_algorithm_config_record,
    delete_camera_algorithm_config_record,
)


router = APIRouter()


@router.get("", summary="获取算法列表")
async def get_algorithms_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_id: Optional[str] = Query(None, description="模型ID"),
    keyword: Optional[str] = Query(None, description="关键词"),
    is_enabled: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取算法列表
    """
    data, total = await list_algorithms(
        db,
        page=page,
        page_size=page_size,
        model_id=model_id,
        keyword=keyword,
        is_enabled=is_enabled,
    )
    return page_response(data, page, page_size, total)


@router.get("/{algorithm_id}", summary="获取算法详情")
async def get_algorithm_api(
    algorithm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取算法详情
    """
    detail = await get_algorithm_detail(db, algorithm_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="算法不存在",
        )
    return success_response(detail)


@router.post("", summary="创建算法")
async def create_algorithm_api(
    algo_data: AlgorithmCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    创建算法 (仅管理员)
    """
    ok, reason, algo_id = await create_algorithm_record(
        db,
        algo_data=algo_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "ALGO_CODE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="算法编码已存在",
            )
        if reason == "MODEL_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模型不存在",
            )
    return success_response({"id": algo_id}, "创建成功")


@router.put("/{algorithm_id}", summary="更新算法")
async def update_algorithm_api(
    algorithm_id: str,
    algo_data: AlgorithmUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新算法 (仅管理员)
    """
    ok, reason = await update_algorithm_record(
        db,
        algorithm_id=algorithm_id,
        algo_data=algo_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="算法不存在",
            )
        if reason == "ALGO_CODE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="算法编码已存在",
            )
    return success_response(None, "更新成功")


@router.delete("/{algorithm_id}", summary="删除算法")
async def delete_algorithm_api(
    algorithm_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    删除算法 (仅管理员)
    """
    ok, reason = await delete_algorithm_record(db, algorithm_id=algorithm_id)
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="算法不存在",
            )
        if reason == "HAS_CAMERA_CONFIGS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="存在关联的摄像头配置，无法删除",
            )
    return success_response(None, "删除成功")


# ==================== 摄像头-算法配置 ====================


@router.get("/camera/{camera_id}/configs", summary="获取摄像头算法配置")
async def get_camera_algorithm_configs_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取摄像头的算法配置列表
    """
    data = await list_camera_algorithm_configs(db, camera_id=camera_id)
    return success_response(data)


@router.post("/camera/{camera_id}/configs", summary="添加摄像头算法配置")
async def create_camera_algorithm_config_api(
    camera_id: str,
    config_data: CameraAlgorithmCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    为摄像头添加算法配置
    """
    ok, reason, config_id = await create_camera_algorithm_config_record(
        db,
        camera_id=camera_id,
        config_data=config_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "CAMERA_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="摄像头不存在",
            )
        if reason == "ALREADY_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该摄像头已配置此算法",
            )
    return success_response({"id": config_id}, "添加成功")


@router.put(
    "/camera/{camera_id}/configs/{config_id}",
    summary="更新摄像头算法配置",
)
async def update_camera_algorithm_config_api(
    camera_id: str,
    config_id: str,
    config_data: CameraAlgorithmUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新摄像头算法配置（置信度 / 区域 / 启用状态等）
    """
    ok, reason = await update_camera_algorithm_config_record(
        db,
        camera_id=camera_id,
        config_id=config_id,
        config_data=config_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在",
            )
    return success_response(None, "更新成功")


@router.delete(
    "/camera/{camera_id}/configs/{config_id}",
    summary="删除摄像头算法配置",
)
async def delete_camera_algorithm_config_api(
    camera_id: str,
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除摄像头算法配置
    """
    ok, reason = await delete_camera_algorithm_config_record(
        db,
        camera_id=camera_id,
        config_id=config_id,
    )
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在",
            )
    return success_response(None, "删除成功")

