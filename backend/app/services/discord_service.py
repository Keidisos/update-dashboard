"""
Discord Notification Service for SOC alerts.
Sends formatted embeds to Discord webhook for critical security incidents.
"""

import logging
from typing import List
from datetime import datetime

import httpx

from app.models.security_incident import SecurityIncident, SeverityLevel
from app.config import get_settings

logger = logging.getLogger(__name__)


class DiscordService:
    """Service for sending Discord notifications."""
    
    # Severity color mapping (Discord embed colors)
    SEVERITY_COLORS = {
        SeverityLevel.CRITICAL: 0xDC143C,  # Crimson Red
        SeverityLevel.HIGH: 0xFF8C00,      # Dark Orange
        SeverityLevel.MEDIUM: 0xFFD700,    # Gold
        SeverityLevel.LOW: 0x808080,       # Gray
    }
    
    def __init__(self):
        self.settings = get_settings()
        self.webhook_url = self.settings.discord_webhook_url
        self.enabled = self.settings.discord_enabled and bool(self.webhook_url)
        
        # Parse notify severities
        if self.settings.discord_notify_severity:
            self.notify_severities = [
                s.strip().upper() 
                for s in self.settings.discord_notify_severity.split(",")
            ]
        else:
            self.notify_severities = ["CRITICAL", "HIGH"]
    
    def should_notify(self, incident: SecurityIncident) -> bool:
        """Check if incident severity warrants notification."""
        if not self.enabled:
            return False
        return incident.severity.value.upper() in self.notify_severities
    
    async def send_incident_alert(self, incident: SecurityIncident, host_name: str = "Unknown") -> bool:
        """
        Send incident alert to Discord.
        
        Args:
            incident: SecurityIncident to report
            host_name: Name of the affected host
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.should_notify(incident):
            logger.debug(f"Skipping Discord notification for {incident.severity.value} incident")
            return False
        
        try:
            embed = self._create_incident_embed(incident, host_name)
            payload = {
                "username": "SOC Alert",
                "embeds": [embed]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                
            logger.info(f"Discord alert sent for incident {incident.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False
    
    def _create_incident_embed(self, incident: SecurityIncident, host_name: str) -> dict:
        """Create Discord embed for incident."""
        color = self.SEVERITY_COLORS.get(incident.severity, 0x808080)
        
        # Build fields
        fields = [
            {
                "name": "🖥️ Host",
                "value": host_name,
                "inline": True
            },
            {
                "name": "⚠️ Severity",
                "value": incident.severity.value.upper(),
                "inline": True
            },
            {
                "name": "📂 Category",
                "value": incident.category.value.replace("_", " ").title(),
                "inline": True
            }
        ]
        
        # Add source IPs if available
        if incident.source_ips:
            ips = incident.source_ips if isinstance(incident.source_ips, list) else []
            if ips:
                fields.append({
                    "name": "🌐 Source IPs",
                    "value": ", ".join(ips[:5]),  # Limit to 5 IPs
                    "inline": False
                })
        
        # Add affected users
        if incident.affected_users:
            users = incident.affected_users if isinstance(incident.affected_users, list) else []
            if users:
                fields.append({
                    "name": "👤 Affected Users",
                    "value": ", ".join(users[:5]),
                    "inline": False
                })
        
        # Add MITRE techniques
        if incident.mitre_techniques:
            techniques = incident.mitre_techniques if isinstance(incident.mitre_techniques, list) else []
            if techniques:
                fields.append({
                    "name": "🎯 MITRE ATT&CK",
                    "value": ", ".join(techniques),
                    "inline": False
                })
        
        # Add threat score if present
        if hasattr(incident, 'threat_score') and incident.threat_score > 0:
            fields.append({
                "name": "📊 Threat Score",
                "value": f"{incident.threat_score:.1f}/100",
                "inline": True
            })
        
        # Add recommendations
        if incident.ai_recommendations:
            fields.append({
                "name": "💡 Recommendations",
                "value": incident.ai_recommendations[:1000],  # Discord limit
                "inline": False
            })
        
        embed = {
            "title": f"🚨 {incident.title}",
            "description": incident.description[:2000],  # Discord limit
            "color": color,
            "fields": fields,
            "timestamp": incident.detected_at.isoformat(),
            "footer": {
                "text": f"Incident ID: {incident.id}"
            }
        }
        
        return embed
    
    async def send_correlation_alert(
        self, 
        incidents: List[SecurityIncident], 
        correlation_id: str,
        threat_score: float
    ) -> bool:
        """
        Send alert for correlated incidents (distributed attack).
        
        Args:
            incidents: List of correlated incidents
            correlation_id: Correlation UUID
            threat_score: Calculated threat score
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            embed = {
                "title": "🔴 DISTRIBUTED ATTACK DETECTED",
                "description": f"**{len(incidents)} correlated incidents** detected across multiple hosts.",
                "color": 0xFF0000,  # Red
                "fields": [
                    {
                        "name": "📊 Threat Score",
                        "value": f"**{threat_score:.1f}/100**",
                        "inline": True
                    },
                    {
                        "name": "🔗 Correlation ID",
                        "value": correlation_id[:8],
                        "inline": True
                    },
                    {
                        "name": "📈 Incident Count",
                        "value": str(len(incidents)),
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "SOC Correlation Engine"
                }
            }
            
            payload = {
                "username": "SOC Alert",
                "content": "@here **CRITICAL: Distributed Attack Pattern Detected**",
                "embeds": [embed]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                
            logger.info(f"Discord correlation alert sent for {correlation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Discord correlation alert: {e}")
            return False
    
    async def test_webhook(self) -> bool:
        """Test Discord webhook connectivity."""
        if not self.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        try:
            payload = {
                "username": "SOC Test",
                "embeds": [{
                    "title": "✅ SOC Discord Integration Test",
                    "description": "Your Discord webhook is configured correctly!",
                    "color": 0x00FF00,
                    "timestamp": datetime.utcnow().isoformat()
                }]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                
            logger.info("Discord webhook test successful")
            return True
            
        except Exception as e:
            logger.error(f"Discord webhook test failed: {e}")
            return False
