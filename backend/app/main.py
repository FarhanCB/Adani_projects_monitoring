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


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": "2.0.0",
        "status": "OPERATIONAL",
        "api_docs": "/docs"
    }
