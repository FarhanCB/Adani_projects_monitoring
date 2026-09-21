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

### 2. One-Click Setup & Run (Windows Batch File)

Simply double-click or run:
```bash
start.bat
# or
run.bat
```
This batch script will automatically:
1. Verify Python and Node/npm installations
2. Create `backend\.venv` if missing and install all `backend/requirements.txt` dependencies
3. Run `npm install` and `npm run build` in `frontend` (configured with base path `/dashboard/`)
4. Start the FastAPI server on port **`8008`** serving both the API and frontend UI under `/dashboard`

### 3. Application URLs (All under `/dashboard`)

- **Web Application**: [http://localhost:8008/dashboard/](http://localhost:8008/dashboard/)
- **REST API Endpoints**: `http://localhost:8008/dashboard/api/*`
- **Swagger Documentation**: [http://localhost:8008/dashboard/docs](http://localhost:8008/dashboard/docs)
- **OpenAPI Schema**: `http://localhost:8008/dashboard/openapi.json`

*(Visiting `http://localhost:8008/` automatically redirects to `/dashboard/`)*

### 4. Deploying Alongside Another Project on Default Port (Nginx Reverse Proxy)

When deploying on a server where another project occupies the default port (port 80 or 443 at `/`), configure Nginx as follows:

```nginx
server {
    listen 80;
    server_name monitoring.yourcompany.com;  # or server IP / domain

    # 1. Existing project on default root
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
    }

    # 2. Adani Monitoring Platform (self-contained under /dashboard)
    location /dashboard {
        proxy_pass http://127.0.0.1:8008;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Manual Setup Steps (Alternative)

```bash
# 1. Build the frontend production bundle
cd frontend
npm install
npm run build
cd ..

# 2. Start the Backend API & Frontend on Port 8008
python run_server.py
```

### 4. Standalone Monitoring Script (Optional)

You can also run the standalone Python monitoring service:
```bash
python monitor.py
```
