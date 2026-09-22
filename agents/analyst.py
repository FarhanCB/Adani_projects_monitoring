"""Analyst agent — diagnoses failed URL checks."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.llm import agents_configured, get_llm, message_text

SYSTEM = """You are the Analyst agent for Ping Tester, an HTTP uptime monitor.
Given a failed check, project metadata, and owners, produce a concise operational diagnosis.
Respond with ONLY valid JSON (no markdown) using this schema:
{
  "summary": "one sentence",
  "likely_cause": "short cause",
  "next_steps": ["step1", "step2", "step3"],
  "notify": ["email@example.com"]
}
Use developer emails in notify when relevant. Be practical and brief."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group(0))
        raise


def analyze_failure(
    project: dict[str, Any],
    entry: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    """Run Analyst on a failed check; returns last_analysis payload."""
    if not agents_configured():
        return {
            "summary": "Analyst unavailable — NVIDIA API key not configured.",
            "likely_cause": "Missing API key",
            "next_steps": ["Add NVIDIA_API_KEY to .env and restart the app."],
            "notify": [],
            "analyzed_at": _utcnow(),
            "based_on_checked_at": result.get("checked_at"),
            "error": "not_configured",
        }

    developers = project.get("developers") or []
    history = (entry.get("history") or [])[:8]
    payload = {
        "project": {
            "name": project.get("name"),
            "project_url": project.get("project_url"),
            "description": project.get("description"),
            "developers": developers,
        },
        "endpoint": {
            "name": entry.get("name"),
            "url": entry.get("url"),
            "expected_status": entry.get("expected_status"),
            "timeout_seconds": entry.get("timeout_seconds"),
        },
        "failure": result,
        "recent_history": history,
    }

    try:
        llm = get_llm(role="analysis", temperature=0.1, max_tokens=220)
        response = llm.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=json.dumps(payload, ensure_ascii=False)),
            ]
        )
        data = _extract_json(message_text(response) or "{}")
        notify = data.get("notify") or [
            d.get("email") for d in developers if d.get("email")
        ]
        steps = data.get("next_steps") or []
        if isinstance(steps, str):
            steps = [steps]
        return {
            "summary": str(data.get("summary") or "Failure analyzed."),
            "likely_cause": str(data.get("likely_cause") or "Unknown"),
            "next_steps": [str(s) for s in steps][:6],
            "notify": [str(e) for e in notify if e][:10],
            "analyzed_at": _utcnow(),
            "based_on_checked_at": result.get("checked_at"),
        }
    except Exception as exc:
        emails = [d.get("email") for d in developers if d.get("email")]
        return {
            "summary": "Analyst could not complete diagnosis.",
            "likely_cause": result.get("message") or "Check failed",
            "next_steps": [
                "Retry the endpoint manually.",
                "Verify DNS, TLS, and service process.",
                "Contact project developers if it persists.",
            ],
            "notify": emails,
            "analyzed_at": _utcnow(),
            "based_on_checked_at": result.get("checked_at"),
            "error": str(exc)[:200],
        }
