import logging
import smtplib
import socket
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.alert import Alert

logger = logging.getLogger("adani.email")


def get_monitoring_server_name() -> str:
    try:
        return f"{socket.gethostname()} (Adani Central Monitor Node)"
    except Exception:
        return "Adani-Monitor-Worker-01"


def send_html_email(
    to_emails: List[str],
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None,
    smtp_override: Optional[dict] = None
) -> dict:
    """Send an HTML email via SMTP. If SMTP fails or is not enabled, logs to console and returns status."""
    if not to_emails:
        return {"status": "SKIPPED", "message": "No recipients specified"}

    cfg_server = (smtp_override.get("smtp_server") if smtp_override else None) or settings.SMTP_SERVER
    cfg_port = int((smtp_override.get("smtp_port") if smtp_override else None) or settings.SMTP_PORT)
    cfg_user = (smtp_override.get("smtp_user") if smtp_override else None) or settings.SMTP_USER
    cfg_password = (smtp_override.get("smtp_password") if smtp_override else None) or settings.SMTP_PASSWORD
    cfg_from = (smtp_override.get("smtp_from_email") if smtp_override else None) or settings.SMTP_FROM_EMAIL
    cfg_tls = (smtp_override.get("smtp_use_tls") if smtp_override else None) if smtp_override and "smtp_use_tls" in smtp_override else settings.SMTP_USE_TLS
    cfg_ssl = (smtp_override.get("smtp_use_ssl") if smtp_override else None) if smtp_override and "smtp_use_ssl" in smtp_override else settings.SMTP_USE_SSL
    cfg_enabled = (smtp_override.get("smtp_enabled") if smtp_override else None) if smtp_override and "smtp_enabled" in smtp_override else settings.SMTP_ENABLED

    # If live SMTP sending is disabled in dev/sandbox, log simulation
    if not cfg_enabled:
        logger.info(f"[SIMULATED EMAIL] To: {', '.join(to_emails)} | Subject: {subject}")
        return {
            "status": "SIMULATED",
            "message": f"SMTP is currently disabled or in simulation mode. Email recorded for {', '.join(to_emails)}."
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg_from
        msg["To"] = ", ".join(to_emails)

        if plain_content:
            msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if cfg_ssl:
            server = smtplib.SMTP_SSL(cfg_server, cfg_port, timeout=10)
        else:
            server = smtplib.SMTP(cfg_server, cfg_port, timeout=10)
            if cfg_tls:
                server.starttls()

        if cfg_user and cfg_password:
            server.login(cfg_user, cfg_password)

        server.sendmail(cfg_from, to_emails, msg.as_string())
        server.quit()

        logger.info(f"Successfully sent email to {to_emails} with subject '{subject}'")
        return {"status": "SENT", "message": f"Email successfully sent to {', '.join(to_emails)}"}

    except Exception as exc:
        logger.warning(f"Failed to send email via SMTP ({cfg_server}:{cfg_port}): {exc}")
        return {"status": "FAILED", "error": str(exc)}


def send_down_alert(
    db: Session,
    project,
    incident,
    monitoring_result,
    recipient_emails: List[str]
):
    """Requirement 5:
    When a website is DOWN, immediately send an email to ALL developers assigned to that project.
    Subject: [DOWN] Plant Maintenance - Website Unavailable
    """
    if not recipient_emails:
        logger.info(f"No developers assigned to {project.name}; skipping DOWN email alert.")
        return

    subject = f"[DOWN] {project.name} - Website Unavailable"
    server_name = get_monitoring_server_name()
    detected_time = monitoring_result.timestamp.strftime("%d %b %Y, %I:%M:%S %p UTC")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #A00020 0%, #EA580C 100%); padding: 20px 24px; color: #ffffff; }}
        .badge {{ display: inline-block; padding: 4px 10px; background: #fee2e2; color: #991b1b; font-weight: 700; border-radius: 9999px; font-size: 12px; margin-bottom: 8px; }}
        .content {{ padding: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        td.val {{ color: #0f172a; font-weight: 500; word-break: break-all; }}
        .footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <span style="background: #ffffff; color: #A00020; font-weight: bold; padding: 3px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase;">OUTAGE ALERT</span>
          <h2 style="margin: 8px 0 0 0; font-size: 20px;">{project.name} is DOWN</h2>
        </div>
        <div class="content">
          <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5;">
            The Adani Automated Monitoring service detected an outage for your monitored website. Immediate action may be required.
          </p>
          <table>
            <tr><td class="label">Project</td><td class="val"><strong>{project.name}</strong></td></tr>
            <tr><td class="label">URL</td><td class="val"><a href="{project.url}" style="color: #A00020;">{project.url}</a></td></tr>
            <tr><td class="label">Detected Time</td><td class="val">{detected_time}</td></tr>
            <tr><td class="label">HTTP Status</td><td class="val"><strong>{monitoring_result.http_status or 'N/A'}</strong></td></tr>
            <tr><td class="label">Error Type</td><td class="val"><span style="color: #dc2626; font-weight: bold;">{monitoring_result.error_type or 'Unknown error'}</span></td></tr>
            <tr><td class="label">Error Message</td><td class="val">{monitoring_result.error_message or 'No response from server'}</td></tr>
            <tr><td class="label">Response Time</td><td class="val">{f"{monitoring_result.response_time_ms:.1f} ms" if monitoring_result.response_time_ms else 'N/A'}</td></tr>
            <tr><td class="label">Monitoring Server</td><td class="val">{server_name}</td></tr>
          </table>
        </div>
        <div class="footer">
          Adani Enterprise Infrastructure Monitoring • Automated Notification
        </div>
      </div>
    </body>
    </html>
    """

    res = send_html_email(recipient_emails, subject, html)

    # Store in alerts table for audit trail
    for email in recipient_emails:
        alert = Alert(
            project_id=project.id,
            incident_id=incident.id if incident else None,
            alert_type="DOWN",
            recipient=email,
            subject=subject,
            content=html,
            status=res["status"]
        )
        db.add(alert)
    db.commit()


def send_resolved_alert(
    db: Session,
    project,
    incident,
    monitoring_result,
    recipient_emails: List[str]
):
    """When a website changes from DOWN -> UP, notify developers."""
    if not recipient_emails:
        return

    subject = f"[RESOLVED] {project.name} - Website Recovered"
    server_name = get_monitoring_server_name()
    resolved_time = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M:%S %p UTC")

    from app.services.uptime import format_duration
    duration_str = format_duration(incident.duration_seconds) if incident and incident.duration_seconds else "N/A"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #15803d 0%, #16a34a 100%); padding: 20px 24px; color: #ffffff; }}
        .content {{ padding: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        td.label {{ color: #64748b; font-weight: 600; width: 35%; }}
        td.val {{ color: #0f172a; font-weight: 500; word-break: break-all; }}
        .footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <span style="background: #ffffff; color: #15803d; font-weight: bold; padding: 3px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase;">INCIDENT RESOLVED</span>
          <h2 style="margin: 8px 0 0 0; font-size: 20px;">{project.name} is back UP</h2>
        </div>
        <div class="content">
          <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5;">
            The website is responding normally with expected HTTP status code {monitoring_result.http_status or 200}.
          </p>
          <table>
            <tr><td class="label">Project</td><td class="val"><strong>{project.name}</strong></td></tr>
            <tr><td class="label">URL</td><td class="val"><a href="{project.url}" style="color: #15803d;">{project.url}</a></td></tr>
            <tr><td class="label">Recovery Time</td><td class="val">{resolved_time}</td></tr>
            <tr><td class="label">Total Downtime</td><td class="val"><strong>{duration_str}</strong></td></tr>
            <tr><td class="label">Response Time</td><td class="val">{f"{monitoring_result.response_time_ms:.1f} ms" if monitoring_result.response_time_ms else 'N/A'}</td></tr>
            <tr><td class="label">Monitoring Server</td><td class="val">{server_name}</td></tr>
          </table>
        </div>
        <div class="footer">
          Adani Enterprise Infrastructure Monitoring • Automated Notification
        </div>
      </div>
    </body>
    </html>
    """

    res = send_html_email(recipient_emails, subject, html)

    for email in recipient_emails:
        alert = Alert(
            project_id=project.id,
            incident_id=incident.id if incident else None,
            alert_type="RESOLVED",
            recipient=email,
            subject=subject,
            content=html,
            status=res["status"]
        )
        db.add(alert)
    db.commit()


def send_admin_daily_report(db: Session, recipients: Optional[List[str]] = None) -> dict:
    """Requirement 6:
    Create a scheduled admin email (Default 8:11 PM IST).
    Shows:
      Total projects, UP projects, DOWN projects, Warning projects, Total incidents, Total downtime
      Table: Project | Status | Uptime | Downtime | Incidents | Last Checked
    """
    from app.models.project import Project
    from app.models.incident import Incident
    from app.services.uptime import calculate_project_uptime, parse_date_range, format_duration

    if not recipients:
        recipients = [e.strip() for e in settings.DAILY_REPORT_RECIPIENTS.split(",") if e.strip()]
    if not recipients:
        return {"status": "SKIPPED", "message": "No recipients configured for daily report"}

    projects = db.query(Project).filter(Project.is_enabled == True).all()

    start_today, end_today, _ = parse_date_range("today")

    total_projects = len(projects)
    up_count = 0
    down_count = 0
    warning_count = 0
    total_incidents_today = 0
    total_downtime_seconds_today = 0

    rows_html = []

    for p in projects:
        latest = p.monitoring_results[0] if p.monitoring_results else None
        status = latest.status if latest else "PENDING"

        if status == "UP":
            up_count += 1
            badge = '<span style="background: #dcfce7; color: #15803d; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 12px;">UP</span>'
        elif status == "DOWN":
            down_count += 1
            badge = '<span style="background: #fee2e2; color: #b91c1c; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 12px;">DOWN</span>'
        elif status == "WARNING":
            warning_count += 1
            badge = '<span style="background: #fef3c7; color: #b45309; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 12px;">WARNING</span>'
        else:
            badge = '<span style="background: #f1f5f9; color: #475569; font-weight: bold; padding: 2px 8px; border-radius: 4px; font-size: 12px;">PENDING</span>'

        stats = calculate_project_uptime(db, p.id, start_today, end_today)
        total_incidents_today += stats["incident_count"]
        total_downtime_seconds_today += stats["total_downtime_seconds"]

        last_checked = latest.timestamp.strftime("%I:%M %p") if latest else "Never"

        rows_html.append(f"""
        <tr>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{p.name}</td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0;">{badge}</td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: { '#15803d' if stats['uptime_pct'] >= 99 else '#b91c1c' };">{stats['uptime_pct']}%</td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0;">{stats['total_downtime_formatted']}</td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0;">{stats['incident_count']}</td>
          <td style="padding: 10px 12px; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">{last_checked}</td>
        </tr>
        """)

    total_downtime_formatted = format_duration(total_downtime_seconds_today)
    report_date = datetime.now(timezone.utc).strftime("%d %B %Y")
    subject = f"Adani Monitoring Daily Report - {report_date}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a; }}
        .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
        .header {{ background: linear-gradient(135deg, #A00020 0%, #EA580C 100%); padding: 24px; color: #ffffff; }}
        .metrics-grid {{ display: table; width: 100%; border-collapse: separate; border-spacing: 12px; padding: 12px; background: #f8fafc; }}
        .metric-card {{ display: table-cell; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; text-align: center; width: 16.6%; }}
        .metric-val {{ font-size: 22px; font-weight: 800; margin-top: 4px; }}
        .metric-lbl {{ font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 600; }}
        .table-wrap {{ padding: 20px 24px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: #f1f5f9; padding: 10px 12px; font-size: 12px; text-transform: uppercase; color: #475569; letter-spacing: 0.5px; border-bottom: 2px solid #e2e8f0; }}
        .footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Adani Corporate Infrastructure</div>
          <h1 style="margin: 6px 0 0 0; font-size: 22px;">Executive Daily Monitoring Report</h1>
          <div style="font-size: 13px; margin-top: 4px; opacity: 0.85;">Reporting Period: Today ({report_date})</div>
        </div>

        <table class="metrics-grid">
          <tr>
            <td class="metric-card">
              <div class="metric-lbl">Total Sites</div>
              <div class="metric-val" style="color: #0f172a;">{total_projects}</div>
            </td>
            <td class="metric-card">
              <div class="metric-lbl">Online (UP)</div>
              <div class="metric-val" style="color: #15803d;">{up_count}</div>
            </td>
            <td class="metric-card">
              <div class="metric-lbl">Offline (DOWN)</div>
              <div class="metric-val" style="color: #b91c1c;">{down_count}</div>
            </td>
            <td class="metric-card">
              <div class="metric-lbl">Warning</div>
              <div class="metric-val" style="color: #b45309;">{warning_count}</div>
            </td>
            <td class="metric-card">
              <div class="metric-lbl">Incidents</div>
              <div class="metric-val" style="color: #A00020;">{total_incidents_today}</div>
            </td>
            <td class="metric-card">
              <div class="metric-lbl">Total Downtime</div>
              <div class="metric-val" style="font-size: 16px; color: #b91c1c;">{total_downtime_formatted}</div>
            </td>
          </tr>
        </table>

        <div class="table-wrap">
          <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #1e293b;">Monitored Services Status Summary</h3>
          <table>
            <thead>
              <tr>
                <th>Project</th>
                <th>Status</th>
                <th>Today Uptime</th>
                <th>Downtime</th>
                <th>Incidents</th>
                <th>Last Checked</th>
              </tr>
            </thead>
            <tbody>
              {''.join(rows_html)}
            </tbody>
          </table>
        </div>

        <div class="footer">
          Generated automatically by Adani Website Monitoring Service & Uptime Analytics Node • {get_monitoring_server_name()}
        </div>
      </div>
    </body>
    </html>
    """

    res = send_html_email(recipients, subject, html)
    return res
