"""Shared NVIDIA NIM / LangChain LLM client with role-based models."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

_API_TXT = ROOT / "NVidiaAPI.txt"
DEFAULT_MODEL = "poolside/laguna-xs-2.1"
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

Role = Literal["analysis", "chat"]


def _ai_from_storage() -> dict[str, Any]:
    try:
        import storage

        return dict(storage.get_settings().get("ai") or {})
    except Exception:
        return {}


def get_api_key() -> str | None:
    stored = (_ai_from_storage().get("api_key") or "").strip()
    if stored:
        return stored
    key = (os.getenv("NVIDIA_API_KEY") or "").strip()
    if key:
        return key
    if _API_TXT.exists():
        return _API_TXT.read_text(encoding="utf-8").strip() or None
    return None


def get_base_url() -> str:
    stored = (_ai_from_storage().get("base_url") or "").strip()
    if stored:
        return stored.rstrip("/")
    return (os.getenv("NVIDIA_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")


def get_model_name(role: Role | str = "chat") -> str:
    ai = _ai_from_storage()
    if role == "analysis":
        model = (ai.get("analysis_model") or "").strip()
    else:
        model = (ai.get("chat_model") or "").strip()
    if model:
        return model
    # Shared fallback: either stored model field or env
    shared = (ai.get("model") or "").strip()
    if shared:
        return shared
    return (os.getenv("NVIDIA_MODEL") or DEFAULT_MODEL).strip()


def agents_configured() -> bool:
    return bool(get_api_key())


def message_text(message: Any) -> str:
    """Extract usable text from OpenAI / reasoning-style responses."""
    content = getattr(message, "content", None)
    text = ""
    if isinstance(content, str) and content.strip():
        text = content.strip()
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                chunk = block.get("text") or block.get("content")
                if chunk:
                    parts.append(str(chunk))
            else:
                chunk = getattr(block, "text", None)
                if chunk:
                    parts.append(str(chunk))
        text = "\n".join(parts).strip()

    if not text:
        extra = getattr(message, "additional_kwargs", None) or {}
        for key in ("reasoning_content", "reasoning", "refusal"):
            val = extra.get(key)
            if isinstance(val, str) and val.strip():
                lines = [ln.strip() for ln in val.strip().splitlines() if ln.strip()]
                if lines:
                    text = lines[-1]
                    break

    return _clean_model_text(text)


def _clean_model_text(text: str) -> str:
    """Strip common reasoning wrappers some NIM models append."""
    if not text:
        return ""
    import re

    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.I)
    cleaned = re.sub(r"</?answer>", "", cleaned, flags=re.I)
    cleaned = cleaned.strip()
    if "</think>" in text.lower() and cleaned:
        parts = [p.strip() for p in re.split(r"\n{2,}", cleaned) if p.strip()]
        if parts:
            return parts[-1]
    return cleaned


@lru_cache(maxsize=8)
def get_llm(
    role: str = "chat",
    temperature: float = 0.2,
    max_tokens: int = 256,
) -> ChatOpenAI:
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "API key missing. Set it in Settings → AI Config or NVIDIA_API_KEY in .env"
        )
    return ChatOpenAI(
        api_key=api_key,
        base_url=get_base_url(),
        model=get_model_name(role),  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=45,
    )


def reset_llm_cache() -> None:
    get_llm.cache_clear()


def list_models(
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[str]:
    key = (api_key or get_api_key() or "").strip()
    if not key:
        raise RuntimeError("API key required to list models.")
    base = (base_url or get_base_url()).strip().rstrip("/")
    response = requests.get(
        f"{base}/models",
        headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    ids: list[str] = []
    for item in payload.get("data") or []:
        mid = item.get("id") if isinstance(item, dict) else None
        if mid:
            ids.append(str(mid))
    return sorted(set(ids), key=str.lower)
