# -*- coding: utf-8 -*-
"""
Redis 模块

职责：
- 提供 FastAPI 应用的 Redis 连接管理（init/close/get）
- 封装常用的 Redis 写操作（模型/算法/摄像头相关），集中管理，便于后期维护与修改
"""
from typing import Optional, List, Dict, Any, Set
import json
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.redis import RedisClient, get_redis_client, RedisKeys
from common.utils.json_utils import to_json
from common.logging import logger
from app.models import Model, Algorithm, Camera


# 全局 Redis 客户端实例（由 FastAPI 生命周期管理）
redis_client: Optional[RedisClient] = None


async def init_redis() -> None:
    """
    初始化 Redis 连接。
    在 FastAPI 应用启动时调用。
    """
    global redis_client
    redis_client = get_redis_client()
    await redis_client.connect()
    logger.info("Redis 连接已初始化")


async def close_redis() -> None:
    """
    关闭 Redis 连接。
    在 FastAPI 应用关闭时调用。
    """
    global redis_client
    if redis_client is not None:
        await redis_client.disconnect()
        redis_client = None
        logger.info("Redis 连接已关闭")


def get_redis() -> RedisClient:
    """
    获取 Redis 客户端。

    Returns:
        RedisClient 实例
    """
    global redis_client
    if redis_client is None:
        redis_client = get_redis_client()
    return redis_client


# ===================== 模型 / 算法 =====================

async def write_model_to_redis(model_id: str, db: AsyncSession) -> None:
    """
    根据 model_id 读取模型及其算法列表，组装完整配置后写入 Redis。

    存储结构示例（model:config:{model_id}）:
    {
      "id": "...",
      "code": "...",
      "name": "...",
      "model_type": "...",
      "model_path": "...",
      "classes": [...],         # 保留原始 classes 列表，兼容旧逻辑
      "is_enabled": true,
      "algorithms": [           # 模型下算法列表，供 Engine 使用
        {
          "id": "algo_1",
          "code": "helmet_detect",
          "name": "安全帽检测",
          "target_classes": ["person"]
        },
        ...
      ]
    }
    """
    # 查询模型
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None:
        logger.warning(f"write_model_to_redis: 模型不存在: {model_id}")
        return

    # 查询该模型下所有算法
    algo_result = await db.execute(
        select(Algorithm).where(Algorithm.model_id == model_id)
    )
    algos = algo_result.scalars().all()
    algo_objs: List[Dict[str, Any]] = []
    for a in algos:
        targets = a.target_classes or []
        algo_objs.append(
            {
                "id": a.id,
                "code": a.code,
                "name": a.name,
                "target_classes": list(targets),
            }
        )

    # 写入 Redis
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.model_config(model.id),
            json.dumps(
                {
                    "id": model.id,
                    "code": model.code,
                    "name": model.name,
                    "model_type": model.model_type,
                    "model_path": model.model_path,
                    "classes": list(model.classes or []),
                    "is_enabled": model.is_enabled,
                    "algorithms": algo_objs,
                },
                ensure_ascii=False,
            ),
        )
        logger.info(
            f"已写入模型配置到 Redis: model_id={model.id}, algorithms={len(algo_objs)}"
        )
    except Exception as e:
        logger.error(f"写入模型配置到 Redis 失败: {e}")


async def write_algorithm_to_redis(algo: Algorithm) -> None:
    """
    将单个算法配置写入 Redis: algorithm:config:{algo_id}
    """
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.algorithm_config(algo.id),
            json.dumps(
                {
                    "id": algo.id,
                    "code": algo.code,
                    "name": algo.name,
                    "model_id": algo.model_id,
                    "target_classes": list(algo.target_classes or []),
                    "default_confidence": algo.default_confidence,
                    "alert_config": algo.alert_config,
                    "is_enabled": algo.is_enabled,
                },
                ensure_ascii=False,
            ),
        )
        logger.info(f"已写入算法配置到 Redis: algo_id={algo.id}")
    except Exception as e:
        logger.error(f"写入算法配置到 Redis 失败: {e}")


async def delete_algorithm_from_redis(algorithm_id: str) -> None:
    """
    从 Redis 中删除单个算法配置: algorithm:config:{algorithm_id}
    """
    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.algorithm_config(algorithm_id))
        logger.info(f"已从 Redis 删除算法配置: algo_id={algorithm_id}")
    except Exception as e:
        logger.error(f"从 Redis 删除算法配置失败: {e}")


# ===================== 摄像头相关 =====================

async def get_inference_started_camera_ids() -> Set[str]:
    """
    获取当前已启动推理的摄像头 ID 集合（来自 Redis 集合 CAMERAS_INFERENCE_STARTED）。
    """
    try:
        redis = get_redis()
        members = await redis.client.smembers(RedisKeys.CAMERAS_INFERENCE_STARTED)
        return {
            x.decode() if isinstance(x, (bytes, bytearray)) else str(x)
            for x in (members or [])
        }
    except Exception as e:
        logger.warning(f"读取推理启动集合失败，将忽略: {e}")
        return set()


async def is_camera_inference_started(camera_id: str) -> bool:
    """
    判断某摄像头是否在“推理已启动”集合中。
    """
    try:
        redis = get_redis()
        return bool(
            await redis.client.sismember(
                RedisKeys.CAMERAS_INFERENCE_STARTED, camera_id
            )
        )
    except Exception as e:
        logger.warning(f"读取推理启动状态失败，将忽略: {e}")
        return False


async def add_camera_inference_started(camera_id: str) -> None:
    """
    将摄像头加入“推理已启动”集合。
    """
    try:
        redis = get_redis()
        await redis.client.sadd(RedisKeys.CAMERAS_INFERENCE_STARTED, camera_id)
    except Exception as e:
        logger.error(f"记录推理启动集合失败: {camera_id}, 错误: {e}")


async def remove_camera_inference_started(camera_id: str) -> None:
    """
    将摄像头从“推理已启动”集合中移除。
    """
    try:
        redis = get_redis()
        await redis.client.srem(RedisKeys.CAMERAS_INFERENCE_STARTED, camera_id)
    except Exception as e:
        logger.error(f"从推理启动集合移除失败: {camera_id}, 错误: {e}")


async def write_camera_to_redis(camera: Camera) -> None:
    """
    将摄像头基础配置写入 Redis: camera:config:{camera_id}
    """
    try:
        redis = get_redis()
        await redis.client.set(
            RedisKeys.camera_config(camera.id),
            json.dumps(
                {
                    "id": camera.id,
                    "name": camera.name,
                    "rtsp_url": camera.full_rtsp_url,
                    "fps": camera.fps,
                    "inference_interval_sec": getattr(camera, "inference_interval_sec", 5),
                    "is_enabled": camera.is_enabled,
                },
                ensure_ascii=False,
            ),
        )
        logger.info(f"已写入摄像头配置到 Redis: camera_id={camera.id}")
    except Exception as e:
        logger.error(f"摄像头写入 Redis 失败: {camera.id}, 错误: {e}")


async def delete_camera_from_redis(camera_id: str) -> None:
    """
    从 Redis 中删除摄像头配置: camera:config:{camera_id}
    """
    try:
        redis = get_redis()
        await redis.client.delete(RedisKeys.camera_config(camera_id))
        logger.info(f"已从 Redis 删除摄像头配置: camera_id={camera_id}")
    except Exception as e:
        logger.error(f"从 Redis 删除摄像头配置失败: {camera_id}, 错误: {e}")


# ===================== 告警相关（Engine → AlarmConsumer） =====================


def push_alarm_to_queue_sync(alarm: Dict[str, Any]) -> None:
    """
    将告警对象同步写入 Redis 告警队列（alarm_queue）。

    供 Engine 调度器（或其他同步上下文）调用，统一通过 app.core.redis 访问 Redis。
    """
    try:
        redis = get_redis()
        payload = to_json(alarm, ensure_ascii=False)
        redis.rpush_sync(RedisKeys.ALARM_QUEUE, payload)
    except Exception as e:
        logger.error(f"push_alarm_to_queue_sync 写入 Redis 告警队列失败: {e}")


async def is_camera_online(camera_id: str) -> bool:
    """
    判断摄像头是否在线（根据 live_heartbeat_monitor 设置的 camera:online:{id} 键）。
    """
    try:
        redis = get_redis()
        key = f"camera:online:{camera_id}"
        exists = await redis.client.exists(key)
        return bool(exists)
    except Exception as e:
        logger.warning(f"读取摄像头在线状态失败: {camera_id}, err={e}")
        return False


async def get_online_camera_ids() -> Set[str]:
    """
    获取当前在线的摄像头 ID 集合（根据 camera:online:{id} 键前缀扫描）。
    """
    try:
        redis = get_redis()
        pattern = "camera:online:*"
        ids: Set[str] = set()
        async for key in redis.client.scan_iter(match=pattern):
            # key 形如 "camera:online:{id}"
            if isinstance(key, bytes):
                key = key.decode("utf-8", errors="ignore")
            parts = str(key).split(":")
            if len(parts) >= 3:
                ids.add(parts[-1])
        return ids
    except Exception as e:
        logger.warning(f"扫描在线摄像头失败: {e}")
        return set()


async def add_camera_live_started(camera_id: str, live_set_ttl_sec: int) -> None:
    """
    将摄像头加入“直播已启动”集合，并为集合设置过期时间。
    live_set_ttl_sec 为集合 TTL（秒），<=0 则不设置 TTL。
    """
    try:
        redis = get_redis()
        await redis.client.sadd(RedisKeys.CAMERAS_LIVE_STARTED, camera_id)
        if live_set_ttl_sec > 0:
            await redis.client.expire(RedisKeys.CAMERAS_LIVE_STARTED, live_set_ttl_sec)
    except Exception as e:
        logger.error(f"记录直播启动集合失败: {camera_id}, 错误: {e}")


async def remove_camera_live_started(camera_id: str) -> None:
    """
    将摄像头从“直播已启动”集合中移除。
    """
    try:
        redis = get_redis()
        await redis.client.srem(RedisKeys.CAMERAS_LIVE_STARTED, camera_id)
    except Exception as e:
        logger.error(f"从直播集合移除失败: {camera_id}, 错误: {e}")


async def update_camera_live_heartbeat(
    camera_id: str, heartbeat_timeout_sec: int
) -> int:
    """
    刷新摄像头直播心跳 Key 的 TTL，并返回使用的时间戳。
    """
    ts = int(time.time())
    try:
        redis = get_redis()
        key = RedisKeys.camera_live_heartbeat(camera_id)
        await redis.client.set(key, str(ts), ex=heartbeat_timeout_sec)
    except Exception as e:
        logger.error(f"更新摄像头直播心跳失败: {camera_id}, 错误: {e}")
    return ts


# ===================== 通知推送配置快照（按条更新，不查全表） =====================
# 使用 Hash：key 为快照键，field 为 id，value 为单条 JSON。增/改 HSET 一条，删 HDEL 一条。
# 消费方 HGETALL 后对 value 做 json.loads 即得列表。


async def set_notification_endpoint_in_redis(item: Dict[str, Any]) -> None:
    """
    新增或更新单条推送通道到 Redis。不查库、不循环，只写一条。
    Hash key: NOTIFICATION_ENDPOINTS_SNAPSHOT，field: id，value: JSON。
    """
    endpoint_id = str((item or {}).get("id") or "").strip()
    if not endpoint_id:
        return
    try:
        redis = get_redis()
        await redis.client.hset(
            RedisKeys.NOTIFICATION_ENDPOINTS_SNAPSHOT,
            endpoint_id,
            json.dumps(item, ensure_ascii=False),
        )
    except Exception as e:
        logger.warning(f"写入推送通道到 Redis 失败: {endpoint_id}, {e}")


async def delete_notification_endpoint_from_redis(endpoint_id: str) -> None:
    """从 Redis 删除单条推送通道。只 HDEL 一条。"""
    try:
        redis = get_redis()
        await redis.client.hdel(RedisKeys.NOTIFICATION_ENDPOINTS_SNAPSHOT, endpoint_id)
    except Exception as e:
        logger.warning(f"从 Redis 删除推送通道失败: {endpoint_id}, {e}")


async def set_notification_template_in_redis(item: Dict[str, Any]) -> None:
    """
    新增或更新单条推送模板到 Redis。不查库、不循环，只写一条。
    Hash key: NOTIFICATION_TEMPLATES_SNAPSHOT，field: id，value: JSON。
    """
    template_id = str((item or {}).get("id") or "").strip()
    if not template_id:
        return
    try:
        redis = get_redis()
        await redis.client.hset(
            RedisKeys.NOTIFICATION_TEMPLATES_SNAPSHOT,
            template_id,
            json.dumps(item, ensure_ascii=False),
        )
    except Exception as e:
        logger.warning(f"写入推送模板到 Redis 失败: {template_id}, {e}")


async def delete_notification_template_from_redis(template_id: str) -> None:
    """从 Redis 删除单条推送模板。只 HDEL 一条。"""
    try:
        redis = get_redis()
        await redis.client.hdel(RedisKeys.NOTIFICATION_TEMPLATES_SNAPSHOT, template_id)
    except Exception as e:
        logger.warning(f"从 Redis 删除推送模板失败: {template_id}, {e}")


async def set_notification_policy_in_redis(item: Dict[str, Any]) -> None:
    """
    新增或更新单条推送策略到 Redis。不查库、不循环，只写一条。
    Hash key:
    - 按类别拆分：NOTIFICATION_POLICIES_AI_SNAPSHOT / NOTIFICATION_POLICIES_SYSTEM_SNAPSHOT
    - field: id，value: JSON
    """
    policy_id = str((item or {}).get("id") or "").strip()
    if not policy_id:
        return
    try:
        redis = get_redis()
        match = (item or {}).get("match") or {}
        category = str(match.get("category") or "").strip().lower() or "ai"
        if category == "system":
            key = RedisKeys.NOTIFICATION_POLICIES_SYSTEM_SNAPSHOT
        else:
            key = RedisKeys.NOTIFICATION_POLICIES_AI_SNAPSHOT

        await redis.client.hset(key, policy_id, json.dumps(item, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"写入推送策略到 Redis 失败: {policy_id}, {e}")


async def delete_notification_policy_from_redis(policy_id: str) -> None:
    """从 Redis 删除单条推送策略。两个类别 Hash 中都尝试删除。"""
    try:
        redis = get_redis()
        await redis.client.hdel(
            RedisKeys.NOTIFICATION_POLICIES_AI_SNAPSHOT, policy_id
        )
        await redis.client.hdel(
            RedisKeys.NOTIFICATION_POLICIES_SYSTEM_SNAPSHOT, policy_id
        )
    except Exception as e:
        logger.warning(f"从 Redis 删除推送策略失败: {policy_id}, {e}")


def delete_camera_area_paths_from_redis(camera_id: str) -> None:
    """删除摄像头区域路径缓存（摄像头变更或所属区域变更时调用）。"""
    if not camera_id:
        return
    try:
        get_redis().sync_client.delete(RedisKeys.camera_area_paths(camera_id))
    except Exception as e:
        logger.warning(f"删除摄像头区域路径缓存失败: camera_id={camera_id}, {e}")


def delete_camera_area_paths_for_cameras(camera_ids: List[str]) -> None:
    """批量删除摄像头区域路径缓存（区域树变更时调用）。"""
    if not camera_ids:
        return
    try:
        client = get_redis().sync_client
        for cid in camera_ids:
            if cid:
                client.delete(RedisKeys.camera_area_paths(cid))
    except Exception as e:
        logger.warning(f"批量删除摄像头区域路径缓存失败: {e}")
