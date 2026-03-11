# -*- coding: utf-8 -*-
"""
告警 API

提供告警查询和处理接口
"""
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User, Alarm, Camera, Algorithm
from app.schemas.alarm import (
    AlarmConfirmRequest,
    AlarmBatchConfirmRequest,
    AlarmStatsData,
    AlarmStatsItem,
    AlarmTrendItem,
    AlarmOverviewStats,
    AlarmDeviceTopItem,
    AlarmAreaTopItem,
    AlarmTypeStatsItem,
    AlarmLevelStatsItem,
    AlarmDashboardStats
)
from app.schemas.common import success_response, page_response
from common.logging import logger
from urllib.parse import quote


router = APIRouter()


@router.get("", summary="获取告警列表")
async def get_alarms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    camera_id: Optional[str] = Query(None, description="摄像头ID"),
    algorithm_id: Optional[str] = Query(None, description="算法ID"),
    level: Optional[str] = Query(None, description="告警级别"),
    status: Optional[str] = Query(None, description="处理状态"),
    area_id: Optional[str] = Query(None, description="区域ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警列表
    """
    # 不使用关联查询，直接使用alarms表中的area_id字段
    query = select(Alarm)
    count_query = select(func.count(Alarm.id))
    
    # 筛选条件
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
    
    # 统计总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.order_by(Alarm.alarm_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    alarms = result.scalars().all()
    
    data = []
    for alarm in alarms:
        # 资源 URL：统一走 files/preview，不直接暴露存储地址
        # 列表页默认使用缩略图，详情页再取原图
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

        data.append({
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
            "confirmed_at": alarm.confirmed_at.isoformat() if alarm.confirmed_at else None,
            "confirm_remark": alarm.confirm_remark,
            "is_pushed": alarm.is_pushed,
            "created_at": alarm.created_at.isoformat()
        })
    
    return page_response(data, page, page_size, total)


@router.get("/stats", summary="获取告警统计")
async def get_alarm_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警统计数据
    """
    # 时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # 总数
    total_result = await db.execute(
        select(func.count(Alarm.id))
        .where(Alarm.alarm_time >= start_time)
    )
    total = total_result.scalar() or 0
    
    # 按状态统计
    status_stats = {}
    for s in ["unconfirmed", "confirmed", "ignored", "processed"]:
        count_result = await db.execute(
            select(func.count(Alarm.id))
            .where(
                Alarm.alarm_time >= start_time,
                Alarm.status == s
            )
        )
        status_stats[s] = count_result.scalar() or 0
    
    # 按级别统计
    level_stats = []
    for level in ["info", "warning", "danger", "critical"]:
        count_result = await db.execute(
            select(func.count(Alarm.id))
            .where(
                Alarm.alarm_time >= start_time,
                Alarm.level == level
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            level_stats.append({"label": level, "value": count})
    
    # 按摄像头统计 (Top 10)
    camera_stats_result = await db.execute(
        select(
            Camera.name,
            func.count(Alarm.id).label("count")
        )
        .join(Alarm, Camera.id == Alarm.camera_id)
        .where(Alarm.alarm_time >= start_time)
        .group_by(Camera.id, Camera.name)
        .order_by(func.count(Alarm.id).desc())
        .limit(10)
    )
    camera_stats = [
        {"label": row[0] or "未知", "value": row[1]}
        for row in camera_stats_result
    ]
    
    # 按算法统计 (Top 10)
    algo_stats_result = await db.execute(
        select(
            Algorithm.name,
            func.count(Alarm.id).label("count")
        )
        .join(Alarm, Algorithm.id == Alarm.algorithm_id)
        .where(Alarm.alarm_time >= start_time)
        .group_by(Algorithm.id, Algorithm.name)
        .order_by(func.count(Alarm.id).desc())
        .limit(10)
    )
    algo_stats = [
        {"label": row[0] or "未知", "value": row[1]}
        for row in algo_stats_result
    ]
    
    # 趋势数据
    trend = []
    for i in range(days):
        day_start = (end_time - timedelta(days=days - i - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        day_end = day_start + timedelta(days=1)
        
        count_result = await db.execute(
            select(func.count(Alarm.id))
            .where(
                Alarm.alarm_time >= day_start,
                Alarm.alarm_time < day_end
            )
        )
        count = count_result.scalar() or 0
        trend.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return success_response({
        "total": total,
        "unconfirmed": status_stats.get("unconfirmed", 0),
        "confirmed": status_stats.get("confirmed", 0),
        "ignored": status_stats.get("ignored", 0),
        "processed": status_stats.get("processed", 0),
        "by_level": level_stats,
        "by_camera": camera_stats,
        "by_algorithm": algo_stats,
        "trend": trend
    })


@router.get("/dashboard", summary="获取告警仪表盘统计")
async def get_alarm_dashboard(
    trend_days: int = Query(1, ge=1, le=30, description="趋势统计天数(1=今日,7=7日等)"),
    stats_days: int = Query(30, ge=1, le=365, description="榜单/分布统计天数(默认30天)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警仪表盘统计数据（完整统计页面数据）
    
    - trend_days: 趋势统计天数，1=今日，7=7日，14=14日，30=30日
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    
    # 趋势统计范围（独立于榜单统计范围）
    if trend_days == 1:
        trend_start = today_start
        trend_range_desc = f"今日 ({today_start.strftime('%Y-%m-%d')})"
    else:
        trend_start = (now - timedelta(days=trend_days)).replace(hour=0, minute=0, second=0, microsecond=0)
        trend_range_desc = f"{trend_start.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}"

    # 榜单/分布统计范围
    stats_start = (now - timedelta(days=stats_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.alarm_time >= today_start)
    )
    today_total = total_result.scalar() or 0
    
    yesterday_result = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.alarm_time >= yesterday_start,
            Alarm.alarm_time < today_start
        )
    )
    yesterday_total = yesterday_result.scalar() or 0
    
    if yesterday_total > 0:
        total_trend = round((today_total - yesterday_total) / yesterday_total * 100, 1)
    else:
        total_trend = 100.0 if today_total > 0 else 0.0
    
    unconfirmed_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.status == "unconfirmed")
    )
    unconfirmed = unconfirmed_result.scalar() or 0
    
    urgent_result = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.status == "unconfirmed",
            Alarm.level == "critical"
        )
    )
    urgent_count = urgent_result.scalar() or 0
    
    confirmed_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.status.in_(["confirmed", "processed"]))
    )
    confirmed = confirmed_result.scalar() or 0
    
    total_all_result = await db.execute(select(func.count(Alarm.id)))
    total_all = total_all_result.scalar() or 0
    
    if total_all > 0:
        completion_rate = round(confirmed / total_all * 100, 1)
    else:
        completion_rate = 100.0
    
    from sqlalchemy import text
    avg_time_result = await db.execute(
        select(
            func.avg(
                func.timestampdiff(text('SECOND'), Alarm.alarm_time, Alarm.confirmed_at)
            )
        ).where(
            Alarm.confirmed_at.isnot(None),
            Alarm.alarm_time >= yesterday_start
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
        site_rank_percent=92.0
    )
    
    trend = []
    if trend_days == 1:
        for hour in range(24):
            hour_start = today_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= hour_start,
                    Alarm.alarm_time < hour_end
                )
            )
            trend.append({
                "date": hour_start.strftime("%H:00"),
                "count": count_result.scalar() or 0
            })
    else:
        for i in range(trend_days):
            day_start = (now - timedelta(days=trend_days - i - 1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= day_start,
                    Alarm.alarm_time < day_end
                )
            )
            trend.append({
                "date": day_start.strftime("%m-%d"),
                "count": count_result.scalar() or 0
            })
    
    device_top_result = await db.execute(
        select(
            Alarm.camera_id,
            Alarm.camera_name,
            Alarm.area_name,
            func.count(Alarm.id).label("count")
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
            count=row[3]
        )
        for row in device_top_result
    ]
    
    area_top_result = await db.execute(
        select(
            Alarm.area_name,
            func.count(Alarm.id).label("count")
        )
        .where(
            Alarm.alarm_time >= stats_start,
            Alarm.area_name.isnot(None)
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
            percentage=round(count / area_total * 100, 1) if area_total > 0 else 0
        )
        for name, count in area_top_raw
    ]
    
    type_stats_result = await db.execute(
        select(
            Alarm.algorithm_id,
            Alarm.algorithm_name,
            func.count(Alarm.id).label("count")
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
            percentage=round(row[2] / type_total * 100, 1) if type_total > 0 else 0
        )
        for row in type_stats_raw
    ]
    
    level_labels = {
        "critical": "致命等级 (Critical)",
        "danger": "危险等级 (Danger)",
        "warning": "警告等级 (Warning)",
        "info": "提示等级 (Info)"
    }
    level_stats = []
    level_total_result = await db.execute(
        select(func.count(Alarm.id)).where(Alarm.alarm_time >= stats_start)
    )
    level_total = level_total_result.scalar() or 0
    
    for level in ["critical", "danger", "warning", "info"]:
        count_result = await db.execute(
            select(func.count(Alarm.id)).where(
                Alarm.alarm_time >= stats_start,
                Alarm.level == level
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            level_stats.append(AlarmLevelStatsItem(
                level=level,
                label=level_labels.get(level, level),
                count=count,
                percentage=round(count / level_total * 100, 1) if level_total > 0 else 0
            ))
    
    return success_response(AlarmDashboardStats(
        overview=overview,
        trend=trend,
        trend_range=trend_range_desc,
        device_top=device_top,
        area_top=area_top,
        type_stats=type_stats,
        level_stats=level_stats
    ).model_dump())


@router.get("/trend", summary="获取告警趋势（按天数切换）")
async def get_alarm_trend(
    days: int = Query(1, ge=1, le=30, description="趋势统计天数(1=今日,7/14/30=近N天)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    仅返回趋势数据，用于前端在「今日/7日/14日/30日」切换时按需加载，避免重复拉取榜单/分布数据。
    """
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if days == 1:
        trend_start = today_start
        trend_range_desc = f"今日 ({today_start.strftime('%Y-%m-%d')})"
    else:
        trend_start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        trend_range_desc = f"{trend_start.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}"

    trend: list[dict] = []
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
            trend.append({"date": hour_start.strftime("%H:00"), "count": count_result.scalar() or 0})
    else:
        for i in range(days):
            day_start = (now - timedelta(days=days - i - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count_result = await db.execute(
                select(func.count(Alarm.id)).where(
                    Alarm.alarm_time >= day_start,
                    Alarm.alarm_time < day_end,
                )
            )
            trend.append({"date": day_start.strftime("%m-%d"), "count": count_result.scalar() or 0})

    return success_response({"trend": trend, "trend_range": trend_range_desc})


@router.get("/{alarm_id}", summary="获取告警详情")
async def get_alarm(
    alarm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警详情
    """
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()
    
    if alarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警不存在"
        )
    
    # 详情页使用原图
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
    
    return success_response({
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
        "confirmed_at": alarm.confirmed_at.isoformat() if alarm.confirmed_at else None,
        "confirm_remark": alarm.confirm_remark,
        "is_pushed": alarm.is_pushed,
        "created_at": alarm.created_at.isoformat()
    })


@router.post("/{alarm_id}/confirm", summary="确认告警")
async def confirm_alarm(
    alarm_id: str,
    confirm_data: AlarmConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    确认告警
    """
    result = await db.execute(
        select(Alarm).where(Alarm.id == alarm_id)
    )
    alarm = result.scalar_one_or_none()
    
    if alarm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警不存在"
        )
    
    if not alarm.can_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"告警状态为 {alarm.status}，无法确认"
        )
    
    alarm.confirm(
        user_id=current_user.id,
        remark=confirm_data.remark,
        new_status=confirm_data.status
    )
    
    await db.commit()
    
    logger.info(f"告警已确认: {alarm_id} -> {confirm_data.status}")
    
    return success_response(None, "确认成功")


@router.post("/batch-confirm", summary="批量确认告警")
async def batch_confirm_alarms(
    confirm_data: AlarmBatchConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量确认告警
    """
    result = await db.execute(
        select(Alarm)
        .where(
            Alarm.id.in_(confirm_data.alarm_ids),
            Alarm.status == "unconfirmed"
        )
    )
    alarms = result.scalars().all()
    
    confirmed_count = 0
    for alarm in alarms:
        try:
            alarm.confirm(
                user_id=current_user.id,
                remark=confirm_data.remark,
                new_status=confirm_data.status
            )
            confirmed_count += 1
        except ValueError:
            continue
    
    await db.commit()
    
    logger.info(f"批量确认告警: {confirmed_count}/{len(confirm_data.alarm_ids)}")
    
    return success_response(
        {"confirmed_count": confirmed_count},
        f"已确认 {confirmed_count} 条告警"
    )
