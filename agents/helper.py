"""Helper agent — fast chat over Ping Tester snapshot (minimal round-trips)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

import storage
from agents.llm import agents_configured, get_llm, message_text

CHAT_LIMIT = 24

SYSTEM = """You are Helper for Ping Tester — a concise ops assistant.
Answer ONLY from the LIVE SNAPSHOT JSON provided in the user message.
Be short and practical. If something is down, mention error + Analyst cause + who to email.
Do not invent projects or statuses. If data is missing, say so briefly."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact_snapshot() -> dict[str, Any]:
    projects = []
    failures = []
    for project in storage.list_projects():
        health = storage.project_health(project)
        services = []
        for entry in project.get("urls") or []:
            result = entry.get("last_result")
            analysis = entry.get("last_analysis") or {}
            svc = {
                "name": entry.get("name"),
                "url": entry.get("url"),
                "enabled": entry.get("enabled", True),
                "status": (
                    "paused"
                    if not entry.get("enabled", True)
                    else (
                        "unknown"
                        if not result
                        else ("ok" if result.get("ok") else result.get("label") or "down")
                    )
                ),
                "message": (result or {}).get("message"),
                "ms": (result or {}).get("response_ms"),
            }
            if result and not result.get("ok") and analysis:
                svc["analysis"] = {
                    "summary": analysis.get("summary"),
                    "cause": analysis.get("likely_cause"),
                    "notify": analysis.get("notify") or [],
                }
                failures.append(
                    {
                        "project": project.get("name"),
                        "service": entry.get("name"),
                        "message": svc["message"],
                        "cause": analysis.get("likely_cause"),
                        "notify": analysis.get("notify")
                        or [d.get("email") for d in (project.get("developers") or []) if d.get("email")],
                    }
                )
            services.append(svc)
        projects.append(
            {
                "name": project.get("name"),
                "project_url": project.get("project_url"),
                "description": project.get("description"),
                "developers": project.get("developers") or [],
                "health": health,
                "services": services,
            }
        )
    return {"projects": projects, "failures": failures}


def get_chat_history() -> list[dict[str, str]]:
    settings = storage.get_settings()
    return list(settings.get("chat_history") or [])


def save_chat_history(history: list[dict[str, str]]) -> None:
    storage.update_settings(chat_history=history[-CHAT_LIMIT:])


def clear_chat_history() -> None:
    storage.update_settings(chat_history=[])


def chat(user_message: str) -> dict[str, Any]:
    message = (user_message or "").strip()
    if not message:
        return {"ok": False, "reply": "Please enter a question."}

    history = get_chat_history()
    history.append({"role": "user", "content": message, "at": _utcnow()})

    if not agents_configured():
        reply = (
            "Helper is offline — NVIDIA API key is not configured. "
            "Add NVIDIA_API_KEY to .env and restart."
        )
        history.append({"role": "assistant", "content": reply, "at": _utcnow()})
        save_chat_history(history)
        return {"ok": False, "reply": reply}

    try:
        snapshot = _compact_snapshot()
        # Keep payload small for speed
        snapshot_json = json.dumps(snapshot, ensure_ascii=False)
        if len(snapshot_json) > 12000:
            snapshot_json = snapshot_json[:12000] + "…"

        recent = []
        for item in history[-6:-1]:
            recent.append(f"{item['role']}: {item['content']}")
        recent_txt = "\n".join(recent) if recent else "(none)"

        prompt = (
            f"LIVE SNAPSHOT:\n{snapshot_json}\n\n"
            f"RECENT CHAT:\n{recent_txt}\n\n"
            f"USER QUESTION:\n{message}\n\n"
            "Answer in under 80 words unless listing multiple failures."
        )

        llm = get_llm(role="chat", temperature=0.1)
        ai = llm.invoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(content=prompt),
            ]
        )
        final_text = message_text(ai).strip()
        if not final_text:
            final_text = "No response generated. Try a shorter question."

        history.append({"role": "assistant", "content": final_text, "at": _utcnow()})
        save_chat_history(history)
        return {"ok": True, "reply": final_text}
    except Exception as exc:
        reply = f"Helper error: {exc}"
        history.append({"role": "assistant", "content": reply, "at": _utcnow()})
        save_chat_history(history)
        return {"ok": False, "reply": reply}
