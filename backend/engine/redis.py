# -*- coding: utf-8 -*-
"""
Engine Redis 模块

职责：
- 封装 Engine 进程内所有 Redis 操作（同步客户端），高内聚低耦合
- 供 Scheduler、StreamWriter、Inferencer 等调用，不直接操作 redis client
"""
import json
from typing import Any, Dict, List, Optional, Set

from common.redis import get_redis_client, RedisChannels, RedisKeys
from common.logging import logger


def get_sync_client():
    """获取已连接的同步 Redis 客户端（供 Pub/Sub 等需直接操作 client 的场景使用）"""
    client = get_redis_client()
    client.connect_sync()
    return client.sync_client


def _get_sync_client():
    return get_sync_client()


def _key_str(k) -> str:
    """将 Redis key 转为 str"""
    return k.decode() if isinstance(k, (bytes, bytearray)) else str(k)


def _val_str(v) -> str:
    """将 Redis value 转为 str（用于 json.loads）"""
    return v.decode() if isinstance(v, (bytes, bytearray)) else str(v)


def _decode_members(members: Any) -> Set[str]:
    """将 Redis smembers 结果解码为 str 集合"""
    if not members:
        return set()
    return {
        x.decode() if isinstance(x, (bytes, bytearray)) else str(x)
        for x in members
    }


# ===================== 直播 / 推理状态 =====================


def mark_camera_live_started(camera_id: str, live_set_ttl_sec: int = 60) -> None:
    """
    将摄像头加入「直播已启动」集合，并为集合设置 TTL。
    StreamWriter 推流时调用，供心跳监控感知当前仍有推流。
    """
    try:
        r = _get_sync_client()
        r.sadd(RedisKeys.CAMERAS_LIVE_STARTED, camera_id)
        r.expire(RedisKeys.CAMERAS_LIVE_STARTED, live_set_ttl_sec)
    except Exception as e:
        logger.warning(f"标记推流状态到 Redis 失败: camera_id={camera_id}, err={e}")


def get_live_started_camera_ids() -> Set[str]:
    """获取「直播已启动」集合中的摄像头 ID"""
    try:
        r = _get_sync_client()
        members = r.smembers(RedisKeys.CAMERAS_LIVE_STARTED) or []
        return _decode_members(members)
    except Exception as e:
        logger.warning(f"读取直播启动集合失败: {e}")
        return set()


def get_inference_started_camera_ids() -> Set[str]:
    """获取「推理已启动」集合中的摄像头 ID"""
    try:
        r = _get_sync_client()
        members = r.smembers(RedisKeys.CAMERAS_INFERENCE_STARTED) or []
        return _decode_members(members)
    except Exception as e:
        logger.warning(f"读取推理启动集合失败: {e}")
        return set()


def is_camera_heartbeat_active(camera_id: str) -> bool:
    """判断摄像头直播心跳 Key 是否存在（未过期）"""
    try:
        r = _get_sync_client()
        key = RedisKeys.camera_live_heartbeat(camera_id)
        return bool(r.exists(key))
    except Exception as e:
        logger.warning(f"检查心跳 Key 失败: camera_id={camera_id}, err={e}")
        return False


# ===================== 配置读取（供 Scheduler / Inferencer） =====================


def get_model_config(model_id: str) -> Optional[Dict[str, Any]]:
    """读取模型配置 JSON"""
    try:
        r = _get_sync_client()
        raw = r.get(RedisKeys.model_config(model_id))
        if not raw:
            return None
        return json.loads(_val_str(raw))
    except Exception as e:
        logger.warning(f"读取模型配置失败: model_id={model_id}, err={e}")
        return None


def get_model_classes(model_id: str) -> Optional[List[str]]:
    """从模型配置读取 classes 列表（供 YOLO Inferencer 使用）"""
    cfg = get_model_config(model_id)
    if not cfg:
        return None
    classes = cfg.get("classes")
    if isinstance(classes, list) and len(classes) > 0:
        return [str(c) for c in classes]
    return None


def get_model_algorithms_class_map(model_id: str) -> Optional[Dict[str, Dict[str, str]]]:
    """
    从 model:config.algorithms 构造 {target_class -> {code, name}} 映射（供 ONNX Inferencer 使用）
    """
    cfg = get_model_config(model_id)
    if not cfg:
        return None
    algorithms_cfg = cfg.get("algorithms")
    if not isinstance(algorithms_cfg, list):
        return None
    class_map: Dict[str, Dict[str, str]] = {}
    for item in algorithms_cfg:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "")
        name = str(item.get("name") or "")
        targets = item.get("target_classes") or []
        if not code or not isinstance(targets, list):
            continue
        for t in targets:
            if t is not None:
                class_map[str(t)] = {"code": code, "name": name}
    return class_map if class_map else None


def get_algorithm_config(algorithm_id: str) -> Optional[Dict[str, Any]]:
    """读取算法配置 JSON"""
    try:
        r = _get_sync_client()
        raw = r.get(RedisKeys.algorithm_config(algorithm_id))
        if not raw:
            return None
        return json.loads(_val_str(raw))
    except Exception as e:
        logger.warning(f"读取算法配置失败: algorithm_id={algorithm_id}, err={e}")
        return None


def get_camera_config(camera_id: str) -> Optional[Dict[str, Any]]:
    """读取摄像头配置 JSON"""
    try:
        r = _get_sync_client()
        raw = r.get(RedisKeys.camera_config(camera_id))
        if not raw:
            return None
        return json.loads(_val_str(raw))
    except Exception as e:
        logger.warning(f"读取摄像头配置失败: camera_id={camera_id}, err={e}")
        return None


def get_camera_algorithm_config(camera_id: str, algorithm_id: str) -> Optional[Dict[str, Any]]:
    """读取摄像头-算法绑定配置 JSON"""
    try:
        r = _get_sync_client()
        key = RedisKeys.camera_algorithm_config(camera_id, algorithm_id)
        raw = r.get(key)
        if not raw:
            return None
        return json.loads(_val_str(raw))
    except Exception as e:
        logger.warning(f"读取摄像头算法配置失败: camera_id={camera_id}, algo={algorithm_id}, err={e}")
        return None


def scan_camera_algorithm_configs(camera_id: str) -> List[Dict[str, Any]]:
    """扫描某摄像头的所有算法绑定配置"""
    result: List[Dict[str, Any]] = []
    try:
        r = _get_sync_client()
        pattern = f"{RedisKeys.CAMERA_ALGORITHM_CONFIG_PREFIX}{camera_id}:*"
        for key in r.scan_iter(pattern):
            raw = r.get(key)
            if not raw:
                continue
            try:
                cfg = json.loads(_val_str(raw))
            except Exception:
                continue
            if not cfg.get("is_enabled", True):
                continue
            key_s = _key_str(key)
            algo_id = cfg.get("algorithm_id") or key_s.split(":")[-1]
            model_id = cfg.get("model_id")
            if not model_id:
                continue
            result.append({
                "id": algo_id,
                "model_id": model_id,
                "config": {
                    "confidence": cfg.get("confidence"),
                    "alert_config": cfg.get("alert_config"),
                    "regions": cfg.get("regions") or [],
                },
            })
    except Exception as e:
        logger.warning(f"扫描摄像头算法配置失败: camera_id={camera_id}, err={e}")
    return result


def scan_model_configs() -> List[tuple]:
    """扫描所有模型配置，返回 (model_id, cfg_dict) 列表"""
    result: List[tuple] = []
    try:
        r = _get_sync_client()
        for key in r.scan_iter(f"{RedisKeys.MODEL_CONFIG_PREFIX}*"):
            raw = r.get(key)
            if not raw:
                continue
            try:
                cfg = json.loads(_val_str(raw))
            except Exception:
                continue
            if not cfg.get("is_enabled", True):
                continue
            key_s = _key_str(key)
            model_id = cfg.get("id") or key_s.split(":")[-1]
            result.append((model_id, cfg))
    except Exception as e:
        logger.warning(f"扫描模型配置失败: {e}")
    return result


def scan_camera_configs() -> List[tuple]:
    """扫描所有摄像头配置，返回 (camera_id, cfg_dict) 列表"""
    result: List[tuple] = []
    try:
        r = _get_sync_client()
        for key in r.scan_iter(f"{RedisKeys.CAMERA_CONFIG_PREFIX}*"):
            raw = r.get(key)
            if not raw:
                continue
            try:
                cfg = json.loads(_val_str(raw))
            except Exception:
                continue
            if not cfg.get("is_enabled", True):
                continue
            key_s = _key_str(key)
            camera_id = cfg.get("id") or key_s.split(":")[-1]
            result.append((camera_id, cfg))
    except Exception as e:
        logger.warning(f"扫描摄像头配置失败: {e}")
    return result


def scan_camera_algorithm_bindings() -> List[tuple]:
    """扫描所有摄像头-算法绑定配置，返回 (camera_id, algorithm_id, cfg_dict) 列表"""
    result: List[tuple] = []
    try:
        r = _get_sync_client()
        for key in r.scan_iter(f"{RedisKeys.CAMERA_ALGORITHM_CONFIG_PREFIX}*"):
            raw = r.get(key)
            if not raw:
                continue
            try:
                cfg = json.loads(_val_str(raw))
            except Exception:
                continue
            if not cfg.get("is_enabled", True):
                continue
            key_s = _key_str(key)
            parts = key_s.split(":")
            if len(parts) < 2:
                continue
            camera_id = cfg.get("camera_id") or parts[-2]
            algorithm_id = cfg.get("algorithm_id") or parts[-1]
            model_id = cfg.get("model_id")
            if not camera_id or not model_id:
                continue
            result.append((camera_id, algorithm_id, cfg))
    except Exception as e:
        logger.warning(f"扫描摄像头算法绑定失败: {e}")
    return result


