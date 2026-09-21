from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.user import DeveloperSummary


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    url: str = Field(..., min_length=8, max_length=1024)
    interval_seconds: int = Field(default=3600, ge=10, le=86400)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    expected_status_codes: str = Field(default="200,201,202,204", max_length=100)
    is_enabled: bool = True


class ProjectCreate(ProjectBase):
    developer_ids: List[int] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    url: Optional[str] = Field(default=None, min_length=8, max_length=1024)
    interval_seconds: Optional[int] = Field(default=None, ge=10, le=86400)
    timeout_seconds: Optional[int] = Field(default=None, ge=1, le=120)
    expected_status_codes: Optional[str] = Field(default=None, max_length=100)
    is_enabled: Optional[bool] = None
    developer_ids: Optional[List[int]] = None


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    developers: List[DeveloperSummary] = []
    developer_count: int = 0

    class Config:
        from_attributes = True


class ProjectCard(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: str
    is_enabled: bool
    interval_seconds: int
    timeout_seconds: int
    current_status: str  # UP, DOWN, WARNING, PAUSED, PENDING
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    last_checked: Optional[datetime] = None
    uptime_percentage: float = 100.0
    developer_count: int = 0
    incident_count: int = 0
    ssl_valid: Optional[bool] = None
    ssl_days_remaining: Optional[int] = None

    class Config:
        from_attributes = True


class ProjectTestResult(BaseModel):
    project_id: Optional[int] = None
    url: str
    status: str  # UP, DOWN, WARNING
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    ssl_valid: Optional[bool] = None
    ssl_days_remaining: Optional[int] = None
    ssl_issuer: Optional[str] = None
    redirect_url: Optional[str] = None
    tested_at: datetime
