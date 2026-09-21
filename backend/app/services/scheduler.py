import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.services.email import send_admin_daily_report
from app.services.monitor import probe_website_sync, record_probe_result, update_worker_heartbeat

logger = logging.getLogger("adani.scheduler")

scheduler = AsyncIOScheduler()


def check_and_monitor_projects():
    """Check all enabled projects whose monitoring interval has elapsed and probe them."""
    db: Session = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.is_enabled == True).all()
        now = datetime.now(timezone.utc)
        checked_count = 0

        for project in projects:
            # Check when this project was last checked
            last_result = (
                db.query(MonitoringResult)
                .filter(MonitoringResult.project_id == project.id)
                .order_by(MonitoringResult.timestamp.desc())
                .first()
            )

            is_due = False
            if not last_result:
                is_due = True
            else:
                last_time = last_result.timestamp
                if not last_time.tzinfo:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                elapsed_seconds = (now - last_time).total_seconds()
                if elapsed_seconds >= project.interval_seconds:
                    is_due = True

            if is_due:
                logger.info(f"Monitoring check due for project '{project.name}' ({project.url})")
                probe = probe_website_sync(
                    url=project.url,
                    timeout_seconds=project.timeout_seconds,
                    expected_status_codes=project.expected_status_codes
                )
                record_probe_result(db, project, probe)
                checked_count += 1

        update_worker_heartbeat(
            db,
            worker_name="primary-monitor",
            meta_info=f"Cycle completed at {now.strftime('%H:%M:%S')}. Checked {checked_count} sites."
        )

    except Exception as exc:
        logger.error(f"Error during monitoring scheduler execution: {exc}")
    finally:
        db.close()


def daily_report_job():
    """Trigger scheduled daily admin email report."""
    logger.info("Executing scheduled Admin Daily Report job...")
    db: Session = SessionLocal()
    try:
        res = send_admin_daily_report(db)
        logger.info(f"Admin Daily Report result: {res}")
    except Exception as exc:
        logger.error(f"Error generating daily admin report: {exc}")
    finally:
        db.close()


def start_scheduler():
    """Initialize APScheduler with monitoring interval job and daily report cron."""
    if not settings.MONITOR_WORKER_ENABLED:
        logger.info("Monitoring worker disabled by configuration.")
        return

    # 1. Periodic website monitor check loop
    scheduler.add_job(
        check_and_monitor_projects,
        "interval",
        seconds=settings.MONITOR_LOOP_INTERVAL_SECONDS,
        id="monitoring_check_loop",
        replace_existing=True,
        max_instances=1
    )

    # 2. Daily report cron job (e.g. 20:11 IST)
    try:
        time_parts = settings.DAILY_REPORT_TIME.split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        scheduler.add_job(
            daily_report_job,
            CronTrigger(hour=hour, minute=minute, timezone=settings.DAILY_REPORT_TIMEZONE),
            id="admin_daily_report",
            replace_existing=True
        )
        logger.info(f"Scheduled Daily Admin Report for {settings.DAILY_REPORT_TIME} {settings.DAILY_REPORT_TIMEZONE}")
    except Exception as e:
        logger.warning(f"Could not parse daily report time '{settings.DAILY_REPORT_TIME}': {e}. Using 20:11.")
        scheduler.add_job(
            daily_report_job,
            CronTrigger(hour=20, minute=11, timezone="Asia/Kolkata"),
            id="admin_daily_report",
            replace_existing=True
        )

    scheduler.start()
    logger.info("Adani Monitoring Background Scheduler started successfully.")


def stop_scheduler():
    """Gracefully shutdown scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Adani Monitoring Background Scheduler stopped.")
