from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class HeatmapBlock(BaseModel):
    timestamp: datetime
    label: str
    status: str  # UP, DOWN, WARNING, NO_DATA
    response_time_ms: Optional[float] = None
    http_status: Optional[int] = None
    error_type: Optional[str] = None


class ChartPoint(BaseModel):
    timestamp: datetime
    label: str
    response_time_ms: Optional[float] = None
    uptime_pct: Optional[float] = None
    incident_count: Optional[int] = None


class ErrorStat(BaseModel):
    error_type: str
    count: int
    percentage: float


class ProjectAnalytics(BaseModel):
    project_id: int
    project_name: str
    range_start: datetime
    range_end: datetime
    range_label: str
    uptime_pct: float
    downtime_pct: float
    total_uptime_seconds: int
    total_downtime_seconds: int
    total_uptime_formatted: str
    total_downtime_formatted: str
    incident_count: int
    avg_incident_duration_seconds: int
    avg_incident_duration_formatted: str
    longest_incident_seconds: int
    longest_incident_formatted: str
    avg_response_time_ms: float
    max_response_time_ms: float
    successful_checks: int
    failed_checks: int
    warning_checks: int
    total_checks: int
    heatmap_blocks: List[HeatmapBlock] = []
    response_time_chart: List[ChartPoint] = []
    error_distribution: List[ErrorStat] = []


class ProjectComparison(BaseModel):
    project_id: int
    project_name: str
    uptime_pct: float
    downtime_seconds: int
    downtime_formatted: str
    incident_count: int
    avg_response_time_ms: float


class GlobalAnalytics(BaseModel):
    range_start: datetime
    range_end: datetime
    range_label: str
    overall_uptime_pct: float
    total_downtime_seconds: int
    total_downtime_formatted: str
    total_incidents: int
    avg_response_time_ms: float
    total_errors: int
    total_projects: int
    project_comparisons: List[ProjectComparison] = []
    error_distribution: List[ErrorStat] = []
    response_time_trends: List[dict] = []
