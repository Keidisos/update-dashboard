"""
Docker Service - Core container management and update logic.

This is the most critical service in the application. It handles:
- Connecting to remote Docker daemons (via SSH tunnel or TCP)
- Listing containers and their configurations
- Updating containers while STRICTLY preserving all configuration
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

import docker
from docker import DockerClient
from docker.models.containers import Container
from docker.errors import DockerException, NotFound, APIError

from app.models.host import Host, ConnectionType
from app.schemas import (
    ContainerInfo, ContainerState, PortMapping, VolumeMount,
    ContainerUpdateResult
)

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """
    Complete container configuration extracted from a running container.
    This class captures ALL settings needed to recreate an identical container.
    """
    # Basic
    name: str
    image: str
    command: Optional[List[str]] = None
    entrypoint: Optional[List[str]] = None
    
    # Environment
    environment: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Networking
    hostname: Optional[str] = None
    domainname: Optional[str] = None
    network_mode: Optional[str] = None
    networks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    ports: Dict[str, Any] = field(default_factory=dict)  # PortBindings format
    extra_hosts: Optional[List[str]] = None
    dns: Optional[List[str]] = None
    dns_search: Optional[List[str]] = None
    mac_address: Optional[str] = None
    
    # Volumes
    volumes: Dict[str, Dict] = field(default_factory=dict)  # Volume config
    mounts: List[Dict[str, Any]] = field(default_factory=list)  # Mount config
    binds: Optional[List[str]] = None
    volumes_from: Optional[List[str]] = None
    
    # Resources
    mem_limit: Optional[int] = None
    memswap_limit: Optional[int] = None
    mem_reservation: Optional[int] = None
    cpu_shares: Optional[int] = None
    cpu_period: Optional[int] = None
    cpu_quota: Optional[int] = None
    cpuset_cpus: Optional[str] = None
    cpuset_mems: Optional[str] = None
    nano_cpus: Optional[int] = None
    
    # Security
    privileged: bool = False
    cap_add: Optional[List[str]] = None
    cap_drop: Optional[List[str]] = None
    security_opt: Optional[List[str]] = None
    user: Optional[str] = None
    group_add: Optional[List[str]] = None
    read_only: bool = False
    
    # Lifecycle
    restart_policy: Dict[str, Any] = field(default_factory=lambda: {"Name": "no"})
    auto_remove: bool = False
    stop_signal: Optional[str] = None
    stop_timeout: Optional[int] = None
    
    # Other
    working_dir: Optional[str] = None
    tty: bool = False
    stdin_open: bool = False
    detach: bool = True
    pid_mode: Optional[str] = None
    ipc_mode: Optional[str] = None
    uts_mode: Optional[str] = None
    userns_mode: Optional[str] = None
    shm_size: Optional[int] = None
    sysctls: Optional[Dict[str, str]] = None
    runtime: Optional[str] = None
    
    # Health check
    healthcheck: Optional[Dict[str, Any]] = None
    
    # Logging
    log_config: Optional[Dict[str, Any]] = None
    
    # Devices
    devices: Optional[List[str]] = None
    device_cgroup_rules: Optional[List[str]] = None
    
    # Ulimits
    ulimits: Optional[List[Dict]] = None
    
    def to_create_kwargs(self) -> Dict[str, Any]:
        """
        Convert configuration to kwargs for docker.containers.create().
        Only includes non-None values.
        """
        kwargs = {
            "name": self.name,
            "image": self.image,
            "detach": self.detach,
        }
        
        # Command and entrypoint
        if self.command:
            kwargs["command"] = self.command
        if self.entrypoint:
            kwargs["entrypoint"] = self.entrypoint
            
        # Environment
        if self.environment:
            kwargs["environment"] = self.environment
        if self.labels:
            kwargs["labels"] = self.labels
            
        # Networking
        if self.hostname:
            kwargs["hostname"] = self.hostname
        if self.domainname:
            kwargs["domainname"] = self.domainname
        if self.network_mode:
            kwargs["network_mode"] = self.network_mode
        if self.ports:
            kwargs["ports"] = self.ports
        if self.extra_hosts:
            kwargs["extra_hosts"] = self.extra_hosts
        if self.dns:
            kwargs["dns"] = self.dns
        if self.dns_search:
            kwargs["dns_search"] = self.dns_search
        if self.mac_address:
            kwargs["mac_address"] = self.mac_address
            
        # Volumes
        if self.volumes:
            kwargs["volumes"] = self.volumes
        if self.mounts:
            kwargs["mounts"] = self.mounts
        if self.volumes_from:
            kwargs["volumes_from"] = self.volumes_from
            
        # Resources
        if self.mem_limit:
            kwargs["mem_limit"] = self.mem_limit
        if self.memswap_limit:
            kwargs["memswap_limit"] = self.memswap_limit
        if self.mem_reservation:
            kwargs["mem_reservation"] = self.mem_reservation
        if self.cpu_shares:
            kwargs["cpu_shares"] = self.cpu_shares
        if self.cpu_period:
            kwargs["cpu_period"] = self.cpu_period
        if self.cpu_quota:
            kwargs["cpu_quota"] = self.cpu_quota
        if self.cpuset_cpus:
            kwargs["cpuset_cpus"] = self.cpuset_cpus
        if self.cpuset_mems:
            kwargs["cpuset_mems"] = self.cpuset_mems
        if self.nano_cpus:
            kwargs["nano_cpus"] = self.nano_cpus
            
        # Security
        if self.privileged:
            kwargs["privileged"] = self.privileged
        if self.cap_add:
            kwargs["cap_add"] = self.cap_add
        if self.cap_drop:
            kwargs["cap_drop"] = self.cap_drop
        if self.security_opt:
            kwargs["security_opt"] = self.security_opt
        if self.user:
            kwargs["user"] = self.user
        if self.group_add:
            kwargs["group_add"] = self.group_add
        if self.read_only:
            kwargs["read_only"] = self.read_only
            
        # Lifecycle
        if self.restart_policy and self.restart_policy.get("Name") != "no":
            kwargs["restart_policy"] = self.restart_policy
        if self.auto_remove:
            kwargs["auto_remove"] = self.auto_remove
        if self.stop_signal:
            kwargs["stop_signal"] = self.stop_signal
        if self.stop_timeout:
            kwargs["stop_timeout"] = self.stop_timeout
            
        # Other
        if self.working_dir:
            kwargs["working_dir"] = self.working_dir
        if self.tty:
            kwargs["tty"] = self.tty
        if self.stdin_open:
            kwargs["stdin_open"] = self.stdin_open
        if self.pid_mode:
            kwargs["pid_mode"] = self.pid_mode
        if self.ipc_mode:
            kwargs["ipc_mode"] = self.ipc_mode
        if self.uts_mode:
            kwargs["uts_mode"] = self.uts_mode
        if self.userns_mode:
            kwargs["userns_mode"] = self.userns_mode
        if self.shm_size:
            kwargs["shm_size"] = self.shm_size
        if self.sysctls:
            kwargs["sysctls"] = self.sysctls
        if self.runtime:
            kwargs["runtime"] = self.runtime
            
        # Health check
        if self.healthcheck:
            kwargs["healthcheck"] = self.healthcheck
            
        # Logging
        if self.log_config:
            kwargs["log_config"] = self.log_config
            
        # Devices
        if self.devices:
            kwargs["devices"] = self.devices
        if self.device_cgroup_rules:
            kwargs["device_cgroup_rules"] = self.device_cgroup_rules
            
        # Ulimits
        if self.ulimits:
            kwargs["ulimits"] = self.ulimits
            
        return kwargs


class DockerService:
    """
    Service for managing Docker containers on remote hosts.
    """
    
    def __init__(
        self, 
        host: Host, 
        ssh_key: Optional[str] = None,
        ssh_password: Optional[str] = None
    ):
        """
        Initialize Docker service for a specific host.
        
        Args:
            host: Host model with connection details
            ssh_key: Decrypted SSH private key (if using SSH connection)
            ssh_password: Decrypted SSH password (if using password auth)
        """
        self.host = host
        self.ssh_key = ssh_key
        self.ssh_password = ssh_password
        self._client: Optional[DockerClient] = None
        
    async def connect(self) -> DockerClient:
        """
        Establish connection to Docker daemon.
        
        Returns:
            DockerClient instance
            
        Raises:
            DockerException: If connection fails
        """
        if self._client is not None:
            return self._client
            
        try:
            if self.host.connection_type == ConnectionType.SSH:
                # Use paramiko directly for SSH to handle custom keys and host verification
                import paramiko
                from io import StringIO
                
                # Create SSH client with auto-add policy (no host key verification)
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                connect_kwargs = {
                    "hostname": self.host.hostname,
                    "port": self.host.ssh_port,
                    "username": self.host.ssh_user,
                    "allow_agent": False,
                    "look_for_keys": False,
                }
                
                if self.ssh_key:
                    # Load private key from string
                    try:
                        # Try RSA first
                        key = paramiko.RSAKey.from_private_key(StringIO(self.ssh_key))
                    except paramiko.SSHException:
                        try:
                            # Try Ed25519
                            key = paramiko.Ed25519Key.from_private_key(StringIO(self.ssh_key))
                        except paramiko.SSHException:
                            try:
                                # Try ECDSA
                                key = paramiko.ECDSAKey.from_private_key(StringIO(self.ssh_key))
                            except paramiko.SSHException:
                                # Try DSS
                                key = paramiko.DSSKey.from_private_key(StringIO(self.ssh_key))
                    connect_kwargs["pkey"] = key
                elif self.ssh_password:
                    connect_kwargs["password"] = self.ssh_password
                
                # Connect via SSH
                ssh_client.connect(**connect_kwargs)
                
                # Create Docker client over SSH transport
                # docker-py uses paramiko transport when provided
                transport = ssh_client.get_transport()
                
                # Use the SSH connection for Docker
                base_url = f"ssh://{self.host.ssh_user}@{self.host.hostname}:{self.host.ssh_port}"
                
                # Store SSH client to keep connection alive
                self._ssh_client = ssh_client
                
                # Create Docker client with custom SSH transport
                # We need to use environment variables for paramiko settings
                import os
                os.environ['DOCKER_HOST'] = base_url
                
                # Create docker client that uses the SSH connection
                self._client = docker.DockerClient(
                    base_url=base_url,
                    use_ssh_client=True,
                    timeout=self.host.docker_timeout if hasattr(self.host, 'docker_timeout') else 120
                )
            else:
                # TCP connection
                protocol = "https" if self.host.docker_tls else "http"
                base_url = f"{protocol}://{self.host.hostname}:{self.host.docker_port}"
                
                tls_config = None
                if self.host.docker_tls:
                    # TLS configuration would go here
                    # tls_config = docker.tls.TLSConfig(...)
                    pass
                    
                self._client = docker.DockerClient(
                    base_url=base_url,
                    tls=tls_config
                )
                
            # Verify connection
            self._client.ping()
            logger.info(f"Connected to Docker on {self.host.name}")
            return self._client
            
        except DockerException as e:
            logger.error(f"Failed to connect to Docker on {self.host.name}: {e}")
            raise
            
    async def disconnect(self):
        """Close Docker client connection."""
        if self._client:
            self._client.close()
            self._client = None
        if hasattr(self, '_ssh_client') and self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None
            
    async def list_containers(self, all: bool = True) -> List[ContainerInfo]:
        """
        List all containers on the host.
        
        Args:
            all: Include stopped containers
            
        Returns:
            List of ContainerInfo objects
        """
        client = await self.connect()
        containers = client.containers.list(all=all)
        
        result = []
        for container in containers:
            info = self._container_to_info(container)
            result.append(info)
            
        return result
        
    async def get_container(self, container_id: str) -> ContainerInfo:
        """Get detailed information about a specific container."""
        client = await self.connect()
        container = client.containers.get(container_id)
        return self._container_to_info(container)
        
    def _container_to_info(self, container: Container) -> ContainerInfo:
        """Convert Docker container to ContainerInfo schema."""
        attrs = container.attrs
        config = attrs.get("Config", {})
        host_config = attrs.get("HostConfig", {})
        network_settings = attrs.get("NetworkSettings", {})
        
        # Parse ports
        ports = []
        port_bindings = host_config.get("PortBindings") or {}
        for container_port, bindings in port_bindings.items():
            port_num, protocol = container_port.split("/")
            if bindings:
                for binding in bindings:
                    ports.append(PortMapping(
                        container_port=int(port_num),
                        host_port=int(binding["HostPort"]) if binding.get("HostPort") else None,
                        protocol=protocol,
                        host_ip=binding.get("HostIp", "0.0.0.0")
                    ))
                    
        # Parse volumes/mounts
        volumes = []
        mounts = attrs.get("Mounts") or []
        for mount in mounts:
            volumes.append(VolumeMount(
                source=mount.get("Source", ""),
                destination=mount.get("Destination", ""),
                mode=mount.get("Mode", "rw"),
                type=mount.get("Type", "bind")
            ))
            
        # Parse environment
        env_dict = {}
        for env in config.get("Env") or []:
            if "=" in env:
                key, value = env.split("=", 1)
                env_dict[key] = value
                
        # Parse networks
        networks = list((network_settings.get("Networks") or {}).keys())
        
        # Get restart policy
        restart = host_config.get("RestartPolicy", {})
        restart_policy = restart.get("Name", "no")
        if restart.get("MaximumRetryCount"):
            restart_policy = f"{restart_policy}:{restart['MaximumRetryCount']}"
            
        # Determine state
        state_str = attrs.get("State", {}).get("Status", "unknown")
        try:
            state = ContainerState(state_str)
        except ValueError:
            state = ContainerState.EXITED
            
        return ContainerInfo(
            id=container.id,
            name=container.name,
            image=config.get("Image", ""),
            image_id=attrs.get("Image", ""),
            state=state,
            status=container.status,
            created=datetime.fromisoformat(attrs.get("Created", "").replace("Z", "+00:00")),
            ports=ports,
            volumes=volumes,
            environment=env_dict,
            networks=networks,
            labels=config.get("Labels") or {},
            restart_policy=restart_policy
        )
        
    def _extract_full_config(self, container: Container) -> ContainerConfig:
        """
        Extract COMPLETE configuration from a running container.
        
        This is the CRITICAL function that ensures we can recreate
        the container exactly as it was.
        
        Args:
            container: Docker container object
            
        Returns:
            ContainerConfig with all settings
        """
        attrs = container.attrs
        config = attrs.get("Config", {})
        host_config = attrs.get("HostConfig", {})
        network_settings = attrs.get("NetworkSettings", {})
        
        # Parse environment to dict
        env_dict = {}
        for env in config.get("Env") or []:
            if "=" in env:
                key, value = env.split("=", 1)
                env_dict[key] = value
                
        # Parse network configuration
        networks = {}
        for net_name, net_config in (network_settings.get("Networks") or {}).items():
            networks[net_name] = {
                "IPAMConfig": net_config.get("IPAMConfig"),
                "Aliases": net_config.get("Aliases"),
            }
            
        # Parse mounts for recreation
        mounts = []
        for mount in attrs.get("Mounts") or []:
            mount_config = {
                "Type": mount.get("Type", "bind"),
                "Source": mount.get("Source", ""),
                "Target": mount.get("Destination", ""),
                "ReadOnly": mount.get("RW") is False,
            }
            if mount.get("Type") == "bind":
                mount_config["Consistency"] = mount.get("Consistency", "default")
            if mount.get("VolumeOptions"):
                mount_config["VolumeOptions"] = mount["VolumeOptions"]
            mounts.append(mount_config)
            
        # Build restart policy dict
        restart = host_config.get("RestartPolicy", {})
        restart_policy = {
            "Name": restart.get("Name", "no"),
        }
        if restart.get("MaximumRetryCount"):
            restart_policy["MaximumRetryCount"] = restart["MaximumRetryCount"]
            
        # Parse ulimits
        ulimits = None
        if host_config.get("Ulimits"):
            ulimits = [
                {"Name": u["Name"], "Soft": u["Soft"], "Hard": u["Hard"]}
                for u in host_config["Ulimits"]
            ]
            
        # Parse log config
        log_config = None
        if host_config.get("LogConfig"):
            log_config = {
                "type": host_config["LogConfig"].get("Type"),
                "config": host_config["LogConfig"].get("Config"),
            }
            
        return ContainerConfig(
            name=container.name,
            image=config.get("Image", ""),
            command=config.get("Cmd"),
            entrypoint=config.get("Entrypoint"),
            environment=env_dict,
            labels=config.get("Labels") or {},
            hostname=config.get("Hostname"),
            domainname=config.get("Domainname"),
            network_mode=host_config.get("NetworkMode"),
            networks=networks,
            ports=host_config.get("PortBindings") or {},
            extra_hosts=host_config.get("ExtraHosts"),
            dns=host_config.get("Dns"),
            dns_search=host_config.get("DnsSearch"),
            mac_address=network_settings.get("MacAddress"),
            volumes=config.get("Volumes") or {},
            mounts=mounts,
            binds=host_config.get("Binds"),
            volumes_from=host_config.get("VolumesFrom"),
            mem_limit=host_config.get("Memory"),
            memswap_limit=host_config.get("MemorySwap"),
            mem_reservation=host_config.get("MemoryReservation"),
            cpu_shares=host_config.get("CpuShares"),
            cpu_period=host_config.get("CpuPeriod"),
            cpu_quota=host_config.get("CpuQuota"),
            cpuset_cpus=host_config.get("CpusetCpus"),
            cpuset_mems=host_config.get("CpusetMems"),
            nano_cpus=host_config.get("NanoCpus"),
            privileged=host_config.get("Privileged", False),
            cap_add=host_config.get("CapAdd"),
            cap_drop=host_config.get("CapDrop"),
            security_opt=host_config.get("SecurityOpt"),
            user=config.get("User"),
            group_add=host_config.get("GroupAdd"),
            read_only=host_config.get("ReadonlyRootfs", False),
            restart_policy=restart_policy,
            auto_remove=host_config.get("AutoRemove", False),
            stop_signal=config.get("StopSignal"),
            stop_timeout=config.get("StopTimeout"),
            working_dir=config.get("WorkingDir"),
            tty=config.get("Tty", False),
            stdin_open=config.get("OpenStdin", False),
            pid_mode=host_config.get("PidMode"),
            ipc_mode=host_config.get("IpcMode"),
            uts_mode=host_config.get("UTSMode"),
            userns_mode=host_config.get("UsernsMode"),
            shm_size=host_config.get("ShmSize"),
            sysctls=host_config.get("Sysctls"),
            runtime=host_config.get("Runtime"),
            healthcheck=config.get("Healthcheck"),
            log_config=log_config,
            devices=host_config.get("Devices"),
            device_cgroup_rules=host_config.get("DeviceCgroupRules"),
            ulimits=ulimits,
        )
        
    async def update_container(
        self,
        container_id: str,
        new_image: Optional[str] = None
    ) -> ContainerUpdateResult:
        """
        Update a container to a new image while preserving ALL configuration.
        
        This is the CORE function of the application. It:
        1. Captures the complete container configuration
        2. Pulls the new image
        3. Stops and renames the old container (for rollback)
        4. Creates a new container with the same config but new image
        5. Reconnects to networks
        6. Starts the new container
        7. Removes the old container on success
        
        Args:
            container_id: ID or name of container to update
            new_image: New image to use (if None, uses same image tag)
            
        Returns:
            ContainerUpdateResult with success/failure details
        """
        logs = []
        client = await self.connect()
        
        try:
            # 1. Get container and extract full config
            logs.append(f"[1/7] Getting container {container_id}...")
            container = client.containers.get(container_id)
            old_container_id = container.id
            config = self._extract_full_config(container)
            old_image = config.image
            
            logs.append(f"    Container: {config.name}")
            logs.append(f"    Current image: {old_image}")
            
            # Determine new image
            if new_image is None:
                new_image = old_image
            config.image = new_image
            
            # 2. Pull new image
            logs.append(f"[2/7] Pulling image {new_image}...")
            try:
                pulled_image = client.images.pull(new_image)
                logs.append(f"    Pulled: {pulled_image.id[:12]}")
            except APIError as e:
                logs.append(f"    Failed to pull image: {e}")
                raise
                
            # 3. Stop the old container
            logs.append(f"[3/7] Stopping container {config.name}...")
            was_running = container.status == "running"
            if was_running:
                container.stop(timeout=30)
                logs.append("    Stopped")
            else:
                logs.append("    Already stopped")
                
            # 4. Rename old container for backup
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config.name}_backup_{timestamp}"
            logs.append(f"[4/7] Renaming to {backup_name}...")
            container.rename(backup_name)
            
            # 5. Create new container with preserved config
            logs.append(f"[5/7] Creating new container {config.name}...")
            
            # Handle network mode vs explicit networks
            create_kwargs = config.to_create_kwargs()
            
            # If using custom networks (not host/bridge/none), 
            # we need to connect after creation
            networks_to_connect = {}
            if config.networks and config.network_mode not in ("host", "none"):
                # Use first network for creation, connect to others after
                first_network = next(iter(config.networks.keys()))
                if first_network not in ("bridge", "host", "none"):
                    create_kwargs["network"] = first_network
                    networks_to_connect = {
                        k: v for k, v in config.networks.items() 
                        if k != first_network
                    }
                    
            new_container = client.containers.create(**create_kwargs)
            logs.append(f"    Created: {new_container.id[:12]}")
            
            # 6. Connect to additional networks
            if networks_to_connect:
                logs.append(f"[6/7] Connecting to {len(networks_to_connect)} additional networks...")
                for net_name, net_config in networks_to_connect.items():
                    try:
                        network = client.networks.get(net_name)
                        network.connect(
                            new_container,
                            aliases=net_config.get("Aliases"),
                            ipv4_address=net_config.get("IPAMConfig", {}).get("IPv4Address") if net_config.get("IPAMConfig") else None,
                        )
                        logs.append(f"    Connected to {net_name}")
                    except Exception as e:
                        logs.append(f"    Warning: Failed to connect to {net_name}: {e}")
            else:
                logs.append("[6/7] No additional networks to connect")
                
            # 7. Start new container (if old was running)
            logs.append("[7/7] Starting new container...")
            if was_running:
                new_container.start()
                logs.append("    Started successfully")
                
                # Verify it's running
                new_container.reload()
                if new_container.status != "running":
                    raise Exception(f"Container failed to start: {new_container.status}")
            else:
                logs.append("    Skipped (original was not running)")
                
            # Success - remove backup container
            logs.append("Cleaning up backup container...")
            try:
                backup_container = client.containers.get(backup_name)
                backup_container.remove(force=True)
                logs.append("    Backup removed")
            except Exception as e:
                logs.append(f"    Warning: Could not remove backup: {e}")
                
            return ContainerUpdateResult(
                success=True,
                container_id=container_id,
                old_container_id=old_container_id,
                new_container_id=new_container.id,
                old_image=old_image,
                new_image=new_image,
                logs=logs
            )
            
        except Exception as e:
            error_msg = str(e)
            logs.append(f"ERROR: {error_msg}")
            
            # Attempt rollback
            logs.append("Attempting rollback...")
            try:
                await self._rollback_update(client, container_id, logs)
            except Exception as rollback_error:
                logs.append(f"Rollback failed: {rollback_error}")
                
            return ContainerUpdateResult(
                success=False,
                container_id=container_id,
                old_container_id=container_id,
                new_container_id=None,
                old_image=old_image if 'old_image' in locals() else "",
                new_image=new_image or "",
                error=error_msg,
                logs=logs
            )
            
    async def _rollback_update(
        self,
        client: DockerClient,
        original_name: str,
        logs: List[str]
    ):
        """
        Attempt to rollback a failed update.
        
        Args:
            client: Docker client
            original_name: Original container name
            logs: Log list to append to
        """
        # Find backup container
        backup_containers = [
            c for c in client.containers.list(all=True)
            if c.name.startswith(f"{original_name}_backup_")
        ]
        
        if not backup_containers:
            logs.append("No backup container found for rollback")
            return
            
        # Use most recent backup
        backup = backup_containers[0]
        logs.append(f"Found backup: {backup.name}")
        
        # Remove failed new container if exists
        try:
            failed_container = client.containers.get(original_name)
            failed_container.remove(force=True)
            logs.append(f"Removed failed container")
        except NotFound:
            pass
            
        # Restore backup
        backup.rename(original_name)
        logs.append(f"Restored backup as {original_name}")
        
        # Start if it should be running
        if backup.attrs.get("State", {}).get("Running"):
            backup.start()
            logs.append("Restarted container")
            
    async def get_image_digest(self, image_name: str) -> Optional[str]:
        """Get the digest of a local image."""
        client = await self.connect()
        try:
            image = client.images.get(image_name)
            # RepoDigests contains the registry digest
            digests = image.attrs.get("RepoDigests", [])
            if digests:
                # Format: repo@sha256:xxx
                return digests[0].split("@")[-1]
            return None
        except NotFound:
            return None
