from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import check_db_connection, get_db
from app.core.security import get_current_user
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.system import WorkerHeartbeat
from app.models.user import User
from app.schemas.system import SystemHealthResponse

router = APIRouter(prefix="/health", tags=["System Health"])


@router.get("", response_model=SystemHealthResponse)
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 14:
    System Health:
    Monitoring Worker: ONLINE/OFFLINE
    Database: CONNECTED/DISCONNECTED
    Email: AVAILABLE/SIMULATED/ERROR
    Last monitoring cycle, last worker heartbeat, enabled vs total projects.
    """
    # 1. Database check
    db_health = check_db_connection()

    # 2. Worker heartbeat
    worker_status = "OFFLINE"
    last_hb_time = None
    hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_name == "primary-monitor").first()

    now = datetime.now(timezone.utc)
    if hb and hb.last_heartbeat:
        last_hb_time = hb.last_heartbeat
        hb_aware = last_hb_time if last_hb_time.tzinfo else last_hb_time.replace(tzinfo=timezone.utc)
        elapsed = (now - hb_aware).total_seconds()
        # If heartbeat received in last 90 seconds, consider ONLINE
        if elapsed < 90:
            worker_status = "ONLINE"
        else:
            worker_status = "OFFLINE"

    # 3. Last monitoring cycle
    latest_check = db.query(MonitoringResult.timestamp).order_by(MonitoringResult.timestamp.desc()).first()
    last_cycle = latest_check[0] if latest_check else None

    # 4. Email health
    if not settings.SMTP_ENABLED:
        email_status = "SIMULATED"
    else:
        email_status = "AVAILABLE"

    # 5. Project stats
    total_projects = db.query(Project).count()
    enabled_projects = db.query(Project).filter(Project.is_enabled == True).count()
    active_incidents = db.query(Incident).filter(Incident.is_resolved == False).count()

    return SystemHealthResponse(
        monitoring_worker=worker_status,
        database=db_health["status"],
        database_dialect=db_health["url_type"],
        database_latency_ms=db_health["latency_ms"],
        email=email_status,
        last_monitoring_cycle=last_cycle,
        last_worker_heartbeat=last_hb_time,
        enabled_projects_count=enabled_projects,
        total_projects_count=total_projects,
        active_incidents_count=active_incidents
    )
