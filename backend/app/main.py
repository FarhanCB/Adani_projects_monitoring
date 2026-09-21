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


import os
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import HTTPException

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    description="Enterprise Website Monitoring, Incident Tracking, and Uptime Analytics Platform",
    lifespan=lifespan,
    docs_url="/dashboard/docs",
    redoc_url="/dashboard/redoc",
    openapi_url="/dashboard/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /dashboard/api (primary) and /api (alias)
api_routers = [
    auth.router,
    projects.router,
    developers.router,
    dashboard.router,
    analytics.router,
    incidents.router,
    logs.router,
    settings_api.router,
    health.router,
]

for router in api_routers:
    app.include_router(router, prefix=settings.API_V1_STR)
    if settings.API_V1_STR != "/api":
        app.include_router(router, prefix="/api")

# Frontend Dist Path
FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
)

# Mount static assets under /dashboard/assets (and /assets as fallback)
if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/dashboard/assets", StaticFiles(directory=assets_dir), name="dashboard-assets")
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/dashboard")
    @app.get("/dashboard/")
    @app.get("/dashboard/{full_path:path}")
    async def serve_dashboard_spa(full_path: str = ""):
        clean_path = full_path.strip("/")
        # If unhandled API or docs call reached here, return 404
        if clean_path.startswith("api") or clean_path in ["docs", "redoc", "openapi.json"]:
            raise HTTPException(status_code=404, detail="Endpoint not found")

        # Check if the requested file directly exists in dist (e.g. favicon, vite.svg)
        target_file = os.path.join(FRONTEND_DIST, clean_path)
        if clean_path and os.path.isfile(target_file):
            return FileResponse(target_file)

        # Fallback to SPA index.html
        index_file = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"app": settings.PROJECT_NAME, "status": "OPERATIONAL", "api_docs": "/dashboard/docs"}

# Redirect root and docs to /dashboard endpoints
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dashboard/", status_code=307)

@app.get("/docs")
def docs_redirect():
    return RedirectResponse(url="/dashboard/docs", status_code=307)

@app.get("/redoc")
def redoc_redirect():
    return RedirectResponse(url="/dashboard/redoc", status_code=307)

# Catch-all redirect for paths accessed without /dashboard prefix
@app.get("/{full_path:path}")
async def catch_all_redirect(full_path: str):
    clean = full_path.strip("/")
    if clean.startswith("api") or clean in ["docs", "redoc", "openapi.json"]:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return RedirectResponse(url=f"/dashboard/{clean}", status_code=307)
