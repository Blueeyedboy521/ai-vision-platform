# -*- coding: utf-8 -*-
"""
本地文件存储实现

将文件存储到本地磁盘
"""
import os
from pathlib import Path
from typing import Optional, BinaryIO, Union

import cv2
import numpy as np

from common.logging import logger
from .interface import StorageInterface


class LocalStorage(StorageInterface):
    """
    本地文件存储实现
    
    将文件存储到本地磁盘目录
    """
    
    def __init__(self, base_path: str = "./data"):
        """
        初始化本地存储
        
        Args:
            base_path: 存储根目录
        """
        self.base_path = Path(base_path).resolve()
        
        # 确保根目录存在
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"本地存储初始化完成: {self.base_path}")
    
    def _get_full_path(self, path: str) -> Path:
        """获取完整路径"""
        full_path = self.base_path / path
        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)
        return full_path
    
    def save_file(
        self,
        file_data: Union[bytes, BinaryIO],
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        保存文件到本地磁盘
        
        Args:
            file_data: 文件数据
            path: 存储路径 (相对于 base_path)
            content_type: 文件类型 (本地存储忽略此参数)
            
        Returns:
            文件相对路径
        """
        full_path = self._get_full_path(path)
        
        try:
            if isinstance(file_data, bytes):
                full_path.write_bytes(file_data)
            else:
                # 文件对象
                with open(full_path, "wb") as f:
                    f.write(file_data.read())
            
            logger.debug(f"文件已保存: {full_path}")
            return path
            
        except Exception as e:
            logger.error(f"保存文件失败: {path}, 错误: {e}")
            raise
    
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
            path: 存储路径 (相对路径)
            quality: JPEG 压缩质量
            
        Returns:
            图片相对路径
        """
        if image is None or image.size == 0:
            raise ValueError("图片数据为空")
        
        # 确保路径有扩展名
        if not path.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = f"{path}.jpg"
        
        full_path = self._get_full_path(path)
        
        try:
            # 根据扩展名选择编码参数
            if path.lower().endswith('.png'):
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            else:
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            
            # 保存图片
            success = cv2.imwrite(str(full_path), image, encode_params)
            
            if not success:
                raise RuntimeError("OpenCV 写入图片失败")
            
            logger.debug(f"图片已保存: {full_path}")
            return path
            
        except Exception as e:
            logger.error(f"保存图片失败: {path}, 错误: {e}")
            raise
    
    def get_file(self, path: str) -> Optional[bytes]:
        """
        获取文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            文件内容，不存在则返回 None
        """
        full_path = self.base_path / path
        
        if not full_path.exists():
            return None
        
        try:
            return full_path.read_bytes()
        except Exception as e:
            logger.error(f"读取文件失败: {path}, 错误: {e}")
            return None
    
    def delete_file(self, path: str) -> bool:
        """
        删除文件
        
        Args:
            path: 文件路径
            
        Returns:
            是否删除成功
        """
        full_path = self.base_path / path
        
        if not full_path.exists():
            return True
        
        try:
            full_path.unlink()
            logger.debug(f"文件已删除: {full_path}")
            return True
        except Exception as e:
            logger.error(f"删除文件失败: {path}, 错误: {e}")
            return False
    
    def exists(self, path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            path: 文件路径
            
        Returns:
            是否存在
        """
        full_path = self.base_path / path
        return full_path.exists()
    
    def get_url(self, path: str) -> str:
        """
        获取文件访问 URL
        
        本地存储返回相对路径，需要通过 API 提供静态文件服务
        
        Args:
            path: 文件路径
            
        Returns:
            文件访问路径
        """
        # 返回相对路径，前端通过 /static/xxx 访问
        return f"/static/{path}"
