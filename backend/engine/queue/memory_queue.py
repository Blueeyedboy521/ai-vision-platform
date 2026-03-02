# -*- coding: utf-8 -*-
"""
内存队列

基于 multiprocessing.Queue 实现的跨进程内存队列
"""
import os
from multiprocessing import Queue
from queue import Empty, Full
from typing import Any, Optional

from .interface import QueueInterface
from loguru import logger
import time
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
        # 直接使用 multiprocessing.Queue。队列实例由 Scheduler 在主进程创建并通过
        # multiprocessing 机制传递给子进程，底层管道本身是跨进程共享的。
        self._queue = Queue(maxsize=maxsize)
        self._maxsize = maxsize
        # 用于调试日志区分不同队列实例
        self._id = hex(id(self))
    
    def _log_prefix(self) -> str:
        return f"[MemoryQueue id={self._id} pid={os.getpid()}]"
    
    def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """放入元素"""
        try:
            self._queue.put(item, block=True, timeout=timeout)
            # logger.debug(f"{self._log_prefix()} put 成功, qsize={self.qsize()}, item_type={type(item).__name__}")
            return True
        except Full:
            logger.debug(f"{self._log_prefix()} put 失败: Full, qsize={self.qsize()}")
            return False
        except Exception as e:
            logger.error(f"{self._log_prefix()} put 异常: {e}")
            return False
    
    def put_nowait(self, item: Any) -> bool:
        """非阻塞放入元素"""
        try:
            self._queue.put_nowait(item)
            # logger.debug(f"{self._log_prefix()} put_nowait 成功, qsize={self.qsize()}, item_type={type(item).__name__}")
            return True
        except Full:
            logger.debug(f"{self._log_prefix()} put_nowait 失败: Full, qsize={self.qsize()}")
            return False
        except Exception as e:
            logger.error(f"{self._log_prefix()} put_nowait 异常: {e}")
            return False
    
    def get(self, timeout: Optional[float] = None) -> Any:
        """获取元素"""
        try:
            item = self._queue.get(block=True, timeout=timeout)
            # logger.debug(f"{self._log_prefix()} get 成功, qsize={self.qsize()}, item_type={type(item).__name__}")
            return item
        except Empty:
            logger.debug(f"{self._log_prefix()} get 超时或空队列返回 None, qsize={self.qsize()}, timeout={timeout}")
            return None
        except Exception as e:
            logger.error(f"{self._log_prefix()} get 异常: {e}")
            return None
    
    def get_nowait(self) -> Any:
        """非阻塞获取元素"""
        try:
            item = self._queue.get_nowait()
            # logger.debug(f"{self._log_prefix()} get_nowait 成功, qsize={self.qsize()}, item_type={type(item).__name__}")
            return item
        except Empty:
            logger.debug(f"{self._log_prefix()} get_nowait 返回 None (Empty), qsize={self.qsize()}")
            return None
        except Exception as e:
            logger.error(f"{self._log_prefix()} get_nowait 异常: {e}")
            return None
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """检查队列是否已满"""
        if self._maxsize <= 0:
            return False
        return self._queue.qsize() >= self._maxsize
    
    def qsize(self) -> int:
        """获取队列大小（注意：multiprocessing.Queue 的 qsize 在多进程下仅供调试参考）"""
        try:
            return self._queue.qsize()
        except NotImplementedError:
            return -1
    
    def clear(self) -> None:
        """清空队列"""
        cleared = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                cleared += 1
            except Empty:
                break
        logger.debug(f"{self._log_prefix()} clear 完成, cleared={cleared}, qsize={self.qsize()}")
    # 主进程中：关闭旧推理进程后，执行队列重置
    def reset_queue(self):
        """重置队列：清空残留数据，释放锁资源"""
        try:
            # 循环清空队列所有数据（非阻塞）
            while True:
                self._queue.get_nowait()
        except Empty:
            pass
        # 短暂休眠，让队列完成内部状态重置
        time.sleep(0.1)
        logger.info("队列已重置，残留数据已清空")