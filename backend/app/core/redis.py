# -*- coding: utf-8 -*-
"""
Redis 模块

提供 FastAPI 应用的 Redis 连接管理
"""
from typing import Optional

from common.redis import RedisClient, get_redis_client
from common.logging import logger


# 重新导出 Redis 客户端
redis_client: Optional[RedisClient] = None


async def init_redis() -> None:
    """
    初始化 Redis 连接
    
    在 FastAPI 应用启动时调用
    """
    global redis_client
    redis_client = get_redis_client()
    await redis_client.connect()
    logger.info("Redis 连接已初始化")


async def close_redis() -> None:
    """
    关闭 Redis 连接
    
    在 FastAPI 应用关闭时调用
    """
    global redis_client
    if redis_client is not None:
        await redis_client.disconnect()
        redis_client = None
        logger.info("Redis 连接已关闭")


def get_redis() -> RedisClient:
    """
    获取 Redis 客户端
    
    Returns:
        RedisClient 实例
        
    Raises:
        RuntimeError: 如果 Redis 未初始化
    """
    global redis_client
    if redis_client is None:
        redis_client = get_redis_client()
    return redis_client
