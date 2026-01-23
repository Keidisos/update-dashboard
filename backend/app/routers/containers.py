"""
Containers API Router - Container management and updates.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.host import Host
from app.models.update_log import UpdateLog, UpdateType, UpdateStatus
from app.schemas import (
    ContainerInfo, ContainerUpdateRequest, ContainerUpdateResult
)
from app.services.docker_service import DockerService
from app.services.registry_service import RegistryService
from app.services.notification_service import NotificationService
from app.utils import decrypt_value
from app.config import get_settings

router = APIRouter(prefix="/containers", tags=["containers"])

settings = get_settings()


async def get_docker_service(host_id: int, db: AsyncSession) -> tuple[DockerService, Host]:
    """Helper to get Docker service for a host."""
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
        except Exception:
            pass
    
    if host.ssh_password_encrypted:
        try:
            ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key)
        except Exception:
            pass
    
    return DockerService(host, ssh_key, ssh_password), host


@router.get("/{host_id}", response_model=List[ContainerInfo])
async def list_containers(
    host_id: int,
    all: bool = True,
    check_updates: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all containers on a host.
    
    Args:
        host_id: Host ID
        all: Include stopped containers
        check_updates: Check registry for available updates (slower)
    """
    docker_service, host = await get_docker_service(host_id, db)
    
    try:
        containers = await docker_service.list_containers(all=all)
        
        if check_updates:
            registry_service = RegistryService()
            
            for container in containers:
                try:
                    # Get local digest
                    local_digest = await docker_service.get_image_digest(container.image)
                    container.local_digest = local_digest
                    
                    if local_digest:
                        # Check for update
                        update_available, remote_digest = await registry_service.check_update_available(
                            container.image,
                            local_digest
                        )
                        container.update_available = update_available
                        container.remote_digest = remote_digest
                except Exception as e:
                    # Ignore individual container update check errors
                    pass
        
        return containers
        
    except Exception as e:
        # If Docker is unreachable, return empty list instead of error
        # This prevents the frontend from showing a scary error message
        str_error = str(e).lower()
        if "docker" in str_error or "connection" in str_error or "refused" in str_error:
            return []
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list containers: {str(e)}"
        )
    finally:
        await docker_service.disconnect()


@router.get("/{host_id}/{container_id}", response_model=ContainerInfo)
async def get_container(
    host_id: int,
    container_id: str,
    check_updates: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific container."""
    docker_service, host = await get_docker_service(host_id, db)
    
    try:
        container = await docker_service.get_container(container_id)
        
        if check_updates:
            registry_service = RegistryService()
            local_digest = await docker_service.get_image_digest(container.image)
            container.local_digest = local_digest
            
            if local_digest:
                update_available, remote_digest = await registry_service.check_update_available(
                    container.image,
                    local_digest
                )
                container.update_available = update_available
                container.remote_digest = remote_digest
        
        return container
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get container: {str(e)}"
        )
    finally:
        await docker_service.disconnect()


@router.post("/{host_id}/update", response_model=ContainerUpdateResult)
async def update_container(
    host_id: int,
    request: ContainerUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a container to a new image.
    
    This is the CORE operation - it preserves all container configuration
    while updating to the new image.
    """
    docker_service, host = await get_docker_service(host_id, db)
    notification_service = NotificationService()
    
    try:
        # Get container info before update
        container = await docker_service.get_container(request.container_id)
        
        # Create update log
        update_log = UpdateLog(
            host_id=host_id,
            update_type=UpdateType.CONTAINER,
            status=UpdateStatus.IN_PROGRESS,
            container_name=container.name,
            container_id=container.id,
            old_image=container.image,
        )
        db.add(update_log)
        await db.commit()
        
        # Perform update
        result = await docker_service.update_container(request.container_id)
        
        # Update log
        update_log.status = UpdateStatus.SUCCESS if result.success else UpdateStatus.FAILED
        update_log.new_image = result.new_image
        update_log.new_image_digest = result.new_container_id
        update_log.error_message = result.error
        update_log.logs = "\n".join(result.logs)
        await db.commit()
        
        # Send notification in background
        if notification_service.is_configured:
            background_tasks.add_task(
                notification_service.notify_container_updated,
                host.name,
                container.name,
                result.old_image,
                result.new_image,
                result.success,
                result.error
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update container: {str(e)}"
        )
    finally:
        await docker_service.disconnect()


@router.post("/{host_id}/check-updates")
async def check_all_updates(
    host_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Check all containers for available updates.
    Sends notifications for any containers with updates.
    """
    docker_service, host = await get_docker_service(host_id, db)
    registry_service = RegistryService()
    notification_service = NotificationService()
    
    try:
        containers = await docker_service.list_containers(all=True)
        updates_found = []
        
        for container in containers:
            local_digest = await docker_service.get_image_digest(container.image)
            
            if local_digest:
                update_available, remote_digest = await registry_service.check_update_available(
                    container.image,
                    local_digest
                )
                
                if update_available:
                    updates_found.append({
                        "container_id": container.id,
                        "container_name": container.name,
                        "image": container.image,
                        "current_digest": local_digest,
                        "new_digest": remote_digest
                    })
                    
                    # Send notification
                    if notification_service.is_configured:
                        background_tasks.add_task(
                            notification_service.notify_container_update_available,
                            host.name,
                            container.name,
                            container.image,
                            local_digest,
                            remote_digest
                        )
        
        return {
            "host_id": host_id,
            "containers_checked": len(containers),
            "updates_available": len(updates_found),
            "updates": updates_found
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check updates: {str(e)}"
        )
    finally:
        await docker_service.disconnect()


@router.delete("/{host_id}/{container_id}")
async def delete_container(
    host_id: int,
    container_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    remove_image: bool = True,
    force: bool = False
):
    """
    Delete a container and optionally its image.
    
    Args:
        host_id: Host ID
        container_id: Container ID or name
        remove_image: Remove the container's image if not used by other containers (default: True)
        force: Force removal even if container is running (default: False)
    """
    docker_service, host = await get_docker_service(host_id, db)
    notification_service = NotificationService()
    
    try:
        # Get container info before deletion
        container = await docker_service.get_container(container_id)
        
        # Create deletion log
        update_log = UpdateLog(
            host_id=host_id,
            update_type=UpdateType.CONTAINER,
            status=UpdateStatus.IN_PROGRESS,
            container_name=container.name,
            container_id=container.id,
            old_image=container.image,
        )
        db.add(update_log)
        await db.commit()
        
        # Perform deletion
        result = await docker_service.delete_container(
            container_id=container_id,
            remove_image=remove_image,
            force=force
        )
        
        # Update log
        update_log.status = UpdateStatus.SUCCESS if result["success"] else UpdateStatus.FAILED
        update_log.error_message = result.get("error")
        update_log.logs = "\n".join(result.get("removed_items", []))
        await db.commit()
        
        # Send notification in background
        if notification_service.is_configured and result["success"]:
            background_tasks.add_task(
                notification_service.notify_container_deleted,
                host.name,
                result["container_name"],
                result.get("image_id", "")[:12],
                result.get("removed_items", [])
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete container: {str(e)}"
        )
    finally:
        await docker_service.disconnect()
