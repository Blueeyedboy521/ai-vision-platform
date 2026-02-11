"""
Alarm model.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Alarm(Base, TimestampMixin):
    """Alarm model."""
    
    __tablename__ = "alarms"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    algorithm_id: Mapped[int] = mapped_column(ForeignKey("algorithms.id"), index=True)
    level: Mapped[str] = mapped_column(String(20))  # info, warning, danger
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, confirmed, resolved, ignored
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    camera = relationship("Camera", back_populates="alarms")
    algorithm = relationship("Algorithm", back_populates="alarms")
