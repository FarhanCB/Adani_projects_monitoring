import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Adani Website Monitoring & Uptime Analytics"
    HOST: str = "0.0.0.0"
    PORT: int = 8008
    API_V1_STR: str = "/api"
    SECRET_KEY: str = "adani-monitoring-super-secret-jwt-key-change-in-prod-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/adani_monitoring"
    FALLBACK_SQLITE_URL: str = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'adani_monitoring.db')}"

    # Monitoring Worker
    MONITOR_WORKER_ENABLED: bool = True
    MONITOR_LOOP_INTERVAL_SECONDS: int = 15  # check for projects needing monitoring every 15s
    DEFAULT_MONITOR_INTERVAL_SECONDS: int = 1800  # default 30 minutes
    DEFAULT_TIMEOUT_SECONDS: int = 10
    WARNING_RESPONSE_TIME_MS: int = 2000  # response time > 2s flagged as warning
    SSL_WARNING_DAYS: int = 14  # SSL cert expiring in < 14 days flagged as warning

    # Email & Alerts (SMTP)
    SMTP_SERVER: str = "smtp.adani.com"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "farhan.vhora@adani.com"
    SMTP_USE_TLS: bool = False
    SMTP_USE_SSL: bool = False
    SMTP_ENABLED: bool = True

    # Daily Report
    DAILY_REPORT_TIME: str = "20:11"  # 8:11 PM IST (HH:MM format)
    DAILY_REPORT_TIMEZONE: str = "Asia/Kolkata"
    DAILY_REPORT_RECIPIENTS: str = "farhanvhora@cognitbotz.com,farhan.vhora@adani.com"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )


settings = Settings()
