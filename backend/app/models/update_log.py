"""
Update log model for tracking update history.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UpdateType(str, Enum):
    """Type of update performed."""
    CONTAINER = "container"
    SYSTEM = "system"


class UpdateStatus(str, Enum):
    """Status of the update operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class UpdateLog(Base):
    """Log of update operations."""
    
    __tablename__ = "update_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), nullable=False)
    
    update_type: Mapped[UpdateType] = mapped_column(
        SQLEnum(UpdateType),
        nullable=False
    )
    status: Mapped[UpdateStatus] = mapped_column(
        SQLEnum(UpdateStatus),
        default=UpdateStatus.PENDING,
        nullable=False
    )
    
    # Container-specific fields
    container_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    container_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    old_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    new_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    old_image_digest: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    new_image_digest: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # System update fields
    packages_updated: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    
    # Execution details
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Notification
    notification_sent: Mapped[bool] = mapped_column(default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<UpdateLog {self.id} {self.update_type.value} {self.status.value}>"
