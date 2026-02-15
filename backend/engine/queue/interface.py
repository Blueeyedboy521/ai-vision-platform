# -*- coding: utf-8 -*-
"""
队列接口定义

定义统一的队列操作接口
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class QueueInterface(ABC):
    """
    队列接口
    
    所有队列实现必须继承此接口
    """
    
    @abstractmethod
    def put(self, item: Any, timeout: Optional[float] = None) -> bool:
        """
        放入元素
        
        Args:
            item: 要放入的元素
            timeout: 超时时间 (秒)，None 表示阻塞
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def put_nowait(self, item: Any) -> bool:
        """
        非阻塞放入元素
        
        Args:
            item: 要放入的元素
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def get(self, timeout: Optional[float] = None) -> Any:
        """
        获取元素
        
        Args:
            timeout: 超时时间 (秒)，None 表示阻塞
            
        Returns:
            队列元素
        """
        pass
    
    @abstractmethod
    def get_nowait(self) -> Any:
        """
        非阻塞获取元素
        
        Returns:
            队列元素
        """
        pass
    
    @abstractmethod
    def empty(self) -> bool:
        """
        检查队列是否为空
        
        Returns:
            是否为空
        """
        pass
    
    @abstractmethod
    def full(self) -> bool:
        """
        检查队列是否已满
        
        Returns:
            是否已满
        """
        pass
    
    @abstractmethod
    def qsize(self) -> int:
        """
        获取队列大小
        
        Returns:
            队列中的元素数量
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空队列"""
        pass
