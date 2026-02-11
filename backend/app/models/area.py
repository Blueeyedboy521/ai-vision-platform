"""
Area model.
"""

from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Area(Base, TimestampMixin):
    """Area model."""
    
    __tablename__ = "areas"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    parent = relationship("Area", remote_side=[id], back_populates="children")
    children: Mapped[List["Area"]] = relationship("Area", back_populates="parent")
    cameras = relationship("Camera", back_populates="area")
