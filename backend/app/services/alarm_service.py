# -*- coding: utf-8 -*-
"""
告警相关业务逻辑：
- 告警列表 / 详情 / 趋势与仪表盘统计
- 告警确认 / 批量确认
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alarm, Camera, Algorithm, User
from app.schemas.alarm import (
    AlarmConfirmRequest,
    AlarmBatchConfirmRequest,
    AlarmOverviewStats,
    AlarmDeviceTopItem,
    AlarmAreaTopItem,
    AlarmTypeStatsItem,
    AlarmLevelStatsItem,
    AlarmDashboardStats,
)
from urllib.parse import quote


async def list_alarms(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    camera_id: Optional[str],
    algorithm_id: Optional[str],
    level: Optional[str],
    status: Optional[str],
    area_id: Optional[str],
    start_time: Optional[datetime],
    end_time: Optional[datetime],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取告警列表及总数。
    """
    query = select(Alarm)
    count_query = select(func.count(Alarm.id))

    conditions = []

    if camera_id:
        conditions.append(Alarm.camera_id == camera_id)

    if algorithm_id:
        conditions.append(Alarm.algorithm_id == algorithm_id)

    if level:
        conditions.append(Alarm.level == level)

    if status:
        conditions.append(Alarm.status == status)

    if area_id:
        conditions.append(Alarm.area_id == area_id)

    if start_time:
        conditions.append(Alarm.alarm_time >= start_time)

    if end_time:
        conditions.append(Alarm.alarm_time <= end_time)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Alarm.alarm_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    alarms = result.scalars().all()

    data: List[Dict[str, Any]] = []
    for alarm in alarms:
        snapshot_url = (
            f"/api/v1/files/preview?filepath={quote(alarm.snapshot_url)}&variant=thumb"
            if alarm.snapshot_url
            else None
        )
        video_url = (
            f"/api/v1/files/preview?filepath={quote(alarm.video_url)}"
            if alarm.video_url
            else None
        )

        data.append(
            {
                "id": alarm.id,
                "camera_id": alarm.camera_id,
                "camera_name": getattr(alarm, "camera_name", None),
                "area_name": getattr(alarm, "area_name", None),
                "algorithm_id": alarm.algorithm_id,
                "algorithm_name": getattr(alarm, "algorithm_name", None),
                "alarm_type": alarm.alarm_type,
                "level": alarm.level,
                "title": alarm.title,
                "description": alarm.description,
                "alarm_time": alarm.alarm_time.isoformat(),
                "snapshot_url": snapshot_url,
                "video_url": video_url,
                "detection_data": alarm.detection_data,
                "status": alarm.status,
                "confirmed_by": alarm.confirmed_by,
                "confirmed_at": alarm.confirmed_at.isoformat()
                if alarm.confirmed_at
                else None,
                "confirm_remark": alarm.confirm_remark,
                "is_pushed": alarm.is_pushed,
                "created_at": alarm.created_at.isoformat(),
            }
        )

    return data, total


async def get_alarm_stats_data(
    db: AsyncSession,
    *,
    days: int,
) -> Dict[str, Any]:
    """
    获取告警统计数据。
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.alarm_time >= start_time)
    )
    total = total_result.scalar() or 0

    status_stats: Dict[str, int] = {}
    for s in ["unconfirmed", "confirmed", "ignored", "processed"]:
        count_result = await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= start_time,
                Alarm.status == s,
            )
        )
        status_stats[s] = count_result.scalar() or 0

    level_stats: List[Dict[str, Any]] = []
    for level in ["info", "warning", "danger", "critical"]:
        count_result = await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= start_time,
                Alarm.level == level,
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            level_stats.append({"label": level, "value": count})

    camera_stats_result = await db.execute(
        select(Camera.name, func.count(Alarm.id).label("count"))
        .join(Alarm, Camera.id == Alarm.camera_id)
        .where(Alarm.alarm_time >= start_time)
        .group_by(Camera.id, Camera.name)
        .order_by(func.count(Alarm.id).desc())
        .limit(10)
    )
    camera_stats = [
        {"label": row[0] or "未知", "value": row[1]} for row in camera_stats_result
    ]

    algo_stats_result = await db.execute(
        select(Algorithm.name, func.count(Alarm.id).label("count"))
        .join(Alarm, Algorithm.id == Alarm.algorithm_id)
        .where(Alarm.alarm_time >= start_time)
        .group_by(Algorithm.id, Algorithm.name)
        .order_by(func.count(Alarm.id).desc())
        .limit(10)
    )
    algo_stats = [
        {"label": row[0] or "未知", "value": row[1]} for row in algo_stats_result
    ]

    trend: List[Dict[str, Any]] = []
    for i in range(days):
        day_start = (end_time - timedelta(days=days - i - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)

        count_result = await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= day_start,
                Alarm.alarm_time < day_end,
            )
        )
        count = count_result.scalar() or 0
        trend.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

    return {
        "total": total,
        "unconfirmed": status_stats.get("unconfirmed", 0),
        "confirmed": status_stats.get("confirmed", 0),
        "ignored": status_stats.get("ignored", 0),
        "processed": status_stats.get("processed", 0),
        "by_level": level_stats,
        "by_camera": camera_stats,
        "by_algorithm": algo_stats,
        "trend": trend,
    }


async def get_alarm_dashboard_data(
    db: AsyncSession,
    *,
    trend_days: int,
    stats_days: int,
) -> AlarmDashboardStats:
    """
    获取完整仪表盘统计数据。
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)

    if trend_days == 1:
        trend_start = today_start
        trend_range_desc = f"今日 ({today_start.strftime('%Y-%m-%d')})"
    else:
        trend_start = (now - timedelta(days=trend_days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        trend_range_desc = (
            f"{trend_start.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}"
        )

    stats_start = (now - timedelta(days=stats_days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    today_total = (
        await db.execute(
            select(func.count(Alarm.id)).where(Alarm.alarm_time >= today_start)
        )
    ).scalar() or 0

    yesterday_total = (
        await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= yesterday_start,
                Alarm.alarm_time < today_start,
            )
        )
    ).scalar() or 0

    if yesterday_total > 0:
        total_trend = round((today_total - yesterday_total) / yesterday_total * 100, 1)
    else:
        total_trend = 100.0 if today_total > 0 else 0.0

    unconfirmed = (
        await db.execute(
            select(func.count(Alarm.id)).where(Alarm.status == "unconfirmed")
        )
    ).scalar() or 0

    urgent_count = (
        await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.status == "unconfirmed",
                Alarm.level == "critical",
            )
        )
    ).scalar() or 0

    confirmed = (
        await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.status.in_(["confirmed", "processed"])
            )
        )
    ).scalar() or 0

    total_all = (await db.execute(select(func.count(Alarm.id)))).scalar() or 0

    if total_all > 0:
        completion_rate = round(confirmed / total_all * 100, 1)
    else:
        completion_rate = 100.0

    avg_time_result = await db.execute(
        select(
            func.avg(
                func.timestampdiff(
                    text("SECOND"),
                    Alarm.alarm_time,
                    Alarm.confirmed_at,
                )
            )
        ).where(
            Alarm.confirmed_at.isnot(None),
            Alarm.alarm_time >= yesterday_start,
        )
    )
    avg_time_seconds = avg_time_result.scalar()
    avg_handle_time = round(avg_time_seconds / 60, 1) if avg_time_seconds else 0.0

    overview = AlarmOverviewStats(
        total=total_all,
        total_trend=total_trend,
        total_new=today_total,
        unconfirmed=unconfirmed,
        unconfirmed_trend=-5.0,
        urgent_count=urgent_count,
        confirmed=confirmed,
        confirmed_trend=15.0,
        avg_handle_time=avg_handle_time,
        completion_rate=completion_rate,
        completion_trend=2.1,
        site_rank_percent=92.0,
    )

    trend: List[Dict[str, Any]] = []
    if trend_days == 1:
        for hour in range(24):
            hour_start = today_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= hour_start,
                    Alarm.alarm_time < hour_end,
                )
            )
            trend.append(
                {
                    "date": hour_start.strftime("%H:00"),
                    "count": count_result.scalar() or 0,
                }
            )
    else:
        for i in range(trend_days):
            day_start = (now - timedelta(days=trend_days - i - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= day_start,
                    Alarm.alarm_time < day_end,
                )
            )
            trend.append(
                {"date": day_start.strftime("%m-%d"), "count": count_result.scalar() or 0}
            )

    device_top_result = await db.execute(
        select(
            Alarm.camera_id,
            Alarm.camera_name,
            Alarm.area_name,
            func.count(Alarm.id).label("count"),
        )
        .where(Alarm.alarm_time >= stats_start)
        .group_by(Alarm.camera_id, Alarm.camera_name, Alarm.area_name)
        .order_by(func.count(Alarm.id).desc())
        .limit(5)
    )
    device_top = [
        AlarmDeviceTopItem(
            camera_id=row[0],
            camera_name=row[1] or "未知设备",
            area_name=row[2],
            count=row[3],
        )
        for row in device_top_result
    ]

    area_top_result = await db.execute(
        select(Alarm.area_name, func.count(Alarm.id).label("count"))
        .where(
            Alarm.alarm_time >= stats_start,
            Alarm.area_name.isnot(None),
        )
        .group_by(Alarm.area_name)
        .order_by(func.count(Alarm.id).desc())
        .limit(5)
    )
    area_top_raw = [(row[0], row[1]) for row in area_top_result]
    area_total = sum(count for _, count in area_top_raw)
    area_top = [
        AlarmAreaTopItem(
            area_name=name,
            count=count,
            percentage=round(count / area_total * 100, 1) if area_total > 0 else 0,
        )
        for name, count in area_top_raw
    ]

    type_stats_result = await db.execute(
        select(
            Alarm.algorithm_id,
            Alarm.algorithm_name,
            func.count(Alarm.id).label("count"),
        )
        .where(Alarm.alarm_time >= stats_start)
        .group_by(Alarm.algorithm_id, Alarm.algorithm_name)
        .order_by(func.count(Alarm.id).desc())
        .limit(4)
    )
    type_stats_raw = [(row[0], row[1], row[2]) for row in type_stats_result]
    type_total = sum(count for _, _, count in type_stats_raw)
    type_stats = [
        AlarmTypeStatsItem(
            algorithm_id=row[0],
            algorithm_name=row[1] or "其他告警",
            count=row[2],
            percentage=round(row[2] / type_total * 100, 1) if type_total > 0 else 0,
        )
        for row in type_stats_raw
    ]

    level_labels = {
        "critical": "致命等级 (Critical)",
        "danger": "危险等级 (Danger)",
        "warning": "警告等级 (Warning)",
        "info": "提示等级 (Info)",
    }
    level_stats: List[AlarmLevelStatsItem] = []
    level_total_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.alarm_time >= stats_start)
    )
    level_total = level_total_result.scalar() or 0

    for level in ["critical", "danger", "warning", "info"]:
        count_result = await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= stats_start,
                Alarm.level == level,
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            level_stats.append(
                AlarmLevelStatsItem(
                    level=level,
                    label=level_labels.get(level, level),
                    count=count,
                    percentage=round(count / level_total * 100, 1)
                    if level_total > 0
                    else 0,
                )
            )

    return AlarmDashboardStats(
        overview=overview,
        trend=trend,
        trend_range=trend_range_desc,
        device_top=device_top,
        area_top=area_top,
        type_stats=type_stats,
        level_stats=level_stats,
    )


async def get_alarm_trend_data(
    db: AsyncSession,
    *,
    days: int,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    获取告警趋势数据和时间范围描述。
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if days == 1:
        trend_start = today_start
        trend_range_desc = f"今日 ({today_start.strftime('%Y-%m-%d')})"
    else:
        trend_start = (now - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        trend_range_desc = (
            f"{trend_start.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}"
        )

    trend: List[Dict[str, Any]] = []
    if days == 1:
        for hour in range(24):
            hour_start = today_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= hour_start,
                    Alarm.alarm_time < hour_end,
                )
            )
            trend.append(
                {"date": hour_start.strftime("%H:00"), "count": count_result.scalar() or 0}
            )
    else:
        for i in range(days):
            day_start = (now - timedelta(days=days - i - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= day_start,
                    Alarm.alarm_time < day_end,
                )
            )
            trend.append(
                {"date": day_start.strftime("%m-%d"), "count": count_result.scalar() or 0}
            )

    return trend, trend_range_desc


async def get_alarm_detail_data(
    db: AsyncSession,
    alarm_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取单条告警详情数据。
    """
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    if alarm is None:
        return None

    snapshot_url = (
        f"/api/v1/files/preview?filepath={quote(alarm.snapshot_url)}&variant=origin"
        if alarm.snapshot_url
        else None
    )
    video_url = (
        f"/api/v1/files/preview?filepath={quote(alarm.video_url)}"
        if alarm.video_url
        else None
    )

    return {
        "id": alarm.id,
        "camera_id": alarm.camera_id,
        "camera_name": getattr(alarm, "camera_name", None),
        "area_name": getattr(alarm, "area_name", None),
        "algorithm_id": alarm.algorithm_id,
        "algorithm_name": getattr(alarm, "algorithm_name", None),
        "alarm_type": alarm.alarm_type,
        "level": alarm.level,
        "title": alarm.title,
        "description": alarm.description,
        "alarm_time": alarm.alarm_time.isoformat(),
        "snapshot_url": snapshot_url,
        "video_url": video_url,
        "detection_data": alarm.detection_data,
        "status": alarm.status,
        "confirmed_by": alarm.confirmed_by,
        "confirmed_at": alarm.confirmed_at.isoformat()
        if alarm.confirmed_at
        else None,
        "confirm_remark": alarm.confirm_remark,
        "is_pushed": alarm.is_pushed,
        "created_at": alarm.created_at.isoformat(),
    }


async def confirm_alarm_record(
    db: AsyncSession,
    *,
    alarm_id: str,
    confirm_data: AlarmConfirmRequest,
    current_user: User,
) -> Tuple[bool, Optional[str]]:
    """
    确认单条告警。
    返回 (ok, error_code):
    - ok=False, "NOT_FOUND" 告警不存在
    - ok=False, "INVALID_STATE" 状态不允许确认
    """
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()
    if alarm is None:
        return False, "NOT_FOUND"

    if not alarm.can_confirm:
        return False, "INVALID_STATE"

    alarm.confirm(
        user_id=current_user.id,
        remark=confirm_data.remark,
        new_status=confirm_data.status,
    )

    await db.commit()
    return True, None


async def batch_confirm_alarm_records(
    db: AsyncSession,
    *,
    confirm_data: AlarmBatchConfirmRequest,
    current_user: User,
) -> int:
    """
    批量确认告警，返回成功数量。
    """
    result = await db.execute(
        select(Alarm).where(
            Alarm.id.in_(confirm_data.alarm_ids),
            Alarm.status == "unconfirmed",
        )
    )
    alarms = result.scalars().all()

    confirmed_count = 0
    for alarm in alarms:
        try:
            alarm.confirm(
                user_id=current_user.id,
                remark=confirm_data.remark,
                new_status=confirm_data.status,
            )
            confirmed_count += 1
        except ValueError:
            continue

    await db.commit()
    return confirmed_count

