# -*- coding: utf-8 -*-
"""
存储接口定义

定义文件存储的抽象接口，所有存储实现都需要继承此接口
"""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Union
from pathlib import Path

import numpy as np


class StorageInterface(ABC):
    """
    存储接口抽象类
    
    定义所有存储实现必须实现的方法
    """
    
    @abstractmethod
    def save_file(
        self,
        file_data: Union[bytes, BinaryIO],
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        保存文件
        
        Args:
            file_data: 文件数据 (bytes 或文件对象)
            path: 存储路径 (相对路径)
            content_type: 文件 MIME 类型
            
        Returns:
            文件访问路径/URL
        """
        pass
    
    @abstractmethod
    def save_image(
        self,
        image: np.ndarray,
        path: str,
        quality: int = 90
    ) -> str:
        """
        保存图片 (从 numpy 数组)
        
        Args:
            image: 图片数据 (numpy 数组, BGR 格式)
            path: 存储路径 (相对路径，不含扩展名)
            quality: JPEG 压缩质量 (1-100)
            
        Returns:
            图片访问路径/URL
        """
        pass
    
    @abstractmethod
    def get_file(self, path: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容，不存在则返回 None
        """
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            是否存在
        """
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        """
        获取文件访问 URL
        
        Args:
            path: 文件路径
            
        Returns:
            文件访问 URL
        """
        pass
    
    def generate_alarm_path(
        self,
        camera_id: str,
        timestamp: float,
        extension: str = "jpg"
    ) -> str:
        """
        生成告警截图存储路径
        
        Args:
            camera_id: 摄像头ID
            timestamp: 时间戳
            extension: 文件扩展名
            
        Returns:
            存储路径
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        date_path = dt.strftime("%Y/%m/%d")
        filename = f"{camera_id}_{int(timestamp * 1000)}.{extension}"
        return f"alarms/{date_path}/{filename}"
    
    def generate_video_path(
        self,
        camera_id: str,
        timestamp: float,
        extension: str = "mp4"
    ) -> str:
        """
        生成视频片段存储路径
        
        Args:
            camera_id: 摄像头ID
            timestamp: 时间戳
            extension: 文件扩展名
            
        Returns:
            存储路径
        """
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        date_path = dt.strftime("%Y/%m/%d")
        filename = f"{camera_id}_{int(timestamp * 1000)}.{extension}"
        return f"videos/{date_path}/{filename}"
