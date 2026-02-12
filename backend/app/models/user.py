# -*- coding: utf-8 -*-
"""
用户模型

定义系统用户的数据结构
"""
from typing import Optional

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, AuditMixin, generate_uuid


class User(Base, AuditMixin):
    """
    用户表
    
    存储系统用户信息，包括管理员和普通用户
    """
    
    __tablename__ = "users"
    __table_args__ = {
        "comment": "用户表"
    }
    
    # ==================== 主键 ====================
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_uuid,
        comment="用户ID (32位UUID)"
    )
    
    # ==================== 基本信息 ====================
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名 (登录名)"
    )
    
    password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="密码 (bcrypt 哈希)"
    )
    
    nickname: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="昵称 (显示名)"
    )
    
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="邮箱地址"
    )
    
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="手机号码"
    )
    
    avatar: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="头像URL"
    )
    
    # ==================== 权限信息 ====================
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        comment="角色: admin(管理员)/user(普通用户)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    # ==================== 扩展信息 ====================
    remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注信息"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
    
    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == "admin"
