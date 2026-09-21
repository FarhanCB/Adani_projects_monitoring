from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.system import SystemSetting
from app.models.user import User
from app.schemas.system import (
    DailyReportSettingsUpdate,
    EmailSettingsUpdate,
    ManualReportRequest,
    MonitoringSettingsUpdate,
    TestEmailRequest,
)
from app.services.email import send_admin_daily_report, send_html_email

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_setting_val(db: Session, key: str, default: str) -> str:
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return row.value if row else default


def set_setting_val(db: Session, key: str, value: str, desc: str = ""):
    row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if row:
        row.value = value
    else:
        row = SystemSetting(key=key, value=value, description=desc)
        db.add(row)
    db.commit()


@router.get("")
def get_all_settings(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Retrieve current system configuration for Monitoring, SMTP, and Daily Report."""
    return {
        "monitoring": {
            "default_interval_seconds": int(get_setting_val(db, "MONITOR_INTERVAL_SECONDS", str(settings.DEFAULT_MONITOR_INTERVAL_SECONDS))),
            "default_timeout_seconds": int(get_setting_val(db, "DEFAULT_TIMEOUT_SECONDS", str(settings.DEFAULT_TIMEOUT_SECONDS))),
            "warning_response_time_ms": int(get_setting_val(db, "WARNING_RESPONSE_TIME_MS", str(settings.WARNING_RESPONSE_TIME_MS))),
            "ssl_warning_days": int(get_setting_val(db, "SSL_WARNING_DAYS", str(settings.SSL_WARNING_DAYS))),
        },
        "email": {
            "smtp_server": get_setting_val(db, "SMTP_SERVER", settings.SMTP_SERVER),
            "smtp_port": int(get_setting_val(db, "SMTP_PORT", str(settings.SMTP_PORT))),
            "smtp_from_email": get_setting_val(db, "SMTP_FROM_EMAIL", settings.SMTP_FROM_EMAIL),
            "smtp_user": get_setting_val(db, "SMTP_USER", settings.SMTP_USER),
            "smtp_use_tls": get_setting_val(db, "SMTP_USE_TLS", str(settings.SMTP_USE_TLS)).lower() == "true",
            "smtp_use_ssl": get_setting_val(db, "SMTP_USE_SSL", str(settings.SMTP_USE_SSL)).lower() == "true",
            "smtp_enabled": get_setting_val(db, "SMTP_ENABLED", str(settings.SMTP_ENABLED)).lower() == "true",
        },
        "daily_report": {
            "daily_report_time": get_setting_val(db, "DAILY_REPORT_TIME", settings.DAILY_REPORT_TIME),
            "daily_report_timezone": get_setting_val(db, "DAILY_REPORT_TIMEZONE", settings.DAILY_REPORT_TIMEZONE),
            "daily_report_recipients": get_setting_val(db, "DAILY_REPORT_RECIPIENTS", settings.DAILY_REPORT_RECIPIENTS),
            "daily_report_enabled": get_setting_val(db, "DAILY_REPORT_ENABLED", "true").lower() == "true",
        }
    }


@router.put("/monitoring")
def update_monitoring_settings(
    payload: MonitoringSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update global monitoring defaults."""
    set_setting_val(db, "MONITOR_INTERVAL_SECONDS", str(payload.default_interval_seconds), "Default probe interval")
    set_setting_val(db, "DEFAULT_TIMEOUT_SECONDS", str(payload.default_timeout_seconds), "Default probe timeout")
    set_setting_val(db, "WARNING_RESPONSE_TIME_MS", str(payload.warning_response_time_ms), "Warning response time threshold")
    set_setting_val(db, "SSL_WARNING_DAYS", str(payload.ssl_warning_days), "SSL expiry warning days")
    return {"status": "SUCCESS", "message": "Monitoring configuration saved"}


@router.put("/email")
def update_email_settings(
    payload: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update SMTP email configuration."""
    set_setting_val(db, "SMTP_SERVER", payload.smtp_server)
    set_setting_val(db, "SMTP_PORT", str(payload.smtp_port))
    set_setting_val(db, "SMTP_FROM_EMAIL", str(payload.smtp_from_email))
    if payload.smtp_user is not None:
        set_setting_val(db, "SMTP_USER", payload.smtp_user)
    if payload.smtp_password:
        set_setting_val(db, "SMTP_PASSWORD", payload.smtp_password)
    set_setting_val(db, "SMTP_USE_TLS", str(payload.smtp_use_tls).lower())
    set_setting_val(db, "SMTP_USE_SSL", str(payload.smtp_use_ssl).lower())
    set_setting_val(db, "SMTP_ENABLED", str(payload.smtp_enabled).lower())
    return {"status": "SUCCESS", "message": "Email settings saved"}


@router.put("/daily-report")
def update_daily_report_settings(
    payload: DailyReportSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Update scheduled daily admin email report settings."""
    set_setting_val(db, "DAILY_REPORT_TIME", payload.daily_report_time)
    set_setting_val(db, "DAILY_REPORT_TIMEZONE", payload.daily_report_timezone)
    set_setting_val(db, "DAILY_REPORT_RECIPIENTS", payload.daily_report_recipients)
    set_setting_val(db, "DAILY_REPORT_ENABLED", str(payload.daily_report_enabled).lower())
    return {"status": "SUCCESS", "message": "Daily report configuration saved"}


@router.post("/test-email")
def test_email_configuration(
    payload: TestEmailRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Send a test email to verify SMTP configuration."""
    # Check if DB has overrides
    server = get_setting_val(db, "SMTP_SERVER", settings.SMTP_SERVER)
    port = int(get_setting_val(db, "SMTP_PORT", str(settings.SMTP_PORT)))
    user = get_setting_val(db, "SMTP_USER", settings.SMTP_USER)
    password = get_setting_val(db, "SMTP_PASSWORD", settings.SMTP_PASSWORD)
    from_email = get_setting_val(db, "SMTP_FROM_EMAIL", settings.SMTP_FROM_EMAIL)
    use_tls = get_setting_val(db, "SMTP_USE_TLS", str(settings.SMTP_USE_TLS)).lower() == "true"
    use_ssl = get_setting_val(db, "SMTP_USE_SSL", str(settings.SMTP_USE_SSL)).lower() == "true"
    enabled = get_setting_val(db, "SMTP_ENABLED", str(settings.SMTP_ENABLED)).lower() == "true"

    smtp_override = {
        "smtp_server": server,
        "smtp_port": port,
        "smtp_user": user,
        "smtp_password": password,
        "smtp_from_email": from_email,
        "smtp_use_tls": use_tls,
        "smtp_use_ssl": use_ssl,
        "smtp_enabled": enabled
    }

    subject = "Adani Monitoring - SMTP Test Email"
    html = f"""
    <div style="font-family: sans-serif; padding: 20px; background: #f8fafc;">
      <div style="max-width: 500px; margin: 0 auto; background: white; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0;">
        <h2 style="color: #A00020; margin-top: 0;">SMTP Test Successful</h2>
        <p>This is a test notification from the Adani Website Monitoring & Uptime Analytics platform.</p>
        <p>Your mail server settings are configured properly!</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
        <small style="color: #64748b;">Sender: {from_email} | Server: {server}:{port}</small>
      </div>
    </div>
    """

    res = send_html_email([payload.recipient], subject, html, smtp_override=smtp_override)
    return res


@router.post("/send-daily-report")
def trigger_daily_report_now(
    payload: ManualReportRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Manually dispatch the Admin Daily Report immediately."""
    recipients = None
    if payload.recipients:
        recipients = [e.strip() for e in payload.recipients.split(",") if e.strip()]
    res = send_admin_daily_report(db, recipients=recipients)
    return res
