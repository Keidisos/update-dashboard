"""
System API Router - OS update management via SSH.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.host import Host
from app.models.update_log import UpdateLog, UpdateType, UpdateStatus
from app.schemas import (
    SystemUpdateStatus, PackageInfo, SystemUpdateRequest, SystemUpdateResult
)
from app.services.ssh_service import SSHService
from app.services.notification_service import NotificationService
from app.utils import decrypt_value
from app.config import get_settings

router = APIRouter(prefix="/system", tags=["system"])

settings = get_settings()


async def get_ssh_service(host_id: int, db: AsyncSession) -> tuple[SSHService, Host]:
    """Helper to get SSH service for a host."""
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    # Decrypt credentials
    private_key = None
    password = None
    
    if host.ssh_key_encrypted:
        try:
            private_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key)
        except Exception:
            pass
            
    if host.ssh_password_encrypted:
        try:
            password = decrypt_value(host.ssh_password_encrypted, settings.secret_key)
        except Exception:
            pass
    
    return SSHService(host, private_key, password), host


@router.get("/{host_id}/updates", response_model=SystemUpdateStatus)
async def check_system_updates(
    host_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Check for available system updates on a host.
    """
    ssh_service, host = await get_ssh_service(host_id, db)
    notification_service = NotificationService()
    
    try:
        # Get system info
        sys_info = await ssh_service.get_system_info()
        
        # Update host with OS info
        host.os_type = sys_info.os_id
        host.os_version = sys_info.os_version
        await db.commit()
        
        # Check for updates
        updates = await ssh_service.check_updates()
        
        # Convert to schema
        packages = [
            PackageInfo(
                name=u.name,
                current_version=u.current_version,
                new_version=u.new_version,
                repository=u.repository
            )
            for u in updates
        ]
        
        # Send notification if updates available
        if updates and notification_service.is_configured:
            background_tasks.add_task(
                notification_service.notify_system_updates_available,
                host.name,
                sys_info.os_name,
                len(updates),
                [u.name for u in updates]
            )
        
        from datetime import datetime
        return SystemUpdateStatus(
            host_id=host_id,
            os_type=sys_info.os_id,
            os_version=sys_info.os_version,
            updates_available=len(updates),
            packages=packages,
            last_checked=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check system updates: {str(e)}"
        )
    finally:
        await ssh_service.disconnect()


@router.post("/{host_id}/updates", response_model=SystemUpdateResult)
async def apply_system_updates(
    host_id: int,
    request: Optional[SystemUpdateRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply system updates on a host.
    
    Args:
        host_id: Host ID
        request: Optional request with specific packages to update
    """
    ssh_service, host = await get_ssh_service(host_id, db)
    notification_service = NotificationService()
    
    packages = request.packages if request else None
    
    try:
        # Create update log
        update_log = UpdateLog(
            host_id=host_id,
            update_type=UpdateType.SYSTEM,
            status=UpdateStatus.IN_PROGRESS,
        )
        db.add(update_log)
        await db.commit()
        
        # Apply updates
        success, output = await ssh_service.apply_updates(packages)
        
        # Determine which packages were updated (best effort)
        packages_updated = packages or ["all"]
        
        # Update log
        update_log.status = UpdateStatus.SUCCESS if success else UpdateStatus.FAILED
        update_log.packages_updated = ",".join(packages_updated)
        update_log.logs = output
        if not success:
            update_log.error_message = "Update command failed"
        await db.commit()
        
        # Send notification
        if notification_service.is_configured and background_tasks:
            background_tasks.add_task(
                notification_service.notify_system_updated,
                host.name,
                packages_updated,
                success,
                None if success else "Update command failed"
            )
        
        return SystemUpdateResult(
            success=success,
            host_id=host_id,
            packages_updated=packages_updated if success else [],
            error=None if success else "Update command failed",
            logs=output
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply system updates: {str(e)}"
        )
    finally:
        await ssh_service.disconnect()


@router.get("/{host_id}/info")
async def get_system_info(
    host_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get operating system information for a host."""
    ssh_service, host = await get_ssh_service(host_id, db)
    
    try:
        sys_info = await ssh_service.get_system_info()
        
        # Update host
        host.os_type = sys_info.os_id
        host.os_version = sys_info.os_version
        await db.commit()
        
        return {
            "host_id": host_id,
            "os_id": sys_info.os_id,
            "os_version": sys_info.os_version,
            "os_name": sys_info.os_name,
            "kernel": sys_info.kernel
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system info: {str(e)}"
        )
    finally:
        await ssh_service.disconnect()
