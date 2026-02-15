# -*- coding: utf-8 -*-
"""
队列抽象层

提供统一的队列接口，支持内存队列和 Redis 队列
"""
from .interface import QueueInterface
from .memory_queue import MemoryQueue

__all__ = ["QueueInterface", "MemoryQueue"]
