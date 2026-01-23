"""
Log Parser Service - Parses various system logs for security analysis.
"""

import re
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LogParserService:
    """Service for parsing system and auth logs."""
    
    @staticmethod
    def parse_auth_log(raw_log: str, max_lines: int = 100) -> str:
        """
        Parse auth.log and extract relevant security events.
        
        Args:
            raw_log: Raw auth.log content
            max_lines: Maximum number of lines to include
            
        Returns:
            Formatted log excerpt for analysis
        """
        lines = raw_log.strip().split('\n')
        
        # Filter relevant lines (ssh, sudo, su, login attempts)
        relevant_keywords = [
            'sshd', 'sudo', 'su:', 'Failed', 'Accepted', 'authentication',
            'session opened', 'session closed', 'Invalid user', 'Disconnected'
        ]
        
        filtered_lines = []
        for line in lines[-500:]:  # Last 500 lines only
            if any(keyword in line for keyword in relevant_keywords):
                filtered_lines.append(line)
        
        # Take the most recent max_lines
        recent_lines = filtered_lines[-max_lines:]
        
        return '\n'.join(recent_lines)
    
    @staticmethod
    def extract_failed_logins(auth_log: str) -> List[Dict[str, Any]]:
        """
        Extract failed SSH login attempts from auth.log.
        
        Returns:
            List of dicts with timestamp, user, ip, count
        """
        failed_pattern = r'Failed password for (?:invalid user )?(\S+) from (\S+)'
        
        failed_attempts = {}
        for line in auth_log.split('\n'):
            match = re.search(failed_pattern, line)
            if match:
                user = match.group(1)
                ip = match.group(2)
                key = f"{user}@{ip}"
                
                if key not in failed_attempts:
                    failed_attempts[key] = {
                        'user': user,
                        'ip': ip,
                        'count': 0,
                        'last_seen': line[:15]  # timestamp from log
                    }
                failed_attempts[key]['count'] += 1
        
        return list(failed_attempts.values())
    
    @staticmethod
    def extract_successful_logins(auth_log: str) -> List[Dict[str, Any]]:
        """Extract successful SSH logins from auth.log."""
        success_pattern = r'Accepted \w+ for (\S+) from (\S+)'
        
        logins = []
        for line in auth_log.split('\n'):
            match = re.search(success_pattern, line)
            if match:
                logins.append({
                    'user': match.group(1),
                    'ip': match.group(2),
                    'timestamp': line[:15]
                })
        
        return logins
    
    @staticmethod
    def extract_sudo_commands(auth_log: str) -> List[Dict[str, Any]]:
        """Extract sudo commands from auth.log."""
        sudo_pattern = r'(\S+) : TTY=\S+ ; PWD=\S+ ; USER=(\S+) ; COMMAND=(.+)'
        
        commands = []
        for line in auth_log.split('\n'):
            if 'sudo:' in line:
                match = re.search(sudo_pattern, line)
                if match:
                    commands.append({
                        'user': match.group(1),
                        'target_user': match.group(2),
                        'command': match.group(3),
                        'timestamp': line[:15]
                    })
        
        return commands
