"""Shared PIN authentication helpers."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import storage

ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_credentials(username: str, password: str) -> bool:
    if (username or "").strip() != ADMIN_USERNAME:
        return False
    settings = storage.get_settings()
    stored = settings.get("admin_password_hash")
    if stored:
        return check_password_hash(stored, password)
    return password == DEFAULT_ADMIN_PASSWORD


def is_setup_complete() -> bool:
    # Admin credentials are built-in; no PIN bootstrap required.
    return True


def set_admin_password(password: str) -> None:
    storage.update_settings(admin_password_hash=hash_password(password), setup_complete=True)


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


# Backwards-compatible aliases (PIN era)
def hash_pin(pin: str) -> str:
    return hash_password(pin)


def verify_pin(pin: str) -> bool:
    return verify_credentials(ADMIN_USERNAME, pin)


def set_pin(pin: str) -> None:
    set_admin_password(pin)
