import logging
import socket
import ssl
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from requests.exceptions import ConnectionError, RequestException, Timeout, SSLError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.system import WorkerHeartbeat
from app.services.email import send_down_alert, send_resolved_alert
from app.services.error_catalog import get_error_diagnostic

logger = logging.getLogger("adani.monitor")

# Global requests Session with trust_env=False
# Crucial for Adani corporate network / VM environment:
# Prevents Python requests from using unwanted proxy settings from environment variables.
session = requests.Session()
session.trust_env = False


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def extract_ssl_info(url: str, timeout: int = 5) -> dict:
    """Extract SSL certificate details for HTTPS endpoints: validity, days remaining, and issuer."""
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return {"ssl_valid": None, "ssl_days_remaining": None, "ssl_issuer": None}

    hostname = parsed.hostname
    port = parsed.port or 443

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        not_after_str = cert.get("notAfter")
        if not_after_str:
            exp_date = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (exp_date - datetime.now(timezone.utc)).days
        else:
            days_left = None

        issuer_tuple = cert.get("issuer", ())
        issuer_parts = []
        for item in issuer_tuple:
            for k, v in item:
                if k in ("organizationName", "commonName"):
                    issuer_parts.append(v)
        issuer = ", ".join(issuer_parts) if issuer_parts else "Corporate CA"

        return {
            "ssl_valid": True,
            "ssl_days_remaining": max(0, days_left) if days_left is not None else None,
            "ssl_issuer": issuer[:255] if issuer else None
        }
    except ssl.SSLCertVerificationError as e:
        return {"ssl_valid": False, "ssl_days_remaining": 0, "ssl_issuer": str(e)[:255]}
    except Exception as e:
        logger.debug(f"SSL probe skipped for {hostname}: {e}")
        return {"ssl_valid": None, "ssl_days_remaining": None, "ssl_issuer": None}


def probe_website_sync(
    url: str,
    timeout_seconds: int = 30,
    expected_status_codes: str = "200,201,202,204,301,302"
) -> dict:
    """Perform HTTP/HTTPS probe with custom proxy bypassing to protect internal company URLs.
    Follows exact logic of monitor.py:
      - Uses requests.Session() with session.trust_env = False
      - Timeout: default 30s
      - 200 <= status_code < 400 is considered UP
      - Classifies errors: Timeout, Connection error, SSL error, HTTP 4xx, HTTP 5xx, Unexpected redirect
    """
    expected_codes = [int(c.strip()) for c in expected_status_codes.split(",") if c.strip().isdigit()]
    if not expected_codes:
        expected_codes = [200, 201, 202, 204, 301, 302]

    # SSL extraction
    ssl_info = extract_ssl_info(url, timeout=min(5, timeout_seconds))

    start_time = time.perf_counter()
    status = "DOWN"
    http_status = None
    response_time_ms = None
    error_type = None
    error_message = None
    redirect_url = None

    try:
        # Probe using requests.Session with trust_env = False
        resp = session.get(
            url,
            timeout=float(timeout_seconds),
            verify=True,
            headers={
                "User-Agent": "Adani-Enterprise-Website-Monitor/2.0 (VM-Health-Check; +https://adani.com)"
            },
            allow_redirects=True
        )
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        http_status = resp.status_code

        if len(resp.history) > 0:
            redirect_url = str(resp.url)

        # In monitor.py: 200 <= status_code < 400 is UP
        if (200 <= http_status < 400) or (http_status in expected_codes):
            if response_time_ms > settings.WARNING_RESPONSE_TIME_MS:
                status = "WARNING"
                error_type = "Slow Response"
                error_message = f"Response time {response_time_ms}ms exceeded warning threshold ({settings.WARNING_RESPONSE_TIME_MS}ms)"
            elif ssl_info["ssl_days_remaining"] is not None and ssl_info["ssl_days_remaining"] <= settings.SSL_WARNING_DAYS:
                status = "WARNING"
                error_type = "SSL Expiring Soon"
                error_message = f"SSL Certificate will expire in {ssl_info['ssl_days_remaining']} days"
            else:
                status = "UP"
        else:
            status = "DOWN"
            if 400 <= http_status < 500:
                error_type = "HTTP 4xx"
                error_message = f"HTTP {http_status} Client Error"
            elif 500 <= http_status < 600:
                error_type = "HTTP 5xx"
                error_message = f"HTTP {http_status} Server Error"
            else:
                error_type = f"HTTP {http_status}"
                error_message = f"Received unexpected HTTP {http_status}"

    except SSLError as exc:
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        # Attempt fallback probe with verify=False to test if server is actually responding
        try:
            fallback_resp = session.get(url, timeout=float(timeout_seconds), verify=False, allow_redirects=True)
            http_status = fallback_resp.status_code
            status = "WARNING"
            error_type = "SSL Certificate Warning"
            error_message = f"Internal/Untrusted SSL certificate, but service is responding (HTTP {http_status})"
        except Exception:
            status = "DOWN"
            error_type = "SSL error"
            error_message = f"SSL verification failed: {exc}"

    except Timeout:
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "DOWN"
        error_type = "Timeout"
        error_message = f"Request timed out after {timeout_seconds}s"

    except ConnectionError as exc:
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "DOWN"
        err_str = str(exc).lower()
        if "getaddrinfo failed" in err_str or "name resolution" in err_str or "dns" in err_str:
            error_type = "DNS error"
            error_message = "DNS error: Hostname not resolved (VPN/Internal DNS required)"
        else:
            error_type = "Connection error"
            error_message = "Connection error: Server refused connection or unreachable"

    except RequestException as exc:
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "DOWN"
        error_type = "Request error"
        error_message = f"Request error: {exc}"

    except Exception as exc:
        response_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        status = "DOWN"
        error_type = "Unexpected error"
        error_message = f"Unexpected error: {exc}"

    # Resolve comprehensive root-cause diagnosis if site is DOWN or WARNING
    diagnostic = None
    if status != "UP":
        diagnostic = get_error_diagnostic(
            http_status=http_status,
            error_type=error_type,
            error_message=error_message,
            url=url
        )
        if diagnostic and diagnostic.get("summary"):
            error_message = f"{diagnostic['title']}: {diagnostic['summary']}"

    return {
        "status": status,
        "http_status": http_status,
        "response_time_ms": response_time_ms,
        "error_type": error_type,
        "error_message": error_message,
        "diagnostic": diagnostic,
        "redirect_url": redirect_url,
        "ssl_valid": ssl_info["ssl_valid"],
        "ssl_days_remaining": ssl_info["ssl_days_remaining"],
        "ssl_issuer": ssl_info["ssl_issuer"],
        "tested_at": get_utc_now()
    }


def record_probe_result(db: Session, project: Project, probe: dict) -> MonitoringResult:
    """Record monitoring result and manage incident lifecycle state machine."""
    now = get_utc_now()

    result = MonitoringResult(
        project_id=project.id,
        timestamp=now,
        status=probe["status"],
        http_status=probe["http_status"],
        response_time_ms=probe["response_time_ms"],
        error_type=probe["error_type"],
        error_message=probe["error_message"],
        redirect_url=probe["redirect_url"],
        ssl_valid=probe["ssl_valid"],
        ssl_days_remaining=probe["ssl_days_remaining"],
        ssl_issuer=probe["ssl_issuer"]
    )
    db.add(result)
    db.flush()

    open_incident = (
        db.query(Incident)
        .filter(Incident.project_id == project.id, Incident.is_resolved == False)
        .first()
    )

    dev_emails = [d.email for d in project.developers if d.email]

    if probe["status"] == "DOWN":
        if not open_incident:
            new_incident = Incident(
                project_id=project.id,
                started_at=now,
                error_type=probe["error_type"] or "Unknown error",
                http_status=probe["http_status"],
                error_message=probe["error_message"],
                is_resolved=False
            )
            db.add(new_incident)
            db.flush()

            logger.warning(f"Project '{project.name}' DOWN. Created incident #{new_incident.id}.")
            try:
                send_down_alert(db, project, new_incident, result, dev_emails)
            except Exception as e:
                logger.error(f"Error dispatching DOWN alert: {e}")
        else:
            logger.info(f"Project '{project.name}' still DOWN. Incident #{open_incident.id} remains open.")

    elif probe["status"] in ("UP", "WARNING"):
        if open_incident:
            open_incident.is_resolved = True
            open_incident.resolved_at = now
            started_aware = open_incident.started_at if open_incident.started_at.tzinfo else open_incident.started_at.replace(tzinfo=timezone.utc)
            duration_sec = int((now - started_aware).total_seconds())
            open_incident.duration_seconds = max(0, duration_sec)

            logger.info(f"Project '{project.name}' recovered. Resolved incident #{open_incident.id} ({duration_sec}s).")
            try:
                send_resolved_alert(db, project, open_incident, result, dev_emails)
            except Exception as e:
                logger.error(f"Error dispatching RESOLVED alert: {e}")

    db.commit()
    return result


def update_worker_heartbeat(db: Session, worker_name: str = "primary-monitor", meta_info: str = "Healthy"):
    try:
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_name == worker_name).first()
        now = get_utc_now()
        if hb:
            hb.last_heartbeat = now
            hb.status = "ONLINE"
            hb.meta_info = meta_info
        else:
            hb = WorkerHeartbeat(
                worker_name=worker_name,
                last_heartbeat=now,
                status="ONLINE",
                meta_info=meta_info
            )
            db.add(hb)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update worker heartbeat: {e}")
        db.rollback()
