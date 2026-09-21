from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.incident import Incident
from app.models.project import Project
from app.models.user import User
from app.schemas.incident import IncidentResponse
from app.services.uptime import format_duration

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    project_id: Optional[int] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    error_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 4 & 10: List incidents with filtering."""
    query = db.query(Incident).join(Project, Incident.project_id == Project.id)

    # All users can view all incidents

    if project_id is not None:
        query = query.filter(Incident.project_id == project_id)
    if is_resolved is not None:
        query = query.filter(Incident.is_resolved == is_resolved)
    if error_type:
        query = query.filter(Incident.error_type == error_type)

    incidents = query.order_by(Incident.started_at.desc()).limit(limit).all()

    now = datetime.now(timezone.utc)
    results = []
    for inc in incidents:
        # If still active, compute current live duration
        if not inc.is_resolved:
            s = inc.started_at if inc.started_at.tzinfo else inc.started_at.replace(tzinfo=timezone.utc)
            duration_sec = int((now - s).total_seconds())
        else:
            duration_sec = inc.duration_seconds or 0

        results.append(IncidentResponse(
            id=inc.id,
            project_id=inc.project_id,
            project_name=inc.project.name if inc.project else f"Project #{inc.project_id}",
            started_at=inc.started_at,
            resolved_at=inc.resolved_at,
            duration_seconds=duration_sec,
            duration_formatted=format_duration(duration_sec),
            error_type=inc.error_type,
            http_status=inc.http_status,
            error_message=inc.error_message,
            is_resolved=inc.is_resolved
        ))

    return results
