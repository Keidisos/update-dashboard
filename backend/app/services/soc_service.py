"""
SOC Service - Security Operations Center coordinator.
Collects logs, analyzes with AI (Ollama or Mistral), and creates security incidents.
"""

import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Host, SecurityIncident
from app.models.security_incident import SeverityLevel, IncidentCategory
from app.services.ollama_service import OllamaService
from app.services.mistral_service import MistralService
from app.services.log_parser_service import LogParserService
from app.services.ssh_service import SSHService
from app.utils import decrypt_value
from app.config import get_settings

logger = logging.getLogger(__name__)


class SOCService:
    """Main SOC service coordinating security analysis."""
    
    def __init__(self):
        settings = get_settings()
        
        # Select AI provider based on configuration
        if settings.ai_provider == "mistral":
            logger.info("🧠 Using Mistral AI for log analysis")
            self.ai_service = MistralService()
        else:
            logger.info("🧠 Using Ollama for log analysis")
            self.ai_service = OllamaService()
        
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
            
            # Step 3: Analyze with AI (Ollama or Mistral)
            analysis = await self.ai_service.analyze_auth_logs(parsed_logs, host.name)
            
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
            # Decrypt SSH credentials
            settings = get_settings()
            
            # Decrypt SSH key if present
            ssh_key = None
            if host.ssh_key_encrypted:
                ssh_key = decrypt_value(host.ssh_key_encrypted, settings.secret_key)
            
            # Decrypt password if present and not provided
            if not ssh_password and host.ssh_password_encrypted:
                ssh_password = decrypt_value(host.ssh_password_encrypted, settings.secret_key)
            
            ssh_service = SSHService(
                host=host,
                private_key=ssh_key,
                password=ssh_password
            )
            
            await ssh_service.connect()
            
            # Try multiple log locations without sudo first
            # Some systems allow read access to auth.log for certain groups
            cmd = "tail -n 500 /var/log/auth.log 2>/dev/null || tail -n 500 /var/log/secure 2>/dev/null || journalctl -n 500 --no-pager 2>/dev/null | grep -i 'sshd\\|sudo\\|su:' || echo 'NO_LOGS'"
            exit_code, stdout, stderr = await ssh_service.run_command(cmd, sudo=False)
            
            await ssh_service.disconnect()
            
            if exit_code == 0 and stdout and stdout.strip() != 'NO_LOGS':
                return stdout
            else:
                logger.warning(f"Failed to collect logs from {host.name}. Exit code: {exit_code}, stderr: {stderr}")
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
        """Create a SecurityIncident from AI analysis with deduplication."""
        
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
        source_ips = analysis.get('source_ips', [])
        
        # ===== DÉDUPLICATION =====
        # Vérifier si un incident similaire existe dans les dernières 24h
        from datetime import timedelta
        from sqlalchemy import and_
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Chercher incidents existants avec même hôte + catégorie dans les 24h
        if source_ips:
            existing_query = select(SecurityIncident).where(
                and_(
                    SecurityIncident.host_id == host_id,
                    SecurityIncident.category == category,
                    SecurityIncident.detected_at >= cutoff_time,
                    SecurityIncident.resolved == False
                )
            )
            
            result = await db.execute(existing_query)
            existing_incidents = list(result.scalars().all())
            
            # Chercher si une IP source correspond
            for existing in existing_incidents:
                existing_ips = set(existing.source_ips or [])
                new_ips = set(source_ips)
                
                # Si intersection non vide → même attaque
                if existing_ips & new_ips:
                    # MISE À JOUR de l'incident existant
                    existing.event_count += analysis.get('event_count', 1)
                    existing.updated_at = datetime.utcnow()
                    
                    # Mettre à jour la sévérité si plus grave
                    if self._severity_weight(severity) > self._severity_weight(existing.severity):
                        existing.severity = severity
                        logger.info(f"⬆️ Incident #{existing.id} upgraded to {severity.value}")
                    
                    await db.commit()
                    await db.refresh(existing)
                    
                    logger.info(
                        f"✅ Incident dédupliqué #{existing.id} "
                        f"(event_count: {existing.event_count}, IPs: {list(existing_ips & new_ips)})"
                    )
                    
                    # NE PAS notifier Discord pour déduplication
                    return existing
        
        # ===== NOUVEL INCIDENT =====
        incident = SecurityIncident(
            host_id=host_id,
            severity=severity,
            category=category,
            title=analysis.get('title', 'Incident détecté'),
            description=analysis.get('description', ''),
            ai_analysis=analysis.get('description', ''),
            ai_recommendations=analysis.get('recommendations', ''),
            log_excerpt=log_excerpt[:5000],  # Limit size
            source_ips=source_ips,
            affected_users=analysis.get('affected_users', []),
            mitre_techniques=analysis.get('mitre_techniques', []),
            event_count=analysis.get('event_count', 1),
            resolved=False,
            detected_at=datetime.utcnow()
        )
        
        db.add(incident)
        await db.commit()
        await db.refresh(incident)
        
        logger.info(f"🆕 Nouvel incident #{incident.id} créé (Severity: {severity.value})")
        
        # Phase 2: Correlation and Discord integration (SEULEMENT pour nouveaux incidents)
        try:
            # Import services here to avoid circular imports
            from app.services.correlation_engine import CorrelationEngine
            from app.services.discord_service import DiscordService
            
            # Correlate with recent incidents
            correlation_engine = CorrelationEngine()
            correlation_id = await correlation_engine.correlate_incidents(incident, db)
            
            if correlation_id:
                logger.info(f"Incident {incident.id} correlated with group {correlation_id}")
            
            # Send Discord notification
            discord_service = DiscordService()
            
            # Get host name for notification
            from app.models import Host
            host_result = await db.execute(select(Host).where(Host.id == host_id))
            host = host_result.scalar_one_or_none()
            host_name = host.name if host else "Unknown"
            
            if discord_service.should_notify(incident):
                await discord_service.send_incident_alert(incident, host_name)
                logger.info(f"Discord alert sent for incident {incident.id}")
            
        except Exception as e:
            logger.error(f"Failed to correlate/notify incident: {e}")
            # Don't fail the whole incident creation if correlation/notification fails
        
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
    
    def _severity_weight(self, severity: SeverityLevel) -> int:
        """Get numeric weight for severity comparison."""
        weights = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4,
        }
        return weights.get(severity, 0)
    
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
