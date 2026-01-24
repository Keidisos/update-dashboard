"""
Update Dashboard - FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import get_settings
from app.database import create_db_and_tables
from app.routers import hosts_router, containers_router, system_router, scheduler_router
from app.services.scheduler_service import get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Update Dashboard...")
    await create_db_and_tables()
    logger.info("Database initialized")
    
    # Start auto-update scheduler
    scheduler = get_scheduler()
    scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Update Dashboard...")
    scheduler.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Manage Docker container and system updates on remote hosts",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(hosts_router, prefix=settings.api_v1_prefix)
app.include_router(containers_router, prefix=settings.api_v1_prefix)
app.include_router(system_router, prefix=settings.api_v1_prefix)
app.include_router(scheduler_router, prefix=settings.api_v1_prefix)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


# API info endpoint
@app.get(f"{settings.api_v1_prefix}")
async def api_info():
    """API information."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "endpoints": {
            "hosts": f"{settings.api_v1_prefix}/hosts",
            "containers": f"{settings.api_v1_prefix}/containers",
            "system": f"{settings.api_v1_prefix}/system",
        }
    }


# Serve static files (frontend) if available
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/assets", StaticFiles(directory=static_path / "assets"), name="assets")
    
    @app.get("/")
    async def serve_frontend():
        """Serve frontend index.html."""
        return FileResponse(static_path / "index.html")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA routes."""
        file_path = static_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_path / "index.html")
