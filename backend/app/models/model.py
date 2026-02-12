# -*- coding: utf-8 -*-
"""
AI模型定义

定义 AI 检测模型的数据结构
"""
import json
from typing import Optional, List, Any, TYPE_CHECKING

from sqlalchemy import String, Boolean, Integer, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from .algorithm import Algorithm


class Model(Base, AuditMixin):
    """
    AI模型表
    
    存储 AI 模型文件信息和配置
    一个模型可以支持多个检测类别，对应多个算法
    """
    
    __tablename__ = "models"
    __table_args__ = {
        "comment": "AI模型表"
    }
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="模型ID (32位UUID)"
    )
    
    # ==================== 基本信息 ====================
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模型名称"
    )
    
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="模型编码 (唯一标识)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模型描述"
    )
    
    # ==================== 模型文件 ====================
    model_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="yolo",
        comment="模型类型: yolo/onnx/tensorrt"
    )
    
    model_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="模型文件路径"
    )
    
    version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="模型版本"
    )
    
    # ==================== 支持的类别 ====================
    _classes: Mapped[Optional[str]] = mapped_column(
        "classes",
        JSON,
        nullable=True,
        comment="支持的检测类别列表 (JSON数组)"
    )
    
    # ==================== 性能参数 ====================
    gpu_memory_mb: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="预估GPU显存占用 (MB)"
    )
    
    inference_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="单帧推理耗时 (ms)"
    )
    
    input_width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="输入图像宽度"
    )
    
    input_height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="输入图像高度"
    )
    
    # ==================== 状态 ====================
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    # ==================== 关系 ====================
    # 关联的算法
    algorithms: Mapped[List["Algorithm"]] = relationship(
        "Algorithm",
        back_populates="model",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Model(id={self.id}, code={self.code}, type={self.model_type})>"
    
    @property
    def classes(self) -> List[str]:
        """获取支持的类别列表"""
        if self._classes is None:
            return []
        if isinstance(self._classes, str):
            try:
                return json.loads(self._classes)
            except (json.JSONDecodeError, TypeError):
                return []
        return self._classes if isinstance(self._classes, list) else []
    
    @classes.setter
    def classes(self, value: List[str]) -> None:
        """设置支持的类别列表"""
        self._classes = value
