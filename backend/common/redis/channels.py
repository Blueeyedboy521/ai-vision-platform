# -*- coding: utf-8 -*-
"""
Redis 频道名称常量定义

统一管理所有 Redis Pub/Sub 频道名称，避免硬编码
"""


class RedisChannels:
    """
    Redis 频道名称常量
    
    使用类常量统一管理，便于维护和引用
    """
    
    # ==================== 检测结果推送 ====================
    # 实时检测框推送 (Engine -> FastAPI -> 前端)
    # 格式: detections:{camera_id}
    DETECTIONS_PREFIX = "detections:"
    
    @staticmethod
    def detections(camera_id: str) -> str:
        """获取指定摄像头的检测结果频道"""
        return f"{RedisChannels.DETECTIONS_PREFIX}{camera_id}"
    
    # ==================== 告警推送 ====================
    # 实时告警通知 (AlarmConsumer -> FastAPI -> 前端)
    ALARMS_REALTIME = "alarms:realtime"
    
    # ==================== 配置更新 ====================
    # 引擎配置更新 (FastAPI -> Engine)
    ENGINE_CONFIG_UPDATE = "engine:config_update"
    
    # 摄像头状态变化 (添加/删除/启停)
    CAMERA_STATUS_CHANGE = "camera:status_change"
    
    # ==================== 系统状态 ====================
    # 引擎心跳
    ENGINE_HEARTBEAT = "engine:heartbeat"
    
    # Pipeline 状态
    PIPELINE_STATUS_PREFIX = "pipeline:status:"
    
    @staticmethod
    def pipeline_status(camera_id: str) -> str:
        """获取指定摄像头的 Pipeline 状态频道"""
        return f"{RedisChannels.PIPELINE_STATUS_PREFIX}{camera_id}"


class RedisKeys:
    """
    Redis Key 名称常量
    
    用于 Redis List、String、Hash 等数据结构的 Key 命名
    """
    
    # ==================== 告警队列 ====================
    # 告警消息队列 (Engine -> AlarmConsumer)
    ALARM_QUEUE = "alarm_queue"
    
    # ==================== Token 黑名单 ====================
    # Token 黑名单前缀
    TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
    
    @staticmethod
    def token_blacklist(token_hash: str) -> str:
        """获取 Token 黑名单的 Key"""
        return f"{RedisKeys.TOKEN_BLACKLIST_PREFIX}{token_hash}"
    
    # ==================== 缓存 ====================
    # 用户信息缓存
    USER_CACHE_PREFIX = "user:cache:"
    
    @staticmethod
    def user_cache(user_id: str) -> str:
        """获取用户缓存的 Key"""
        return f"{RedisKeys.USER_CACHE_PREFIX}{user_id}"
    
    # 摄像头配置缓存 (FastAPI -> Engine)
    CAMERA_CONFIG_PREFIX = "camera:config:"
    
    @staticmethod
    def camera_config(camera_id: str) -> str:
        """获取摄像头配置缓存的 Key"""
        return f"{RedisKeys.CAMERA_CONFIG_PREFIX}{camera_id}"
    
    # 模型配置缓存 (FastAPI -> Engine)
    MODEL_CONFIG_PREFIX = "model:config:"
    
    @staticmethod
    def model_config(model_id: str) -> str:
        """获取模型配置缓存的 Key"""
        return f"{RedisKeys.MODEL_CONFIG_PREFIX}{model_id}"
    
    # 算法配置缓存 (FastAPI -> Engine)
    ALGORITHM_CONFIG_PREFIX = "algorithm:config:"
    
    @staticmethod
    def algorithm_config(algorithm_id: str) -> str:
        """获取算法配置缓存的 Key"""
        return f"{RedisKeys.ALGORITHM_CONFIG_PREFIX}{algorithm_id}"
    
    # 摄像头-算法绑定配置缓存 (FastAPI -> Engine)
    CAMERA_ALGORITHM_CONFIG_PREFIX = "camera:algorithm:config:"
    
    @staticmethod
    def camera_algorithm_config(camera_id: str, algorithm_id: str) -> str:
        """获取摄像头-算法配置缓存的 Key"""
        return f"{RedisKeys.CAMERA_ALGORITHM_CONFIG_PREFIX}{camera_id}:{algorithm_id}"
    
    # ==================== 去重 ====================
    # 告警去重 Key 前缀
    ALARM_DEDUP_PREFIX = "alarm:dedup:"
    
    @staticmethod
    def alarm_dedup(camera_id: str, algorithm_id: str) -> str:
        """获取告警去重的 Key"""
        return f"{RedisKeys.ALARM_DEDUP_PREFIX}{camera_id}:{algorithm_id}"
