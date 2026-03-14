# -*- coding: utf-8 -*-
"""
直播心跳超时检测

后台任务：
1. 定期遍历所有摄像头，通过抓拍更新 Redis 中的在线状态（camera:online:{id}）；
2. 当在线状态发生「上线/掉线」边沿变化时，写入系统告警到 notification_queue；
3. 检查「已启动直播」但心跳过期的摄像头，从集合移除并通知 Engine 关闭该路推流。
"""
import asyncio
import json
import time
from typing import Any, Set

from common.logging import logger
from common.redis import RedisKeys
from app.core.redis import get_redis
from app.services.config_publisher import get_config_publisher
from config.settings import settings


# 检测间隔（秒）
CHECK_INTERVAL_SEC = 45


async def _run_heartbeat_check() -> None:
    """
    执行一次心跳检测与在线状态更新：
    1. 遍历所有摄像头，尝试抓拍更新快照：成功则在 Redis 中标记 ONLINE 状态（TTL=100s），失败则删除 ONLINE 状态；
    2. 在此基础上继续执行原有的直播心跳超时检测逻辑。
    """
    try:
        from sqlalchemy import select
        from app.core.database import get_db_session
        from app.models import Camera
        from app.services.snapshot import save_snapshot
        logger.info("开始执行心跳检测")
        redis = get_redis()
        client = redis.client

        # 1. 遍历所有摄像头，基于抓拍更新“在线状态”
        async with get_db_session() as session:
            result = await session.execute(select(Camera))
            cameras = result.scalars().all()

        for cam in cameras:
            camera_id = cam.id
            camera_name = cam.name
            ok, _ = save_snapshot(
                camera_id=camera_id,
                rtsp_url=cam.full_rtsp_url,
                save_dir=None,  # 已不再使用本地目录
                username=None,
                password=None,
            )
            online_key = f"camera:online:{camera_id}"
            was_online = bool(await client.exists(online_key))
            if ok:
                # 抓拍成功，认为流正常：设置在线状态 TTL=100s
                await client.set(online_key, "1", ex=100)
                now_online = True
            else:
                # 抓拍失败：删除在线状态
                await client.delete(online_key)
                now_online = False

            # 在线状态发生变化时，写入系统告警事件到 notification_queue（camera_online/camera_offline）
            if was_online != now_online:
                logger.info(f"摄像头{camera_name}（{camera_id}）在线状态发生变化: was_online={was_online}, now_online={now_online}")
                try:
                    from app.services.notification_service import enqueue_notification_event

                    payload = {
                        "category": "system",
                        "alarm_id": f"camera_{'online' if now_online else 'offline'}_{camera_id}_{int(time.time())}",
                        "alarm_type": "camera_online" if now_online else "camera_offline",
                        "level": "info" if now_online else "warning",
                        "camera_id": camera_id,
                        "camera_name": camera_name,
                        # 目前仅携带名称，后续可升级为完整层级路径
                        "area_id_path": None,
                        "area_name_path": None,
                        "area_name": None,
                        "algorithm_id": None,
                        "algorithm_name": None,
                        "title": f"摄像头{'上线' if now_online else '掉线'}",
                        "text": f"摄像头 {camera_name}已{'恢复在线' if now_online else '离线'}。",
                        "image_url": None,
                        "link_url": None,
                    }
                    enqueue_notification_event(payload)
                except Exception as e:
                    logger.warning(f"写入摄像头在线状态系统告警失败: camera_id={camera_id}, err={e}")

        # 2. 原有逻辑：检查“已启动直播”但心跳过期的摄像头，通知 Engine 停止推流
        members: Set[Any] = await client.smembers(RedisKeys.CAMERAS_LIVE_STARTED)
        if not members:
            return
        publisher = get_config_publisher()
        for raw_id in members:
            try:
                camera_id = raw_id.decode("utf-8") if isinstance(raw_id, bytes) else str(raw_id)
            except Exception:
                continue
            key = RedisKeys.camera_live_heartbeat(camera_id)
            exists = await client.exists(key)
            if exists:
                continue
            # 心跳已过期，从集合移除并通知 Engine 停止推流
            await client.srem(RedisKeys.CAMERAS_LIVE_STARTED, camera_id)
            await publisher.publish_camera_stop(camera_id)
            logger.info(f"直播心跳超时，已通知 Engine 关闭推流: camera_id={camera_id}")
    except Exception as e:
        logger.error(f"直播心跳检测异常: {e}")


async def live_heartbeat_monitor_loop() -> None:
    """后台循环：按间隔执行心跳超时检测"""
    logger.info("直播心跳超时检测任务已启动")
    while True:
        try:
            await asyncio.sleep(CHECK_INTERVAL_SEC)
            await _run_heartbeat_check()
        except asyncio.CancelledError:
            logger.info("直播心跳超时检测任务已停止")
            break
        except Exception as e:
            logger.error(f"直播心跳检测任务异常: {e}")


# 全局任务句柄，用于 lifespan 中取消
_monitor_task: asyncio.Task = None


def start_live_heartbeat_monitor() -> asyncio.Task:
    """启动心跳检测后台任务"""
    global _monitor_task
    if _monitor_task is not None and not _monitor_task.done():
        return _monitor_task
    _monitor_task = asyncio.create_task(live_heartbeat_monitor_loop())
    return _monitor_task


def stop_live_heartbeat_monitor() -> None:
    """停止心跳检测后台任务（lifespan 关闭时 cancel，由事件循环自然结束）"""
    global _monitor_task
    if _monitor_task is None:
        return
    _monitor_task.cancel()
    _monitor_task = None
