# -*- coding: utf-8 -*-
"""
告警模型

定义告警记录的数据结构
"""
import json
from datetime import datetime
from typing import Optional, Any, Dict, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid


class Alarm(Base, AuditMixin):
    """
    告警记录表
    
    存储所有检测产生的告警记录
    """
    
    __tablename__ = "alarms"
    __table_args__ = (
        Index("idx_alarm_camera_time", "camera_id", "alarm_time"),
        Index("idx_alarm_status_level", "status", "level"),
        {"comment": "告警记录表"}
    )
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="告警ID (32位UUID)"
    )
    
    # ==================== 关联信息 ====================
    camera_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="摄像头ID"
    )
    
    algorithm_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("algorithms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="算法ID"
    )

    # ==================== 冗余信息（用于减少列表页关联查询） ====================
    camera_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="摄像头名称(冗余)"
    )
    algorithm_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="算法名称(冗余)"
    )
    area_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="区域ID(冗余)"
    )
    area_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="区域名称(冗余)"
    )
    
    # ==================== 告警信息 ====================
    alarm_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="detection",
        comment="告警类型: detection(检测)/offline(离线)/error(异常)"
    )
    
    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="warning",
        index=True,
        comment="告警级别: info/warning/danger/critical"
    )
    
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="告警标题"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="告警描述"
    )
    
    # ==================== 时间信息 ====================
    alarm_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        index=True,
        comment="告警时间"
    )
    
    # ==================== 截图和视频 ====================
    snapshot_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="告警截图URL"
    )
    
    video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="告警视频URL"
    )
    
    # ==================== 检测数据 ====================
    _detection_data: Mapped[Optional[str]] = mapped_column(
        "detection_data",
        JSON,
        nullable=True,
        comment="检测详细数据 (JSON，通常为检测结果列表)"
    )
    
    # ==================== 处理状态 ====================
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unconfirmed",
        index=True,
        comment="处理状态: unconfirmed(未确认)/confirmed(已确认)/ignored(已忽略)/processed(已处理)"
    )
    
    confirmed_by: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="确认人ID"
    )
    
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="确认时间"
    )
    
    confirm_remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="确认备注"
    )
    
    # ==================== 推送状态 ====================
    is_pushed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已推送通知"
    )
    
    push_channels: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="已推送的渠道 (逗号分隔)"
    )
    
    def __repr__(self) -> str:
        return f"<Alarm(id={self.id}, camera_id={self.camera_id}, level={self.level}, status={self.status})>"
    
    @property
    def detection_data(self) -> Any:
        """
        获取检测数据。

        兼容历史与当前两种存储格式：
        - 旧版本：dict
        - 当前版本：list[dict]（直接存整帧的 detections 列表，用于前端绘框）
        """
        if self._detection_data is None:
            return []
        raw = self._detection_data
        # 字符串时尝试反序列化
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return []
        # dict 或 list 都直接透出，交给上层按需使用
        if isinstance(raw, (dict, list)):
            return raw
        return []
    
    @detection_data.setter
    def detection_data(self, value: Any) -> None:
        """设置检测数据，允许 dict 或 list"""
        self._detection_data = value
    
    @property
    def is_confirmed(self) -> bool:
        """是否已确认"""
        return self.status in ("confirmed", "processed")
    
    @property
    def can_confirm(self) -> bool:
        """是否可以确认"""
        return self.status == "unconfirmed"
    
    def confirm(
        self,
        user_id: str,
        remark: Optional[str] = None,
        new_status: str = "confirmed"
    ) -> None:
        """
        确认告警
        
        Args:
            user_id: 确认人ID
            remark: 确认备注
            new_status: 新状态
        """
        if not self.can_confirm:
            raise ValueError(f"告警状态为 {self.status}，无法确认")
        
        self.status = new_status
        self.confirmed_by = user_id
        self.confirmed_at = datetime.now()
        self.confirm_remark = remark
