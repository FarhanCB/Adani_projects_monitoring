import logging
import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("adani.database")

Base = declarative_base()

# Attempt connection to configured DATABASE_URL; fallback to SQLite if PostgreSQL is unreachable
active_db_url = settings.DATABASE_URL
connect_args = {}

if active_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Test if PostgreSQL is reachable
    try:
        test_engine = create_engine(active_db_url, pool_pre_ping=True)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected successfully to PostgreSQL at {active_db_url.split('@')[-1] if '@' in active_db_url else active_db_url}")
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Using local fallback SQLite database ({settings.FALLBACK_SQLITE_URL}) for seamless local execution.")
        active_db_url = settings.FALLBACK_SQLITE_URL
        connect_args = {"check_same_thread": False}

engine = create_engine(
    active_db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> dict:
    """Check database health and measure roundtrip latency in ms."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        dialect = engine.dialect.name
        return {
            "status": "CONNECTED",
            "dialect": dialect,
            "latency_ms": latency_ms,
            "url_type": "PostgreSQL" if "postgres" in dialect else "SQLite"
        }
    except Exception as exc:
        return {
            "status": "DISCONNECTED",
            "error": str(exc),
            "latency_ms": -1,
            "url_type": "unknown"
        }
