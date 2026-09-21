# Adani_projects_monitoring

Enterprise Website Monitoring & Uptime Analytics platform designed for continuous internal and corporate infrastructure observability.

---

## Architecture Overview

```
React Frontend (Vite + TS + Tailwind CSS)
            ↓ REST API
FastAPI Backend (Python 3.10+)
            ↓ SQLAlchemy
PostgreSQL / SQLite Database
            ↑
Background Monitoring Engine (Probes every 30 mins)
            ↓ SMTP
Email Alerts & Executive Daily Reports
```

---

## Key Features

- **Continuous Website & Endpoint Monitoring**: Automatically tests all configured projects every 30 minutes (customizable per project).
- **Comprehensive Diagnostics & Root-Cause Analysis**: Identifies root causes for HTTP 4xx, HTTP 5xx, DNS failures, SSL expiration/warnings, and connection timeouts.
- **Immediate Outage Alerts**: Instant email alerts dispatched via SMTP to assigned developers upon downtime detection and recovery.
- **Scheduled Daily Status Reports**: Automated daily executive summary report emailed to designated stakeholders.
- **Enterprise UI**: Clean Adani tri-color brand gradient, static status indicators (UP/DOWN/WARNING), and response time latency charts.
- **Live Real-World Metrics**: Accurate uptime percentage calculation derived strictly from real monitoring checks and verified incident durations.

---

## 13 Monitored Endpoints

1. **F & A Report Optimization**: `https://agel-agents-uat.adani.com/fna/dashboard/financial-summary`
2. **Akasha Intelligence Cross Platform**: `https://digitalized-dpr-uat.adani.com/akasha`
3. **PMAG Cost Process**: `https://agel-agents-uat.adani.com/pmag/details`
4. **NDC**: `https://agel-agents-uat.adani.com/ndc/ndc-reporting/overview`
5. **ENOC**: `https://agel-agents-uat.adani.com/enoc`
6. **Landed Tariff**: `https://agel-agents-uat.adani.com/landed-tariff/dashboard`
7. **Debt Pulse**: `https://aegis.adani.com/debt-markets/`
8. **DPR**: `https://digitalized-dpr.adani.com/`
9. **IR**: `https://aegis.adani.com/equity-dashboard/`
10. **AEGIS**: `https://aegis.adani.com/`
11. **Carbon Credit**: `https://agel-agents.adani.com/carbon-credit-tracker/`
12. **Plant Maintenance**: `https://agel-agents-uat.adani.com/plant-maintenance/`
13. **Cobot Dashboard**: `http://aegis.adani.com/cobot/home`

---

## Getting Started

### 1. Environment Configuration

Copy `.env.example` to `.env` in both root and backend directories:
```bash
cp .env.example backend/.env
```

Configure your SMTP settings:
```env
SMTP_SERVER=smtp.adani.com
SMTP_PORT=25
SMTP_FROM_EMAIL=farhan.vhora@adani.com
SMTP_ENABLED=true
DEFAULT_MONITOR_INTERVAL_SECONDS=1800
DAILY_REPORT_RECIPIENTS=farhanvhora@cognitbotz.com,farhan.vhora@adani.com
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Standalone Monitoring Script (Optional)

You can also run the standalone Python monitoring service:
```bash
python monitor.py
```
