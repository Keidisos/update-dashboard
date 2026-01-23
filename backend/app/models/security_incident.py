"""
Security Incident model for SOC (Security Operations Center).
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import String, Text, Boolean, DateTime, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.database import Base


class SeverityLevel(str, Enum):
    """Severity level of a security incident."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCategory(str, Enum):
    """Category of security incident."""
    SSH_INTRUSION = "ssh_intrusion"
    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_COMMAND = "suspicious_command"
    MALWARE_DETECTION = "malware_detection"
    ANOMALY = "anomaly"
    OTHER = "other"


class SecurityIncident(Base):
    """Security incident detected by SOC analysis."""
    
    __tablename__ = "security_incidents"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Associated host
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), nullable=False)
    
    # Incident classification
    severity: Mapped[SeverityLevel] = mapped_column(
        SQLEnum(SeverityLevel),
        nullable=False
    )
    category: Mapped[IncidentCategory] = mapped_column(
        SQLEnum(IncidentCategory),
        default=IncidentCategory.OTHER,
        nullable=False
    )
    
    # Main description
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # AI Analysis from Ollama
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Technical details
    log_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_ips: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # List of IPs
    affected_users: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # List of users
    mitre_techniques: Mapped[Optional[str]] = mapped_column(JSON, nullable=True)  # MITRE ATT&CK IDs
    
    # Event count (for aggregated incidents)
    event_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<SecurityIncident {self.id} ({self.severity.value} - {self.category.value})>"
