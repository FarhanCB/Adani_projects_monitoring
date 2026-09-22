# Ping Tester — Design Spec

**Date:** 2026-09-07  
**Status:** Approved for implementation

## Goal

A Python Flask web dashboard that monitors HTTP URLs across multiple projects, stores everything in a single root `data.json` (no database), and runs background checks every 60 seconds on the VM even when the browser is closed.

## Decisions

| Topic | Choice |
|--------|--------|
| Stack | Flask + APScheduler + Jinja templates |
| Storage | Single `data.json` in project root |
| Check interval | 60 seconds (global) |
| Success criteria | Per-URL expected HTTP status (default 200) |
| Auth | Shared PIN (hashed in JSON) |
| Results | Latest status + last 20 history entries per URL |
| Deploy | Drop on VM, `pip install`, `python app.py` |

## Architecture

One process serves:

1. **Web UI** — PIN login, project CRUD, URL CRUD, live status, short history
2. **Checker** — APScheduler job every 60s; HTTP GET; classify OK / issue / service down
3. **Storage** — atomic JSON read/write for settings, projects, URLs, results

## Data model

See `data.json` shape: `settings` (pin_hash, check_interval_seconds) + `projects[]` with `urls[]`, each URL having `expected_status`, `last_result`, and capped `history` (max 20).

## Status classification

- Status code matches expected → **OK**
- Reachable but wrong status → **Issue** (show code + reason)
- Timeout / DNS / connection error → **Service down** (short error when available)

## UI screens

1. **Login** — shared PIN
2. **Dashboard** — project list with health summary (X/Y up), add/edit/delete projects
3. **Project detail** — URL table with status badges, latency, last checked; add/edit/delete URLs; expandable last-20 history; manual “Check now”
4. **Settings** — change PIN

Visual direction: professional ops dashboard — cool slate base, teal accents, clear green/amber/red status; expressive sans (IBM Plex / Source Sans via Google Fonts); subtle gradient atmosphere; clean tables over card clutter.

## File layout

```
app.py              # Flask routes + scheduler bootstrap
storage.py          # JSON load/save, CRUD helpers
checker.py          # HTTP check + history update
auth.py             # PIN hash/verify, session gate
data.json           # created at runtime
requirements.txt
README.md
static/css/style.css
static/js/app.js
templates/
  base.html
  login.html
  dashboard.html
  project.html
  settings.html
```

## Security notes

- PIN stored as Werkzeug password hash
- Session cookie required for mutating routes
- Intended for private/VPN VM networks; not a public multi-tenant product

## Out of scope

- Email/SMS alerts
- Per-project intervals
- Multi-user accounts
- Database
- ICMP ping (HTTP(S) status checks only)
