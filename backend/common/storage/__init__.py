# -*- coding: utf-8 -*-
"""
存储模块

提供文件存储功能的抽象接口和多种实现
"""
from typing import Optional
from .interface import StorageInterface
from common.logging import logger
__all__ = ["StorageInterface", "LocalStorage", "get_storage"]


# 闭包封装单例逻辑，避免全局变量
def _create_storage_singleton():
    """闭包：封装存储实例的单例逻辑"""
    _instance: Optional[StorageInterface] = None  # 闭包内的变量，非全局
    
    def _get_storage() -> StorageInterface:
        nonlocal _instance  # 声明引用闭包内的_instance，而非局部变量
        from config.settings import settings
        
        if _instance is None:
            if settings.STORAGE_TYPE == "local":
                from .local_storage import LocalStorage
                _instance = LocalStorage(settings.LOCAL_STORAGE_PATH)
            elif settings.STORAGE_TYPE == "minio":
                from .minio_storage import MinIOStorage
                try:
                    _instance = MinIOStorage(
                        endpoint=settings.MINIO_ENDPOINT,
                        access_key=settings.MINIO_ACCESS_KEY,
                        secret_key=settings.MINIO_SECRET_KEY,
                        bucket=settings.MINIO_BUCKET,
                        secure=settings.MINIO_SECURE
                    )
                except Exception as e:
                    logger.error(f"MinIO 初始化失败，降级到本地存储: {e}")
                    from .local_storage import LocalStorage
                    _instance = LocalStorage(settings.LOCAL_STORAGE_PATH)
            else:
                from .local_storage import LocalStorage
                _instance = LocalStorage(settings.LOCAL_STORAGE_PATH)
        return _instance
    
    return _get_storage

# 创建单例函数
get_storage = _create_storage_singleton()