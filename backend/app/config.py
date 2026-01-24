"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_name: str = "Update Dashboard"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/update_dashboard.db"
    
    # Discord Notifications
    discord_webhook_url: Optional[str] = None
    
    # SSH Defaults
    ssh_key_path: Optional[str] = None
    ssh_timeout: int = 30
    
    # Docker
    docker_timeout: int = 120
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # Auto-update Scheduler
    auto_check_enabled: bool = True
    auto_check_interval_minutes: int = 60
    auto_update_containers: bool = False
    auto_update_system: bool = False
    
    # Discord Notifications
    discord_webhook_url: Optional[str] = None
    discord_enabled: bool = True



@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
