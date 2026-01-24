"""
Scheduler API routes for managing automatic updates.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.scheduler_service import get_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


class SchedulerStatus(BaseModel):
    """Scheduler status response."""

    is_running: bool
    last_run: str | None
    next_run: str | None


class SchedulerRunResponse(BaseModel):
    """Response for manual run."""

    message: str
    status: str


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    """Get the current status of the auto-update scheduler."""
    scheduler = get_scheduler()

    return SchedulerStatus(
        is_running=scheduler.is_running,
        last_run=scheduler.last_run.isoformat() if scheduler.last_run else None,
        next_run=scheduler.next_run.isoformat() if scheduler.next_run else None,
    )


@router.post("/run-now", response_model=SchedulerRunResponse)
async def trigger_manual_run():
    """Manually trigger an update check (bypasses the schedule)."""
    scheduler = get_scheduler()

    if not scheduler.is_running:
        return SchedulerRunResponse(
            message="Scheduler is not running", status="disabled"
        )

    await scheduler.run_now()

    return SchedulerRunResponse(
        message="Manual update check completed", status="success"
    )
