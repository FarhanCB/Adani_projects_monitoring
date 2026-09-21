from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class MonitoringResult(Base):
    __tablename__ = "monitoring_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # UP, DOWN, WARNING
    http_status = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_type = Column(String(100), nullable=True)  # Timeout, DNS error, Connection error, SSL error, HTTP 4xx, HTTP 5xx, Unexpected redirect, Unknown error
    error_message = Column(Text, nullable=True)
    redirect_url = Column(String(1024), nullable=True)
    ssl_valid = Column(Boolean, nullable=True)
    ssl_days_remaining = Column(Integer, nullable=True)
    ssl_issuer = Column(String(255), nullable=True)

    project = relationship("Project", back_populates="monitoring_results")

    __table_args__ = (
        Index("idx_monitoring_project_time", "project_id", "timestamp"),
        Index("idx_monitoring_status_time", "status", "timestamp"),
    )
