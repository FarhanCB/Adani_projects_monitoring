from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds into human-readable duration: e.g., '2d 4h 12m' or '32m' or '45s'."""
    if seconds is None or seconds <= 0:
        return "0m"
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or (days == 0 and hours == 0 and secs == 0):
        parts.append(f"{minutes}m")
    if days == 0 and hours == 0 and minutes == 0 and secs > 0:
        parts.append(f"{secs}s")
    return " ".join(parts)


def parse_date_range(
    range_preset: str = "last_30_days",
    custom_start: Optional[datetime] = None,
    custom_end: Optional[datetime] = None
) -> Tuple[datetime, datetime, str]:
    """Resolve range preset or custom dates into (start_datetime, end_datetime, label).
    All dates are returned in UTC.
    """
    now = get_utc_now()

    if range_preset == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now, "Today"
    elif range_preset == "this_week":
        # Monday of current week
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now, "This Week"
    elif range_preset == "last_7_days":
        start = now - timedelta(days=7)
        return start, now, "Last 7 Days"
    elif range_preset == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start, now, "This Month"
    elif range_preset == "last_30_days":
        start = now - timedelta(days=30)
        return start, now, "Last 30 Days"
    elif range_preset == "last_90_days":
        start = now - timedelta(days=90)
        return start, now, "Last 90 Days"
    elif range_preset == "custom" and custom_start and custom_end:
        start = custom_start if custom_start.tzinfo else custom_start.replace(tzinfo=timezone.utc)
        end = custom_end if custom_end.tzinfo else custom_end.replace(tzinfo=timezone.utc)
        return start, end, f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"
    else:
        # Default fallback
        start = now - timedelta(days=30)
        return start, now, "Last 30 Days"


def calculate_project_uptime(
    db: Session,
    project_id: int,
    range_start: datetime,
    range_end: datetime
) -> dict:
    """Requirement 9:
    Calculate uptime using actual downtime / incident duration, NOT simply successful_checks / total_checks.
    If an incident overlaps the selected date range, only count the portion inside that date range.
    Example:
      Incident: Yesterday 11:50 PM -> Today 12:20 AM
      For today's analytics count only: 12:00 AM -> 12:20 AM (20 minutes).
    """
    now = get_utc_now()
    effective_end = min(range_end, now)
    if effective_end <= range_start:
        effective_end = range_start + timedelta(seconds=1)

    total_window_seconds = max(1, int((effective_end - range_start).total_seconds()))

    # Ensure tz awareness or comparability
    def make_aware(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    r_start_aware = make_aware(range_start)
    r_end_aware = make_aware(effective_end)

    # Fetch incidents that intersect with [range_start, effective_end]
    # Incident starts before window end, and resolves after window start (or is currently unresolved)
    incidents = (
        db.query(Incident)
        .filter(
            Incident.project_id == project_id,
            Incident.started_at <= effective_end,
            (Incident.resolved_at == None) | (Incident.resolved_at >= range_start)
        )
        .all()
    )

    # Collect overlapping downtime intervals: list of (start, end)
    intervals: List[Tuple[datetime, datetime]] = []
    for inc in incidents:
        inc_start = make_aware(inc.started_at)
        inc_end = make_aware(inc.resolved_at) or r_end_aware

        # Clip to date range
        clipped_start = max(inc_start, r_start_aware)
        clipped_end = min(inc_end, r_end_aware)

        if clipped_end > clipped_start:
            intervals.append((clipped_start, clipped_end))

    # Merge overlapping intervals in case multiple incident records overlapped
    merged_intervals = []
    if intervals:
        intervals.sort(key=lambda x: x[0])
        curr_start, curr_end = intervals[0]
        for next_start, next_end in intervals[1:]:
            if next_start <= curr_end:
                curr_end = max(curr_end, next_end)
            else:
                merged_intervals.append((curr_start, curr_end))
                curr_start, curr_end = next_start, next_end
        merged_intervals.append((curr_start, curr_end))

    # Query actual real monitoring checks inside the time window
    checks = (
        db.query(MonitoringResult)
        .filter(
            MonitoringResult.project_id == project_id,
            MonitoringResult.timestamp >= range_start,
            MonitoringResult.timestamp <= effective_end
        )
        .all()
    )

    total_checks = len(checks)
    if total_checks > 0:
        successful_checks = sum(1 for c in checks if c.status in ("UP", "WARNING"))
        uptime_pct = round((successful_checks / total_checks) * 100.0, 2)
        downtime_pct = round(100.0 - uptime_pct, 2)
        total_downtime_seconds = sum(
            int((end - start).total_seconds()) for start, end in merged_intervals
        )
        if total_downtime_seconds == 0 and uptime_pct < 100.0:
            failed_count = total_checks - successful_checks
            total_downtime_seconds = failed_count * 1800
        total_uptime_seconds = max(0, total_window_seconds - total_downtime_seconds)
    else:
        # If no checks have been performed yet
        uptime_pct = 100.0
        downtime_pct = 0.0
        total_downtime_seconds = 0
        total_uptime_seconds = total_window_seconds

    # Incident stats inside window
    incident_count = len(incidents)
    durations = [
        int(((make_aware(i.resolved_at) or r_end_aware) - make_aware(i.started_at)).total_seconds())
        for i in incidents
    ]
    avg_duration_sec = int(sum(durations) / incident_count) if incident_count > 0 else 0
    longest_incident_sec = max(durations) if durations else 0

    return {
        "range_start": range_start,
        "range_end": range_end,
        "total_window_seconds": total_window_seconds,
        "total_uptime_seconds": total_uptime_seconds,
        "total_downtime_seconds": total_downtime_seconds,
        "uptime_pct": uptime_pct,
        "downtime_pct": downtime_pct,
        "total_uptime_formatted": format_duration(total_uptime_seconds),
        "total_downtime_formatted": format_duration(total_downtime_seconds),
        "incident_count": incident_count,
        "avg_incident_duration_seconds": avg_duration_sec,
        "avg_incident_duration_formatted": format_duration(avg_duration_sec),
        "longest_incident_seconds": longest_incident_sec,
        "longest_incident_formatted": format_duration(longest_incident_sec),
    }
