import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.user import User
from app.schemas.analytics import (
    ChartPoint,
    ErrorStat,
    GlobalAnalytics,
    HeatmapBlock,
    ProjectAnalytics,
    ProjectComparison,
)
from app.services.uptime import calculate_project_uptime, format_duration, parse_date_range

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/project/{project_id}", response_model=ProjectAnalytics)
def get_project_analytics(
    project_id: int,
    range_preset: str = Query("last_30_days"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 8 & 10:
    Project detailed analytics with date range filters, timeline heatmap blocks,
    response time trends, error distribution, and incident duration calculations.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # All authenticated users have access to project analytics

    range_start, range_end, range_label = parse_date_range(range_preset, start_date, end_date)

    # 1. Exact uptime / downtime calculation based on incident overlap
    stats = calculate_project_uptime(db, project_id, range_start, range_end)

    # 2. Monitoring checks inside date range
    checks = (
        db.query(MonitoringResult)
        .filter(
            MonitoringResult.project_id == project_id,
            MonitoringResult.timestamp >= range_start,
            MonitoringResult.timestamp <= range_end
        )
        .order_by(MonitoringResult.timestamp.asc())
        .all()
    )

    total_checks = len(checks)
    successful_checks = sum(1 for c in checks if c.status == "UP")
    failed_checks = sum(1 for c in checks if c.status == "DOWN")
    warning_checks = sum(1 for c in checks if c.status == "WARNING")

    # Response time aggregations
    valid_rt = [c.response_time_ms for c in checks if c.response_time_ms is not None]
    avg_rt = round(sum(valid_rt) / len(valid_rt), 1) if valid_rt else 0.0
    max_rt = round(max(valid_rt), 1) if valid_rt else 0.0

    # 3. Response time chart points (grouped into max 50 intervals for clean rendering)
    chart_points: list[ChartPoint] = []
    if checks:
        step = max(1, len(checks) // 40)
        for i in range(0, len(checks), step):
            subset = checks[i : i + step]
            sub_rt = [c.response_time_ms for c in subset if c.response_time_ms is not None]
            avg_sub_rt = round(sum(sub_rt) / len(sub_rt), 1) if sub_rt else None
            mid_check = subset[len(subset) // 2]
            chart_points.append(ChartPoint(
                timestamp=mid_check.timestamp,
                label=mid_check.timestamp.strftime("%d %b %H:%M"),
                response_time_ms=avg_sub_rt,
                incident_count=sum(1 for c in subset if c.status == "DOWN")
            ))

    # 4. Heatmap blocks: 30 to 48 chronological blocks across the window
    num_blocks = 36
    window_delta = (range_end - range_start) / num_blocks
    heatmap_blocks: list[HeatmapBlock] = []

    for b in range(num_blocks):
        b_start = range_start + (window_delta * b)
        b_end = b_start + window_delta
        b_checks = [c for c in checks if b_start <= (c.timestamp if c.timestamp.tzinfo else c.timestamp.replace(tzinfo=timezone.utc)) < b_end]

        if not b_checks:
            block_status = "NO_DATA"
            b_rt = None
            b_http = None
            b_err = None
        else:
            # If any check was DOWN, block is marked DOWN
            if any(c.status == "DOWN" for c in b_checks):
                block_status = "DOWN"
                down_c = next(c for c in b_checks if c.status == "DOWN")
                b_rt = down_c.response_time_ms
                b_http = down_c.http_status
                b_err = down_c.error_type
            elif any(c.status == "WARNING" for c in b_checks):
                block_status = "WARNING"
                warn_c = next(c for c in b_checks if c.status == "WARNING")
                b_rt = warn_c.response_time_ms
                b_http = warn_c.http_status
                b_err = warn_c.error_type
            else:
                block_status = "UP"
                last_c = b_checks[-1]
                b_rt = last_c.response_time_ms
                b_http = last_c.http_status
                b_err = None

        heatmap_blocks.append(HeatmapBlock(
            timestamp=b_start,
            label=b_start.strftime("%d %b %H:%M"),
            status=block_status,
            response_time_ms=b_rt,
            http_status=b_http,
            error_type=b_err
        ))

    # 5. Error distribution
    error_counts = {}
    for c in checks:
        if c.error_type:
            error_counts[c.error_type] = error_counts.get(c.error_type, 0) + 1

    total_errs = sum(error_counts.values())
    error_distribution = [
        ErrorStat(
            error_type=k,
            count=v,
            percentage=round((v / total_errs) * 100, 1) if total_errs > 0 else 0
        )
        for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return ProjectAnalytics(
        project_id=project.id,
        project_name=project.name,
        range_start=range_start,
        range_end=range_end,
        range_label=range_label,
        uptime_pct=stats["uptime_pct"],
        downtime_pct=stats["downtime_pct"],
        total_uptime_seconds=stats["total_uptime_seconds"],
        total_downtime_seconds=stats["total_downtime_seconds"],
        total_uptime_formatted=stats["total_uptime_formatted"],
        total_downtime_formatted=stats["total_downtime_formatted"],
        incident_count=stats["incident_count"],
        avg_incident_duration_seconds=stats["avg_incident_duration_seconds"],
        avg_incident_duration_formatted=stats["avg_incident_duration_formatted"],
        longest_incident_seconds=stats["longest_incident_seconds"],
        longest_incident_formatted=stats["longest_incident_formatted"],
        avg_response_time_ms=avg_rt,
        max_response_time_ms=max_rt,
        successful_checks=successful_checks,
        failed_checks=failed_checks,
        warning_checks=warning_checks,
        total_checks=total_checks,
        heatmap_blocks=heatmap_blocks,
        response_time_chart=chart_points,
        error_distribution=error_distribution
    )


@router.get("/global", response_model=GlobalAnalytics)
def get_global_analytics(
    range_preset: str = Query("last_30_days"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Requirement 12: Global Analytics across all monitored projects."""
    projects = db.query(Project).all()

    range_start, range_end, range_label = parse_date_range(range_preset, start_date, end_date)

    total_projects = len(projects)
    project_comparisons = []
    total_downtime_all = 0
    total_incidents_all = 0
    all_rt_vals = []
    global_error_counts = {}

    for p in projects:
        stats = calculate_project_uptime(db, p.id, range_start, range_end)
        total_downtime_all += stats["total_downtime_seconds"]
        total_incidents_all += stats["incident_count"]

        # Checks for this project
        p_checks = (
            db.query(MonitoringResult)
            .filter(
                MonitoringResult.project_id == p.id,
                MonitoringResult.timestamp >= range_start,
                MonitoringResult.timestamp <= range_end
            )
            .all()
        )
        rts = [c.response_time_ms for c in p_checks if c.response_time_ms is not None]
        avg_p_rt = round(sum(rts) / len(rts), 1) if rts else 0.0
        all_rt_vals.extend(rts)

        for c in p_checks:
            if c.error_type:
                global_error_counts[c.error_type] = global_error_counts.get(c.error_type, 0) + 1

        project_comparisons.append(ProjectComparison(
            project_id=p.id,
            project_name=p.name,
            uptime_pct=stats["uptime_pct"],
            downtime_seconds=stats["total_downtime_seconds"],
            downtime_formatted=stats["total_downtime_formatted"],
            incident_count=stats["incident_count"],
            avg_response_time_ms=avg_p_rt
        ))

    # Overall uptime calculation
    if project_comparisons:
        overall_uptime_pct = round(sum(c.uptime_pct for c in project_comparisons) / len(project_comparisons), 2)
    else:
        overall_uptime_pct = 100.0

    global_avg_rt = round(sum(all_rt_vals) / len(all_rt_vals), 1) if all_rt_vals else 0.0
    total_errs = sum(global_error_counts.values())

    error_distribution = [
        ErrorStat(
            error_type=k,
            count=v,
            percentage=round((v / total_errs) * 100, 1) if total_errs > 0 else 0
        )
        for k, v in sorted(global_error_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    return GlobalAnalytics(
        range_start=range_start,
        range_end=range_end,
        range_label=range_label,
        overall_uptime_pct=overall_uptime_pct,
        total_downtime_seconds=total_downtime_all,
        total_downtime_formatted=format_duration(total_downtime_all),
        total_incidents=total_incidents_all,
        avg_response_time_ms=global_avg_rt,
        total_errors=total_errs,
        total_projects=total_projects,
        project_comparisons=project_comparisons,
        error_distribution=error_distribution,
        response_time_trends=[]
    )


@router.get("/export/csv")
def export_analytics_csv(
    range_preset: str = Query("last_30_days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export global analytics comparison table as CSV."""
    projects = db.query(Project).all()

    range_start, range_end, range_label = parse_date_range(range_preset)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Project ID", "Project Name", "URL", "Range", "Uptime %", "Downtime", "Incidents", "Avg RT (ms)"])

    for p in projects:
        stats = calculate_project_uptime(db, p.id, range_start, range_end)
        checks = (
            db.query(MonitoringResult.response_time_ms)
            .filter(
                MonitoringResult.project_id == p.id,
                MonitoringResult.timestamp >= range_start,
                MonitoringResult.timestamp <= range_end,
                MonitoringResult.response_time_ms != None
            )
            .all()
        )
        rt_vals = [c[0] for c in checks]
        avg_rt = round(sum(rt_vals) / len(rt_vals), 1) if rt_vals else 0.0

        writer.writerow([
            p.id,
            p.name,
            p.url,
            range_label,
            stats["uptime_pct"],
            stats["total_downtime_formatted"],
            stats["incident_count"],
            avg_rt
        ])

    csv_content = output.getvalue()
    filename = f"adani_uptime_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
