# -*- coding: utf-8 -*-
"""
API 模块

包含所有 API 路由
"""
from fastapi import APIRouter

from .endpoints import (
    auth,
    cameras,
    areas,
    models,
    algorithms,
    alarms,
    system,
    media_hooks
)


# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证"]
)

api_router.include_router(
    cameras.router,
    prefix="/cameras",
    tags=["摄像头"]
)

api_router.include_router(
    areas.router,
    prefix="/areas",
    tags=["区域"]
)

api_router.include_router(
    models.router,
    prefix="/models",
    tags=["模型"]
)

api_router.include_router(
    algorithms.router,
    prefix="/algorithms",
    tags=["算法"]
)

api_router.include_router(
    alarms.router,
    prefix="/alarms",
    tags=["告警"]
)

api_router.include_router(
    system.router,
    prefix="/system",
    tags=["系统"]
)

api_router.include_router(
    media_hooks.router,
    prefix="/media/hook",
    tags=["流媒体Hook"]
)
