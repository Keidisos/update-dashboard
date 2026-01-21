"""
Registry Service - Compare local and remote image digests.

Handles communication with Docker registries (Docker Hub, private registries)
to check if newer image versions are available.
"""

import logging
import re
import base64
from typing import Optional, Tuple
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ImageReference:
    """Parsed Docker image reference."""
    registry: str
    repository: str
    tag: str
    
    @property
    def full_name(self) -> str:
        if self.registry == "docker.io":
            return f"{self.repository}:{self.tag}"
        return f"{self.registry}/{self.repository}:{self.tag}"


class RegistryService:
    """
    Service for interacting with Docker registries.
    """
    
    # Docker Hub registry endpoints
    DOCKER_HUB_AUTH = "https://auth.docker.io/token"
    DOCKER_HUB_REGISTRY = "https://registry-1.docker.io"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize registry service.
        
        Args:
            username: Registry username (for private repos)
            password: Registry password or token
        """
        self.username = username
        self.password = password
        self._tokens: dict[str, str] = {}
        
    def parse_image_name(self, image: str) -> ImageReference:
        """
        Parse a Docker image name into its components.
        
        Examples:
            - nginx -> docker.io/library/nginx:latest
            - nginx:1.25 -> docker.io/library/nginx:1.25
            - myuser/myapp:v1 -> docker.io/myuser/myapp:v1
            - ghcr.io/owner/repo:tag -> ghcr.io/owner/repo:tag
            
        Args:
            image: Image name string
            
        Returns:
            ImageReference with registry, repository, tag
        """
        # Default values
        registry = "docker.io"
        tag = "latest"
        
        # Check if image contains a tag
        if ":" in image and "@" not in image:
            image, tag = image.rsplit(":", 1)
            
        # Handle digest format (image@sha256:...)
        if "@" in image:
            image = image.split("@")[0]
            
        # Check if first part is a registry
        parts = image.split("/")
        
        if len(parts) == 1:
            # Simple name like "nginx"
            repository = f"library/{parts[0]}"
        elif len(parts) == 2:
            # Could be registry/repo or user/repo
            if "." in parts[0] or ":" in parts[0] or parts[0] == "localhost":
                # It's a registry
                registry = parts[0]
                repository = parts[1]
            else:
                # It's user/repo on Docker Hub
                repository = image
        else:
            # registry/namespace/repo format
            registry = parts[0]
            repository = "/".join(parts[1:])
            
        return ImageReference(registry=registry, repository=repository, tag=tag)
        
    async def get_docker_hub_token(self, repository: str) -> str:
        """
        Get authentication token for Docker Hub.
        
        Args:
            repository: Repository name (e.g., "library/nginx")
            
        Returns:
            Bearer token
        """
        cache_key = f"docker.io/{repository}"
        if cache_key in self._tokens:
            return self._tokens[cache_key]
            
        async with httpx.AsyncClient() as client:
            params = {
                "service": "registry.docker.io",
                "scope": f"repository:{repository}:pull"
            }
            
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)
                
            response = await client.get(
                self.DOCKER_HUB_AUTH,
                params=params,
                auth=auth
            )
            response.raise_for_status()
            
            token = response.json()["token"]
            self._tokens[cache_key] = token
            return token
            
    async def get_remote_digest(self, image: str) -> Optional[str]:
        """
        Get the digest of an image from the remote registry.
        
        Args:
            image: Full image name (e.g., "nginx:latest")
            
        Returns:
            Image digest (sha256:...) or None if not found
        """
        ref = self.parse_image_name(image)
        
        try:
            if ref.registry == "docker.io":
                return await self._get_docker_hub_digest(ref)
            else:
                return await self._get_generic_registry_digest(ref)
        except Exception as e:
            logger.error(f"Failed to get remote digest for {image}: {e}")
            return None
            
    async def _get_docker_hub_digest(self, ref: ImageReference) -> Optional[str]:
        """Get digest from Docker Hub."""
        token = await self.get_docker_hub_token(ref.repository)
        
        async with httpx.AsyncClient() as client:
            # Request manifest with proper Accept header for digest
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": ", ".join([
                    "application/vnd.docker.distribution.manifest.v2+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.oci.image.index.v1+json",
                ])
            }
            
            url = f"{self.DOCKER_HUB_REGISTRY}/v2/{ref.repository}/manifests/{ref.tag}"
            response = await client.head(url, headers=headers)
            
            if response.status_code == 404:
                logger.warning(f"Image not found: {ref.full_name}")
                return None
                
            response.raise_for_status()
            
            # Digest is in the Docker-Content-Digest header
            digest = response.headers.get("Docker-Content-Digest")
            return digest
            
    async def _get_generic_registry_digest(self, ref: ImageReference) -> Optional[str]:
        """Get digest from a generic OCI registry."""
        # Determine protocol (default to https)
        if ref.registry.startswith("localhost") or ref.registry.startswith("127."):
            base_url = f"http://{ref.registry}"
        else:
            base_url = f"https://{ref.registry}"
            
        async with httpx.AsyncClient(verify=False) as client:
            headers = {
                "Accept": ", ".join([
                    "application/vnd.docker.distribution.manifest.v2+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.oci.image.index.v1+json",
                ])
            }
            
            # Add basic auth if credentials provided
            if self.username and self.password:
                credentials = base64.b64encode(
                    f"{self.username}:{self.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
                
            url = f"{base_url}/v2/{ref.repository}/manifests/{ref.tag}"
            response = await client.head(url, headers=headers)
            
            if response.status_code == 401:
                # Try to handle WWW-Authenticate challenge
                # This is a simplified version - full implementation would parse the challenge
                logger.warning(f"Authentication required for {ref.registry}")
                return None
                
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            return response.headers.get("Docker-Content-Digest")
            
    async def check_update_available(
        self,
        image: str,
        local_digest: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an update is available for an image.
        
        Args:
            image: Image name
            local_digest: Local image digest
            
        Returns:
            Tuple of (update_available, remote_digest)
        """
        if not local_digest:
            # Can't compare without local digest
            return False, None
            
        remote_digest = await self.get_remote_digest(image)
        
        if not remote_digest:
            # Couldn't get remote digest
            return False, None
            
        update_available = local_digest != remote_digest
        
        if update_available:
            logger.info(f"Update available for {image}: {local_digest[:16]}... -> {remote_digest[:16]}...")
            
        return update_available, remote_digest
