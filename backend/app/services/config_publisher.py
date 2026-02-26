# -*- coding: utf-8 -*-
"""
配置发布服务

发布配置变更消息到 Engine
"""
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from common.logging import logger
from common.redis import get_redis_client, RedisChannels


class ConfigAction(str, Enum):
    """配置动作类型"""
    
    # 摄像头相关
    CAMERA_ADD = "camera_add"
    CAMERA_UPDATE = "camera_update"
    CAMERA_DELETE = "camera_delete"
    CAMERA_START = "camera_start"
    CAMERA_STOP = "camera_stop"
    CAMERA_INFERENCE_START = "camera_inference_start"
    CAMERA_INFERENCE_STOP = "camera_inference_stop"
    
    # 算法相关
    ALGORITHM_ADD = "algorithm_add"
    ALGORITHM_UPDATE = "algorithm_update"
    ALGORITHM_DELETE = "algorithm_delete"
    
    # 摄像头-算法配置
    CAMERA_ALGORITHM_ADD = "camera_algorithm_add"
    CAMERA_ALGORITHM_UPDATE = "camera_algorithm_update"
    CAMERA_ALGORITHM_DELETE = "camera_algorithm_delete"
    
    # 模型相关
    MODEL_ADD = "model_add"
    MODEL_UPDATE = "model_update"
    MODEL_DELETE = "model_delete"


class ConfigPublisher:
    """
    配置发布器
    
    通过 Redis Pub/Sub 向 Engine 发布配置变更
    """
    
    def __init__(self):
        """初始化发布器"""
        self._redis = get_redis_client()
    
    async def publish(
        self,
        action: ConfigAction,
        data: Dict[str, Any]
    ) -> bool:
        """
        发布配置变更
        
        Args:
            action: 动作类型
            data: 变更数据
            
        Returns:
            是否发布成功
        """
        message = {
            "action": action.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self._redis.client.publish(
                RedisChannels.ENGINE_CONFIG_UPDATE,
                json.dumps(message, ensure_ascii=False)
            )
            logger.info(f"配置变更已发布: {action.value}")
            return True
            
        except Exception as e:
            logger.error(f"发布配置变更失败: {action.value}, 错误: {e}")
            return False
    
    # ==================== 摄像头操作 ====================
    
    async def publish_camera_add(self, camera_data: Dict[str, Any]) -> bool:
        """发布摄像头添加"""
        return await self.publish(ConfigAction.CAMERA_ADD, camera_data)
    
    async def publish_camera_update(self, camera_data: Dict[str, Any]) -> bool:
        """发布摄像头更新"""
        return await self.publish(ConfigAction.CAMERA_UPDATE, camera_data)
    
    async def publish_camera_delete(self, camera_id: str) -> bool:
        """发布摄像头删除"""
        return await self.publish(
            ConfigAction.CAMERA_DELETE,
            {"camera_id": camera_id}
        )
    
    async def publish_camera_start(self, camera_id: str) -> bool:
        """发布摄像头启动"""
        return await self.publish(
            ConfigAction.CAMERA_START,
            {"camera_id": camera_id}
        )
    
    async def publish_camera_stop(self, camera_id: str) -> bool:
        """发布摄像头停止"""
        return await self.publish(
            ConfigAction.CAMERA_STOP,
            {"camera_id": camera_id}
        )

    async def publish_camera_inference_start(self, camera_id: str) -> bool:
        """发布摄像头推理启动"""
        return await self.publish(
            ConfigAction.CAMERA_INFERENCE_START,
            {"camera_id": camera_id}
        )

    async def publish_camera_inference_stop(self, camera_id: str) -> bool:
        """发布摄像头推理停止"""
        return await self.publish(
            ConfigAction.CAMERA_INFERENCE_STOP,
            {"camera_id": camera_id}
        )
    
    # ==================== 算法操作 ====================
    
    async def publish_algorithm_add(self, algorithm_data: Dict[str, Any]) -> bool:
        """发布算法添加"""
        return await self.publish(ConfigAction.ALGORITHM_ADD, algorithm_data)
    
    async def publish_algorithm_update(self, algorithm_data: Dict[str, Any]) -> bool:
        """发布算法更新"""
        return await self.publish(ConfigAction.ALGORITHM_UPDATE, algorithm_data)
    
    async def publish_algorithm_delete(self, algorithm_id: str) -> bool:
        """发布算法删除"""
        return await self.publish(
            ConfigAction.ALGORITHM_DELETE,
            {"algorithm_id": algorithm_id}
        )
    
    # ==================== 摄像头-算法配置操作 ====================
    
    async def publish_camera_algorithm_add(
        self,
        camera_id: str,
        algorithm_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """发布摄像头-算法配置添加"""
        return await self.publish(
            ConfigAction.CAMERA_ALGORITHM_ADD,
            {
                "camera_id": camera_id,
                "algorithm_id": algorithm_id,
                "config": config
            }
        )
    
    async def publish_camera_algorithm_update(
        self,
        camera_id: str,
        algorithm_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """发布摄像头-算法配置更新"""
        return await self.publish(
            ConfigAction.CAMERA_ALGORITHM_UPDATE,
            {
                "camera_id": camera_id,
                "algorithm_id": algorithm_id,
                "config": config
            }
        )
    
    async def publish_camera_algorithm_delete(
        self,
        camera_id: str,
        algorithm_id: str
    ) -> bool:
        """发布摄像头-算法配置删除"""
        return await self.publish(
            ConfigAction.CAMERA_ALGORITHM_DELETE,
            {
                "camera_id": camera_id,
                "algorithm_id": algorithm_id
            }
        )
    
    # ==================== 模型操作 ====================
    
    async def publish_model_add(self, model_data: Dict[str, Any]) -> bool:
        """发布模型添加"""
        return await self.publish(ConfigAction.MODEL_ADD, model_data)
    
    async def publish_model_update(self, model_data: Dict[str, Any]) -> bool:
        """发布模型更新"""
        return await self.publish(ConfigAction.MODEL_UPDATE, model_data)
    
    async def publish_model_delete(self, model_id: str) -> bool:
        """发布模型删除"""
        return await self.publish(
            ConfigAction.MODEL_DELETE,
            {"model_id": model_id}
        )


# 全局发布器实例
_config_publisher: Optional[ConfigPublisher] = None


def get_config_publisher() -> ConfigPublisher:
    """
    获取配置发布器实例
    
    Returns:
        ConfigPublisher 实例
    """
    global _config_publisher
    if _config_publisher is None:
        _config_publisher = ConfigPublisher()
    return _config_publisher
