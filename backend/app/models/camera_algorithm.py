# -*- coding: utf-8 -*-
"""
摄像头-算法关联模型

定义摄像头和算法的关联配置
"""
import json
from typing import Optional, List, Any, Dict, TYPE_CHECKING

from sqlalchemy import String, Boolean, Float, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from .camera import Camera
    from .algorithm import Algorithm
    from .model import Model


class CameraAlgorithm(Base, AuditMixin):
    """
    摄像头-算法关联表
    
    记录每个摄像头启用的算法及其配置
    可以覆盖算法的默认配置，如置信度、检测区域等
    """
    
    __tablename__ = "camera_algorithms"
    __table_args__ = (
        UniqueConstraint("camera_id", "algorithm_id", name="uk_camera_algorithm"),
        {"comment": "摄像头-算法关联表"}
    )
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="关联ID (32位UUID)"
    )
    
    # ==================== 关联键 ====================
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
    
    model_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="模型ID (冗余字段，便于查询)"
    )
    
    # ==================== 覆盖配置 ====================
    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="置信度阈值 (覆盖算法默认值)"
    )
    
    _alert_config: Mapped[Optional[str]] = mapped_column(
        "alert_config",
        JSON,
        nullable=True,
        comment="告警配置 (覆盖算法默认值)"
    )
    
    _regions: Mapped[Optional[str]] = mapped_column(
        "regions",
        JSON,
        nullable=True,
        comment="检测区域 (多边形坐标列表)"
    )
    
    # ==================== 抽帧与告警间隔 ====================
    inference_interval_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="识别间隔(秒)，控制后台算法抽帧分析间隔"
    )
    alarm_interval_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="告警间隔(秒)，同一告警在此间隔内不重复推送，须>=识别间隔"
    )

    # ==================== 状态 ====================
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    # ==================== 关系 ====================
    camera: Mapped["Camera"] = relationship(
        "Camera",
        back_populates="algorithm_configs"
    )
    
    algorithm: Mapped["Algorithm"] = relationship(
        "Algorithm",
        back_populates="camera_configs"
    )
    
    def __repr__(self) -> str:
        return f"<CameraAlgorithm(camera_id={self.camera_id}, algorithm_id={self.algorithm_id})>"
    
    @property
    def alert_config(self) -> Optional[Dict[str, Any]]:
        """获取告警配置 (覆盖值)"""
        if self._alert_config is None:
            return None
        if isinstance(self._alert_config, str):
            try:
                return json.loads(self._alert_config)
            except (json.JSONDecodeError, TypeError):
                return None
        return self._alert_config if isinstance(self._alert_config, dict) else None
    
    @alert_config.setter
    def alert_config(self, value: Optional[Dict[str, Any]]) -> None:
        """设置告警配置"""
        self._alert_config = value
    
    @property
    def regions(self) -> List[List[List[float]]]:
        """
        获取检测区域列表
        
        格式: [
            [[x1,y1], [x2,y2], [x3,y3], ...],  # 多边形1
            [[x1,y1], [x2,y2], [x3,y3], ...],  # 多边形2
        ]
        """
        if self._regions is None:
            return []
        if isinstance(self._regions, str):
            try:
                return json.loads(self._regions)
            except (json.JSONDecodeError, TypeError):
                return []
        return self._regions if isinstance(self._regions, list) else []
    
    @regions.setter
    def regions(self, value: List[List[List[float]]]) -> None:
        """设置检测区域"""
        self._regions = value
    
    def get_effective_confidence(self) -> float:
        """
        获取生效的置信度
        
        优先使用覆盖值，否则使用算法默认值
        """
        if self.confidence is not None:
            return self.confidence
        if self.algorithm is not None:
            return self.algorithm.default_confidence
        return 0.5
    
    def get_effective_alert_config(self) -> Dict[str, Any]:
        """
        获取生效的告警配置
        
        合并算法默认配置和覆盖配置
        """
        base_config = {}
        if self.algorithm is not None:
            base_config = self.algorithm.alert_config.copy()
        
        override = self.alert_config
        if override is not None:
            base_config.update(override)
        
        return base_config
