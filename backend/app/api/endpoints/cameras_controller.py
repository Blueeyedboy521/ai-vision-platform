# -*- coding: utf-8 -*-
"""
摄像头 API Controller

- 负责路由、参数与权限校验
- 业务逻辑全部委托给 camera_service
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.camera import CameraCreate, CameraUpdate
from app.schemas.common import success_response, page_response
from app.services.camera_service import (
    list_cameras,
    probe_stream_info_data,
    get_camera_detail,
    start_camera_inference_action,
    stop_camera_inference_action,
    create_camera_record,
    update_camera_record,
    delete_camera_record,
    start_camera_action,
    stop_camera_action,
    update_live_heartbeat,
    get_camera_play_urls,
    snapshot_camera,
)


class ProbeStreamRequest(BaseModel):
    """流通性测试请求"""

    rtsp_url: str = Field(..., description="RTSP 流地址（可含认证）")


router = APIRouter()


@router.get("", summary="获取摄像头列表")
async def get_cameras_api(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    area_id: Optional[str] = Query(None, description="区域ID"),
    status: Optional[str] = Query(None, description="状态"),
    keyword: Optional[str] = Query(None, description="关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取摄像头列表
    """
    data, total = await list_cameras(
        db,
        page=page,
        page_size=page_size,
        area_id=area_id,
        status=status,
        keyword=keyword,
    )
    return page_response(data, page, page_size, total)


@router.post("/probe-stream", summary="流通性测试（获取宽高、帧率）")
async def probe_stream_info_api(
    body: ProbeStreamRequest = Body(...),
    current_user: User = Depends(get_current_user),
):
    """
    使用 OpenCV/ffprobe 探测 RTSP 流，返回宽、高、帧率等信息
    """
    result = await probe_stream_info_data(body.rtsp_url)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "流探测失败"),
        )
    return success_response(
        {
            "width": result["width"],
            "height": result["height"],
            "fps": result["fps"],
            "resolution": result["resolution"],
        }
    )


@router.get("/{camera_id}", summary="获取摄像头详情")
async def get_camera_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取摄像头详情
    """
    detail = await get_camera_detail(db, camera_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(detail)


@router.post("/{camera_id}/start-inference", summary="启动摄像头推理")
async def start_camera_inference_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    启动摄像头推理
    """
    ok, reason = await start_camera_inference_action(db, camera_id)
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="摄像头不存在",
            )
        if reason == "NOT_ENABLED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="摄像头未启用",
            )
        if reason == "NO_ENABLED_ALGORITHM":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未启用任何算法，无法启动推理",
            )
    return success_response(None, "推理启动命令已发送")


@router.post("/{camera_id}/stop-inference", summary="停止摄像头推理")
async def stop_camera_inference_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    停止摄像头推理
    """
    ok, reason = await stop_camera_inference_action(db, camera_id)
    if not ok and reason == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(None, "推理停止命令已发送")


@router.post("", summary="创建摄像头")
async def create_camera_api(
    camera_data: CameraCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建摄像头
    """
    ok, reason, camera_id = await create_camera_record(
        db,
        camera_data=camera_data,
        current_user=current_user,
    )
    if not ok:
        if reason == "CODE_EXISTS":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="摄像头编码已存在",
            )
        if reason == "AREA_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域不存在",
            )
    return success_response({"id": camera_id}, "创建成功")


@router.put("/{camera_id}", summary="更新摄像头")
async def update_camera_api(
    camera_id: str,
    camera_data: CameraUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新摄像头
    """
    ok, reason = await update_camera_record(
        db,
        camera_id=camera_id,
        camera_data=camera_data,
        current_user=current_user,
    )
    if not ok and reason == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(None, "更新成功")


@router.delete("/{camera_id}", summary="删除摄像头")
async def delete_camera_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除摄像头
    """
    ok, reason = await delete_camera_record(db, camera_id=camera_id)
    if not ok and reason == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(None, "删除成功")


@router.post("/{camera_id}/start", summary="启动摄像头")
async def start_camera_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    启动摄像头（开始拉流/推流/分析）。仅当摄像头启用状态下允许启动。
    """
    ok, reason = await start_camera_action(db, camera_id=camera_id)
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="摄像头不存在",
            )
        if reason == "NOT_ENABLED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="摄像头未启用，请先在编辑页启用后再播放",
            )
    return success_response(None, "启动命令已发送")


@router.post("/{camera_id}/stop", summary="停止摄像头")
async def stop_camera_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    停止摄像头（停止拉流/推流）。同时从“直播已启动”集合移除。
    """
    ok, reason = await stop_camera_action(db, camera_id=camera_id)
    if not ok and reason == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(None, "停止命令已发送")


@router.post("/{camera_id}/live-heartbeat", summary="摄像头直播心跳")
async def camera_live_heartbeat_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    前端播放摄像头直播流时每 60 秒调用一次
    """
    payload = await update_live_heartbeat(camera_id)
    return success_response(payload, "心跳已更新")


@router.get("/{camera_id}/play-url", summary="获取播放地址")
async def get_play_url_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取摄像头播放地址
    """
    ok, reason, data = await get_camera_play_urls(db, camera_id=camera_id)
    if not ok and reason == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在",
        )
    return success_response(data)


@router.post("/{camera_id}/snapshot", summary="抓拍")
async def camera_snapshot_api(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    从摄像头 RTSP 流抓拍一帧
    """
    ok, reason, snapshot_url = await snapshot_camera(
        db,
        camera_id=camera_id,
        current_user=current_user,
    )
    if not ok:
        if reason == "NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="摄像头不存在",
            )
        if reason == "SNAPSHOT_FAILED":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="抓拍失败，请检查 RTSP 是否可达",
            )
    return success_response({"snapshot_url": snapshot_url}, "抓拍成功")

