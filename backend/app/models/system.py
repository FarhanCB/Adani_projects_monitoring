from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"

    id = Column(Integer, primary_key=True, index=True)
    worker_name = Column(String(100), unique=True, nullable=False, default="primary-monitor")
    last_heartbeat = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String(50), default="ONLINE", nullable=False)
    meta_info = Column(Text, nullable=True)  # JSON or status summary string


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
