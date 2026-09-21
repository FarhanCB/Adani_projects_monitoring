from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IncidentResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    started_at: datetime
    resolved_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    duration_formatted: Optional[str] = None
    error_type: str
    http_status: Optional[int] = None
    error_message: Optional[str] = None
    is_resolved: bool

    class Config:
        from_attributes = True
