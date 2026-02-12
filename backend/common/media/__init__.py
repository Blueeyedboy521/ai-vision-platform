# -*- coding: utf-8 -*-
"""
流媒体模块

提供 ZLMediaKit 流媒体服务器的 API 封装
"""
from .zlm_client import ZLMediaKitClient, get_zlm_client
from .stream_manager import StreamManager

__all__ = ["ZLMediaKitClient", "get_zlm_client", "StreamManager"]
