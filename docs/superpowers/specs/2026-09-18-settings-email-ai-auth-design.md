# Ping Tester — Admin Auth, Settings Tabs, Email Alerts, AI Config

**Date:** 2026-09-18  
**Status:** Approved in chat; awaiting final spec review  
**Approach:** Settings-in-`data.json` + thin modules (`mailer.py`, extended `agents/llm.py`)

## Goal

Make Ping Tester a live observability console with:

1. Admin username/password login (replace shared PIN)
2. Settings page with **Email Config** and **AI Config** tabs
3. Real SMTP alerts on Issue/Down transitions + recovery emails
4. Shared NVIDIA-compatible API key/base URL with separate Analysis vs Chatbot models (models listed from API)
5. More interactive / live UI polish

## Decisions (locked)

| Topic | Choice |
|--------|--------|
| Auth | Hardcoded default `admin` / `admin123`; replace PIN |
| Alert recipients | Settings Email Config list only (not project developers) |
| Mail transport | Full SMTP form + **Send test email** |
| AI keys | One shared API key + base URL; separate models for Analysis and Chatbot |
| Alert timing | On change to Issue/Down + recovery email when back to OK |
| Persistence | Config in `data.json` (Approach 1) |

## Auth

- Login form: **Username** + **Password** (no PIN, no setup PIN flow).
- Defaults: username `admin`, password `admin123`.
- Password may be changed in Settings (Account section or Email/AI page footer): store `admin_password_hash` in `data.json`. If unset, verify against default `admin123`.
- Username remains `admin` (single admin).
- `setup_complete` becomes true automatically when store loads if projects already exist, or on first successful default login path; remove `/setup` PIN UI (redirect to login).
- Migrate: ignore `pin_hash`; stop requiring it for `is_setup_complete`.

## Settings UI

Route `/settings` with two tabs:

### Tab 1 — Email Config

Fields:

- SMTP host, port, encryption (`none` | `starttls` | `ssl`)
- SMTP username, SMTP password
- From address
- Recipients (multi: comma-separated or chip/list UI)
- Enable alerts toggle
- Buttons: **Save**, **Send test email**

### Tab 2 — AI Config

Fields:

- API key (masked after save; leave blank to keep existing)
- Base URL (default `https://integrate.api.nvidia.com/v1`)
- Analysis model (select)
- Chatbot model (select)
- Button: **Fetch models** → `GET {base_url}/models` with Bearer key → populate both dropdowns
- Buttons: **Save**
- Show online/offline status for Analysis and Chatbot based on key + selected model

Fallback: if Settings API key empty, use existing `.env` / `NVidiaAPI.txt` (current behavior).

## Email alerts (runtime)

New module: `mailer.py`

- `send_email(subject, body, to=None)` using SMTP settings from storage
- `maybe_alert_on_transition(project, entry, previous_result, new_result)`:
  - If alerts disabled or SMTP incomplete → no-op
  - Previous label was `ok`/`unknown`/missing → new `issue` or `down` → send failure mail
  - Previous `issue`/`down` → new `ok` → send recovery mail
  - Same bad state repeated → no mail
- Subject failure: `{Project name} — {Issue|Down}`
- Subject recovery: `{Project name} — Recovered`
- Body: service name, URL, expected vs actual status, message, response_ms, checked_at, Analyst summary/cause if present

Wire from `checker.py` after `apply_check_result`, comparing previous `last_result` captured before overwrite.

Test email uses current SMTP + recipients with subject `Ping Tester — Test email`.

## AI runtime

Extend `agents/llm.py`:

- `get_ai_settings()` merges storage AI config over env defaults
- `get_llm(role="analysis"|"chat", ...)` uses role-specific model
- `list_models(api_key, base_url)` → list of model ids
- `reset_llm_cache()` whenever AI settings saved
- Analyst uses `role=analysis`; Helper uses `role=chat`

API:

- `POST /settings/email` / `POST /settings/ai` (or single settings page with `action=` field)
- `POST /api/settings/email/test`
- `GET /api/settings/ai/models` (uses saved or form-provided key/url)

## Live UI polish

- Settings tabbed panel with clear active state
- Topbar live pulse / last-refresh indicator on Insights (existing `/api/status` poll)
- Stronger Issue/Down visual pulse on fleet cards
- Login page updated for username/password, observability branding
- Bump static `?v=` cache buster

Out of scope for this change: multi-user RBAC, Slack/Teams, encrypted secret vault, Docker.

## Data shape (`settings` additions)

```json
{
  "admin_password_hash": null,
  "setup_complete": true,
  "email": {
    "enabled": false,
    "smtp_host": "",
    "smtp_port": 587,
    "encryption": "starttls",
    "smtp_user": "",
    "smtp_password": "",
    "from_address": "",
    "recipients": []
  },
  "ai": {
    "api_key": "",
    "base_url": "https://integrate.api.nvidia.com/v1",
    "analysis_model": "",
    "chat_model": ""
  }
}
```

SMTP password and API key stored in `data.json` (VM-local trust model). Do not commit secrets to git.

## Testing (E2E)

1. Login with `admin` / `admin123`
2. Open Settings → both tabs render and save
3. Fetch models with valid key → dropdowns populate
4. Test email (with real SMTP if available; otherwise verify validation errors)
5. Simulate status transition → alert path called (unit/smoke); recovery path similarly
6. Helper chat uses chat model; failed check analysis uses analysis model
7. App runs on `:5050`

## Spec self-review

- [x] No unresolved placeholders
- [x] Decisions match chat (A recipients, B SMTP+test, B shared AI key, C transition+recovery, admin/admin123)
- [x] Scope excludes multi-tenant/RBAC
- [x] Checker must read previous result before overwrite (explicit)
- [x] PIN migration path defined
