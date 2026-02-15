# -*- coding: utf-8 -*-
"""
内存队列

基于 multiprocessing.Queue 实现的内存队列
"""
from multiprocessing import Queue
from queue import Empty, Full
from typing import Any, Optional

from .interface import QueueInterface


class MemoryQueue(QueueInterface):
    """
    内存队列
    
    基于 multiprocessing.Queue 实现，支持跨进程通信
    """
    
    def __init__(self, maxsize: int = 0):
        """
        初始化内存队列
        
        Args:
            maxsize: 队列最大容量，0 表示无限
        """
        self._queue = Queue(maxsize=maxsize)
        self._maxsize = maxsize
    
    def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """放入元素"""
        try:
            self._queue.put(item, block=True, timeout=timeout)
            return True
        except Full:
            return False
    
    def put_nowait(self, item: Any) -> bool:
        """非阻塞放入元素"""
        try:
            self._queue.put_nowait(item)
            return True
        except Full:
            return False
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """获取元素"""
        return self._queue.get(block=True, timeout=timeout)
    
    def get_nowait(self) -> Any:
        """非阻塞获取元素"""
        return self._queue.get_nowait()
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """检查队列是否已满"""
        if self._maxsize <= 0:
            return False
        return self._queue.qsize() >= self._maxsize
    
    def qsize(self) -> int:
        """获取队列大小"""
        return self._queue.qsize()
    
    def clear(self) -> None:
        """清空队列"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Empty:
                break
