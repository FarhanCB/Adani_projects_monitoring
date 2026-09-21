from datetime import datetime, timedelta, timezone
from app.services.uptime import calculate_project_uptime, format_duration


def test_format_duration():
    assert format_duration(30) == "30s"
    assert format_duration(120) == "2m"
    assert format_duration(3660) == "1h 1m"
    assert format_duration(90000) == "1d 1h"
    assert format_duration(0) == "0m"
    assert format_duration(None) == "0m"


def test_overlapping_incident_uptime_logic():
    """Requirement 9 Test:
    Website DOWN: 10:15 AM -> 10:45 AM (30 mins).
    Window: 10:00 AM -> 11:00 AM (60 mins).
    Expected downtime = 30 mins (1800s).
    Expected uptime = 30 mins (1800s) -> 50.0%.

    If Incident started yesterday 11:50 PM -> today 12:20 AM:
    For today's window (12:00 AM -> 01:00 AM):
    Only count 12:00 AM -> 12:20 AM (20 mins = 1200s).
    """
    from unittest.mock import MagicMock
    from app.models.incident import Incident

    mock_db = MagicMock()

    # Window: Today 00:00 to 01:00 (3600 seconds)
    window_start = datetime(2026, 9, 21, 0, 0, 0, tzinfo=timezone.utc)
    window_end = datetime(2026, 9, 21, 1, 0, 0, tzinfo=timezone.utc)

    # Incident: Started Yesterday 23:50, Resolved Today 00:20
    inc = Incident(
        id=1,
        project_id=10,
        started_at=datetime(2026, 9, 20, 23, 50, 0, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 9, 21, 0, 20, 0, tzinfo=timezone.utc),
        duration_seconds=1800,
        error_type="HTTP 500",
        is_resolved=True
    )

    mock_db.query.return_value.filter.return_value.all.return_value = [inc]

    result = calculate_project_uptime(mock_db, 10, window_start, window_end)

    # Overlapping window is 00:00 to 00:20 = 20 minutes = 1200 seconds
    assert result["total_downtime_seconds"] == 1200
    assert result["total_uptime_seconds"] == 2400
    assert result["uptime_pct"] == 66.67
    assert result["downtime_pct"] == 33.33
