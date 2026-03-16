# -*- coding: utf-8 -*-
"""
系统相关业务逻辑：
- FFmpeg 路径解析
- 健康检查数据
- 系统信息与仪表盘统计
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_online_camera_ids
from app.core.config import settings
from app.models import User, Camera, Area, Algorithm, Alarm
from app.websocket.manager import connection_manager
from app.consumer.worker_pool import alarm_worker_pool


def resolve_ffmpeg_paths() -> Dict[str, Any]:
    """
    解析 ffmpeg / ffprobe 路径。
    """
    from engine.utils.ffmpeg_path import resolve_ffmpeg_path, resolve_ffprobe_path

    ffmpeg = resolve_ffmpeg_path(settings.FFMPEG_PATH or None)
    ffprobe = resolve_ffprobe_path(settings.FFPROBE_PATH or None)
    return {
        "ffmpeg_path": ffmpeg,
        "ffprobe_path": ffprobe,
        "configured_ffmpeg": bool(settings.FFMPEG_PATH and settings.FFMPEG_PATH.strip()),
        "configured_ffprobe": bool(
            settings.FFPROBE_PATH and settings.FFPROBE_PATH.strip()
        ),
    }


def get_health_payload() -> Dict[str, Any]:
    """
    健康检查返回数据。
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


async def get_system_info_data(db: AsyncSession) -> Dict[str, Any]:
    """
    系统信息统计。
    """
    camera_count = (
        await db.execute(select(func.count(Camera.id)))
    ).scalar() or 0

    online_ids = await get_online_camera_ids()
    online_camera_count = len(online_ids)

    area_count = (
        await db.execute(select(func.count(Area.id)))
    ).scalar() or 0

    algorithm_count = (
        await db.execute(select(func.count(Algorithm.id)))
    ).scalar() or 0

    alarm_count = (
        await db.execute(select(func.count(Alarm.id)))
    ).scalar() or 0

    unconfirmed_alarm_count = (
        await db.execute(
            select(func.count(Alarm.id)).where(Alarm.status == "unconfirmed")
        )
    ).scalar() or 0

    user_count = (
        await db.execute(select(func.count(User.id)))
    ).scalar() or 0

    return {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "statistics": {
            "cameras": {
                "total": camera_count,
                "online": online_camera_count,
            },
            "areas": area_count,
            "algorithms": algorithm_count,
            "alarms": {
                "total": alarm_count,
                "unconfirmed": unconfirmed_alarm_count,
            },
            "users": user_count,
        },
        "services": {
            "websocket_connections": connection_manager.get_connection_count(),
            "alarm_workers": {
                "running": alarm_worker_pool.is_running,
                "count": alarm_worker_pool.worker_count,
            },
        },
    }


async def get_dashboard_data(db: AsyncSession) -> Dict[str, Any]:
    """
    仪表盘统计数据。
    """
    total_cameras = (
        await db.execute(select(func.count(Camera.id)))
    ).scalar() or 0

    online_cameras = len(await get_online_camera_ids())
    offline_cameras = max(total_cameras - online_cameras, 0)
    error_cameras = 0

    today_start = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    today_alarms = (
        await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= today_start
            )
        )
    ).scalar() or 0

    today_unconfirmed = (
        await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= today_start,
                Alarm.status == "unconfirmed",
            )
        )
    ).scalar() or 0

    level_stats = []
    for level in ["info", "warning", "danger", "critical"]:
        count = (
            await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= today_start,
                    Alarm.level == level,
                )
            )
        ).scalar() or 0
        level_stats.append({"label": level, "value": count})

    total_algorithms = (
        await db.execute(select(func.count(Algorithm.id)))
    ).scalar() or 0

    enabled_algorithms = (
        await db.execute(
            select(func.count(Algorithm.id)).where(
                Algorithm.is_enabled == True  # noqa: E712
            )
        )
    ).scalar() or 0

    try:
        from app.models import Model

        total_models = (
            await db.execute(select(func.count(Model.id)))
        ).scalar() or 0

        loaded_models = (
            await db.execute(
                select(func.count(Model.id)).where(
                    Model.is_enabled == True  # noqa: E712
                )
            )
        ).scalar() or 0
    except ImportError:
        total_models = 0
        loaded_models = 0

    total_users = (
        await db.execute(select(func.count(User.id)))
    ).scalar() or 0

    return {
        "cameras": {
            "total": total_cameras,
            "online": online_cameras,
            "offline": offline_cameras,
            "error": error_cameras,
        },
        "algorithms": {
            "total": total_algorithms,
            "enabled": enabled_algorithms,
        },
        "models": {
            "total": total_models,
            "loaded": loaded_models,
        },
        "today_alarms": {
            "total": today_alarms,
            "unconfirmed": today_unconfirmed,
            "by_level": level_stats,
        },
        "users": {
            "total": total_users,
            "active": 0,
        },
    }

