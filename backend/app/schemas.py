"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============== Host Schemas ==============

class ConnectionType(str, Enum):
    SSH = "ssh"
    TCP = "tcp"


class HostBase(BaseModel):
    """Base host schema."""
    name: str = Field(..., min_length=1, max_length=255)
    hostname: str = Field(..., min_length=1, max_length=255)
    connection_type: ConnectionType = ConnectionType.SSH
    
    # SSH
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_user: Optional[str] = None
    
    # Docker TCP
    docker_port: int = Field(default=2376, ge=1, le=65535)
    docker_tls: bool = True


class HostCreate(HostBase):
    """Schema for creating a new host."""
    ssh_key: Optional[str] = None  # Private key content
    ssh_password: Optional[str] = None
    docker_cert: Optional[str] = None


class HostUpdate(BaseModel):
    """Schema for updating a host."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, min_length=1, max_length=255)
    connection_type: Optional[ConnectionType] = None
    ssh_port: Optional[int] = Field(None, ge=1, le=65535)
    ssh_user: Optional[str] = None
    ssh_key: Optional[str] = None
    ssh_password: Optional[str] = None
    docker_port: Optional[int] = Field(None, ge=1, le=65535)
    docker_tls: Optional[bool] = None
    docker_cert: Optional[str] = None
    is_active: Optional[bool] = None


class HostResponse(HostBase):
    """Schema for host response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    is_active: bool
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class HostStatus(BaseModel):
    """Host connection status."""
    host_id: int
    connected: bool
    docker_version: Optional[str] = None
    os_info: Optional[str] = None
    error: Optional[str] = None


# ============== Container Schemas ==============

class ContainerState(str, Enum):
    RUNNING = "running"
    EXITED = "exited"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    CREATED = "created"


class PortMapping(BaseModel):
    """Container port mapping."""
    container_port: int
    host_port: Optional[int] = None
    protocol: str = "tcp"
    host_ip: str = "0.0.0.0"


class VolumeMount(BaseModel):
    """Container volume mount."""
    source: str
    destination: str
    mode: str = "rw"
    type: str = "bind"  # bind, volume, tmpfs


class ContainerInfo(BaseModel):
    """Container information."""
    id: str
    name: str
    image: str
    image_id: str
    state: ContainerState
    status: str  # Human-readable status
    created: datetime
    
    # Configuration
    ports: List[PortMapping] = []
    volumes: List[VolumeMount] = []
    environment: Dict[str, str] = {}
    networks: List[str] = []
    labels: Dict[str, str] = {}
    restart_policy: str = "no"
    
    # Update status
    update_available: bool = False
    local_digest: Optional[str] = None
    remote_digest: Optional[str] = None


class ContainerUpdateRequest(BaseModel):
    """Request to update a container."""
    container_id: str
    force: bool = False  # Force update even if no new image


class ContainerUpdateResult(BaseModel):
    """Result of container update."""
    success: bool
    container_id: str
    old_container_id: str
    new_container_id: Optional[str] = None
    old_image: str
    new_image: str
    error: Optional[str] = None
    logs: List[str] = []


# ============== System Update Schemas ==============

class PackageInfo(BaseModel):
    """System package information."""
    name: str
    current_version: str
    new_version: str
    repository: Optional[str] = None


class SystemUpdateStatus(BaseModel):
    """System update status."""
    host_id: int
    os_type: str
    os_version: str
    updates_available: int
    packages: List[PackageInfo] = []
    last_checked: datetime


class SystemUpdateRequest(BaseModel):
    """Request to perform system update."""
    host_id: int
    packages: Optional[List[str]] = None  # None = update all


class SystemUpdateResult(BaseModel):
    """Result of system update."""
    success: bool
    host_id: int
    packages_updated: List[str] = []
    error: Optional[str] = None
    logs: str = ""


# ============== Notification Schemas ==============

class NotificationPayload(BaseModel):
    """Discord notification payload."""
    title: str
    description: str
    color: int = 0x00FF00  # Green by default
    fields: List[Dict[str, Any]] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
