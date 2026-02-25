# -*- coding: utf-8 -*-
"""
WebSocket 消息处理器

处理来自 Redis Pub/Sub 的消息并转发到 WebSocket 客户端
"""
import json
import asyncio
from typing import Optional

from common.logging import logger
from common.redis import RedisPubSub, PubSubMessage, RedisChannels
from .manager import connection_manager


class WebSocketHandler:
    """
    WebSocket 消息处理器
    
    订阅 Redis 频道并将消息转发到 WebSocket 客户端
    """
    
    def __init__(self):
        """初始化处理器"""
        # 这个实例变量的类型，既可以是 RedisPubSub 类的实例，也可以是 None
        self._pubsub: Optional[RedisPubSub] = None
        self._running = False
    
    async def start(self) -> None:
        """
        启动处理器
        
        开始订阅 Redis 频道
        """
        if self._running:
            return
        
        self._pubsub = RedisPubSub()
        
        await self._pubsub.start()
        self._running = True
        
        # 订阅检测结果频道 (模式匹配)
        await self._pubsub.psubscribe(
            f"{RedisChannels.DETECTIONS_PREFIX}*",
            self._handle_detection_message
        )
        
        # 订阅告警频道（精准匹配）
        await self._pubsub.subscribe(
            RedisChannels.ALARMS_REALTIME,
            self._handle_alarm_message
        )
        
        logger.info("WebSocket 处理器已启动")
    
    async def stop(self) -> None:
        """停止处理器"""
        self._running = False
        
        if self._pubsub is not None:
            await self._pubsub.stop()
            self._pubsub = None
        
        logger.info("WebSocket 处理器已停止")
    
    async def _handle_detection_message(self, message: PubSubMessage) -> None:
        """
        处理检测结果消息
        
        Args:
            message: Redis 消息
        """
        try:
            # 从频道名称提取 camera_id
            # 频道格式: detections:{camera_id}
            channel = message.channel
            if not channel.startswith(RedisChannels.DETECTIONS_PREFIX):
                return
            
            camera_id = channel[len(RedisChannels.DETECTIONS_PREFIX):]
            
            # 解析消息数据
            data = message.data_json
            if data is None:
                return
            
            # 构建 WebSocket 消息
            ws_message = {
                "type": "detection",
                "camera_id": camera_id,
                "data": data
            }
            
            # 向订阅该摄像头的客户端广播
            ws_channel = f"camera:{camera_id}"
            count = await connection_manager.broadcast_to_channel(
                ws_channel,
                ws_message
            )
            
            if count > 0:
                logger.debug(
                    f"检测结果已推送: camera_id={camera_id}, "
                    f"接收者数={count}"
                )
                
        except Exception as e:
            logger.error(f"处理检测消息失败: {e}")
    
    async def _handle_alarm_message(self, message: PubSubMessage) -> None:
        """
        处理告警消息
        
        Args:
            message: Redis 消息
        """
        try:
            # 解析消息数据
            data = message.data_json
            if data is None:
                return
            
            # 构建 WebSocket 消息
            ws_message = {
                "type": "alarm",
                "data": data
            }
            
            # 向所有订阅告警频道的客户端广播
            count = await connection_manager.broadcast_to_channel(
                "alarms",
                ws_message
            )
            
            logger.info(
                f"告警已推送: alarm_id={data.get('alarm_id')}, "
                f"接收者数={count}"
            )
            
        except Exception as e:
            logger.error(f"处理告警消息失败: {e}")
    
    async def publish_detection(
        self,
        camera_id: str,
        data: dict
    ) -> int:
        """
        发布检测结果到 WebSocket
        
        直接发布，不经过 Redis
        
        Args:
            camera_id: 摄像头ID
            data: 检测数据
            
        Returns:
            接收者数量
        """
        ws_message = {
            "type": "detection",
            "camera_id": camera_id,
            "data": data
        }
        
        ws_channel = f"camera:{camera_id}"
        return await connection_manager.broadcast_to_channel(
            ws_channel,
            ws_message
        )
    
    async def publish_alarm(self, data: dict) -> int:
        """
        发布告警到 WebSocket
        
        直接发布，不经过 Redis
        
        Args:
            data: 告警数据
            
        Returns:
            接收者数量
        """
        ws_message = {
            "type": "alarm",
            "data": data
        }
        
        return await connection_manager.broadcast_to_channel(
            "alarms",
            ws_message
        )


# 全局处理器实例
websocket_handler = WebSocketHandler()
