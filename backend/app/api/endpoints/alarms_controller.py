# -*- coding: utf-8 -*-
"""
告警 API Controller

- 负责 HTTP 路由、参数与权限校验
- 业务逻辑委托给 alarm_service
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.alarm import (
    AlarmConfirmRequest,
    AlarmBatchConfirmRequest,
)
from app.schemas.common import success_response, page_response
from app.services.alarm_service import (
    list_alarms,
    get_alarm_stats_data,
    get_alarm_dashboard_data,
    get_alarm_trend_data,
    get_alarm_detail_data,
    confirm_alarm_record,
    batch_confirm_alarm_records,
)
from common.logging import logger


router = APIRouter()


@router.get("", summary="获取告警列表")
async def get_alarms_api(
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
    db: AsyncSession = Depends(get_db),
):
    """
    获取告警列表
    """
    data, total = await list_alarms(
        db,
        page=page,
        page_size=page_size,
        camera_id=camera_id,
        algorithm_id=algorithm_id,
        level=level,
        status=status,
        area_id=area_id,
        start_time=start_time,
        end_time=end_time,
    )
    return page_response(data, page, page_size, total)


@router.get("/stats", summary="获取告警统计")
async def get_alarm_stats_api(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取告警统计数据
    """
    data = await get_alarm_stats_data(db, days=days)
    return success_response(data)


@router.get("/dashboard", summary="获取告警仪表盘统计")
async def get_alarm_dashboard_api(
    trend_days: int = Query(
        1, ge=1, le=30, description="趋势统计天数(1=今日,7=7日等)"
    ),
    stats_days: int = Query(
        30, ge=1, le=365, description="榜单/分布统计天数(默认30天)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取告警仪表盘统计数据（完整统计页面数据）
    """
    stats = await get_alarm_dashboard_data(
        db,
        trend_days=trend_days,
        stats_days=stats_days,
    )
    return success_response(stats.model_dump())


@router.get("/trend", summary="获取告警趋势（按天数切换）")
async def get_alarm_trend_api(
    days: int = Query(
        1, ge=1, le=30, description="趋势统计天数(1=今日,7/14/30=近N天)"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    仅返回趋势数据
    """
    trend, trend_range = await get_alarm_trend_data(db, days=days)
    return success_response({"trend": trend, "trend_range": trend_range})


@router.get("/{alarm_id}", summary="获取告警详情")
async def get_alarm_api(
    alarm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取告警详情
    """
    detail = await get_alarm_detail_data(db, alarm_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="告警不存在",
        )
    return success_response(detail)


@router.post("/{alarm_id}/confirm", summary="确认告警")
async def confirm_alarm_api(
    alarm_id: str,
    confirm_data: AlarmConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    确认告警
    """
    ok, reason = await confirm_alarm_record(
        db,
        alarm_id=alarm_id,
        confirm_data=confirm_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在",
            )
        if reason == "INVALID_STATE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"当前状态无法确认",
            )

    logger.info(f"告警已确认: {alarm_id} -> {confirm_data.status}")
    return success_response(None, "确认成功")


@router.post("/batch-confirm", summary="批量确认告警")
async def batch_confirm_alarms_api(
    confirm_data: AlarmBatchConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    批量确认告警
    """
    confirmed_count = await batch_confirm_alarm_records(
        db,
        confirm_data=confirm_data,
        current_user=current_user,
    )
    logger.info(
        f"批量确认告警: {confirmed_count}/{len(confirm_data.alarm_ids)}"
    )
    return success_response(
        {"confirmed_count": confirmed_count},
        f"已确认 {confirmed_count} 条告警",
    )

