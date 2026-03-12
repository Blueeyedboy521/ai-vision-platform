# -*- coding: utf-8 -*-
"""
ORM 模型模块

导出所有数据库模型
"""
from .base import Base, TimestampMixin, AuditMixin, generate_uuid
from .user import User
from .area import Area
from .camera import Camera
from .model import Model
from .algorithm import Algorithm
from .camera_algorithm import CameraAlgorithm
from .alarm import Alarm
from .notification import (
    NotificationEndpoint,
    NotificationTemplate,
    NotificationPolicy,
    NotificationDeliveryLog,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "AuditMixin",
    "generate_uuid",
    "User",
    "Area",
    "Camera",
    "Model",
    "Algorithm",
    "CameraAlgorithm",
    "Alarm",
    "NotificationEndpoint",
    "NotificationTemplate",
    "NotificationPolicy",
    "NotificationDeliveryLog",
]
