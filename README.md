# Ping Tester

HTTP uptime dashboard for a VM. Manage multiple projects and URLs from a web UI, store everything in one `data.json` file, and run background checks every 60 seconds.

## Features

- Multi-project live insights dashboard
- Project metadata: name, project URL, description, developers (name + email)
- Per-URL expected HTTP status (default `200`)
- Background scheduler (checks continue with the browser closed)
- Admin login (`admin` / `admin123` by default)
- Settings tabs: **Email Config** (SMTP alerts) and **AI Config** (shared API key, separate Analysis/Chatbot models)
- Alert emails on Issue/Down transitions + recovery emails
- Latest status + last 20 checks per URL
- **Analyst** — diagnoses every failed check
- **Helper** — chat drawer for health / ownership questions
- Manual “Check now” for a project or single URL
- No database — all data in `data.json` in this folder

## Quick start (VM)

```bash
cd Ping-Tester
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python app.py
```

Open `http://<vm-ip>:5050`

Login: **admin** / **admin123**

Then open **Settings**:
1. Email Config — SMTP + recipients, optional test email
2. AI Config — API key, Fetch models, pick Analysis + Chatbot models

## Status meaning

| Result | Meaning |
|--------|---------|
| **OK** | Response status matches expected code |
| **Issue** | Reachable, but status did not match |
| **Down** | Timeout / connection failure — service down |

## Notes

- Bind address is `0.0.0.0:5050`
- Email/AI secrets live in `data.json` (VM-local). Prefer not committing that file with secrets.
- Fallback: if AI Settings key is empty, `.env` / `NVidiaAPI.txt` still work.
