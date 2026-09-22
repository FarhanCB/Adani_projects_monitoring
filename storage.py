"""JSON persistence for Ping Tester — single data.json in project root."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"
HISTORY_LIMIT = 20
DEFAULT_INTERVAL = 60
DEFAULT_TIMEOUT = 10

_lock = threading.RLock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_email_settings() -> dict[str, Any]:
    return {
        "enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "encryption": "starttls",
        "smtp_user": "",
        "smtp_password": "",
        "from_address": "",
        "recipients": [],
    }


def default_ai_settings() -> dict[str, Any]:
    return {
        "api_key": "",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "analysis_model": "",
        "chat_model": "",
    }


def _empty_store() -> dict[str, Any]:
    return {
        "settings": {
            "pin_hash": None,
            "admin_password_hash": None,
            "check_interval_seconds": DEFAULT_INTERVAL,
            "setup_complete": True,
            "chat_history": [],
            "email": default_email_settings(),
            "ai": default_ai_settings(),
        },
        "projects": [],
    }


def normalize_developers(raw: Any) -> list[dict[str, str]]:
    """Normalize developer list from form/API into [{name, email}]."""
    if not raw:
        return []
    if isinstance(raw, str):
        # "Name <a@b.com>, Name2 <c@d.com>"
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        out: list[dict[str, str]] = []
        for part in parts:
            if "<" in part and ">" in part:
                name = part.split("<", 1)[0].strip()
                email = part.split("<", 1)[1].split(">", 1)[0].strip()
            elif "@" in part:
                name = part.split("@", 1)[0].strip()
                email = part.strip()
            else:
                name, email = part, ""
            if name or email:
                out.append({"name": name, "email": email})
        return out
    if isinstance(raw, list):
        out = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            email = str(item.get("email") or "").strip()
            if name or email:
                out.append({"name": name, "email": email})
        return out
    return []


def developers_from_form(form: Any) -> list[dict[str, str]]:
    names = form.getlist("developer_name") if hasattr(form, "getlist") else []
    emails = form.getlist("developer_email") if hasattr(form, "getlist") else []
    out: list[dict[str, str]] = []
    for i in range(max(len(names), len(emails))):
        name = (names[i] if i < len(names) else "").strip()
        email = (emails[i] if i < len(emails) else "").strip()
        if name or email:
            out.append({"name": name, "email": email})
    return out


def services_from_form(form: Any) -> list[dict[str, Any]]:
    """Parse multi-service rows: service_name[], service_url[], expected, timeout."""
    if not hasattr(form, "getlist"):
        return []
    names = form.getlist("service_name")
    urls = form.getlist("service_url")
    expecteds = form.getlist("service_expected")
    timeouts = form.getlist("service_timeout")
    out: list[dict[str, Any]] = []
    for i in range(max(len(names), len(urls))):
        name = (names[i] if i < len(names) else "").strip()
        url = (urls[i] if i < len(urls) else "").strip()
        if not name and not url:
            continue
        expected_raw = (expecteds[i] if i < len(expecteds) else "200") or "200"
        timeout_raw = (timeouts[i] if i < len(timeouts) else "10") or "10"
        try:
            expected = int(expected_raw)
        except ValueError:
            expected = 200
        try:
            timeout = int(timeout_raw)
        except ValueError:
            timeout = DEFAULT_TIMEOUT
        out.append(
            {
                "name": name or url,
                "url": url,
                "expected_status": expected,
                "timeout_seconds": timeout,
            }
        )
    return out


def _normalize_project(project: dict[str, Any]) -> dict[str, Any]:
    project.setdefault("project_url", "")
    project.setdefault("description", "")
    project.setdefault("developers", [])
    project["developers"] = normalize_developers(project.get("developers"))
    for entry in project.get("urls") or []:
        entry.setdefault("last_analysis", None)
        entry.setdefault("history", [])
        entry.setdefault("enabled", True)
    return project


def load() -> dict[str, Any]:
    with _lock:
        if not DATA_FILE.exists():
            store = _empty_store()
            _write_unlocked(store)
            return store
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            store = json.load(f)
        store.setdefault("settings", {})
        settings = store["settings"]
        settings.setdefault("chat_history", [])
        settings.setdefault("admin_password_hash", None)
        settings.setdefault("setup_complete", True)
        settings["setup_complete"] = True
        email = settings.setdefault("email", default_email_settings())
        for key, value in default_email_settings().items():
            email.setdefault(key, value)
        ai = settings.setdefault("ai", default_ai_settings())
        for key, value in default_ai_settings().items():
            ai.setdefault(key, value)
        store.setdefault("projects", [])
        for project in store["projects"]:
            _normalize_project(project)
        return store


def save(store: dict[str, Any]) -> None:
    with _lock:
        _write_unlocked(store)


def _write_unlocked(store: dict[str, Any]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(DATA_FILE.parent), prefix=".data_", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_settings() -> dict[str, Any]:
    return load()["settings"]


def update_settings(**kwargs: Any) -> dict[str, Any]:
    with _lock:
        store = load()
        store["settings"].update(kwargs)
        _write_unlocked(store)
        return deepcopy(store["settings"])


def list_projects() -> list[dict[str, Any]]:
    return deepcopy(load()["projects"])


def get_project(project_id: str) -> dict[str, Any] | None:
    for project in load()["projects"]:
        if project["id"] == project_id:
            return deepcopy(project)
    return None


def create_project(
    name: str,
    description: str = "",
    project_url: str = "",
    developers: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    with _lock:
        store = load()
        project = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "project_url": (project_url or "").strip(),
            "description": description.strip(),
            "developers": normalize_developers(developers or []),
            "created_at": _utcnow(),
            "urls": [],
        }
        store["projects"].append(project)
        _write_unlocked(store)
        return deepcopy(project)


def update_project(
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    project_url: str | None = None,
    developers: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] == project_id:
                if name is not None:
                    project["name"] = name.strip()
                if description is not None:
                    project["description"] = description.strip()
                if project_url is not None:
                    project["project_url"] = project_url.strip()
                if developers is not None:
                    project["developers"] = normalize_developers(developers)
                _normalize_project(project)
                _write_unlocked(store)
                return deepcopy(project)
        return None


def delete_project(project_id: str) -> bool:
    with _lock:
        store = load()
        before = len(store["projects"])
        store["projects"] = [p for p in store["projects"] if p["id"] != project_id]
        if len(store["projects"]) == before:
            return False
        _write_unlocked(store)
        return True


def add_url(
    project_id: str,
    name: str,
    url: str,
    expected_status: int = 200,
    timeout_seconds: int = DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] == project_id:
                entry = {
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "url": url.strip(),
                    "expected_status": int(expected_status),
                    "timeout_seconds": int(timeout_seconds),
                    "enabled": True,
                    "last_result": None,
                    "last_analysis": None,
                    "history": [],
                }
                project["urls"].append(entry)
                _write_unlocked(store)
                return deepcopy(entry)
        return None


def update_url(project_id: str, url_id: str, **fields: Any) -> dict[str, Any] | None:
    allowed = {"name", "url", "expected_status", "timeout_seconds", "enabled"}
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] != project_id:
                continue
            for entry in project["urls"]:
                if entry["id"] != url_id:
                    continue
                for key, value in fields.items():
                    if key not in allowed:
                        continue
                    if key in ("name", "url") and isinstance(value, str):
                        entry[key] = value.strip()
                    elif key in ("expected_status", "timeout_seconds"):
                        entry[key] = int(value)
                    elif key == "enabled":
                        entry[key] = bool(value)
                    else:
                        entry[key] = value
                _write_unlocked(store)
                return deepcopy(entry)
        return None


def delete_url(project_id: str, url_id: str) -> bool:
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] != project_id:
                continue
            before = len(project["urls"])
            project["urls"] = [u for u in project["urls"] if u["id"] != url_id]
            if len(project["urls"]) == before:
                return False
            _write_unlocked(store)
            return True
        return False


def apply_check_result(
    project_id: str, url_id: str, result: dict[str, Any]
) -> dict[str, Any] | None:
    """Apply result; return previous last_result (if any) for transition alerts."""
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] != project_id:
                continue
            for entry in project["urls"]:
                if entry["id"] != url_id:
                    continue
                previous = deepcopy(entry.get("last_result")) if entry.get("last_result") else None
                entry["last_result"] = result
                history = entry.setdefault("history", [])
                history.insert(0, result)
                entry["history"] = history[:HISTORY_LIMIT]
                _write_unlocked(store)
                return previous
        return None


def apply_analysis(project_id: str, url_id: str, analysis: dict[str, Any]) -> None:
    with _lock:
        store = load()
        for project in store["projects"]:
            if project["id"] != project_id:
                continue
            for entry in project["urls"]:
                if entry["id"] != url_id:
                    continue
                entry["last_analysis"] = analysis
                _write_unlocked(store)
                return


def project_health(project: dict[str, Any]) -> dict[str, int]:
    urls = project.get("urls") or []
    enabled = [u for u in urls if u.get("enabled", True)]
    total = len(enabled)
    up = 0
    down = 0
    unknown = 0
    for entry in enabled:
        result = entry.get("last_result")
        if not result:
            unknown += 1
        elif result.get("ok"):
            up += 1
        else:
            down += 1
    return {"total": total, "up": up, "down": down, "unknown": unknown}


def all_enabled_targets() -> list[tuple[str, dict[str, Any]]]:
    """Return list of (project_id, url_entry) for enabled URLs."""
    targets: list[tuple[str, dict[str, Any]]] = []
    for project in load()["projects"]:
        for entry in project.get("urls") or []:
            if entry.get("enabled", True):
                targets.append((project["id"], deepcopy(entry)))
    return targets
