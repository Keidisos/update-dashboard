"""
Incident Correlation Engine for SOC.
Detects patterns across multiple incidents and calculates threat scores.
"""

import logging
import uuid
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.security_incident import SecurityIncident, SeverityLevel
from app.config import get_settings

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Engine for correlating security incidents."""
    
    # MITRE ATT&CK technique relationships
    RELATED_TECHNIQUES = {
        "T1078": ["T1110", "T1021"],  # Valid Accounts → Brute Force, Remote Services
        "T1110": ["T1078", "T1021"],  # Brute Force → Valid Accounts, Remote Services
        "T1548": ["T1068", "T1078"],  # Privilege Escalation → Exploit, Valid Accounts
    }
    
    # Severity score weights
    SEVERITY_SCORES = {
        SeverityLevel.LOW: 10,
        SeverityLevel.MEDIUM: 30,
        SeverityLevel.HIGH: 60,
        SeverityLevel.CRITICAL: 100,
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.correlation_window = self.settings.soc_correlation_window  # minutes
        self.enabled = self.settings.soc_correlation_enabled
    
    async def correlate_incidents(
        self,
        new_incident: SecurityIncident,
        db: AsyncSession
    ) -> Optional[str]:
        """
        Correlate a new incident with recent incidents.
        
        Args:
            new_incident: Newly created incident
            db: Database session
            
        Returns:
            Correlation ID if correlated, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            # Get recent incidents within correlation window
            cutoff_time = datetime.utcnow() - timedelta(minutes=self.correlation_window)
            
            query = select(SecurityIncident).where(
                and_(
                    SecurityIncident.id != new_incident.id,
                    SecurityIncident.detected_at >= cutoff_time,
                    SecurityIncident.resolved == False
                )
            )
            
            result = await db.execute(query)
            recent_incidents = list(result.scalars().all())
            
            if not recent_incidents:
                return None
            
            # Find correlated incidents
            correlated = self._find_correlated_incidents(new_incident, recent_incidents)
            
            if not correlated:
                return None
            
            # Check if any already have a correlation_id
            existing_correlation_id = None
            for incident in correlated:
                if incident.correlation_id:
                    existing_correlation_id = incident.correlation_id
                    break
            
            # Use existing or create new correlation ID
            correlation_id = existing_correlation_id or str(uuid.uuid4())
            
            # Update all correlated incidents + new one
            all_incidents = correlated + [new_incident]
            for incident in all_incidents:
                incident.correlation_id = correlation_id
                incident.threat_score = self._calculate_threat_score(all_incidents)
            
            await db.commit()
            
            logger.info(
                f"Correlated incident {new_incident.id} with {len(correlated)} others. "
                f"Correlation ID: {correlation_id}"
            )
            
            return correlation_id
            
        except Exception as e:
            logger.error(f"Correlation failed: {e}")
            return None
    
    def _find_correlated_incidents(
        self,
        new_incident: SecurityIncident,
        recent_incidents: List[SecurityIncident]
    ) -> List[SecurityIncident]:
        """Find incidents that correlate with the new incident."""
        correlated = []
        
        for incident in recent_incidents:
            if self._are_incidents_related(new_incident, incident):
                correlated.append(incident)
        
        return correlated
    
    def _are_incidents_related(
        self,
        incident1: SecurityIncident,
        incident2: SecurityIncident
    ) -> bool:
        """Check if two incidents are related."""
        
        # Same source IP
        if self._have_common_ips(incident1, incident2):
            logger.debug(f"Incidents {incident1.id} and {incident2.id} share source IPs")
            return True
        
        # Same category
        if incident1.category == incident2.category:
            logger.debug(f"Incidents {incident1.id} and {incident2.id} share category")
            return True
        
        # Related MITRE techniques
        if self._have_related_techniques(incident1, incident2):
            logger.debug(f"Incidents {incident1.id} and {incident2.id} have related MITRE techniques")
            return True
        
        # Same affected user
        if self._have_common_users(incident1, incident2):
            logger.debug(f"Incidents {incident1.id} and {incident2.id} share affected users")
            return True
        
        return False
    
    def _have_common_ips(self, inc1: SecurityIncident, inc2: SecurityIncident) -> bool:
        """Check if incidents share source IPs."""
        if not inc1.source_ips or not inc2.source_ips:
            return False
        
        ips1 = set(inc1.source_ips if isinstance(inc1.source_ips, list) else [])
        ips2 = set(inc2.source_ips if isinstance(inc2.source_ips, list) else [])
        
        return bool(ips1 & ips2)
    
    def _have_common_users(self, inc1: SecurityIncident, inc2: SecurityIncident) -> bool:
        """Check if incidents share affected users."""
        if not inc1.affected_users or not inc2.affected_users:
            return False
        
        users1 = set(inc1.affected_users if isinstance(inc1.affected_users, list) else [])
        users2 = set(inc2.affected_users if isinstance(inc2.affected_users, list) else [])
        
        return bool(users1 & users2)
    
    def _have_related_techniques(self, inc1: SecurityIncident, inc2: SecurityIncident) -> bool:
        """Check if incidents have related MITRE techniques."""
        if not inc1.mitre_techniques or not inc2.mitre_techniques:
            return False
        
        techniques1 = set(inc1.mitre_techniques if isinstance(inc1.mitre_techniques, list) else [])
        techniques2 = set(inc2.mitre_techniques if isinstance(inc2.mitre_techniques, list) else [])
        
        # Direct match
        if techniques1 & techniques2:
            return True
        
        # Check related techniques
        for tech1 in techniques1:
            if tech1 in self.RELATED_TECHNIQUES:
                related = set(self.RELATED_TECHNIQUES[tech1])
                if related & techniques2:
                    return True
        
        return False
    
    def _calculate_threat_score(self, incidents: List[SecurityIncident]) -> float:
        """
        Calculate threat score for correlated incidents.
        
        Score based on:
        - Number of incidents
        - Severity levels
        - Number of affected hosts
        - Time distribution
        """
        if not incidents:
            return 0.0
        
        # Base score from severity (weighted average)
        severity_sum = sum(
            self.SEVERITY_SCORES.get(inc.severity, 0) 
            for inc in incidents
        )
        avg_severity = severity_sum / len(incidents)
        
        # Multiplier for incident count (distributed attack)
        count_multiplier = min(1.0 + (len(incidents) - 1) * 0.2, 2.0)
        
        # Multiplier for affected hosts
        unique_hosts = len(set(inc.host_id for inc in incidents))
        host_multiplier = min(1.0 + (unique_hosts - 1) * 0.15, 1.5)
        
        # Final score (0-100)
        score = avg_severity * count_multiplier * host_multiplier
        return min(score, 100.0)
    
    async def get_correlated_groups(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> List[dict]:
        """Get groups of correlated incidents."""
        try:
            # Get all incidents with correlation_id
            query = select(SecurityIncident).where(
                SecurityIncident.correlation_id.isnot(None)
            ).order_by(SecurityIncident.detected_at.desc())
            
            result = await db.execute(query)
            incidents = list(result.scalars().all())
            
            # Group by correlation_id
            groups = defaultdict(list)
            for incident in incidents:
                groups[incident.correlation_id].append(incident)
            
            # Format response
            correlation_groups = []
            for correlation_id, group_incidents in list(groups.items())[:limit]:
                threat_score = self._calculate_threat_score(group_incidents)
                
                correlation_groups.append({
                    "correlation_id": correlation_id,
                    "incident_count": len(group_incidents),
                    "threat_score": threat_score,
                    "incidents": group_incidents,
                    "first_detected": min(inc.detected_at for inc in group_incidents),
                    "last_detected": max(inc.detected_at for inc in group_incidents),
                    "affected_hosts": len(set(inc.host_id for inc in group_incidents)),
                    "max_severity": max(
                        group_incidents, 
                        key=lambda x: self.SEVERITY_SCORES.get(x.severity, 0)
                    ).severity.value
                })
            
            # Sort by threat score
            correlation_groups.sort(key=lambda x: x["threat_score"], reverse=True)
            
            return correlation_groups
            
        except Exception as e:
            logger.error(f"Failed to get correlation groups: {e}")
            return []
    
    async def resolve_correlation_group(
        self,
        correlation_id: str,
        resolution_notes: str,
        db: AsyncSession
    ) -> int:
        """Resolve all incidents in a correlation group."""
        try:
            query = select(SecurityIncident).where(
                SecurityIncident.correlation_id == correlation_id
            )
            
            result = await db.execute(query)
            incidents = list(result.scalars().all())
            
            for incident in incidents:
                incident.resolved = True
                incident.resolved_at = datetime.utcnow()
                incident.resolution_notes = resolution_notes
            
            await db.commit()
            
            logger.info(f"Resolved {len(incidents)} incidents in correlation group {correlation_id}")
            return len(incidents)
            
        except Exception as e:
            logger.error(f"Failed to resolve correlation group: {e}")
            return 0
