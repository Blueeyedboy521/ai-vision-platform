# -*- coding: utf-8 -*-
"""
Redis Pub/Sub 封装模块

提供更便捷的发布订阅功能
"""
import json
import asyncio
from typing import Callable, Dict, List, Optional, Any, Coroutine
from dataclasses import dataclass

import redis.asyncio as aioredis

from common.logging import logger
from .client import get_redis_client


@dataclass
class PubSubMessage:
    """
    Pub/Sub 消息数据类
    """
    channel: str          # 频道名称
    data: Any             # 消息数据
    pattern: Optional[str] = None  # 匹配的模式(如果是模式订阅)
    
    @property
    def data_json(self) -> Optional[Any]:
        """尝试将 data 解析为 JSON"""
        if isinstance(self.data, str):
            try:
                return json.loads(self.data)
            except json.JSONDecodeError:
                return None
        return self.data


class RedisPubSub:
    """
    Redis Pub/Sub 封装类
    
    提供更便捷的发布订阅功能，支持:
    - 异步消息监听
    - 自动重连
    - 回调函数注册
    """
    
    def __init__(self):
        """初始化 PubSub 实例"""
        self._client = get_redis_client()
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._handlers: Dict[str, List[Callable]] = {}
        self._pattern_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """启动 Pub/Sub 监听"""
        if self._running:
            logger.warning("PubSub 已经在运行中")
            return
        
        await self._client.connect()
        self._pubsub = self._client.pubsub()
        self._running = True
        
        # 启动监听任务
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("PubSub 监听已启动")
    
    async def stop(self) -> None:
        """停止 Pub/Sub 监听"""
        self._running = False
        
        if self._listen_task is not None:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
        
        if self._pubsub is not None:
            await self._pubsub.unsubscribe()
            await self._pubsub.punsubscribe()
            await self._pubsub.close()
            self._pubsub = None
        
        logger.info("PubSub 监听已停止")
    
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[PubSubMessage], Coroutine]
    ) -> None:
        """
        订阅频道
        
        Args:
            channel: 频道名称
            handler: 消息处理函数，接收 PubSubMessage 参数
        """
        if self._pubsub is None:
            raise RuntimeError("PubSub 未启动，请先调用 start()")
        
        # 注册处理函数
        if channel not in self._handlers:
            self._handlers[channel] = []
            await self._pubsub.subscribe(channel)
            logger.info(f"已订阅频道: {channel}")
        
        self._handlers[channel].append(handler)
    
    async def psubscribe(
        self,
        pattern: str,
        handler: Callable[[PubSubMessage], Coroutine]
    ) -> None:
        """
        模式订阅
        
        Args:
            pattern: 频道模式 (如 "detections:*")
            handler: 消息处理函数
        """
        if self._pubsub is None:
            raise RuntimeError("PubSub 未启动，请先调用 start()")
        
        if pattern not in self._pattern_handlers:
            self._pattern_handlers[pattern] = []
            await self._pubsub.psubscribe(pattern)
            logger.info(f"已订阅模式: {pattern}")
        
        self._pattern_handlers[pattern].append(handler)
    
    async def unsubscribe(self, channel: str) -> None:
        """
        取消订阅频道
        
        Args:
            channel: 频道名称
        """
        if self._pubsub is None:
            return
        
        if channel in self._handlers:
            del self._handlers[channel]
            await self._pubsub.unsubscribe(channel)
            logger.info(f"已取消订阅频道: {channel}")
    
    async def punsubscribe(self, pattern: str) -> None:
        """
        取消模式订阅
        
        Args:
            pattern: 频道模式
        """
        if self._pubsub is None:
            return
        
        if pattern in self._pattern_handlers:
            del self._pattern_handlers[pattern]
            await self._pubsub.punsubscribe(pattern)
            logger.info(f"已取消订阅模式: {pattern}")
    
    async def publish(self, channel: str, message: Any) -> int:
        """
        发布消息
        
        Args:
            channel: 频道名称
            message: 消息内容，如果是 dict/list 会自动序列化为 JSON
            
        Returns:
            接收到消息的订阅者数量
        """
        return await self._client.publish(channel, message)
    
    async def _listen_loop(self) -> None:
        """消息监听循环"""
        while self._running:
            try:
                if self._pubsub is None:
                    await asyncio.sleep(0.1)
                    continue
                
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                
                if message is None:
                    continue
                
                await self._handle_message(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"PubSub 监听异常: {e}")
                await asyncio.sleep(1.0)
    
    async def _handle_message(self, message: dict) -> None:
        """
        处理接收到的消息
        
        Args:
            message: Redis 原始消息
        """
        msg_type = message.get("type")
        
        if msg_type == "message":
            # 普通消息
            channel = message.get("channel", "")
            data = message.get("data")
            
            pubsub_msg = PubSubMessage(channel=channel, data=data)
            handlers = self._handlers.get(channel, [])
            
            for handler in handlers:
                try:
                    await handler(pubsub_msg)
                except Exception as e:
                    logger.error(f"消息处理函数异常: channel={channel}, error={e}")
        
        elif msg_type == "pmessage":
            # 模式消息
            pattern = message.get("pattern", "")
            channel = message.get("channel", "")
            data = message.get("data")
            
            pubsub_msg = PubSubMessage(channel=channel, data=data, pattern=pattern)
            handlers = self._pattern_handlers.get(pattern, [])
            
            for handler in handlers:
                try:
                    await handler(pubsub_msg)
                except Exception as e:
                    logger.error(f"消息处理函数异常: pattern={pattern}, channel={channel}, error={e}")
