# -*- coding: utf-8 -*-
"""
存储模块

提供文件存储功能的抽象接口和多种实现
"""
from .interface import StorageInterface
from .local_storage import LocalStorage

__all__ = ["StorageInterface", "LocalStorage", "get_storage"]


def get_storage() -> StorageInterface:
    """
    获取存储实例
    
    根据配置自动选择存储实现
    
    Returns:
        存储接口实例
    """
    from config.settings import settings
    
    if settings.STORAGE_TYPE == "local":
        return LocalStorage(settings.LOCAL_STORAGE_PATH)
    elif settings.STORAGE_TYPE == "minio":
        from .minio_storage import MinIOStorage
        return MinIOStorage(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE
        )
    else:
        # 默认使用本地存储
        return LocalStorage(settings.LOCAL_STORAGE_PATH)
