import asyncio
import logging
import signal
import sys
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.monitor import update_worker_heartbeat
from app.services.scheduler import check_and_monitor_projects, daily_report_job, start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MONITOR-WORKER] [%(levelname)s]: %(message)s"
)
logger = logging.getLogger("adani.worker")


async def main():
    logger.info("=" * 60)
    logger.info("ADANI CENTRAL MONITORING BACKGROUND WORKER DAEMON")
    logger.info("=" * 60)
    logger.info(f"Loop interval: {settings.MONITOR_LOOP_INTERVAL_SECONDS}s")
    logger.info(f"Daily report schedule: {settings.DAILY_REPORT_TIME} {settings.DAILY_REPORT_TIMEZONE}")
    logger.info("Monitoring continues independently of dashboard status.")

    db = SessionLocal()
    try:
        update_worker_heartbeat(db, worker_name="standalone-worker", meta_info="Worker daemon initialized")
    finally:
        db.close()

    start_scheduler()

    # Run immediate check at launch
    check_and_monitor_projects()

    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Termination signal received. Shutting down worker...")
        stop_scheduler()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
