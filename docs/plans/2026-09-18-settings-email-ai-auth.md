# Settings Email AI Auth Implementation Plan

> **For Claude:** Execute task-by-task; verify after each logical group.

**Goal:** Admin login, Settings Email/AI tabs, SMTP alerts on transitions+recovery, shared AI key with separate models, live UI polish.

**Architecture:** Persist config in `data.json`; `mailer.py` for SMTP; extend `agents/llm.py` for role-based models + `/models` fetch; wire alerts in `checker.py`.

**Tech Stack:** Flask, APScheduler, requests, smtplib, langchain-openai, Chart.js/Lucide UI

---

### Task 1: Storage defaults for email + AI + admin hash
### Task 2: Auth → admin/admin123 (hashed override optional)
### Task 3: mailer.py + checker transition hooks
### Task 4: llm.py role models + list_models
### Task 5: Settings routes + tabbed UI + APIs
### Task 6: Login/setup/live UI polish
### Task 7: Run app and E2E smoke tests
