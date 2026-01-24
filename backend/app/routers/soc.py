"""
SOC API Routes - Security Operations Center endpoints.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models import Host, SecurityIncident
from app.services.soc_service import SOCService
from app.services.ollama_service import OllamaService
from app.services.correlation_engine import CorrelationEngine
from app.services.discord_service import DiscordService
from app.services.scheduler_service import get_scheduler
from app.config import get_settings
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/soc", tags=["SOC"])


# Pydantic schemas
class IncidentResponse(BaseModel):
    id: int
    host_id: int
    severity: str
    category: str
    title: str
    description: str
    ai_recommendations: Optional[str]
    source_ips: Optional[List[str]]
    affected_users: Optional[List[str]]
    mitre_techniques: Optional[List[str]]
    event_count: int
    resolved: bool
    detected_at: str
    # Phase 2 fields
    correlation_id: Optional[str] = None
    parent_incident_id: Optional[int] = None
    threat_score: float = 0.0
    
    class Config:
        from_attributes = True


class SOCStats(BaseModel):
    total_incidents: int
    unresolved_incidents: int
    critical_incidents: int
    incidents_by_severity: dict
    incidents_by_category: dict


class ResolveIncidentRequest(BaseModel):
    resolution_notes: str


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    host_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List security incidents."""
    soc = SOCService()
    incidents = await soc.get_recent_incidents(
        db=db,
        host_id=host_id,
        limit=limit,
        resolved=resolved
    )
    
    # Convert to response format
    return [
        IncidentResponse(
            id=inc.id,
            host_id=inc.host_id,
            severity=inc.severity.value,
            category=inc.category.value,
            title=inc.title,
            description=inc.description,
            ai_recommendations=inc.ai_recommendations,
            source_ips=inc.source_ips or [],
            affected_users=inc.affected_users or [],
            mitre_techniques=inc.mitre_techniques or [],
            event_count=inc.event_count,
            resolved=inc.resolved,
            detected_at=inc.detected_at.isoformat()
        )
        for inc in incidents
    ]


@router.post("/analyze/{host_id}")
async def analyze_host(
    host_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger SOC analysis for a specific host."""
    # Get host
    result = await db.execute(select(Host).where(Host.id == host_id))
    host = result.scalar_one_or_none()
    
    if not host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host {host_id} not found"
        )
    
    # Run analysis in background
    soc =SOCService()
    background_tasks.add_task(soc.analyze_host, host, db)
    
    return {
        "message": f"SOC analysis started for {host.name}",
        "host_id": host_id
    }


@router.get("/stats", response_model=SOCStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get SOC statistics."""
    # Total incidents
    total = await db.execute(select(func.count(SecurityIncident.id)))
    total_count = total.scalar() or 0
    
    # Unresolved
    unresolved = await db.execute(
        select(func.count(SecurityIncident.id)).where(SecurityIncident.resolved == False)
    )
    unresolved_count = unresolved.scalar() or 0
    
    # Critical
    critical = await db.execute(
        select(func.count(SecurityIncident.id)).where(
            SecurityIncident.severity == "critical",
            SecurityIncident.resolved == False
        )
    )
    critical_count = critical.scalar() or 0
    
    # By severity
    incidents = await db.execute(select(SecurityIncident))
    all_incidents = incidents.scalars().all()
    
    severity_counts = {}
    category_counts = {}
    
    for inc in all_incidents:
        sev = inc.severity.value
        cat = inc.category.value
        
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    return SOCStats(
        total_incidents=total_count,
        unresolved_incidents=unresolved_count,
        critical_incidents=critical_count,
        incidents_by_severity=severity_counts,
        incidents_by_category=category_counts
    )


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    request: ResolveIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Mark an incident as resolved."""
    soc = SOCService()
    incident = await soc.resolve_incident(incident_id, request.resolution_notes, db)
    
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found"
        )
    
    return {"message": f"Incident {incident_id} resolved", "incident_id": incident_id}


@router.get("/health")
async def health_check():
    """Check if Ollama is available."""
    ollama = OllamaService()
    is_connected = await ollama.check_connection()
    
    return {
        "ollama_connected": is_connected,
        "ollama_host": ollama.host,
        "ollama_model": ollama.model
    }


@router.post("/auth")
async def authenticate(password: str):
    """
    Authenticate for SOC access.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict with success status and token
    """
    settings = get_settings()
    
    if password == settings.soc_password:
        # In production, generate a proper JWT token
        # For now, return a simple success token
        return {
            "success": True,
            "token": "authenticated",
            "message": "Authentication successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )


# ====== Phase 2 Endpoints ======

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get SOC scheduler status."""
    scheduler = get_scheduler()
    status = {
        "running": scheduler.is_running,
        "interval_minutes": get_settings().soc_analysis_interval,
        "next_run": None,
        "last_run": None
    }
    
    if scheduler.is_running:
        try:
            soc_job = scheduler.scheduler.get_job('soc_analysis')
            if soc_job:
                status["next_run"] = soc_job.next_run_time.isoformat() if soc_job.next_run_time else None
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
    
    return status


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the SOC scheduler."""
    scheduler = get_scheduler()
    
    if scheduler.is_running:
        return {"message": "Scheduler already running"}
    
    scheduler.start()
    return {"message": "SOC scheduler started"}


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the SOC scheduler."""
    scheduler = get_scheduler()
    
    if not scheduler.is_running:
        return {"message": "Scheduler not running"}
    
    scheduler.stop()
    return {"message": "SOC scheduler stopped"}


@router.get("/correlations")
async def get_correlations(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get correlated incident groups."""
    engine = CorrelationEngine()
    groups = await engine.get_correlated_groups(db, limit=limit)
    
    return {"correlations": groups}


@router.post("/correlations/{correlation_id}/resolve")
async def resolve_correlation(
    correlation_id: str,
    request: ResolveIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resolve all incidents in a correlation group."""
    engine = CorrelationEngine()
    count = await engine.resolve_correlation_group(correlation_id, request.resolution_notes, db)
    
    return {
        "message": f"Resolved {count} incidents in correlation group",
        "correlation_id": correlation_id,
        "incidents_resolved": count
    }


@router.post("/test-discord")
async def test_discord():
    """Test Discord webhook connectivity."""
    discord = DiscordService()
    
    if not discord.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discord webhook URL not configured"
        )
    
    success = await discord.test_webhook()
    
    if success:
        return {"message": "Discord webhook test successful"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Discord webhook test failed"
        )


@router.get("/timeline")
async def get_timeline(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get incident timeline for graphing."""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    result = await db.execute(
        select(SecurityIncident).where(SecurityIncident.detected_at >= cutoff)
    )
    incidents = list(result.scalars().all())
    
    # Group by hour and severity
    timeline = defaultdict(lambda: {"low": 0, "medium": 0, "high": 0, "critical": 0})
    
    for incident in incidents:
        hour = incident.detected_at.replace(minute=0, second=0, microsecond=0)
        hour_str = hour.isoformat()
        timeline[hour_str][incident.severity.value] += 1
    
    # Convert to list format for frontend
    timeline_list = [
        {
            "timestamp": ts,
            "counts": counts
        }
        for ts, counts in sorted(timeline.items())
    ]
    
    return {"timeline": timeline_list}
