import csv
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.user import User
from app.schemas.monitoring import MonitoringResultResponse, PaginatedLogsResponse

router = APIRouter(prefix="/logs", tags=["Monitoring Logs"])


@router.get("", response_model=PaginatedLogsResponse)
def get_monitoring_logs(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 11: Server-side paginated monitoring checks history."""
    query = db.query(MonitoringResult).join(Project, MonitoringResult.project_id == Project.id)

    # All users can view all monitoring logs

    if project_id:
        query = query.filter(MonitoringResult.project_id == project_id)
    if status:
        query = query.filter(MonitoringResult.status == status.upper())
    if error_type:
        query = query.filter(MonitoringResult.error_type == error_type)
    if start_date:
        query = query.filter(MonitoringResult.timestamp >= start_date)
    if end_date:
        query = query.filter(MonitoringResult.timestamp <= end_date)

    total = query.count()
    offset = (page - 1) * size
    records = query.order_by(MonitoringResult.timestamp.desc()).offset(offset).limit(size).all()

    items = []
    for r in records:
        # Find matching incident if it was down
        inc_id = None
        if r.status == "DOWN":
            inc = (
                db.query(Incident.id)
                .filter(
                    Incident.project_id == r.project_id,
                    Incident.started_at <= r.timestamp,
                    (Incident.resolved_at == None) | (Incident.resolved_at >= r.timestamp)
                )
                .first()
            )
            if inc:
                inc_id = inc[0]

        items.append(MonitoringResultResponse(
            id=r.id,
            project_id=r.project_id,
            project_name=r.project.name if r.project else f"Project #{r.project_id}",
            timestamp=r.timestamp,
            status=r.status,
            http_status=r.http_status,
            response_time_ms=r.response_time_ms,
            error_type=r.error_type,
            error_message=r.error_message,
            redirect_url=r.redirect_url,
            ssl_valid=r.ssl_valid,
            ssl_days_remaining=r.ssl_days_remaining,
            ssl_issuer=r.ssl_issuer,
            incident_id=inc_id
        ))

    total_pages = (total + size - 1) // size if total > 0 else 1

    return PaginatedLogsResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/export/csv")
def export_logs_csv(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    limit: int = Query(2000, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export monitoring logs as CSV."""
    query = db.query(MonitoringResult).join(Project, MonitoringResult.project_id == Project.id)

    # All users can export monitoring logs

    if project_id:
        query = query.filter(MonitoringResult.project_id == project_id)
    if status:
        query = query.filter(MonitoringResult.status == status.upper())
    if error_type:
        query = query.filter(MonitoringResult.error_type == error_type)

    records = query.order_by(MonitoringResult.timestamp.desc()).limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Timestamp (UTC)",
        "Project Name",
        "Status",
        "HTTP Status",
        "Response Time (ms)",
        "Error Type",
        "Error Message",
        "Redirect URL",
        "SSL Valid",
        "SSL Days Remaining"
    ])

    for r in records:
        writer.writerow([
            r.timestamp.isoformat(),
            r.project.name if r.project else "",
            r.status,
            r.http_status or "",
            f"{r.response_time_ms:.1f}" if r.response_time_ms else "",
            r.error_type or "",
            r.error_message or "",
            r.redirect_url or "",
            r.ssl_valid if r.ssl_valid is not None else "",
            r.ssl_days_remaining if r.ssl_days_remaining is not None else ""
        ])

    csv_content = output.getvalue()
    filename = f"adani_monitoring_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
