# -*- coding: utf-8 -*-
"""
通知接口定义

定义消息推送的抽象接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationLevel(str, Enum):
    """通知级别"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


@dataclass
class NotificationMessage:
    """
    通知消息数据类
    """
    title: str                              # 消息标题
    content: str                            # 消息内容
    level: NotificationLevel = NotificationLevel.INFO  # 消息级别
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    
    # 额外信息
    camera_name: Optional[str] = None       # 摄像头名称
    camera_id: Optional[str] = None         # 摄像头ID
    algorithm_name: Optional[str] = None    # 算法名称
    alarm_id: Optional[str] = None          # 告警ID
    snapshot_url: Optional[str] = None      # 告警截图URL
    
    # 接收者 (可选)
    recipients: List[str] = field(default_factory=list)  # 接收者列表 (邮箱/手机号)
    
    # 扩展数据
    extra: Dict[str, Any] = field(default_factory=dict)  # 其他扩展数据
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level.value,
            "timestamp": self.timestamp.isoformat(),
            "camera_name": self.camera_name,
            "camera_id": self.camera_id,
            "algorithm_name": self.algorithm_name,
            "alarm_id": self.alarm_id,
            "snapshot_url": self.snapshot_url,
            "recipients": self.recipients,
            "extra": self.extra
        }
    
    @classmethod
    def from_alarm(
        cls,
        alarm_data: dict,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> "NotificationMessage":
        """
        从告警数据创建通知消息
        
        Args:
            alarm_data: 告警数据字典
            title: 自定义标题
            content: 自定义内容
        """
        level_map = {
            "info": NotificationLevel.INFO,
            "warning": NotificationLevel.WARNING,
            "danger": NotificationLevel.DANGER,
            "critical": NotificationLevel.CRITICAL,
            "high": NotificationLevel.DANGER,
            "medium": NotificationLevel.WARNING,
            "low": NotificationLevel.INFO
        }
        
        alarm_level = alarm_data.get("alert_level", "info")
        level = level_map.get(alarm_level, NotificationLevel.INFO)
        
        algorithm_name = alarm_data.get("algorithm_name", "未知算法")
        camera_name = alarm_data.get("camera_name", "未知摄像头")
        
        if title is None:
            title = f"【{level.value.upper()}】{algorithm_name}"
        
        if content is None:
            timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"摄像头: {camera_name}\n" \
                     f"检测算法: {algorithm_name}\n" \
                     f"告警时间: {timestamp_str}"
        
        return cls(
            title=title,
            content=content,
            level=level,
            camera_name=camera_name,
            camera_id=alarm_data.get("camera_id"),
            algorithm_name=algorithm_name,
            alarm_id=alarm_data.get("alarm_id"),
            snapshot_url=alarm_data.get("snapshot_path")
        )


class NotificationInterface(ABC):
    """
    通知接口抽象类
    
    所有通知渠道的实现都需要继承此接口
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """通知渠道名称"""
        pass
    
    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """
        发送通知
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    def send_sync(self, message: NotificationMessage) -> bool:
        """
        同步发送通知
        
        Args:
            message: 通知消息
            
        Returns:
            是否发送成功
        """
        pass
    
    def is_enabled(self) -> bool:
        """检查通知渠道是否已启用"""
        return True
