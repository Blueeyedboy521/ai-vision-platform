# -*- coding: utf-8 -*-
"""
应用配置模块

从全局配置模块导入配置，提供给 app 模块使用
"""
from config.settings import settings, Settings, get_settings

__all__ = ["settings", "Settings", "get_settings"]
