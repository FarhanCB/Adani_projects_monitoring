from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)  # DOWN, RESOLVED, DAILY_REPORT
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String(50), default="SENT", nullable=False)  # SENT, FAILED, SIMULATED

    project = relationship("Project", back_populates="alerts")
    incident = relationship("Incident", back_populates="alerts")
