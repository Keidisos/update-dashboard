"""
Ollama Service - AI-powered log analysis using locally running Ollama.
"""

import logging
from typing import Optional, Dict, Any
import json

import ollama

from app.config import get_settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with Ollama AI for security analysis."""
    
    def __init__(self):
        settings = get_settings()
        self.host = settings.ollama_host
        self.model = settings.ollama_model
        self.client = ollama.Client(host=self.host)
    
    async def analyze_auth_logs(self, logs: str, host_name: str) -> Dict[str, Any]:
        """
        Analyze authentication logs for security threats.
        
        Args:
            logs: Raw or parsed authentication logs
            host_name: Name of the host being analyzed
            
        Returns:
            Dict with: severity, threat_type, description, recommendations, mitre_techniques
        """
        prompt = f"""Analyse ces logs d'authentification SSH de l'hôte '{host_name}' et identifie les menaces de sécurité.

LOGS:
{logs}

ANALYSE REQUISE:
1. Détecte les tentatives de brute-force (multiples échecs)
2. Identifie les connexions depuis des IPs inhabituelles
3. Repère les escalades de privilèges suspectes
4. Liste les commandes suspectes exécutées

RETOURNE UN JSON avec:
{{
  "severity": "low|medium|high|critical",
  "threat_type": "brute_force|ssh_intrusion|privilege_escalation|suspicious_command|anomaly|none",
  "title": "Court titre de l'incident (max 100 chars)",
  "description": "Description technique détaillée",
  "recommendations": "Actions de remédiation recommandées",
  "mitre_techniques": ["T1078", "T1110"],
  "source_ips": ["192.168.1.100"],
  "affected_users": ["root", "admin"],
  "event_count": 5
}}

RETOURNE UNIQUEMENT LE JSON, RIEN D'AUTRE."""

        try:
            logger.info(f"Analyzing logs for {host_name} with {self.model}")
            
            response = self.client.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            content = response['message']['content']
            logger.debug(f"Ollama response: {content}")
            
            # Parse JSON response
            # Remove markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(content)
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response as JSON: {e}")
            # Return a default non-threat response
            return {
                "severity": "low",
                "threat_type": "none",
                "title": "Analyse échouée - Format JSON invalide",
                "description": f"Impossible de parser la réponse de l'IA: {str(e)}",
                "recommendations": "Vérifier la configuration d'Ollama",
                "mitre_techniques": [],
                "source_ips": [],
                "affected_users": [],
                "event_count": 0
            }
        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")
            raise
    
    async def check_connection(self) -> bool:
        """Check if Ollama is reachable and the model is available."""
        try:
            models = self.client.list()
            model_names = [m['name'] for m in models['models']]
            
            if self.model in model_names:
                logger.info(f"Ollama connected successfully. Model {self.model} is available.")
                return True
            else:
                logger.warning(f"Ollama connected but model {self.model} not found. Available: {model_names}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama at {self.host}: {e}")
            return False
