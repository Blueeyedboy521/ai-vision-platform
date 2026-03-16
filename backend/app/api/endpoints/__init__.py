# -*- coding: utf-8 -*-
"""
API 端点模块
"""
from . import auth_controller
from . import cameras_controller
from . import areas_controller
from . import models_controller
from . import algorithms_controller
from . import alarms_controller
from . import system_controller
from . import media_hooks_controller
from . import notifications_controller
from . import files_controller

__all__ = [
    "auth_controller",
    "cameras_controller",
    "areas_controller",
    "models_controller",
    "algorithms_controller",
    "alarms_controller",
    "system_controller",
    "media_hooks_controller",
    "notifications_controller",
    "files_controller",
]
