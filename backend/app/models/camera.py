# -*- coding: utf-8 -*-
"""
摄像头模型

定义摄像头/监控点位的数据结构
"""
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from .area import Area
    from .camera_algorithm import CameraAlgorithm


class Camera(Base, AuditMixin):
    """
    摄像头表
    
    存储摄像头设备信息和配置
    """
    
    __tablename__ = "cameras"
    __table_args__ = {
        "comment": "摄像头表"
    }
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="摄像头ID (32位UUID)"
    )
    
    # ==================== 基本信息 ====================
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="摄像头名称"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="摄像头编码 (可选)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="摄像头描述"
    )
    
    # ==================== 所属区域 ====================
    area_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="所属区域ID"
    )
    
    # ==================== 连接信息 ====================
    rtsp_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="RTSP 流地址"
    )
    
    rtsp_username: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="RTSP 用户名"
    )
    
    rtsp_password: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="RTSP 密码"
    )
    
    # ==================== 设备信息 ====================
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="设备厂商"
    )
    
    device_model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="设备型号"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="设备IP地址"
    )
    
    # ==================== 位置信息 ====================
    location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="安装位置描述"
    )
    
    longitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="经度"
    )
    
    latitude: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="纬度"
    )
    
    # ==================== 状态信息 ====================
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="offline",
        comment="在线状态: online/offline/error"
    )
    
    # ==================== 视频参数 ====================
    fps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=25,
        comment="帧率"
    )
    
    resolution: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="分辨率 (如 1920x1080)"
    )
    
    # ==================== 关系 ====================
    # 所属区域
    area: Mapped[Optional["Area"]] = relationship(
        "Area",
        back_populates="cameras"
    )
    
    # 关联的算法配置
    algorithm_configs: Mapped[List["CameraAlgorithm"]] = relationship(
        "CameraAlgorithm",
        back_populates="camera",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Camera(id={self.id}, name={self.name}, status={self.status})>"
    
    @property
    def is_online(self) -> bool:
        """是否在线"""
        return self.status == "online"
    
    @property
    def full_rtsp_url(self) -> str:
        """获取完整的 RTSP URL (包含认证信息)"""
        if not self.rtsp_username or not self.rtsp_password:
            return self.rtsp_url
        
        # 解析并插入认证信息
        if "://" in self.rtsp_url:
            protocol, rest = self.rtsp_url.split("://", 1)
            return f"{protocol}://{self.rtsp_username}:{self.rtsp_password}@{rest}"
        
        return self.rtsp_url
