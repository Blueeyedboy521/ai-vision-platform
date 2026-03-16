# -*- coding: utf-8 -*-
"""
摄像头业务逻辑：
- 列表 / 详情 / CRUD
- 推理控制、流控制、心跳与抓拍
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from app.core.redis import (
    get_inference_started_camera_ids,
    is_camera_inference_started,
    add_camera_inference_started,
    remove_camera_inference_started,
    write_camera_to_redis,
    delete_camera_from_redis,
    add_camera_live_started,
    remove_camera_live_started,
    update_camera_live_heartbeat,
    is_camera_online,
    delete_camera_area_paths_from_redis,
)
from app.models import Camera, Area, CameraAlgorithm, User
from app.models.base import generate_uuid
from app.schemas.camera import CameraCreate, CameraUpdate
from app.services.config_publisher import get_config_publisher
from app.services.stream_probe import probe_stream
from app.services.snapshot import save_snapshot
from common.media import get_stream_manager
from common.logging import logger
from common.storage import get_storage


async def list_cameras(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    area_id: Optional[str],
    status: Optional[str],
    keyword: Optional[str],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取摄像头列表及总数。
    """
    query = select(Camera)
    count_query = select(func.count(Camera.id))

    if area_id:
        query = query.where(Camera.area_id == area_id)
        count_query = count_query.where(Camera.area_id == area_id)

    if status:
        query = query.where(Camera.status == status)
        count_query = count_query.where(Camera.status == status)

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.where(
            (Camera.name.ilike(keyword_filter))
            | (Camera.code.ilike(keyword_filter))
            | (Camera.location.ilike(keyword_filter))
        )
        count_query = count_query.where(
            (Camera.name.ilike(keyword_filter))
            | (Camera.code.ilike(keyword_filter))
            | (Camera.location.ilike(keyword_filter))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Camera.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    cameras = result.scalars().all()

    inference_started: set[str] = await get_inference_started_camera_ids()

    data: List[Dict[str, Any]] = []
    for camera in cameras:
        algo_count_result = await db.execute(
            select(func.count(CameraAlgorithm.id)).where(
                CameraAlgorithm.camera_id == camera.id
            )
        )
        algo_count = algo_count_result.scalar() or 0

        snapshot_url = None
        if getattr(camera, "last_snapshot_path", None):
            storage = get_storage()
            try:
                snapshot_url = storage.get_url(camera.last_snapshot_path)
            except Exception as e:
                logger.error(f"构建摄像头快照 URL 失败: {e}")

        online = await is_camera_online(camera.id)

        data.append(
            {
                "id": camera.id,
                "name": camera.name,
                "code": camera.code,
                "description": camera.description,
                "area_id": camera.area_id,
                "area_name": None,
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
                "online": online,
                "inference_started": camera.id in inference_started,
                "algorithm_count": algo_count,
                "snapshot_url": snapshot_url,
                "created_at": camera.created_at.isoformat(),
                "updated_at": camera.updated_at.isoformat(),
            }
        )

    return data, total


async def probe_stream_info_data(rtsp_url: str) -> Dict[str, Any]:
    """
    探测 RTSP 流信息。
    """
    result = probe_stream(
        rtsp_url,
        username=None,
        password=None,
        timeout_sec=10,
    )
    return result


async def get_camera_detail(
    db: AsyncSession,
    camera_id: str,
) -> Optional[Dict[str, Any]]:
    """
    获取摄像头详情。
    """
    result = await db.execute(
        select(Camera)
        .options(selectinload(Camera.area))
        .where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    if camera is None:
        return None

    algo_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id)).where(
            CameraAlgorithm.camera_id == camera.id
        )
    )
    algo_count = algo_count_result.scalar() or 0

    snapshot_url = None
    if getattr(camera, "last_snapshot_path", None):
        storage = get_storage()
        try:
            snapshot_url = storage.get_url(camera.last_snapshot_path)
        except Exception as e:
            logger.error(f"构建摄像头快照 URL 失败: {e}")

    inference_started = await is_camera_inference_started(camera_id)
    online = await is_camera_online(camera_id)

    return {
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
        "inference_interval_sec": getattr(
            camera, "inference_interval_sec", 5
        ),
        "is_enabled": camera.is_enabled,
        "status": camera.status,
        "online": online,
        "inference_started": inference_started,
        "algorithm_count": algo_count,
        "snapshot_url": snapshot_url,
        "created_at": camera.created_at.isoformat(),
        "updated_at": camera.updated_at.isoformat(),
    }


async def start_camera_inference_action(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    启动摄像头推理。
    返回 (ok, error_code)
    - "NOT_FOUND"
    - "NOT_ENABLED"
    - "NO_ENABLED_ALGORITHM"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"
    if not camera.is_enabled:
        return False, "NOT_ENABLED"

    algo_count_result = await db.execute(
        select(func.count(CameraAlgorithm.id)).where(
            CameraAlgorithm.camera_id == camera_id,
            CameraAlgorithm.is_enabled == True,  # noqa: E712
        )
    )
    enabled_algo_count = algo_count_result.scalar() or 0
    if enabled_algo_count <= 0:
        return False, "NO_ENABLED_ALGORITHM"

    await add_camera_inference_started(camera_id)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_inference_start(camera_id)
    logger.info(f"摄像头推理启动命令已发送: {camera_id}")
    return True, None


async def stop_camera_inference_action(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    停止摄像头推理。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"

    await remove_camera_inference_started(camera_id)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_inference_stop(camera_id)
    logger.info(f"摄像头推理停止命令已发送: {camera_id}")
    return True, None


async def create_camera_record(
    db: AsyncSession,
    camera_data: CameraCreate,
    current_user: User,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    创建摄像头。
    返回 (ok, error_code, camera_id)
    - "CODE_EXISTS"
    - "AREA_NOT_FOUND"
    """
    if camera_data.code:
        existing = await db.execute(
            select(Camera).where(Camera.code == camera_data.code)
        )
        if existing.scalar_one_or_none():
            return False, "CODE_EXISTS", None

    if camera_data.area_id:
        area_result = await db.execute(
            select(Area).where(Area.id == camera_data.area_id)
        )
        if area_result.scalar_one_or_none() is None:
            return False, "AREA_NOT_FOUND", None

    camera = Camera(
        id=generate_uuid(),
        name=camera_data.name,
        code=camera_data.code,
        description=camera_data.description,
        area_id=camera_data.area_id,
        rtsp_url=camera_data.rtsp_url,
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
        updated_by=current_user.id,
    )

    db.add(camera)
    await db.commit()

    await write_camera_to_redis(camera)
    delete_camera_area_paths_from_redis(camera.id)

    stream_manager = get_stream_manager()
    stream_manager.register_stream(camera.id, camera.full_rtsp_url)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_add(
        {
            "camera_id": camera.id,
            "name": camera.name,
            "rtsp_url": camera.full_rtsp_url,
            "fps": camera.fps,
            "is_enabled": camera.is_enabled,
        }
    )

    logger.info(f"摄像头已创建: {camera.id} - {camera.name}")
    return True, None, camera.id


async def update_camera_record(
    db: AsyncSession,
    camera_id: str,
    camera_data: CameraUpdate,
    current_user: User,
) -> Tuple[bool, Optional[str]]:
    """
    更新摄像头。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"

    update_data = camera_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    camera.updated_by = current_user.id
    await db.commit()

    if not camera.is_enabled:
        await remove_camera_live_started(camera.id)
        config_publisher = get_config_publisher()
        await config_publisher.publish_camera_stop(camera.id)
        logger.info(f"摄像头已禁用，已发送停止命令: {camera.id}")

    await write_camera_to_redis(camera)
    delete_camera_area_paths_from_redis(camera_id)

    stream_manager = get_stream_manager()
    stream_manager.register_stream(camera.id, camera.full_rtsp_url)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_update(
        {
            "camera_id": camera.id,
            "name": camera.name,
            "rtsp_url": camera.full_rtsp_url,
            "fps": camera.fps,
            "is_enabled": camera.is_enabled,
        }
    )

    logger.info(f"摄像头已更新: {camera.id}")
    return True, None


async def delete_camera_record(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    删除摄像头。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"

    await db.delete(camera)
    await db.commit()

    await remove_camera_live_started(camera_id)
    await delete_camera_from_redis(camera_id)
    delete_camera_area_paths_from_redis(camera_id)

    stream_manager = get_stream_manager()
    stream_manager.unregister_stream(camera_id)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_delete(camera_id)

    logger.info(f"摄像头已删除: {camera_id}")
    return True, None


async def start_camera_action(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    启动摄像头。
    返回 (ok, error_code)
    - "NOT_FOUND"
    - "NOT_ENABLED"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"
    if not camera.is_enabled:
        return False, "NOT_ENABLED"

    await add_camera_live_started(camera_id, live_set_ttl_sec=60)
    await update_camera_live_heartbeat(camera_id, LIVE_HEARTBEAT_TIMEOUT_SEC)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_start(camera_id)

    logger.info(f"摄像头启动命令已发送: {camera_id}")
    return True, None


async def stop_camera_action(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    停止摄像头。
    返回 (ok, error_code)
    - "NOT_FOUND"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND"

    await remove_camera_live_started(camera_id)

    config_publisher = get_config_publisher()
    await config_publisher.publish_camera_stop(camera_id)

    logger.info(f"摄像头停止命令已发送: {camera_id}")
    return True, None


LIVE_HEARTBEAT_TIMEOUT_SEC = 90


async def update_live_heartbeat(camera_id: str) -> Dict[str, Any]:
    """
    更新摄像头直播心跳。
    """
    ts = await update_camera_live_heartbeat(camera_id, LIVE_HEARTBEAT_TIMEOUT_SEC)
    return {"camera_id": camera_id, "timestamp": ts}


async def get_camera_play_urls(
    db: AsyncSession,
    camera_id: str,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    获取摄像头播放地址。
    返回 (ok, error_code, data)
    - "NOT_FOUND"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND", None

    stream_manager = get_stream_manager()
    urls = stream_manager.get_play_urls(camera_id)

    return True, None, {
        "camera_id": camera_id,
        "flv_url": urls.get("flv"),
        "rtsp_url": urls.get("rtsp"),
        "hls_url": urls.get("hls"),
    }


async def snapshot_camera(
    db: AsyncSession,
    camera_id: str,
    current_user: User,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    抓拍摄像头。
    返回 (ok, error_code, snapshot_url)
    - "NOT_FOUND"
    - "SNAPSHOT_FAILED"
    """
    result = await db.execute(select(Camera).where(Camera.id == camera_id))
    camera = result.scalar_one_or_none()
    if camera is None:
        return False, "NOT_FOUND", None

    save_dir = Path(settings.LOCAL_STORAGE_PATH) / "snapshots"
    ok, storage_key = save_snapshot(
        camera_id,
        camera.rtsp_url,
        username=None,
        password=None,
        save_dir=save_dir,
    )
    if not ok or not storage_key:
        return False, "SNAPSHOT_FAILED", None

    camera.last_snapshot_path = storage_key
    camera.updated_by = current_user.id
    await db.commit()

    storage = get_storage()
    snapshot_url = storage.get_url(storage_key)
    logger.info(f"摄像头抓拍已保存: {camera_id} -> {storage_key}")
    return True, None, snapshot_url

