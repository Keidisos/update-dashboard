"""
Host model for storing remote host configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConnectionType(str, Enum):
    """Type of connection to the Docker daemon."""
    SSH = "ssh"
    TCP = "tcp"


class Host(Base):
    """Remote host configuration."""
    
    __tablename__ = "hosts"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Connection type
    connection_type: Mapped[ConnectionType] = mapped_column(
        SQLEnum(ConnectionType),
        default=ConnectionType.SSH,
        nullable=False
    )
    
    # SSH Configuration
    ssh_port: Mapped[int] = mapped_column(default=22)
    ssh_user: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ssh_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ssh_password_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Docker TCP Configuration
    docker_port: Mapped[int] = mapped_column(default=2376)
    docker_tls: Mapped[bool] = mapped_column(default=True)
    docker_cert_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # OS Information (auto-detected)
    os_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # debian, ubuntu, centos, etc.
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    last_connected: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Host {self.name} ({self.hostname})>"
