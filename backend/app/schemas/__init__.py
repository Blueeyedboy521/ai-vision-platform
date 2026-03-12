# -*- coding: utf-8 -*-
"""
Pydantic Schema 模块

定义 API 请求和响应的数据模式
"""
from .common import (
    ResponseBase,
    PageRequest,
    PageResponse,
    IdResponse,
    MessageResponse,
    ErrorResponse
)
from .auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    RefreshTokenRequest,
    UserInfo
)
from .user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse
)
from .area import (
    AreaCreate,
    AreaUpdate,
    AreaResponse,
    AreaTreeResponse,
    AreaListResponse
)
from .camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraStatusResponse
)
from .model import (
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    ModelListResponse
)
from .algorithm import (
    AlgorithmCreate,
    AlgorithmUpdate,
    AlgorithmResponse,
    AlgorithmListResponse,
    CameraAlgorithmCreate,
    CameraAlgorithmUpdate,
    CameraAlgorithmResponse
)
from .alarm import (
    AlarmResponse,
    AlarmListResponse,
    AlarmConfirmRequest,
    AlarmStatsResponse
)
from .notification import (
    NotificationEndpointCreate,
    NotificationEndpointUpdate,
    NotificationEndpointResponse,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    NotificationPolicyCreate,
    NotificationPolicyUpdate,
    NotificationPolicyResponse,
    NotificationDeliveryLogResponse,
    NotificationTestSendRequest,
)

__all__ = [
    # Common
    "ResponseBase",
    "PageRequest",
    "PageResponse",
    "IdResponse",
    "MessageResponse",
    "ErrorResponse",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserInfo",
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    # Area
    "AreaCreate",
    "AreaUpdate",
    "AreaResponse",
    "AreaTreeResponse",
    "AreaListResponse",
    # Camera
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "CameraListResponse",
    "CameraStatusResponse",
    # Model
    "ModelCreate",
    "ModelUpdate",
    "ModelResponse",
    "ModelListResponse",
    # Algorithm
    "AlgorithmCreate",
    "AlgorithmUpdate",
    "AlgorithmResponse",
    "AlgorithmListResponse",
    "CameraAlgorithmCreate",
    "CameraAlgorithmUpdate",
    "CameraAlgorithmResponse",
    # Alarm
    "AlarmResponse",
    "AlarmListResponse",
    "AlarmConfirmRequest",
    "AlarmStatsResponse",
    # Notification
    "NotificationEndpointCreate",
    "NotificationEndpointUpdate",
    "NotificationEndpointResponse",
    "NotificationTemplateCreate",
    "NotificationTemplateUpdate",
    "NotificationTemplateResponse",
    "NotificationPolicyCreate",
    "NotificationPolicyUpdate",
    "NotificationPolicyResponse",
    "NotificationDeliveryLogResponse",
    "NotificationTestSendRequest",
]
