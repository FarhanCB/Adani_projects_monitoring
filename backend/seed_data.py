import logging
import random
from datetime import datetime, timedelta, timezone
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.monitoring import MonitoringResult
from app.models.project import Project
from app.models.system import SystemSetting, WorkerHeartbeat
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

RAW_PROJECTS = [
    {
        "name": "F & A Report Optimization",
        "url": "https://agel-agents-uat.adani.com/fna/dashboard/financial-summary",
        "developers": [
            "naumanpathan@adani.com",
            "sahil.singh1@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "Akasha Intelligence Cross Platform",
        "url": "https://digitalized-dpr-uat.adani.com/akasha",
        "developers": [
            "praveen.gunja@adani.com",
            "NikithaM@cognitbotz.com"
        ],
        "enabled": True
    },
    {
        "name": "PMAG Cost Process",
        "url": "https://agel-agents-uat.adani.com/pmag/details",
        "developers": [
            "VenkatHarshith@cognitbotz.com",
            "sahil.singh1@adani.com",
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "NDC",
        "url": "https://agel-agents-uat.adani.com/ndc/ndc-reporting/overview",
        "developers": [
            "laxminarayana@adani.com",
            "sahil.singh1@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "ENOC",
        "url": "https://agel-agents-uat.adani.com/enoc",
        "developers": [
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "Landed Tariff",
        "url": "https://agel-agents-uat.adani.com/landed-tariff/dashboard",
        "developers": [
            "SaiManohar@cognitbotz.com",
            "SaiBhargav@cognitbotz.com"
        ],
        "enabled": True
    },
    {
        "name": "Debt Pulse",
        "url": "https://aegis.adani.com/debt-markets/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "GuruPrasad@cognitbotz.com"
        ],
        "enabled": True
    },
    {
        "name": "DPR",
        "url": "https://digitalized-dpr.adani.com/",
        "developers": [
            "praveen.gunja@adani.com",
            "NikithaM@cognitbotz.com"
        ],
        "enabled": True
    },
    {
        "name": "IR",
        "url": "https://aegis.adani.com/equity-dashboard/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "pallavi.namburi@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "AEGIS",
        "url": "https://aegis.adani.com/",
        "developers": [
            "Abhishek.MahadevMane@adani.com",
            "SreejaK@cognitbotz.com",
            "Sreecharan@cognitbotz.com",
            "Satwik.Narwa@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "Carbon Credit",
        "url": "https://agel-agents.adani.com/carbon-credit-tracker/",
        "developers": [
            "Rahul.Chenna@adani.com"
        ],
        "enabled": True
    },
    {
        "name": "Plant Maintenance",
        "url": "https://agel-agents-uat.adani.com/plant-maintenance/",
        "developers": [
            "farhan.vhora@adani.com",
            "naumanpathan@adani.com",
            "FarhanVhora@cognitbotz.com"
        ],
        "enabled": True
    },
    {
        "name": "Cobot Dashboard",
        "url": "http://aegis.adani.com/cobot/home",
        "developers": [
            "praveen.gunja@adani.com"
        ],
        "enabled": True
    }
]


def seed():
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # 1. Admin Users
        admin_emails = ["admin@adani.com", "farhan.vhora@adani.com", "farhan@adani.com"]
        for a_email in admin_emails:
            clean_email = a_email.lower().strip()
            admin = db.query(User).filter(User.email == clean_email).first()
            if not admin:
                name = "Farhan Vhora" if "farhan" in clean_email else "Adani Operations"
                admin = User(
                    email=clean_email,
                    full_name=name,
                    hashed_password=get_password_hash("Adani@12345"),
                    role="USER",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                logger.info(f"Created User: {clean_email}")

        # 2. Extract and create all unique developers
        all_dev_emails = set()
        for p in RAW_PROJECTS:
            for d in p["developers"]:
                all_dev_emails.add(d.lower().strip())

        dev_user_map = {}
        for d_email in all_dev_emails:
            dev = db.query(User).filter(User.email == d_email).first()
            if not dev:
                uname = d_email.split("@")[0].replace(".", " ").title()
                dev = User(
                    email=d_email,
                    full_name=uname,
                    hashed_password=get_password_hash("Adani@12345"),
                    role="USER",
                    is_active=True
                )
                db.add(dev)
                db.commit()
                logger.info(f"Created Developer: {d_email}")
            dev_user_map[d_email] = dev

        # Re-fetch developer objects with IDs
        for d_email in all_dev_emails:
            dev_user_map[d_email.lower()] = db.query(User).filter(User.email == d_email.lower()).first()

        # 3. Create or update the 13 official Adani projects
        projects_created = []
        for p_data in RAW_PROJECTS:
            proj = db.query(Project).filter(Project.name == p_data["name"]).first()
            devs_to_assign = [dev_user_map[d.lower()] for d in p_data["developers"] if d.lower() in dev_user_map]

            if not proj:
                proj = Project(
                    name=p_data["name"],
                    description=f"Adani Enterprise Service: {p_data['name']}",
                    url=p_data["url"],
                    interval_seconds=1800,
                    timeout_seconds=30,
                    expected_status_codes="200,201,202,204,301,302",
                    is_enabled=p_data.get("enabled", True),
                    developers=devs_to_assign
                )
                db.add(proj)
                db.flush()
                logger.info(f"Created Project: {proj.name}")
            else:
                proj.url = p_data["url"]
                proj.interval_seconds = 1800
                proj.is_enabled = p_data.get("enabled", True)
                proj.developers = devs_to_assign
                db.flush()

            projects_created.append(proj)

        db.commit()

        # 4. Probe each project for real live telemetry data
        from app.services.monitor import probe_website_sync, record_probe_result
        logger.info("Executing initial live probe for all 13 projects with real HTTP requests...")
        for proj in projects_created:
            if proj.is_enabled:
                try:
                    probe = probe_website_sync(
                        url=proj.url,
                        timeout_seconds=proj.timeout_seconds,
                        expected_status_codes=proj.expected_status_codes
                    )
                    record_probe_result(db, proj, probe)
                    logger.info(f"Probed {proj.name}: {probe['status']} (HTTP {probe['http_status']}, {probe['response_time_ms']}ms)")
                except Exception as ex:
                    logger.warning(f"Probe error for {proj.name}: {ex}")

        db.commit()

        # Heartbeat update
        hb = db.query(WorkerHeartbeat).filter(WorkerHeartbeat.worker_name == "primary-monitor").first()
        if not hb:
            db.add(WorkerHeartbeat(
                worker_name="primary-monitor",
                last_heartbeat=now,
                status="ONLINE",
                meta_info="System online and monitoring all 13 Adani services"
            ))
        else:
            hb.last_heartbeat = now
            hb.status = "ONLINE"
            hb.meta_info = f"Monitoring {len(projects_created)} Adani services"

        db.commit()
        logger.info("Database seeding completed successfully with all 13 Adani projects!")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
