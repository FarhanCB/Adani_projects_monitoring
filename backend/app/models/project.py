from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# Association table for Project <-> Developer (User)
project_developers = Table(
    "project_developers",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(1024), nullable=False)
    interval_seconds = Column(Integer, default=3600, nullable=False)  # default 1 hour
    timeout_seconds = Column(Integer, default=10, nullable=False)
    expected_status_codes = Column(String(100), default="200,201,202,204", nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    developers = relationship(
        "User",
        secondary=project_developers,
        back_populates="projects"
    )
    monitoring_results = relationship(
        "MonitoringResult",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(MonitoringResult.timestamp)"
    )
    incidents = relationship(
        "Incident",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(Incident.started_at)"
    )
    alerts = relationship(
        "Alert",
        back_populates="project",
        cascade="all, delete-orphan"
    )
