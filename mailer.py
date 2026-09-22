"""SMTP alert mailer for Ping Tester status transitions."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Any


def _email_settings(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    import storage

    raw = (settings or storage.get_settings()).get("email") or {}
    return {
        "enabled": bool(raw.get("enabled")),
        "smtp_host": (raw.get("smtp_host") or "").strip(),
        "smtp_port": int(raw.get("smtp_port") or 587),
        "encryption": (raw.get("encryption") or "starttls").strip().lower(),
        "smtp_user": (raw.get("smtp_user") or "").strip(),
        "smtp_password": raw.get("smtp_password") or "",
        "from_address": (raw.get("from_address") or "").strip(),
        "recipients": [
            e.strip()
            for e in (raw.get("recipients") or [])
            if isinstance(e, str) and e.strip()
        ],
    }


def email_ready(cfg: dict[str, Any] | None = None) -> tuple[bool, str]:
    cfg = cfg or _email_settings()
    if not cfg["smtp_host"]:
        return False, "SMTP host is required."
    if not cfg["from_address"]:
        return False, "From address is required."
    if not cfg["recipients"]:
        return False, "At least one recipient is required."
    return True, "ok"


def send_email(
    subject: str,
    body: str,
    *,
    to: list[str] | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = _email_settings(settings)
    recipients = to if to is not None else cfg["recipients"]
    recipients = [r.strip() for r in recipients if r and str(r).strip()]
    ok, reason = email_ready({**cfg, "recipients": recipients})
    if not ok:
        return {"ok": False, "error": reason}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["from_address"]
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)

    host = cfg["smtp_host"]
    port = cfg["smtp_port"]
    enc = cfg["encryption"]
    user = cfg["smtp_user"]
    password = cfg["smtp_password"]

    try:
        if enc == "ssl":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as smtp:
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.ehlo()
                if enc == "starttls":
                    context = ssl.create_default_context()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                if user:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return {"ok": True, "to": recipients}
    except Exception as exc:  # noqa: BLE001 — surface SMTP errors to UI
        return {"ok": False, "error": str(exc)}


def _label(result: dict[str, Any] | None) -> str:
    if not result:
        return "unknown"
    if result.get("ok"):
        return "ok"
    return (result.get("label") or "issue").lower()


def _is_bad(label: str) -> bool:
    return label in ("issue", "down")


def _format_failure_body(
    project: dict[str, Any],
    entry: dict[str, Any],
    result: dict[str, Any],
) -> str:
    analysis = entry.get("last_analysis") or {}
    lines = [
        f"Project: {project.get('name')}",
        f"Service: {entry.get('name')}",
        f"URL: {entry.get('url')}",
        f"Status: {(result.get('label') or 'issue').upper()}",
        f"Expected HTTP: {entry.get('expected_status', 200)}",
        f"Actual HTTP: {result.get('status_code')}",
        f"Message: {result.get('message')}",
        f"Latency (ms): {result.get('response_ms')}",
        f"Checked at (UTC): {result.get('checked_at')}",
    ]
    if analysis.get("summary"):
        lines.extend(
            [
                "",
                "Analyst summary:",
                str(analysis.get("summary")),
                f"Likely cause: {analysis.get('likely_cause') or '—'}",
            ]
        )
        steps = analysis.get("next_steps") or []
        if steps:
            lines.append("Next steps:")
            lines.extend(f"- {s}" for s in steps)
    lines.extend(["", "— Ping Tester"])
    return "\n".join(lines)


def _format_recovery_body(
    project: dict[str, Any],
    entry: dict[str, Any],
    result: dict[str, Any],
) -> str:
    return "\n".join(
        [
            f"Project: {project.get('name')}",
            f"Service: {entry.get('name')}",
            f"URL: {entry.get('url')}",
            "Status: RECOVERED (OK)",
            f"HTTP: {result.get('status_code')}",
            f"Latency (ms): {result.get('response_ms')}",
            f"Checked at (UTC): {result.get('checked_at')}",
            "",
            "— Ping Tester",
        ]
    )


def maybe_alert_on_transition(
    project: dict[str, Any],
    entry: dict[str, Any],
    previous: dict[str, Any] | None,
    new_result: dict[str, Any],
) -> dict[str, Any] | None:
    """Send mail only on ok/unknown → bad, or bad → ok. Never spam same state."""
    cfg = _email_settings()
    if not cfg.get("enabled"):
        return None
    ready, _ = email_ready(cfg)
    if not ready:
        return None

    prev = _label(previous)
    cur = _label(new_result)
    project_name = project.get("name") or "Project"

    if not _is_bad(prev) and _is_bad(cur):
        kind = "Down" if cur == "down" else "Issue"
        subject = f"{project_name} — {kind}"
        body = _format_failure_body(project, entry, new_result)
        return send_email(subject, body)

    if _is_bad(prev) and cur == "ok":
        subject = f"{project_name} — Recovered"
        body = _format_recovery_body(project, entry, new_result)
        return send_email(subject, body)

    return None
