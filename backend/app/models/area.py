# -*- coding: utf-8 -*-
"""
区域模型

定义摄像头区域/点位分组的数据结构
"""
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, AuditMixin, generate_uuid

if TYPE_CHECKING:
    from .camera import Camera


class Area(Base, AuditMixin):
    """
    区域表
    
    用于组织和管理摄像头，支持树形结构
    """
    
    __tablename__ = "areas"
    __table_args__ = {
        "comment": "区域表"
    }
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="区域ID (32位UUID)"
    )
    
    # ==================== 基本信息 ====================
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="区域名称"
    )
    
    code: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        comment="区域编码 (可选)"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="区域描述"
    )
    
    # ==================== 树形结构 ====================
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="父区域ID"
    )

    # ==================== 层级冗余（用于快速展示/查询） ====================
    # level: 深度（根=1）
    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="层级深度（根=1）"
    )
    # hierarchy_path: 按名称拼接的层级路径，如 “根节点/车间/A区域”
    hierarchy_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="层级路径（按名称拼接，用于展示）"
    )
    # id_path: ID 层级路径，如 /root_id/1/1.1，用于策略 area 通配符匹配
    id_path: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="ID层级路径，用于策略区域匹配"
    )

    # ==================== 排序 ====================
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="排序序号 (越小越靠前)"
    )
    
    # ==================== 关系 ====================
    # 父区域
    parent: Mapped[Optional["Area"]] = relationship(
        "Area",
        remote_side=[id],
        back_populates="children"
    )
    
    # 子区域
    children: Mapped[List["Area"]] = relationship(
        "Area",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # 该区域下的摄像头
    cameras: Mapped[List["Camera"]] = relationship(
        "Camera",
        back_populates="area",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Area(id={self.id}, name={self.name})>"
    
    @property
    def full_path(self) -> str:
        """获取完整路径名称"""
        if self.parent is None:
            return self.name
        return f"{self.parent.full_path}/{self.name}"

    def compute_hierarchy(self, parent: Optional["Area"]) -> None:
        """
        计算并写入 level / hierarchy_path / id_path。
        hierarchy_path：名称层级路径；id_path：ID 层级路径，供策略 area 匹配。
        """
        if parent is None:
            self.level = 1
            self.hierarchy_path = self.name
            self.id_path = f"/{self.id}"
        else:
            self.level = int(getattr(parent, "level", 1)) + 1
            base = getattr(parent, "hierarchy_path", None) or parent.name
            self.hierarchy_path = f"{base}/{self.name}"
            parent_id_path = getattr(parent, "id_path", None) or f"/{parent.id}"
            self.id_path = f"{parent_id_path.rstrip('/')}/{self.id}"
