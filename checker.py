"""HTTP status checker for monitored URLs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

import mailer
import storage


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_url(entry: dict[str, Any]) -> dict[str, Any]:
    url = entry["url"]
    expected = int(entry.get("expected_status", 200))
    timeout = float(entry.get("timeout_seconds", 10))
    started = datetime.now(timezone.utc)

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "PingTester/1.0"},
        )
        elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        code = response.status_code
        ok = code == expected
        if ok:
            message = "OK"
            label = "ok"
        else:
            reason = response.reason or "Unexpected status"
            message = f"Expected {expected}, got {code} ({reason})"
            label = "issue"
        return {
            "ok": ok,
            "label": label,
            "status_code": code,
            "message": message,
            "response_ms": elapsed_ms,
            "checked_at": _utcnow(),
        }
    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "label": "down",
            "status_code": None,
            "message": "Service down — request timed out",
            "response_ms": int(timeout * 1000),
            "checked_at": _utcnow(),
        }
    except requests.exceptions.ConnectionError as exc:
        detail = str(exc.__cause__ or exc)
        if len(detail) > 160:
            detail = detail[:157] + "..."
        return {
            "ok": False,
            "label": "down",
            "status_code": None,
            "message": f"Service down — {detail}" if detail else "Service down",
            "response_ms": None,
            "checked_at": _utcnow(),
        }
    except requests.exceptions.RequestException as exc:
        detail = str(exc)
        if len(detail) > 160:
            detail = detail[:157] + "..."
        return {
            "ok": False,
            "label": "down",
            "status_code": None,
            "message": f"Service down — {detail}" if detail else "Service down",
            "response_ms": None,
            "checked_at": _utcnow(),
        }


def _maybe_analyze(project_id: str, entry: dict[str, Any], result: dict[str, Any]) -> None:
    if result.get("ok"):
        return
    try:
        from agents.analyst import analyze_failure

        project = storage.get_project(project_id)
        if not project:
            return
        fresh = next((u for u in project["urls"] if u["id"] == entry["id"]), entry)
        analysis = analyze_failure(project, fresh, result)
        storage.apply_analysis(project_id, entry["id"], analysis)
    except Exception:
        pass


def _maybe_alert(
    project_id: str,
    entry: dict[str, Any],
    previous: dict[str, Any] | None,
    result: dict[str, Any],
) -> None:
    try:
        project = storage.get_project(project_id)
        if not project:
            return
        fresh = next((u for u in project["urls"] if u["id"] == entry["id"]), entry)
        mailer.maybe_alert_on_transition(project, fresh, previous, result)
    except Exception:
        pass


def run_single(project_id: str, url_id: str) -> dict[str, Any] | None:
    project = storage.get_project(project_id)
    if not project:
        return None
    entry = next((u for u in project["urls"] if u["id"] == url_id), None)
    if not entry:
        return None
    result = check_url(entry)
    previous = storage.apply_check_result(project_id, url_id, result)
    _maybe_analyze(project_id, entry, result)
    _maybe_alert(project_id, entry, previous, result)
    return result


def run_project(project_id: str) -> list[dict[str, Any]]:
    project = storage.get_project(project_id)
    if not project:
        return []
    results = []
    for entry in project.get("urls") or []:
        if not entry.get("enabled", True):
            continue
        result = check_url(entry)
        previous = storage.apply_check_result(project_id, entry["id"], result)
        _maybe_analyze(project_id, entry, result)
        _maybe_alert(project_id, entry, previous, result)
        results.append({"url_id": entry["id"], "result": result})
    return results


def run_all() -> int:
    count = 0
    for project_id, entry in storage.all_enabled_targets():
        result = check_url(entry)
        previous = storage.apply_check_result(project_id, entry["id"], result)
        _maybe_analyze(project_id, entry, result)
        _maybe_alert(project_id, entry, previous, result)
        count += 1
    return count
