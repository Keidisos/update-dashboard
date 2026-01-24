"""
Notification Service - Discord webhook notifications.

Sends alerts when updates are detected or completed.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via Discord webhooks.
    """

    # Discord embed colors
    COLOR_SUCCESS = 0x00FF00  # Green
    COLOR_WARNING = 0xFFAA00  # Orange
    COLOR_ERROR = 0xFF0000  # Red
    COLOR_INFO = 0x0099FF  # Blue

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize notification service.

        Args:
            webhook_url: Discord webhook URL. If not provided, uses config.
        """
        settings = get_settings()
        self.webhook_url = webhook_url or settings.discord_webhook_url

    @property
    def is_configured(self) -> bool:
        """Check if notifications are configured."""
        return bool(self.webhook_url)

    async def send_notification(
        self,
        title: str,
        description: str,
        color: int = COLOR_INFO,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[str] = None,
    ) -> bool:
        """
        Send a Discord notification.

        Args:
            title: Embed title
            description: Embed description
            color: Embed color (hex)
            fields: List of field dicts with name, value, inline
            footer: Optional footer text

        Returns:
            True if sent successfully
        """
        if not self.is_configured:
            logger.warning("Discord webhook not configured, skipping notification")
            return False

        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = {"text": footer}

        payload = {"embeds": [embed]}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Discord notification sent: {title}")
                return True
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False

    async def notify_container_update_available(
        self,
        host_name: str,
        container_name: str,
        image: str,
        current_digest: str,
        new_digest: str,
    ) -> bool:
        """Notify that a container update is available."""
        return await self.send_notification(
            title="🐳 Container Update Available",
            description=f"A new image is available for container **{container_name}**",
            color=self.COLOR_WARNING,
            fields=[
                {"name": "Host", "value": host_name, "inline": True},
                {"name": "Container", "value": container_name, "inline": True},
                {"name": "Image", "value": image, "inline": False},
                {
                    "name": "Current Digest",
                    "value": f"`{current_digest[:16]}...`",
                    "inline": True,
                },
                {
                    "name": "New Digest",
                    "value": f"`{new_digest[:16]}...`",
                    "inline": True,
                },
            ],
            footer="Update Dashboard",
        )

    async def notify_container_updated(
        self,
        host_name: str,
        container_name: str,
        old_image: str,
        new_image: str,
        success: bool,
        error: Optional[str] = None,
    ) -> bool:
        """Notify that a container was updated (or failed)."""
        if success:
            return await self.send_notification(
                title="✅ Container Updated Successfully",
                description=f"Container **{container_name}** has been updated",
                color=self.COLOR_SUCCESS,
                fields=[
                    {"name": "Host", "value": host_name, "inline": True},
                    {"name": "Container", "value": container_name, "inline": True},
                    {"name": "Old Image", "value": old_image, "inline": False},
                    {"name": "New Image", "value": new_image, "inline": False},
                ],
                footer="Update Dashboard",
            )
        else:
            return await self.send_notification(
                title="❌ Container Update Failed",
                description=f"Failed to update container **{container_name}**",
                color=self.COLOR_ERROR,
                fields=[
                    {"name": "Host", "value": host_name, "inline": True},
                    {"name": "Container", "value": container_name, "inline": True},
                    {"name": "Image", "value": new_image, "inline": False},
                    {
                        "name": "Error",
                        "value": error or "Unknown error",
                        "inline": False,
                    },
                ],
                footer="Update Dashboard",
            )

    async def notify_system_updates_available(
        self,
        host_name: str,
        os_name: str,
        package_count: int,
        packages: Optional[List[str]] = None,
    ) -> bool:
        """Notify that system updates are available."""
        description = f"**{package_count}** package(s) can be upgraded"

        fields = [
            {"name": "Host", "value": host_name, "inline": True},
            {"name": "OS", "value": os_name, "inline": True},
            {"name": "Updates", "value": str(package_count), "inline": True},
        ]

        if packages and len(packages) <= 10:
            fields.append(
                {"name": "Packages", "value": ", ".join(packages), "inline": False}
            )
        elif packages:
            fields.append(
                {
                    "name": "Packages (first 10)",
                    "value": ", ".join(packages[:10])
                    + f" ... and {len(packages) - 10} more",
                    "inline": False,
                }
            )

        return await self.send_notification(
            title="🖥️ System Updates Available",
            description=description,
            color=self.COLOR_WARNING,
            fields=fields,
            footer="Update Dashboard",
        )

    async def notify_system_updated(
        self,
        host_name: str,
        packages_updated: List[str],
        success: bool,
        error: Optional[str] = None,
    ) -> bool:
        """Notify that system updates were applied."""
        if success:
            return await self.send_notification(
                title="✅ System Updated Successfully",
                description=f"**{len(packages_updated)}** package(s) were updated on **{host_name}**",
                color=self.COLOR_SUCCESS,
                fields=[
                    {"name": "Host", "value": host_name, "inline": True},
                    {
                        "name": "Packages Updated",
                        "value": str(len(packages_updated)),
                        "inline": True,
                    },
                ],
                footer="Update Dashboard",
            )
        else:
            return await self.send_notification(
                title="❌ System Update Failed",
                description=f"Failed to update system on **{host_name}**",
                color=self.COLOR_ERROR,
                fields=[
                    {"name": "Host", "value": host_name, "inline": True},
                    {
                        "name": "Error",
                        "value": error or "Unknown error",
                        "inline": False,
                    },
                ],
                footer="Update Dashboard",
            )

    async def notify_container_deleted(
        self,
        host_name: str,
        container_name: str,
        image_id: str,
        removed_items: List[str],
    ) -> bool:
        """Notify that a container was deleted."""
        items_text = (
            "\n".join(f"• {item}" for item in removed_items)
            if removed_items
            else "Container removed"
        )

        return await self.send_notification(
            title="🗑️ Container Deleted",
            description=f"Container **{container_name}** has been removed from **{host_name}**",
            color=self.COLOR_INFO,
            fields=[
                {"name": "Host", "value": host_name, "inline": True},
                {"name": "Container", "value": container_name, "inline": True},
                {"name": "Image ID", "value": f"`{image_id}`", "inline": True},
                {"name": "Actions Performed", "value": items_text, "inline": False},
            ],
            footer="Update Dashboard",
        )


# Helper function for scheduler
async def send_discord_notification(
    title: str, description: str, color: int = 0x0099FF
) -> bool:
    """
    Quick helper to send Discord notifications.

    Args:
        title: Notification title
        description: Notification description
        color: Embed color (hex)

    Returns:
        True if sent successfully
    """
    service = NotificationService()
    return await service.send_notification(title, description, color)
