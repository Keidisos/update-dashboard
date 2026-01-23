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
