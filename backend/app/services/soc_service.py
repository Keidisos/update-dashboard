"""
SOC Service - Security Operations Center coordinator.
Collects logs, analyzes with Ollama, and creates security incidents.
"""

import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Host, SecurityIncident
from app.models.security_incident import SeverityLevel, IncidentCategory
from app.services.ollama_service import OllamaService
from app.services.log_parser_service import LogParserService
from app.services.ssh_service import SSHService
from app.utils import decrypt_value
from app.config import get_settings

logger = logging.getLogger(__name__)


class SOCService:
    """Main SOC service coordinating security analysis."""
    
    def __init__(self):
        self.ollama = OllamaService()
        self.parser = LogParserService()
    
    async def analyze_host(
        self,
        host: Host,
        db: AsyncSession,
        ssh_password: Optional[str] = None
    ) -> Optional[SecurityIncident]:
        """
        Analyze a host's logs for security threats.
        
        Args:
            host: Host to analyze
            db: Database session
            ssh_password: Decrypted SSH password if applicable
            
        Returns:
            SecurityIncident if threat detected, None otherwise
        """
        try:
            logger.info(f"Starting SOC analysis for host: {host.name}")
            
            # Decrypt SSH credentials if not provided
            if not ssh_password:
                settings = get_settings()
                if host.ssh_password_encrypted:
                    ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key)
                # Could also decrypt ssh_key if needed
                # ssh_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key) if host.ssh_key_encrypted else None
            
            # Step 1: Collect auth.log
            raw_logs = await self._collect_auth_logs(host, ssh_password)
            if not raw_logs:
                logger.warning(f"No logs collected from {host.name}")
                return None
            
            # Step 2: Parse logs
            parsed_logs = self.parser.parse_auth_log(raw_logs, max_lines=100)
            if len(parsed_logs) < 50:  # Too few logs to analyze
                logger.info(f"Insufficient log data from {host.name}")
                return None
            
            # Step 3: Analyze with Ollama
            analysis = await self.ollama.analyze_auth_logs(parsed_logs, host.name)
            
            # Step 4: Create incident if threat detected
            if analysis.get('threat_type') and analysis['threat_type'] != 'none':
                incident = await self._create_incident(host.id, analysis, parsed_logs, db)
                logger.info(f"Created incident {incident.id} for {host.name}")
                return incident
            else:
                logger.info(f"No threats detected on {host.name}")
                return None
                
        except Exception as e:
            logger.error(f"SOC analysis failed for {host.name}: {e}")
            return None
    
    async def _collect_auth_logs(
        self,
        host: Host,
        ssh_password: Optional[str] = None
    ) -> Optional[str]:
        """Collect auth.log from a host via SSH."""
        try:
            ssh_service = SSHService(
                host=host,
                password=ssh_password
            )
            
            await ssh_service.connect()
            
            # Get last 500 lines of auth.log
            cmd = "sudo tail -n 500 /var/log/auth.log 2>/dev/null || tail -n 500 /var/log/secure 2>/dev/null"
            stdout, stderr, exit_code = await ssh_service.execute_command(cmd)
            
            await ssh_service.disconnect()
            
            if exit_code == 0 and stdout:
                return stdout
            else:
                logger.warning(f"Failed to collect logs from {host.name}: {stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Log collection failed for {host.name}: {e}")
            return None
    
    async def _create_incident(
        self,
        host_id: int,
        analysis: dict,
        log_excerpt: str,
        db: AsyncSession
    ) -> SecurityIncident:
        """Create a SecurityIncident from AI analysis."""
        
        # Map threat_type to IncidentCategory
        category_map = {
            'brute_force': IncidentCategory.BRUTE_FORCE,
            'ssh_intrusion': IncidentCategory.SSH_INTRUSION,
            'privilege_escalation': IncidentCategory.PRIVILEGE_ESCALATION,
            'suspicious_command': IncidentCategory.SUSPICIOUS_COMMAND,
            'anomaly': IncidentCategory.ANOMALY,
        }
        
        category = category_map.get(
            analysis.get('threat_type', 'other'),
            IncidentCategory.OTHER
        )
        
        # Map severity string to enum
        severity = SeverityLevel(analysis.get('severity', 'low').lower())
        
        incident = SecurityIncident(
            host_id=host_id,
            severity=severity,
            category=category,
            title=analysis.get('title', 'Incident détecté'),
            description=analysis.get('description', ''),
            ai_analysis=analysis.get('description', ''),
            ai_recommendations=analysis.get('recommendations', ''),
            log_excerpt=log_excerpt[:5000],  # Limit size
            source_ips=analysis.get('source_ips', []),
            affected_users=analysis.get('affected_users', []),
            mitre_techniques=analysis.get('mitre_techniques', []),
            event_count=analysis.get('event_count', 1),
            resolved=False,
            detected_at=datetime.utcnow()
        )
        
        db.add(incident)
        await db.commit()
        await db.refresh(incident)
        
        return incident
    
    async def get_recent_incidents(
        self,
        db: AsyncSession,
        host_id: Optional[int] = None,
        limit: int = 50,
        resolved: Optional[bool] = None
    ) -> List[SecurityIncident]:
        """Get recent security incidents."""
        query = select(SecurityIncident).order_by(SecurityIncident.detected_at.desc())
        
        if host_id is not None:
            query = query.where(SecurityIncident.host_id == host_id)
        
        if resolved is not None:
            query = query.where(SecurityIncident.resolved == resolved)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def resolve_incident(
        self,
        incident_id: int,
        resolution_notes: str,
        db: AsyncSession
    ) -> Optional[SecurityIncident]:
        """Mark an incident as resolved."""
        result = await db.execute(
            select(SecurityIncident).where(SecurityIncident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        
        if incident:
            incident.resolved = True
            incident.resolved_at = datetime.utcnow()
            incident.resolution_notes = resolution_notes
            await db.commit()
            await db.refresh(incident)
        
        return incident
