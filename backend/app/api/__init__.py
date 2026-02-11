"""
API Router aggregation.
"""

from fastapi import APIRouter

from app.api.endpoints import auth, cameras, areas, alarms, algorithms, system

api_router = APIRouter()

# Authentication
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# Business modules
api_router.include_router(cameras.router, prefix="/cameras", tags=["摄像头管理"])
api_router.include_router(areas.router, prefix="/areas", tags=["区域管理"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["告警管理"])
api_router.include_router(algorithms.router, prefix="/algorithms", tags=["算法管理"])

# System
api_router.include_router(system.router, prefix="/system", tags=["系统管理"])
