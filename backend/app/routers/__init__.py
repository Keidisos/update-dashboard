"""
API Routers package.
"""

from app.routers.hosts import router as hosts_router
from app.routers.containers import router as containers_router
from app.routers.system import router as system_router
from app.routers.scheduler import router as scheduler_router

__all__ = ["hosts_router", "containers_router", "system_router", "scheduler_router"]
