"""
SSH Service - Remote host management via SSH.

Handles SSH connections for:
- System update detection and execution
- OS information gathering
"""

import logging
import asyncio
from typing import Optional, List, Tuple
from dataclasses import dataclass
from io import StringIO

import asyncssh
from asyncssh import SSHClientConnection, SSHCompletedProcess

from app.models.host import Host

logger = logging.getLogger(__name__)


@dataclass
class PackageUpdate:
    """Represents an available package update."""
    name: str
    current_version: str
    new_version: str
    repository: Optional[str] = None


@dataclass
class SystemInfo:
    """System information gathered from host."""
    os_id: str  # debian, ubuntu, centos, fedora, etc.
    os_version: str
    os_name: str  # Pretty name
    kernel: str
    

class SSHService:
    """
    Service for SSH-based operations on remote hosts.
    """
    
    def __init__(
        self,
        host: Host,
        private_key: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize SSH service for a host.
        
        Args:
            host: Host model with connection details
            private_key: Decrypted SSH private key content
            password: SSH password (if not using key)
        """
        self.host = host
        self.private_key = private_key
        self.password = password
        self._conn: Optional[SSHClientConnection] = None
        
    async def connect(self) -> SSHClientConnection:
        """
        Establish SSH connection to the host.
        
        Returns:
            SSH connection
        """
        # Check if we have an active connection
        if self._conn is not None:
            try:
                # Test if connection is still alive
                if not getattr(self._conn, '_transport', None) or self._conn._transport.is_closing():
                    self._conn = None
                else:
                    return self._conn
            except Exception:
                self._conn = None
            
        try:
            connect_kwargs = {
                "host": self.host.hostname,
                "port": self.host.ssh_port,
                "username": self.host.ssh_user,
                "known_hosts": None,  # Disable host key checking
            }
            
            if self.private_key:
                # Load key from string
                key = asyncssh.import_private_key(self.private_key)
                connect_kwargs["client_keys"] = [key]
            elif self.password:
                connect_kwargs["password"] = self.password
                
            self._conn = await asyncssh.connect(**connect_kwargs)
            logger.info(f"SSH connected to {self.host.name}")
            return self._conn
            
        except Exception as e:
            logger.error(f"SSH connection failed to {self.host.name}: {e}")
            raise
            
    async def disconnect(self):
        """Close SSH connection."""
        if self._conn:
            self._conn.close()
            try:
                await self._conn.wait_closed()
            except Exception:
                pass
            self._conn = None
            
    async def run_command(
        self,
        command: str,
        sudo: bool = False,
        timeout: int = 300
    ) -> Tuple[int, str, str]:
        """
        Execute a command on the remote host.
        
        Args:
            command: Command to execute
            sudo: Whether to run with sudo
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        conn = await self.connect()
        
        if sudo:
            command = f"sudo {command}"
            
        try:
            result: SSHCompletedProcess = await asyncio.wait_for(
                conn.run(command, check=False),
                timeout=timeout
            )
            return result.returncode or 0, result.stdout or "", result.stderr or ""
        except asyncio.TimeoutError:
            logger.error(f"Command timed out: {command}")
            return -1, "", "Command timed out"
            
    async def get_system_info(self) -> SystemInfo:
        """
        Get operating system information.
        
        Returns:
            SystemInfo object
        """
        # Get OS release info
        code, stdout, _ = await self.run_command("cat /etc/os-release")
        
        os_info = {}
        for line in stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                os_info[key] = value.strip('"')
                
        # Get kernel version
        code, kernel, _ = await self.run_command("uname -r")
        
        return SystemInfo(
            os_id=os_info.get("ID", "unknown"),
            os_version=os_info.get("VERSION_ID", "unknown"),
            os_name=os_info.get("PRETTY_NAME", "Unknown Linux"),
            kernel=kernel.strip()
        )
        
    async def check_updates(self) -> List[PackageUpdate]:
        """
        Check for available system updates.
        
        Returns:
            List of available package updates
        """
        sys_info = await self.get_system_info()
        
        if sys_info.os_id in ("debian", "ubuntu", "linuxmint"):
            return await self._check_apt_updates()
        elif sys_info.os_id in ("centos", "rhel", "fedora", "rocky", "almalinux"):
            return await self._check_yum_updates()
        elif sys_info.os_id == "alpine":
            return await self._check_apk_updates()
        else:
            logger.warning(f"Unsupported OS for update check: {sys_info.os_id}")
            return []
            
    async def _check_apt_updates(self) -> List[PackageUpdate]:
        """Check for updates on Debian/Ubuntu systems."""
        # First update package lists
        await self.run_command("apt-get update", sudo=True, timeout=120)
        
        # Get upgradable packages
        code, stdout, _ = await self.run_command(
            "apt list --upgradable 2>/dev/null | tail -n +2"
        )
        
        updates = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            # Format: package/repo version arch [upgradable from: old_version]
            try:
                parts = line.split()
                name_repo = parts[0]
                name = name_repo.split("/")[0]
                new_version = parts[1]
                
                # Extract old version from [upgradable from: x.x.x]
                old_version = "unknown"
                if "upgradable from:" in line:
                    old_version = line.split("upgradable from:")[1].strip().rstrip("]")
                    
                updates.append(PackageUpdate(
                    name=name,
                    current_version=old_version,
                    new_version=new_version,
                    repository=name_repo.split("/")[1] if "/" in name_repo else None
                ))
            except (IndexError, ValueError) as e:
                logger.warning(f"Failed to parse apt update line: {line}")
                continue
                
        return updates
        
    async def _check_yum_updates(self) -> List[PackageUpdate]:
        """Check for updates on RHEL/CentOS systems."""
        code, stdout, _ = await self.run_command(
            "yum check-update --quiet 2>/dev/null || true"
        )
        
        updates = []
        for line in stdout.strip().split("\n"):
            if not line or line.startswith("Obsoleting"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    name = parts[0].rsplit(".", 1)[0]  # Remove arch
                    new_version = parts[1]
                    updates.append(PackageUpdate(
                        name=name,
                        current_version="installed",
                        new_version=new_version,
                        repository=parts[2] if len(parts) > 2 else None
                    ))
                except (IndexError, ValueError):
                    continue
                    
        return updates
        
    async def _check_apk_updates(self) -> List[PackageUpdate]:
        """Check for updates on Alpine systems."""
        await self.run_command("apk update", sudo=True, timeout=60)
        
        code, stdout, _ = await self.run_command("apk version -l '<'")
        
        updates = []
        for line in stdout.strip().split("\n"):
            if not line or line.startswith("Installed:"):
                continue
            # Format: package-version < new-version
            parts = line.split("<")
            if len(parts) == 2:
                name_version = parts[0].strip()
                new_version = parts[1].strip()
                # Extract name from name-version
                name = "-".join(name_version.rsplit("-", 2)[:-2])
                current = name_version.rsplit("-", 2)[-2]
                updates.append(PackageUpdate(
                    name=name,
                    current_version=current,
                    new_version=new_version
                ))
                
        return updates
        
    async def apply_updates(
        self,
        packages: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """
        Apply system updates.
        
        Args:
            packages: List of specific packages to update, or None for all
            
        Returns:
            Tuple of (success, output_log)
        """
        sys_info = await self.get_system_info()
        
        if sys_info.os_id in ("debian", "ubuntu", "linuxmint"):
            return await self._apply_apt_updates(packages)
        elif sys_info.os_id in ("centos", "rhel", "fedora", "rocky", "almalinux"):
            return await self._apply_yum_updates(packages)
        elif sys_info.os_id == "alpine":
            return await self._apply_apk_updates(packages)
        else:
            return False, f"Unsupported OS: {sys_info.os_id}"
            
    async def _apply_apt_updates(
        self,
        packages: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Apply updates on Debian/Ubuntu."""
        if packages:
            pkg_list = " ".join(packages)
            cmd = f"apt-get install -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' {pkg_list}"
        else:
            cmd = "apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'"
            
        code, stdout, stderr = await self.run_command(cmd, sudo=True, timeout=600)
        
        return code == 0, stdout + stderr
        
    async def _apply_yum_updates(
        self,
        packages: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Apply updates on RHEL/CentOS."""
        if packages:
            pkg_list = " ".join(packages)
            cmd = f"yum update -y {pkg_list}"
        else:
            cmd = "yum update -y"
            
        code, stdout, stderr = await self.run_command(cmd, sudo=True, timeout=600)
        
        return code == 0, stdout + stderr
        
    async def _apply_apk_updates(
        self,
        packages: Optional[List[str]] = None
    ) -> Tuple[bool, str]:
        """Apply updates on Alpine."""
        if packages:
            pkg_list = " ".join(packages)
            cmd = f"apk upgrade {pkg_list}"
        else:
            cmd = "apk upgrade"
            
        code, stdout, stderr = await self.run_command(cmd, sudo=True, timeout=300)
        
        return code == 0, stdout + stderr
