# -*- coding: utf-8 -*-
"""
算法模型

定义检测算法/检测能力的数据结构
"""
import json
from typing import Optional, List, Any, Dict, TYPE_CHECKING

from sqlalchemy import String, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from .model import Model
    from .camera_algorithm import CameraAlgorithm


class Algorithm(Base, AuditMixin):
    """
    检测算法表
    
    定义具体的检测能力，如"人员入侵检测"、"安全帽检测"等
    一个算法绑定到一个模型，使用模型支持的部分类别
    """
    
    __tablename__ = "algorithms"
    __table_args__ = {
        "comment": "检测算法表"
    }
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="算法ID (32位UUID)"
    )
    
    # ==================== 基本信息 ====================
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="算法名称"
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="算法编码 (唯一标识)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="算法描述"
    )
    
    # ==================== 关联模型 ====================
    model_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的模型ID"
    )
    
    # ==================== 检测配置 ====================
    _target_classes: Mapped[Optional[str]] = mapped_column(
        "target_classes",
        JSON,
        nullable=True,
        comment="目标检测类别列表 (JSON数组)"
    )
    
    default_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.5,
        comment="默认置信度阈值"
    )
    
    # ==================== 告警配置 ====================
    _alert_config: Mapped[Optional[str]] = mapped_column(
        "alert_config",
        JSON,
        nullable=True,
        comment="告警配置 (JSON对象)"
    )
    
    # ==================== 状态 ====================
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    # ==================== 关系 ====================
    # 关联的模型
    model: Mapped["Model"] = relationship(
        "Model",
        back_populates="algorithms"
    )
    
    # 摄像头配置
    camera_configs: Mapped[List["CameraAlgorithm"]] = relationship(
        "CameraAlgorithm",
        back_populates="algorithm",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Algorithm(id={self.id}, code={self.code}, model_id={self.model_id})>"
    
    @property
    def target_classes(self) -> List[str]:
        """获取目标检测类别列表"""
        if self._target_classes is None:
            return []
        if isinstance(self._target_classes, str):
            try:
                return json.loads(self._target_classes)
            except (json.JSONDecodeError, TypeError):
                return []
        return self._target_classes if isinstance(self._target_classes, list) else []
    
    @target_classes.setter
    def target_classes(self, value: List[str]) -> None:
        """设置目标检测类别列表"""
        self._target_classes = value
    
    @property
    def alert_config(self) -> Dict[str, Any]:
        """
        获取告警配置
        
        Returns:
            告警配置字典，包含:
            - trigger_type: 触发类型 (instant/duration/count)
            - duration_seconds: 持续时间阈值
            - count_threshold: 数量阈值
            - cooldown_seconds: 告警冷却时间
            - alert_level: 告警级别
        """
        default_config = {
            "trigger_type": "instant",
            "duration_seconds": 0,
            "count_threshold": 0,
            "cooldown_seconds": 30,
            "alert_level": "warning"
        }
        
        if self._alert_config is None:
            return default_config
        
        if isinstance(self._alert_config, str):
            try:
                config = json.loads(self._alert_config)
                return {**default_config, **config}
            except (json.JSONDecodeError, TypeError):
                return default_config
        
        if isinstance(self._alert_config, dict):
            return {**default_config, **self._alert_config}
        
        return default_config
    
    @alert_config.setter
    def alert_config(self, value: Dict[str, Any]) -> None:
        """设置告警配置"""
        self._alert_config = value
