from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class SystemHealthResponse(BaseModel):
    monitoring_worker: str  # ONLINE, OFFLINE
    database: str  # CONNECTED, DISCONNECTED
    database_dialect: str
    database_latency_ms: float
    email: str  # AVAILABLE, SIMULATED, ERROR
    last_monitoring_cycle: Optional[datetime] = None
    last_worker_heartbeat: Optional[datetime] = None
    enabled_projects_count: int
    total_projects_count: int
    active_incidents_count: int


class EmailSettingsUpdate(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_from_email: EmailStr
    smtp_user: Optional[str] = ""
    smtp_password: Optional[str] = ""
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    smtp_enabled: bool = False


class DailyReportSettingsUpdate(BaseModel):
    daily_report_time: str  # e.g. "20:11"
    daily_report_timezone: str = "Asia/Kolkata"
    daily_report_recipients: str  # comma separated emails
    daily_report_enabled: bool = True


class MonitoringSettingsUpdate(BaseModel):
    default_interval_seconds: int = 3600
    default_timeout_seconds: int = 10
    warning_response_time_ms: int = 2000
    ssl_warning_days: int = 14


class TestEmailRequest(BaseModel):
    recipient: EmailStr


class ManualReportRequest(BaseModel):
    recipients: Optional[str] = None
