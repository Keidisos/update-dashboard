"""
Database configuration and session management.
"""

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Ensure data directory exists (use absolute path)
# In Docker, WORKDIR is /app, so data will be at /app/data
data_dir = Path("/app/data") if os.path.exists("/app") else Path("./data")
try:
    data_dir.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # Directory might already exist with different permissions
    pass

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def create_db_and_tables():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
