from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCard
from app.services.uptime import calculate_project_uptime, format_duration, parse_date_range

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 7:
    Dashboard cards: Total Projects, UP, DOWN, WARNING, Total Incidents, Total Downtime.
    Project cards with current status, response time, last checked, uptime %, developer count, incident count.
    """
    projects = db.query(Project).order_by(Project.name).all()

    # Date range for uptime calculations: last 30 days
    start_30d, end_30d, _ = parse_date_range("last_30_days")

    total_projects = len(projects)
    up_count = 0
    down_count = 0
    warning_count = 0
    total_downtime_seconds_all = 0
    total_incidents_all = 0

    project_cards: List[ProjectCard] = []

    for p in projects:
        # Latest check result
        latest = (
            db.query(MonitoringResult)
            .filter(MonitoringResult.project_id == p.id)
            .order_by(MonitoringResult.timestamp.desc())
            .first()
        )

        if not p.is_enabled:
            current_status = "PAUSED"
        elif not latest:
            current_status = "PENDING"
        else:
            current_status = latest.status.upper()

        if current_status == "UP":
            up_count += 1
        elif current_status == "DOWN":
            down_count += 1
        elif current_status == "WARNING":
            warning_count += 1

        # Calculate accurate uptime % using actual downtime
        stats = calculate_project_uptime(db, p.id, start_30d, end_30d)
        total_downtime_seconds_all += stats["total_downtime_seconds"]
        total_incidents_all += stats["incident_count"]

        project_cards.append(ProjectCard(
            id=p.id,
            name=p.name,
            description=p.description,
            url=p.url,
            is_enabled=p.is_enabled,
            interval_seconds=p.interval_seconds,
            timeout_seconds=p.timeout_seconds,
            current_status=current_status,
            http_status=latest.http_status if latest else None,
            response_time_ms=latest.response_time_ms if latest else None,
            last_checked=latest.timestamp if latest else None,
            uptime_percentage=stats["uptime_pct"],
            developer_count=len(p.developers),
            incident_count=stats["incident_count"],
            ssl_valid=latest.ssl_valid if latest else None,
            ssl_days_remaining=latest.ssl_days_remaining if latest else None
        ))

    return {
        "metrics": {
            "total_projects": total_projects,
            "up_count": up_count,
            "down_count": down_count,
            "warning_count": warning_count,
            "total_incidents": total_incidents_all,
            "total_downtime_seconds": total_downtime_seconds_all,
            "total_downtime_formatted": format_duration(total_downtime_seconds_all),
        },
        "projects": project_cards
    }
