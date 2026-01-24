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
    
    # SOC (Security Operations Center)
    soc_enabled: bool = True
    soc_password: str = "admin"  # Default password, should be changed in production
    
    # Mistral AI Configuration
    mistral_api_key: str = ""
    mistral_model: str = "mistral-small-latest"  # Fast and cost-effective
    
    # SOC Phase 2
    soc_analysis_interval: int = 15  # minutes between auto-analysis
    soc_scheduler_enabled: bool = True  # auto-start scheduler on boot
    soc_container_logs_enabled: bool = True  # analyze container logs
    soc_correlation_enabled: bool = True  # enable incident correlation
    soc_correlation_window: int = 60  # minutes for correlation window
    
    # Discord Notifications
    discord_webhook_url: Optional[str] = None
    discord_notify_severity: str = "critical,high"  # severities to notify
    discord_enabled: bool = True



@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
