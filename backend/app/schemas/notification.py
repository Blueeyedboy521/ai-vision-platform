# -*- coding: utf-8 -*-
"""
通知/推送相关 Schema
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field


ProviderType = Literal["wecom_bot", "dingtalk_bot"]
TemplateType = Literal["text", "rich"]
CategoryType = Literal["ai", "system"]
DeliveryStatus = Literal["success", "failed", "skipped"]


class TimeWindow(BaseModel):
    start: str = Field(..., description="开始时间 HH:MM")
    end: str = Field(..., description="结束时间 HH:MM")


class NotificationEndpointCreate(BaseModel):
    name: str
    provider: ProviderType
    is_enabled: bool = True
    # 注意：仅写入时传明文，读取时后端会脱敏
    config: Dict[str, Any] = Field(default_factory=dict, description="通道配置（明文，仅写入用）")


class NotificationEndpointUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    # 仅当需要更新时传；若不传表示保持原值
    config: Optional[Dict[str, Any]] = None


class NotificationEndpointResponse(BaseModel):
    id: str
    name: str
    provider: ProviderType
    is_enabled: bool
    config_masked: Dict[str, Any] = Field(default_factory=dict, description="脱敏后的配置（用于前端回显）")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NotificationTemplateCreate(BaseModel):
    name: str
    type: TemplateType
    is_enabled: bool = True
    content: Dict[str, Any] = Field(default_factory=dict, description="模板内容 JSON（title/text/image_url/link_url 等）")


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    content: Optional[Dict[str, Any]] = None


class NotificationTemplateResponse(BaseModel):
    id: str
    name: str
    type: TemplateType
    is_enabled: bool
    content: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NotificationPolicyCreate(BaseModel):
    name: str
    priority: int = 100
    is_enabled: bool = True
    match: Dict[str, Any] = Field(
        default_factory=dict,
        description="匹配条件 JSON（支持多选/通配符/exclude/time_window 等）",
    )
    actions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "动作数组 actions[]（每个 action: endpoint_ids/template_id/throttle_sec/dedup_key/push_order/"
            "retry_times/retry_interval_sec 等）"
        ),
    )


class NotificationPolicyUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    is_enabled: Optional[bool] = None
    match: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None


class NotificationPolicyResponse(BaseModel):
    id: str
    name: str
    priority: int
    is_enabled: bool
    match: Dict[str, Any]
    actions: List[Dict[str, Any]]
    match_desc: Optional[str] = None
    actions_desc: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NotificationDeliveryLogResponse(BaseModel):
    id: str
    alarm_id: Optional[str]
    category: CategoryType
    alarm_type: str
    level: str
    endpoint_id: str
    provider: ProviderType
    template_id: Optional[str]
    status: DeliveryStatus
    error: Optional[str]
    created_at: Optional[str] = None


class NotificationTestSendRequest(BaseModel):
    endpoint_id: str
    template_id: Optional[str] = None
    category: CategoryType = "system"
    alarm_type: str = "test"
    level: str = "info"
    title: str = "测试通知"
    text: str = "这是一条测试通知"
    image_url: Optional[str] = None
    link_url: Optional[str] = None

