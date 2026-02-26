# -*- coding: utf-8 -*-
"""
直播心跳超时检测

后台任务：定期检查「已启动直播」的摄像头是否仍在心跳有效期内；
若某路超时未收到心跳，则从集合移除并通知 Engine 关闭该路推流。
"""
import asyncio
from typing import Any, Set

from common.logging import logger
from common.redis import RedisKeys
from app.core.redis import get_redis
from app.services.config_publisher import get_config_publisher


# 检测间隔（秒）
CHECK_INTERVAL_SEC = 45


async def _run_heartbeat_check() -> None:
    """执行一次心跳超时检测"""
    try:
        redis = get_redis()
        client = redis.client
        # 获取当前在“直播已启动”集合中的摄像头（decode_responses 时为 str）
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
