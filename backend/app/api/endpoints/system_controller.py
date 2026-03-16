# -*- coding: utf-8 -*-
"""
系统 API Controller

- 负责路由与权限校验
- 业务逻辑委托给 system_service
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.common import success_response
from app.services.system_service import (
    resolve_ffmpeg_paths,
    get_health_payload,
    get_system_info_data,
    get_dashboard_data,
)


router = APIRouter()


@router.get("/ffmpeg-path", summary="FFmpeg 安装路径（自动检测）")
async def get_ffmpeg_path_api(
    current_user: User = Depends(get_current_user),
):
    """
    返回 ffmpeg / ffprobe 可执行文件路径。
    """
    data = resolve_ffmpeg_paths()
    return success_response(data)


@router.get("/health", summary="健康检查")
async def health_check_api():
    """
    健康检查
    """
    return get_health_payload()


@router.get("/info", summary="系统信息")
async def system_info_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取系统信息
    """
    data = await get_system_info_data(db)
    return success_response(data)


@router.get("/dashboard", summary="仪表盘数据")
async def dashboard_api(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取仪表盘数据
    """
    data = await get_dashboard_data(db)
    return success_response(data)

