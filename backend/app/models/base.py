# -*- coding: utf-8 -*-
"""
ORM 模型基类

提供所有模型的基类和通用 Mixin
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def generate_uuid() -> str:
    """
    生成 32 位 UUID (不带连字符)
    
    Returns:
        32 位十六进制字符串
    """
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    """
    所有 ORM 模型的基类
    
    继承自 SQLAlchemy 的 DeclarativeBase
    """
    pass


class TimestampMixin:
    """
    时间戳 Mixin
    
    提供 created_at 和 updated_at 字段
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class AuditMixin(TimestampMixin):
    """
    审计 Mixin
    
    继承 TimestampMixin，额外提供 created_by 和 updated_by 字段
    用于记录数据的创建者和最后修改者
    """
    
    created_by: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="创建人ID"
    )
    
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True,
        comment="更新人ID"
    )
