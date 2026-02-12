# -*- coding: utf-8 -*-
"""
Redis 客户端模块

提供同步和异步 Redis 客户端的封装
"""
import json
from typing import Any, Optional, Union, List
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import redis

from common.logging import logger


class RedisClient:
    """
    Redis 客户端封装
    
    提供常用的 Redis 操作方法，支持同步和异步模式
    """
    
    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        max_connections: int = 50,
        decode_responses: bool = True
    ):
        """
        初始化 Redis 客户端
        
        Args:
            url: Redis 连接URL
            max_connections: 最大连接数
            decode_responses: 是否自动解码响应
        """
        self.url = url
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        
        self._async_client: Optional[aioredis.Redis] = None
        self._sync_client: Optional[redis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
    
    async def connect(self) -> None:
        """建立异步连接"""
        if self._async_client is None:
            self._connection_pool = aioredis.ConnectionPool.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses
            )
            self._async_client = aioredis.Redis(connection_pool=self._connection_pool)
            logger.info(f"Redis 异步连接已建立: {self.url}")
    
    async def disconnect(self) -> None:
        """断开异步连接"""
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None
            logger.info("Redis 异步连接已断开")
        
        if self._connection_pool is not None:
            await self._connection_pool.disconnect()
            self._connection_pool = None
    
    def connect_sync(self) -> None:
        """建立同步连接"""
        if self._sync_client is None:
            self._sync_client = redis.from_url(
                self.url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses
            )
            logger.info(f"Redis 同步连接已建立: {self.url}")
    
    def disconnect_sync(self) -> None:
        """断开同步连接"""
        if self._sync_client is not None:
            self._sync_client.close()
            self._sync_client = None
            logger.info("Redis 同步连接已断开")
    
    @property
    def client(self) -> aioredis.Redis:
        """获取异步客户端实例"""
        if self._async_client is None:
            raise RuntimeError("Redis 异步客户端未连接，请先调用 connect()")
        return self._async_client
    
    @property
    def sync_client(self) -> redis.Redis:
        """获取同步客户端实例"""
        if self._sync_client is None:
            raise RuntimeError("Redis 同步客户端未连接，请先调用 connect_sync()")
        return self._sync_client
    
    # ==================== 异步方法 ====================
    
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        return await self.client.get(key)
    
    async def set(
        self,
        key: str,
        value: Union[str, int, float],
        ex: Optional[int] = None,
        px: Optional[int] = None
    ) -> bool:
        """
        设置字符串值
        
        Args:
            key: 键
            value: 值
            ex: 过期时间(秒)
            px: 过期时间(毫秒)
        """
        return await self.client.set(key, value, ex=ex, px=px)
    
    async def setex(self, key: str, seconds: int, value: Union[str, int, float]) -> bool:
        """设置带过期时间的字符串值"""
        return await self.client.setex(key, seconds, value)
    
    async def delete(self, *keys: str) -> int:
        """删除键"""
        if not keys:
            return 0
        return await self.client.delete(*keys)
    
    async def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        if not keys:
            return 0
        return await self.client.exists(*keys)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置键的过期时间"""
        return await self.client.expire(key, seconds)
    
    async def ttl(self, key: str) -> int:
        """获取键的剩余过期时间"""
        return await self.client.ttl(key)
    
    # ==================== List 操作 ====================
    
    async def lpush(self, key: str, *values: Any) -> int:
        """从左侧插入列表"""
        return await self.client.lpush(key, *values)
    
    async def rpush(self, key: str, *values: Any) -> int:
        """从右侧插入列表"""
        return await self.client.rpush(key, *values)
    
    async def lpop(self, key: str) -> Optional[str]:
        """从左侧弹出元素"""
        return await self.client.lpop(key)
    
    async def rpop(self, key: str) -> Optional[str]:
        """从右侧弹出元素"""
        return await self.client.rpop(key)
    
    async def blpop(self, keys: Union[str, List[str]], timeout: int = 0) -> Optional[tuple]:
        """阻塞式从左侧弹出元素"""
        if isinstance(keys, str):
            keys = [keys]
        return await self.client.blpop(keys, timeout=timeout)
    
    async def brpop(self, keys: Union[str, List[str]], timeout: int = 0) -> Optional[tuple]:
        """阻塞式从右侧弹出元素"""
        if isinstance(keys, str):
            keys = [keys]
        return await self.client.brpop(keys, timeout=timeout)
    
    async def llen(self, key: str) -> int:
        """获取列表长度"""
        return await self.client.llen(key)
    
    async def lrange(self, key: str, start: int, end: int) -> List[str]:
        """获取列表范围内的元素"""
        return await self.client.lrange(key, start, end)
    
    # ==================== Pub/Sub 操作 ====================
    
    async def publish(self, channel: str, message: Union[str, dict]) -> int:
        """
        发布消息到频道
        
        Args:
            channel: 频道名称
            message: 消息内容，如果是 dict 会自动序列化为 JSON
            
        Returns:
            接收到消息的订阅者数量
        """
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
        return await self.client.publish(channel, message)
    
    def pubsub(self) -> aioredis.client.PubSub:
        """获取 Pub/Sub 对象"""
        return self.client.pubsub()
    
    # ==================== Hash 操作 ====================
    
    async def hset(self, name: str, key: str, value: Any) -> int:
        """设置哈希字段"""
        return await self.client.hset(name, key, value)
    
    async def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段"""
        return await self.client.hget(name, key)
    
    async def hmset(self, name: str, mapping: dict) -> bool:
        """批量设置哈希字段"""
        return await self.client.hset(name, mapping=mapping)
    
    async def hmget(self, name: str, keys: List[str]) -> List[Optional[str]]:
        """批量获取哈希字段"""
        return await self.client.hmget(name, keys)
    
    async def hgetall(self, name: str) -> dict:
        """获取所有哈希字段"""
        return await self.client.hgetall(name)
    
    async def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        return await self.client.hdel(name, *keys)
    
    # ==================== JSON 便捷方法 ====================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取 JSON 值并解析"""
        value = await self.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning(f"JSON 解析失败: key={key}, value={value}")
            return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None
    ) -> bool:
        """将值序列化为 JSON 并存储"""
        json_str = json.dumps(value, ensure_ascii=False)
        return await self.set(key, json_str, ex=ex)
    
    # ==================== 同步方法 ====================
    
    def get_sync(self, key: str) -> Optional[str]:
        """同步获取字符串值"""
        return self.sync_client.get(key)
    
    def set_sync(
        self,
        key: str,
        value: Union[str, int, float],
        ex: Optional[int] = None
    ) -> bool:
        """同步设置字符串值"""
        return self.sync_client.set(key, value, ex=ex)
    
    def publish_sync(self, channel: str, message: Union[str, dict]) -> int:
        """同步发布消息"""
        if isinstance(message, dict):
            message = json.dumps(message, ensure_ascii=False)
        return self.sync_client.publish(channel, message)
    
    def rpush_sync(self, key: str, *values: Any) -> int:
        """同步从右侧插入列表"""
        return self.sync_client.rpush(key, *values)
    
    def blpop_sync(self, keys: Union[str, List[str]], timeout: int = 0) -> Optional[tuple]:
        """同步阻塞式从左侧弹出元素"""
        if isinstance(keys, str):
            keys = [keys]
        return self.sync_client.blpop(keys, timeout=timeout)


# 全局 Redis 客户端实例
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    获取全局 Redis 客户端实例
    
    Returns:
        RedisClient 实例
    """
    global _redis_client
    if _redis_client is None:
        from config.settings import settings
        _redis_client = RedisClient(
            url=settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS
        )
    return _redis_client


async def init_redis() -> None:
    """初始化 Redis 连接"""
    client = get_redis_client()
    await client.connect()


async def close_redis() -> None:
    """关闭 Redis 连接"""
    client = get_redis_client()
    await client.disconnect()
