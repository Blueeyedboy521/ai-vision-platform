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
    AlarmTrendItem
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
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取告警列表
    """
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
        snapshot_url = (
            f"/api/v1/files/preview?filepath={quote(alarm.snapshot_url)}"
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
    
    snapshot_url = (
        f"/api/v1/files/preview?filepath={quote(alarm.snapshot_url)}"
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
