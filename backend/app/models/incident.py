from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True, index=True)
    duration_seconds = Column(Integer, nullable=True)  # Populated once resolved or computed on the fly
    error_type = Column(String(100), nullable=False)
    http_status = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)

    project = relationship("Project", back_populates="incidents")
    alerts = relationship("Alert", back_populates="incident")

    __table_args__ = (
        Index("idx_incident_project_resolved", "project_id", "is_resolved"),
        Index("idx_incident_time_window", "started_at", "resolved_at"),
    )
