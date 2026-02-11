"""
Algorithm model.
"""

from typing import Optional, List

from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Algorithm(Base, TimestampMixin):
    """Algorithm model."""
    
    __tablename__ = "algorithms"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50))  # detection, classification, segmentation
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # Relationships
    alarms: Mapped[List["Alarm"]] = relationship("Alarm", back_populates="algorithm")
