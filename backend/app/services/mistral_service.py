"""
Mistral AI Service for SOC log analysis.
Cloud-based AI alternative to local Ollama for faster analysis.
"""

import logging
import json
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class MistralService:
    """Service for analyzing security logs using Mistral AI."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.mistral_api_key
        self.model = self.settings.mistral_model
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
    
    async def analyze_auth_logs(self, parsed_logs: str, host_name: str = "unknown") -> dict:
        """
        Analyze authentication logs using Mistral AI.
        
        Args:
            parsed_logs: Pre-parsed log lines as string
            host_name: Name of the host being analyzed
            
        Returns:
            Dict with threat analysis in standardized format
        """
        logger.info(f"Analyzing logs for {host_name} with Mistral AI ({self.model})")
        
        # Build prompt for security analysis
        system_prompt = """You are a cybersecurity expert analyzing server logs for security threats.
Analyze the provided logs and identify potential security incidents.

Focus on:
- Brute force attacks (multiple failed login attempts)
- Successful logins from suspicious IPs
- Privilege escalation attempts
- Unusual commands or patterns

Return ONLY a valid JSON object with this exact structure:
{
    "threat_type": "brute_force|ssh_intrusion|privilege_escalation|suspicious_command|anomaly|none",
    "severity": "low|medium|high|critical",
    "title": "Short incident title",
    "description": "Detailed description of the threat",
    "recommendations": "Security recommendations",
    "source_ips": ["list", "of", "IPs"],
    "affected_users": ["list", "of", "usernames"],
    "mitre_techniques": ["T1110", "T1078"],
    "event_count": 1
}"""

        user_message = f"""Analyze these authentication logs from host '{host_name}':

{parsed_logs[:4000]}

Identify security threats and return JSON analysis."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Extract AI response
                ai_response = result["choices"][0]["message"]["content"]
                logger.debug(f"Mistral AI response: {ai_response}")
                
                # Parse JSON response
                analysis = json.loads(ai_response)
                
                # Validate required fields
                if "threat_type" not in analysis:
                    analysis["threat_type"] = "none"
                if "severity" not in analysis:
                    analysis["severity"] = "low"
                
                logger.info(f"Analysis complete: {analysis.get('threat_type')} - {analysis.get('severity')}")
                return analysis
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API HTTP error: {e.response.status_code} - {e.response.text}")
            return self._default_response()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Mistral response as JSON: {e}")
            return self._default_response()
        except Exception as e:
            logger.error(f"Mistral AI analysis failed: {e}")
            return self._default_response()
    
    async def check_connection(self) -> bool:
        """Check if Mistral AI API is accessible."""
        if not self.api_key:
            logger.error("Mistral API key not configured")
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                logger.info("Mistral AI connection successful")
                return True
        except Exception as e:
            logger.error(f"Mistral AI connection failed: {e}")
            return False
    
    def _default_response(self) -> dict:
        """Return default response when AI analysis fails."""
        return {
            "threat_type": "none",
            "severity": "low",
            "title": "Analysis incomplete",
            "description": "AI analysis failed or timed out",
            "recommendations": "Manual review recommended",
            "source_ips": [],
            "affected_users": [],
            "mitre_techniques": [],
            "event_count": 0
        }
