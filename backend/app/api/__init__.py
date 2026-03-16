# -*- coding: utf-8 -*-
"""
API 模块

包含所有 API 路由
"""
from fastapi import APIRouter

from .endpoints import (
    auth_controller,
    cameras_controller,
    areas_controller,
    models_controller,
    algorithms_controller,
    alarms_controller,
    system_controller,
    media_hooks_controller,
    notifications_controller,
    files_controller,
)


# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    auth_controller.router,
    prefix="/auth",
    tags=["认证"],
)

api_router.include_router(
    cameras_controller.router,
    prefix="/cameras",
    tags=["摄像头"],
)

api_router.include_router(
    areas_controller.router,
    prefix="/areas",
    tags=["区域"],
)

api_router.include_router(
    models_controller.router,
    prefix="/models",
    tags=["模型"],
)

api_router.include_router(
    algorithms_controller.router,
    prefix="/algorithms",
    tags=["算法"],
)

api_router.include_router(
    alarms_controller.router,
    prefix="/alarms",
    tags=["告警"],
)

api_router.include_router(
    system_controller.router,
    prefix="/system",
    tags=["系统"],
)

api_router.include_router(
    files_controller.router,
    prefix="/files",
    tags=["文件"],
)

api_router.include_router(
    media_hooks_controller.router,
    prefix="/media/hook",
    tags=["流媒体Hook"],
)

api_router.include_router(
    notifications_controller.router,
    prefix="/notifications",
    tags=["推送配置"]
)
