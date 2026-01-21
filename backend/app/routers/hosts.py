"""
Hosts API Router - CRUD operations for remote hosts.
"""

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.host import Host, ConnectionType
from app.schemas import HostCreate, HostUpdate, HostResponse, HostStatus
from app.utils import encrypt_value
from app.config import get_settings

router = APIRouter(prefix="/hosts", tags=["hosts"])

settings = get_settings()


@router.get("", response_model=List[HostResponse])
async def list_hosts(
    db: AsyncSession = Depends(get_db),
    include_inactive: bool = False
):
    """List all configured hosts."""
    query = select(Host)
    if not include_inactive:
        query = query.where(Host.is_active == True)
    
    result = await db.execute(query)
    hosts = result.scalars().all()
    return hosts


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific host by ID."""
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    return host


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(host_data: HostCreate, db: AsyncSession = Depends(get_db)):
    """Create a new host configuration."""
    # Check for duplicate name
    result = await db.execute(select(Host).where(Host.name == host_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Host with name '{host_data.name}' already exists"
        )
    
    # Encrypt sensitive data
    ssh_key_encrypted = None
    ssh_password_encrypted = None
    docker_cert_encrypted = None
    
    if host_data.ssh_key:
        ssh_key_encrypted = encrypt_value(host_data.ssh_key, settings.secret_key)
    if host_data.ssh_password:
        ssh_password_encrypted = encrypt_value(host_data.ssh_password, settings.secret_key)
    if host_data.docker_cert:
        docker_cert_encrypted = encrypt_value(host_data.docker_cert, settings.secret_key)
    
    host = Host(
        name=host_data.name,
        hostname=host_data.hostname,
        connection_type=ConnectionType(host_data.connection_type.value),
        ssh_port=host_data.ssh_port,
        ssh_user=host_data.ssh_user,
        ssh_key_encrypted=ssh_key_encrypted,
        ssh_password_encrypted=ssh_password_encrypted,
        docker_port=host_data.docker_port,
        docker_tls=host_data.docker_tls,
        docker_cert_encrypted=docker_cert_encrypted,
    )
    
    db.add(host)
    await db.commit()
    await db.refresh(host)
    
    return host


@router.patch("/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: int,
    host_data: HostUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a host configuration."""
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    # Update fields
    update_data = host_data.model_dump(exclude_unset=True)
    
    # Handle encrypted fields
    if "ssh_key" in update_data:
        if update_data["ssh_key"]:
            host.ssh_key_encrypted = encrypt_value(update_data["ssh_key"], settings.secret_key)
        else:
            host.ssh_key_encrypted = None
        del update_data["ssh_key"]
        
    if "ssh_password" in update_data:
        if update_data["ssh_password"]:
            host.ssh_password_encrypted = encrypt_value(update_data["ssh_password"], settings.secret_key)
        else:
            host.ssh_password_encrypted = None
        del update_data["ssh_password"]
        
    if "docker_cert" in update_data:
        if update_data["docker_cert"]:
            host.docker_cert_encrypted = encrypt_value(update_data["docker_cert"], settings.secret_key)
        else:
            host.docker_cert_encrypted = None
        del update_data["docker_cert"]
    
    # Handle connection_type enum conversion
    if "connection_type" in update_data and update_data["connection_type"]:
        update_data["connection_type"] = ConnectionType(update_data["connection_type"].value)
    
    for key, value in update_data.items():
        setattr(host, key, value)
    
    host.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(host)
    
    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(host_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a host configuration."""
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    await db.delete(host)
    await db.commit()


@router.get("/{host_id}/status", response_model=HostStatus)
async def get_host_status(host_id: int, db: AsyncSession = Depends(get_db)):
    """Test connection to a host and get status."""
    from app.services.docker_service import DockerService
    from app.utils import decrypt_value
    
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    # Decrypt SSH credentials if present
    ssh_key = None
    ssh_password = None
    
    if host.ssh_key_encrypted:
        try:
            ssh_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key)
        except Exception as e:
            pass
            
    if host.ssh_password_encrypted:
        try:
            ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key)
        except Exception:
            pass
    
    # Try to connect
    docker_service = DockerService(host, ssh_key, ssh_password)
    
    try:
        client = await docker_service.connect()
        version = client.version()
        
        # Update last connected
        host.last_connected = datetime.utcnow()
        host.last_error = None
        await db.commit()
        
        return HostStatus(
            host_id=host_id,
            connected=True,
            docker_version=version.get("Version"),
            os_info=f"{version.get('Os')}/{version.get('Arch')}"
        )
    except Exception as e:
        host.last_error = str(e)
        await db.commit()
        
        return HostStatus(
            host_id=host_id,
            connected=False,
            error=str(e)
        )
    finally:
        await docker_service.disconnect()
