# -*- coding: utf-8 -*-
"""
系统 API

提供系统信息和健康检查接口
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_online_camera_ids
from app.core.config import settings
from app.api.deps import get_current_user, get_current_admin
from app.models import User, Camera, Area, Algorithm, Alarm
from app.websocket.manager import connection_manager
from app.consumer.worker_pool import alarm_worker_pool
from app.schemas.common import success_response
from common.logging import logger


router = APIRouter()


@router.get("/ffmpeg-path", summary="FFmpeg 安装路径（自动检测）")
async def get_ffmpeg_path(
    current_user: User = Depends(get_current_user),
):
    """
    返回 ffmpeg / ffprobe 可执行文件路径。
    优先使用配置 FFMPEG_PATH/FFPROBE_PATH，未配置时自动检测（which + Windows 常见目录）。
    """
    from engine.utils.ffmpeg_path import resolve_ffmpeg_path, resolve_ffprobe_path
    ffmpeg = resolve_ffmpeg_path(settings.FFMPEG_PATH or None)
    ffprobe = resolve_ffprobe_path(settings.FFPROBE_PATH or None)
    return success_response({
        "ffmpeg_path": ffmpeg,
        "ffprobe_path": ffprobe,
        "configured_ffmpeg": bool(settings.FFMPEG_PATH and settings.FFMPEG_PATH.strip()),
        "configured_ffprobe": bool(settings.FFPROBE_PATH and settings.FFPROBE_PATH.strip()),
    })


@router.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查
    
    用于负载均衡和监控
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/info", summary="系统信息")
async def system_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取系统信息
    """
    # 统计摄像头总数
    camera_count = (await db.execute(
        select(func.count(Camera.id))
    )).scalar() or 0

    # 在线摄像头数量从 Redis 读取（camera:online:{id}）
    online_ids = await get_online_camera_ids()
    online_camera_count = len(online_ids)
    
    area_count = (await db.execute(
        select(func.count(Area.id))
    )).scalar() or 0
    
    algorithm_count = (await db.execute(
        select(func.count(Algorithm.id))
    )).scalar() or 0
    
    alarm_count = (await db.execute(
        select(func.count(Alarm.id))
    )).scalar() or 0
    
    unconfirmed_alarm_count = (await db.execute(
        select(func.count(Alarm.id))
        .where(Alarm.status == "unconfirmed")
    )).scalar() or 0
    
    user_count = (await db.execute(
        select(func.count(User.id))
    )).scalar() or 0
    
    return success_response({
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "statistics": {
            "cameras": {
                "total": camera_count,
                "online": online_camera_count
            },
            "areas": area_count,
            "algorithms": algorithm_count,
            "alarms": {
                "total": alarm_count,
                "unconfirmed": unconfirmed_alarm_count
            },
            "users": user_count
        },
        "services": {
            "websocket_connections": connection_manager.get_connection_count(),
            "alarm_workers": {
                "running": alarm_worker_pool.is_running,
                "count": alarm_worker_pool.worker_count
            }
        }
    })


@router.get("/dashboard", summary="仪表盘数据")
async def dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取仪表盘数据
    """
    # 摄像头状态（总数仍来自 DB，在线数改用 Redis）
    total_cameras = (await db.execute(
        select(func.count(Camera.id))
    )).scalar() or 0

    online_cameras = len(await get_online_camera_ids())
    offline_cameras = max(total_cameras - online_cameras, 0)
    error_cameras = 0  # 如需更精细状态可后续从 DB 或其他指标计算
    
    # 今日告警
    from datetime import timedelta
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    today_alarms = (await db.execute(
        select(func.count(Alarm.id))
        .where(Alarm.alarm_time >= today_start)
    )).scalar() or 0
    
    today_unconfirmed = (await db.execute(
        select(func.count(Alarm.id))
        .where(
            Alarm.alarm_time >= today_start,
            Alarm.status == "unconfirmed"
        )
    )).scalar() or 0
    
    # 按级别统计今日告警
    level_stats = []
    for level in ["info", "warning", "danger", "critical"]:
        count = (await db.execute(
            select(func.count(Alarm.id))
            .where(
                Alarm.alarm_time >= today_start,
                Alarm.level == level
            )
        )).scalar() or 0
        level_stats.append({"label": level, "value": count})
    
    return success_response({
        "cameras": {
            "total": total_cameras,
            "online": online_cameras,
            "offline": offline_cameras,
            "error": error_cameras
        },
        "today_alarms": {
            "total": today_alarms,
            "unconfirmed": today_unconfirmed,
            "by_level": level_stats
        }
    })
