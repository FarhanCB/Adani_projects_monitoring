import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import (
    analytics,
    auth,
    dashboard,
    developers,
    health,
    incidents,
    logs,
    projects,
    settings as settings_api,
)
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.monitor import update_worker_heartbeat
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("adani.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Adani Website Monitoring & Uptime Analytics Platform...")

    # 1. Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")

    # Auto-seed admin and sample projects if database is empty
    db = SessionLocal()
    try:
        from app.models.user import User
        if db.query(User).count() == 0:
            logger.info("Database is empty. Automatically initializing Admin and sample projects...")
            try:
                import seed_data
                seed_data.seed()
            except Exception as se:
                logger.error(f"Auto-seed error: {se}")
        update_worker_heartbeat(db, meta_info="Service started")
    finally:
        db.close()

    # 3. Start background monitoring scheduler
    start_scheduler()

    yield

    # Shutdown
    logger.info("Stopping background scheduler and shutting down...")
    stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Enterprise Website Monitoring, Incident Tracking, and Uptime Analytics Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(developers.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(incidents.router, prefix=settings.API_V1_STR)
app.include_router(logs.router, prefix=settings.API_V1_STR)
app.include_router(settings_api.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)

# Frontend Dist Path
FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
)

# Mount static assets if build exists
if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API, docs, redoc, openapi.json to pass through if not handled
        if full_path.startswith("api") or full_path in ["docs", "redoc", "openapi.json"]:
            return {"detail": "Not Found"}
        
        # Check if the requested file directly exists in dist (e.g. favicon, vite.svg)
        target_file = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        
        # SPA index fallback
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"app": settings.PROJECT_NAME, "status": "OPERATIONAL", "api_docs": "/docs"}
else:
    @app.get("/")
    def root():
        return {
            "app": settings.PROJECT_NAME,
            "version": "2.0.0",
            "status": "OPERATIONAL",
            "api_docs": "/docs",
            "notice": "Frontend build not found. Run 'npm run build' inside frontend directory."
        }
