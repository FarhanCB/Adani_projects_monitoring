from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MonitoringResultResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    timestamp: datetime
    status: str
    http_status: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    redirect_url: Optional[str] = None
    ssl_valid: Optional[bool] = None
    ssl_days_remaining: Optional[int] = None
    ssl_issuer: Optional[str] = None
    incident_id: Optional[int] = None

    class Config:
        from_attributes = True


class PaginatedLogsResponse(BaseModel):
    items: List[MonitoringResultResponse]
    total: int
    page: int
    size: int
    total_pages: int
