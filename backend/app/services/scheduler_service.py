"""
Background scheduler service for automatic update checks and application.
"""

import asyncio
import logging
from datetime import datetime
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session_maker
from app.models.host import Host
from app.services.docker_service import DockerService
from app.services.ssh_service import SSHService
from app.services.notification_service import send_discord_notification
from app.utils import decrypt_value

logger = logging.getLogger(__name__)
settings = get_settings()


class UpdateScheduler:
    """Manages automatic update checking and application."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_run: datetime | None = None
        self.next_run: datetime | None = None
        
    def start(self):
        """Start the scheduler."""
        if not settings.auto_check_enabled:
            logger.info("🔕 Auto-update scheduler is disabled (AUTO_CHECK_ENABLED=false)")
            return
            
        logger.info(f"🚀 Starting auto-update scheduler (interval: {settings.auto_check_interval_minutes} minutes)")
        
        # Add the periodic job
        self.scheduler.add_job(
            self._check_and_update_all_hosts,
            trigger=IntervalTrigger(minutes=settings.auto_check_interval_minutes),
            id='auto_update_check',
            name='Auto Update Check',
            replace_existing=True,
            max_instances=1,  # Prevent concurrent runs
        )
        
        self.scheduler.start()
        self.is_running = True
        
        # Update next run time
        job = self.scheduler.get_job('auto_update_check')
        if job:
            self.next_run = job.next_run_time
            
        logger.info(f"✅ Scheduler started. Next check: {self.next_run}")
    
    def stop(self):
        """Stop the scheduler."""
        if self.is_running:
            logger.info("🛑 Stopping auto-update scheduler")
            self.scheduler.shutdown()
            self.is_running = False
    
    async def run_now(self):
        """Manually trigger an update check."""
        logger.info("▶️ Manual update check triggered")
        await self._check_and_update_all_hosts()
    
    async def _check_and_update_all_hosts(self):
        """Check and update all hosts."""
        self.last_run = datetime.now()
        
        try:
            logger.info("=" * 60)
            logger.info(f"🔍 Starting automatic update check at {self.last_run}")
            logger.info("=" * 60)
            
            # Get all hosts from database
            async with async_session_maker() as session:
                result = await session.execute(select(Host))
                hosts = result.scalars().all()
                
                if not hosts:
                    logger.info("ℹ️ No hosts configured")
                    return
                
                logger.info(f"📝 Found {len(hosts)} host(s) to check")
                
                for host in hosts:
                    await self._process_host(host, session)
                
            logger.info("=" * 60)
            logger.info("✅ Automatic update check completed")
            logger.info("=" * 60)
            
            # Update next run time
            job = self.scheduler.get_job('auto_update_check')
            if job:
                self.next_run = job.next_run_time
                
        except Exception as e:
            logger.error(f"❌ Error during automatic update check: {e}", exc_info=True)
    
    async def _process_host(self, host: Host, session):
        """Process a single host for updates."""
        logger.info(f"\n📡 Checking host: {host.name} ({host.hostname})")
        
        try:
            # Check containers if enabled
            if settings.auto_update_containers:
                await self._check_containers(host)
            else:
                logger.info(f"  ⏭️ Container updates disabled (AUTO_UPDATE_CONTAINERS=false)")
            
            # Check system updates if enabled
            if settings.auto_update_system:
                await self._check_system(host)
            else:
                logger.info(f"  ⏭️ System updates disabled (AUTO_UPDATE_SYSTEM=false)")
                
        except Exception as e:
            logger.error(f"  ❌ Error processing host {host.name}: {e}")
            await send_discord_notification(
                f"❌ Auto-update failed for **{host.name}**",
                f"```{str(e)}```",
                color=0xFF0000
            )
    
    async def _check_containers(self, host: Host):
        """Check and update containers for a host."""
        logger.info(f"  🐳 Checking containers...")
        
        try:
            # Decrypt credentials
            ssh_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key) if host.ssh_key_encrypted else None
            ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key) if host.ssh_password_encrypted else None
            
            # Connect to Docker
            docker_service = DockerService(
                host=host,
                ssh_key=ssh_key,
                ssh_password=ssh_password,
            )
            
            # List containers with update check
            containers = await docker_service.list_containers(all=True)
            
            # Find containers with updates
            updates_available = [c for c in containers if c.update_available]
            
            if not updates_available:
                logger.info(f"  ✅ All containers up to date ({len(containers)} total)")
                return
            
            logger.info(f"  🔄 Found {len(updates_available)} container(s) with updates")
            
            # Update each container
            for container in updates_available:
                container_name = container.name or container.id
                logger.info(f"    📦 Updating: {container_name}")
                
                try:
                    result = await docker_service.update_container(container.id)
                    
                    if result.get('success'):
                        logger.info(f"    ✅ {container_name} updated successfully")
                        await send_discord_notification(
                            f"✅ Container updated on **{host.name}**",
                            f"**{container_name}** has been updated to the latest version",
                            color=0x00FF00
                        )
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        logger.error(f"    ❌ {container_name} update failed: {error_msg}")
                        await send_discord_notification(
                            f"❌ Container update failed on **{host.name}**",
                            f"**{container_name}**: {error_msg}",
                            color=0xFF0000
                        )
                    
                except Exception as e:
                    logger.error(f"    ❌ Error updating {container_name}: {e}")
                    
        except Exception as e:
            logger.error(f"  ❌ Docker check failed: {e}")
            raise
    
    async def _check_system(self, host: Host):
        """Check and update system packages for a host."""
        logger.info(f"  💻 Checking system updates...")
        
        try:
            # Decrypt credentials
            ssh_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key) if host.ssh_key_encrypted else None
            ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key) if host.ssh_password_encrypted else None
            
            # Connect via SSH
            ssh_service = SSHService(
                host=host,
                private_key=ssh_key,
                password=ssh_password,
            )
            
            await ssh_service.connect()
            
            try:
                # Check for updates
                updates = await ssh_service.check_updates()
                
                if updates['updates_available'] == 0:
                    logger.info(f"  ✅ System is up to date")
                    return
                
                logger.info(f"  🔄 Found {updates['updates_available']} system update(s)")
                
                # Apply updates
                success, output = await ssh_service.apply_updates()
                
                if success:
                    logger.info(f"  ✅ System updates applied successfully")
                    await send_discord_notification(
                        f"✅ System updated on **{host.name}**",
                        f"{updates['updates_available']} package(s) updated",
                        color=0x00FF00
                    )
                else:
                    logger.error(f"  ❌ System update failed")
                    await send_discord_notification(
                        f"❌ System update failed on **{host.name}**",
                        f"Check logs for details",
                        color=0xFF0000
                    )
                    
            finally:
                await ssh_service.disconnect()
                
        except Exception as e:
            logger.error(f"  ❌ System check failed: {e}")
            raise


# Global scheduler instance
scheduler = UpdateScheduler()


def get_scheduler() -> UpdateScheduler:
    """Get the global scheduler instance."""
    return scheduler
