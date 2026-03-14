# -*- coding: utf-8 -*-
"""
通知/推送相关 ORM 模型

- NotificationEndpoint: 通道实例（如某个企微/钉钉机器人 webhook）
- NotificationTemplate: 模板（业务侧只区分 text/rich）
- NotificationPolicy: 路由策略（match + actions + time_window）
- NotificationDeliveryLog: 推送审计日志（系统告警只记录此表，不入 alarms）
"""

from __future__ import annotations

from typing import Optional, Any, Dict

from sqlalchemy import String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class NotificationEndpoint(Base, TimestampMixin):
    __tablename__ = "notification_endpoints"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="通道名称")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="provider: wecom_bot/dingtalk_bot")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    # 加密后的配置（JSON 字符串加密后 base64）
    encrypted_config: Mapped[str] = mapped_column(Text, nullable=False, comment="加密配置")

    # 便于列表展示/筛选的非敏感字段（可选，脱敏后也行）
    config_hint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="配置提示（脱敏）")


class NotificationTemplate(Base, TimestampMixin):
    __tablename__ = "notification_templates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    type: Mapped[str] = mapped_column(String(16), nullable=False, comment="text/rich")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    # 模板内容：建议存 JSON，包含 title/text 的模板字符串
    # 例如：{"title":"...", "text":"..."}；rich 可额外包含 image_url/link_url
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="模板内容 JSON")


class NotificationPolicy(Base, TimestampMixin):
    __tablename__ = "notification_policies"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="策略名称")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, comment="优先级（小优先）")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, comment="是否启用")

    # 匹配条件（JSON）：支持多选/通配符/排除：
    # category, alarm_type[], area_config[]（项内 area_id_path 与 event.area_id_path 匹配）, camera_id[], algorithm_id[], level[], exclude{}, time_window{}
    match: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, comment="匹配条件 JSON")

    # 动作（JSON）：标准为 list[dict]（同一 match 下可配置多个 action）
    actions: Mapped[Any] = mapped_column(JSON, nullable=False, comment="动作 JSON（actions 数组）")

    # 冗余中文描述：便于前端列表展示与搜索（因为 match/actions 中大量为 id）
    match_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="匹配条件中文描述（冗余）")
    actions_desc: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="动作中文描述（冗余）")


class NotificationDeliveryLog(Base, TimestampMixin):
    __tablename__ = "notification_delivery_logs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)

    # 业务/系统事件定位：
    # - 业务告警：alarm_id = alarms.id
    # - 系统告警：alarm_id 为系统侧生成的唯一 ID（不入 alarms 表，但用于链路追踪与审计）
    alarm_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="告警ID（业务告警）")

    category: Mapped[str] = mapped_column(String(16), nullable=False, comment="ai/system")
    alarm_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="告警类型/系统类型")
    level: Mapped[str] = mapped_column(String(16), nullable=False, comment="info/warning/danger/critical")

    endpoint_id: Mapped[str] = mapped_column(String(32), nullable=False, comment="endpoint_id")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, comment="provider")
    template_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="template_id")

    status: Mapped[str] = mapped_column(String(16), nullable=False, comment="success/failed/skipped")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="错误（脱敏）")

    request_meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="请求元信息（脱敏）")
    response_meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="响应元信息（脱敏）")

