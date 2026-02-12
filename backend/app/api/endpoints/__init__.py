# -*- coding: utf-8 -*-
"""
API 端点模块
"""
from . import auth
from . import cameras
from . import areas
from . import models
from . import algorithms
from . import alarms
from . import system
from . import media_hooks

__all__ = [
    "auth",
    "cameras",
    "areas",
    "models",
    "algorithms",
    "alarms",
    "system",
    "media_hooks"
]
