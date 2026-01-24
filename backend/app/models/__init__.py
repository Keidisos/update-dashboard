"""
Database models package.
"""

from app.models.host import Host
from app.models.update_log import UpdateLog

__all__ = ["Host", "UpdateLog"]
