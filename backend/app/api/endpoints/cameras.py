# -*- coding: utf-8 -*-
"""
摄像头 API

提供摄像头 CRUD 和流媒体控制接口
"""
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.api.deps import get_current_user
from app.models import User, Camera, Area, CameraAlgorithm
from app.models.base import generate_uuid
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraStatusResponse,
    CameraPlayUrlResponse
)
from app.schemas.common import MessageResponse, success_response, page_response
from app.services.config_publisher import get_config_publisher
from app.services.stream_probe import probe_stream
from app.services.snapshot import save_snapshot
from common.media import get_stream_manager
from common.logging import logger
from common.storage import get_storage
from common.redis import RedisKeys


class ProbeStreamRequest(BaseModel):
    """流通性测试请求"""
    rtsp_url: str = Field(..., description="RTSP 流地址")
    rtsp_username: Optional[str] = Field(None, description="RTSP 用户名")
    rtsp_password: Optional[str] = Field(None, description="RTSP 密码")


router = APIRouter()


@router.get("", summary="获取摄像头列表")
async def get_cameras(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    area_id: Optional[str] = Query(None, description="区域ID"),
    status: Optional[str] = Query(None, description="状态"),
    keyword: Optional[str] = Query(None, description="关键词"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取摄像头列表
    
    支持按区域、状态、关键词筛选
    """
    # 构建查询
    query = select(Camera)
    count_query = select(func.count(Camera.id))
    
    # 筛选条件
    if area_id:
        query = query.where(Camera.area_id == area_id)
        count_query = count_query.where(Camera.area_id == area_id)
    
    if status:
        query = query.where(Camera.status == status)
        count_query = count_query.where(Camera.status == status)
    
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Camera.name.ilike(keyword_filter)) |
            (Camera.code.ilike(keyword_filter)) |
            (Camera.location.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Camera.name.ilike(keyword_filter)) |
            (Camera.code.ilike(keyword_filter)) |
            (Camera.location.ilike(keyword_filter))
        )
    
    # 统计总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 分页查询
    query = query.options(selectinload(Camera.area))
    query = query.order_by(Camera.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    cameras = result.scalars().all()
    
    # 构建响应
    data = []
    for camera in cameras:
        # 统计关联算法数量
        algo_count_result = await db.execute(
            select(func.count(CameraAlgorithm.id))
            .where(CameraAlgorithm.camera_id == camera.id)
        )
        algo_count = algo_count_result.scalar() or 0

        snapshot_url = None
        if getattr(camera, "last_snapshot_path", None):
            storage = get_storage()
            try:
                snapshot_url = storage.get_url(camera.last_snapshot_path)
            except Exception as e:
                logger.error(f"构建摄像头快照 URL 失败: {e}")
        data.append({
            "id": camera.id,
            "name": camera.name,
            "code": camera.code,
            "description": camera.description,
            "area_id": camera.area_id,
            "area_name": camera.area.name if camera.area else None,
            "rtsp_url": camera.rtsp_url,
            "manufacturer": camera.manufacturer,
            "device_model": camera.device_model,
            "ip_address": camera.ip_address,
            "location": camera.location,
            "longitude": camera.longitude,
            "latitude": camera.latitude,
            "fps": camera.fps,
            "resolution": camera.resolution,
            "is_enabled": camera.is_enabled,
            "status": camera.status,
            "algorithm_count": algo_count,
            "snapshot_url": snapshot_url,
            "created_at": camera.created_at.isoformat(),
            "updated_at": camera.updated_at.isoformat()
        })
    
    return page_response(data, page, page_size, total)


@router.post("/probe-stream", summary="流通性测试（获取宽高、帧率）")
async def probe_stream_info(
    body: ProbeStreamRequest = Body(...),
    current_user: User = Depends(get_current_user),
):
    """
    使用 OpenCV/ffprobe 探测 RTSP 流，返回宽、高、帧率等信息
    """
    result = probe_stream(
        body.rtsp_url,
        username=body.rtsp_username,
        password=body.rtsp_password,
        timeout_sec=10
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "流探测失败")
        )
    return success_response({
        "width": result["width"],
        "height": result["height"],
        "fps": result["fps"],
        "resolution": result["resolution"]
    })


@router.get("/{camera_id}", summary="获取摄像头详情")
async def get_camera(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取摄像头详情
    """
    result = await db.execute(
        select(Camera)
        .options(selectinload(Camera.area))
        .where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 统计关联算法数量
    algo_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id))
        .where(CameraAlgorithm.camera_id == camera.id)
    )
    algo_count = algo_count_result.scalar() or 0

    snapshot_url = None
    if getattr(camera, "last_snapshot_path", None):
        storage = get_storage()
        try:
            snapshot_url = storage.get_url(camera.last_snapshot_path)
        except Exception as e:
            logger.error(f"构建摄像头快照 URL 失败: {e}")
    return success_response({
        "id": camera.id,
        "name": camera.name,
        "code": camera.code,
        "description": camera.description,
        "area_id": camera.area_id,
        "area_name": camera.area.name if camera.area else None,
        "rtsp_url": camera.rtsp_url,
        "rtsp_username": camera.rtsp_username,
        "rtsp_password": camera.rtsp_password,
        "manufacturer": camera.manufacturer,
        "device_model": camera.device_model,
        "ip_address": camera.ip_address,
        "location": camera.location,
        "longitude": camera.longitude,
        "latitude": camera.latitude,
        "fps": camera.fps,
        "resolution": camera.resolution,
        "is_enabled": camera.is_enabled,
        "status": camera.status,
        "algorithm_count": algo_count,
        "snapshot_url": snapshot_url,
        "created_at": camera.created_at.isoformat(),
        "updated_at": camera.updated_at.isoformat()
    })


@router.post("", summary="创建摄像头")
async def create_camera(
    camera_data: CameraCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建摄像头
    """
    # 检查编码是否重复
    if camera_data.code:
        existing = await db.execute(
            select(Camera).where(Camera.code == camera_data.code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="摄像头编码已存在"
            )
    
    # 检查区域是否存在
    if camera_data.area_id:
        area_result = await db.execute(
            select(Area).where(Area.id == camera_data.area_id)
        )
        if area_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="区域不存在"
            )
    
    # 创建摄像头
    camera = Camera(
        id=generate_uuid(),
        name=camera_data.name,
        code=camera_data.code,
        description=camera_data.description,
        area_id=camera_data.area_id,
        rtsp_url=camera_data.rtsp_url,
        rtsp_username=camera_data.rtsp_username,
        rtsp_password=camera_data.rtsp_password,
        manufacturer=camera_data.manufacturer,
        device_model=camera_data.device_model,
        ip_address=camera_data.ip_address,
        location=camera_data.location,
        longitude=camera_data.longitude,
        latitude=camera_data.latitude,
        fps=camera_data.fps,
        resolution=camera_data.resolution,
        is_enabled=camera_data.is_enabled,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    
    # 注册流
    stream_manager = get_stream_manager()
    stream_manager.register_stream(camera.id, camera.full_rtsp_url)
    
    # 发布配置变更
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_add({
        "camera_id": camera.id,
        "name": camera.name,
        "rtsp_url": camera.full_rtsp_url,
        "fps": camera.fps,
        "is_enabled": camera.is_enabled
    })
    
    logger.info(f"摄像头已创建: {camera.id} - {camera.name}")
    
    return success_response({"id": camera.id}, "创建成功")


@router.put("/{camera_id}", summary="更新摄像头")
async def update_camera(
    camera_id: str,
    camera_data: CameraUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新摄像头
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 更新字段
    update_data = camera_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(camera, field, value)
    
    camera.updated_by = current_user.id
    
    await db.commit()
    
    # 发布配置变更
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_update({
        "camera_id": camera.id,
        "name": camera.name,
        "rtsp_url": camera.full_rtsp_url,
        "fps": camera.fps,
        "is_enabled": camera.is_enabled
    })
    
    logger.info(f"摄像头已更新: {camera.id}")
    
    return success_response(None, "更新成功")


@router.delete("/{camera_id}", summary="删除摄像头")
async def delete_camera(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除摄像头
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    await db.delete(camera)
    await db.commit()
    
    # 注销流
    stream_manager = get_stream_manager()
    stream_manager.unregister_stream(camera_id)
    
    # 发布配置变更
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_delete(camera_id)
    
    logger.info(f"摄像头已删除: {camera_id}")
    
    return success_response(None, "删除成功")


@router.post("/{camera_id}/start", summary="启动摄像头")
async def start_camera(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启动摄像头 (开始分析)
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )

    # 发布启动命令
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_start(camera_id)
    
    logger.info(f"摄像头启动命令已发送: {camera_id}")
    
    return success_response(None, "启动命令已发送")


@router.post("/{camera_id}/stop", summary="停止摄像头")
async def stop_camera(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    停止摄像头 (停止分析)
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )

    # 发布停止命令
    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_stop(camera_id)
    
    logger.info(f"摄像头停止命令已发送: {camera_id}")
    
    return success_response(None, "停止命令已发送")


@router.post("/{camera_id}/live-heartbeat", summary="摄像头直播心跳")
async def camera_live_heartbeat(
    camera_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    前端播放摄像头直播流时每 60 秒调用一次，用于保活。
    后端仅记录心跳时间，后续可由后台任务检测超时并通知 Engine 停止推流/管道。
    """
    redis = get_redis()
    import time
    ts = int(time.time())
    key = RedisKeys.camera_live_heartbeat(camera_id)
    await redis.client.set(key, str(ts))
    return success_response({"camera_id": camera_id, "timestamp": ts}, "心跳已更新")


@router.get("/{camera_id}/play-url", summary="获取播放地址")
async def get_play_url(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取摄像头播放地址
    
    返回 HTTP-FLV、RTSP、HLS 等多种格式的播放地址
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    
    # 获取播放地址
    stream_manager = get_stream_manager()
    urls = stream_manager.get_play_urls(camera_id)
    
    return success_response({
        "camera_id": camera_id,
        "flv_url": urls.get("flv"),
        "rtsp_url": urls.get("rtsp"),
        "hls_url": urls.get("hls")
    })


@router.post("/{camera_id}/snapshot", summary="抓拍")
async def camera_snapshot(
    camera_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    从摄像头 RTSP 流抓拍一帧，保存为最新抓拍图，列表页将显示此图
    """
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    if camera is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="摄像头不存在"
        )
    save_dir = Path(settings.LOCAL_STORAGE_PATH) / "snapshots"
    ok, storage_key = save_snapshot(
        camera_id,
        camera.rtsp_url,
        username=camera.rtsp_username,
        password=camera.rtsp_password,
        save_dir=save_dir,
    )
    if not ok or not storage_key:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="抓拍失败，请检查 RTSP 是否可达"
        )
    camera.last_snapshot_path = storage_key
    camera.updated_by = current_user.id
    await db.commit()
    storage = get_storage()
    snapshot_url = storage.get_url(storage_key)
    logger.info(f"摄像头抓拍已保存: {camera_id} -> {storage_key}")
    return success_response({"snapshot_url": snapshot_url}, "抓拍成功")
