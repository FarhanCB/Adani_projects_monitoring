"""Azure OpenAI client that shells out to the system `curl` binary.

On the secured Adani VM, Python's HTTP libraries (requests/httpx, used by
`requests` and by langchain-openai) can't complete TLS to the internal
Azure OpenAI endpoint — the VM's certificate trust / proxy setup isn't one
Python's bundled CA store (certifi) trusts. The system `curl.exe` (Windows
10+, Schannel backend) uses the OS certificate store instead and works.
So for the Azure provider we call curl as a subprocess rather than using
an HTTP client library, matching the known-working setup on that VM.

Config comes entirely from environment variables (see .env.example):
    LLM_PROVIDER=azure
    AZURE_OPENAI_KEY=...
    AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
    AZURE_OPENAI_DEPLOYMENT=<deployment-name>
    AZURE_OPENAI_API_VERSION=2023-12-01-preview
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any

CURL_TIMEOUT_SECONDS = 45


def _azure_config() -> dict[str, str]:
    return {
        "key": (os.getenv("AZURE_OPENAI_KEY") or "").strip(),
        "endpoint": (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip().rstrip("/"),
        "deployment": (os.getenv("AZURE_OPENAI_DEPLOYMENT") or "").strip(),
        "api_version": (os.getenv("AZURE_OPENAI_API_VERSION") or "2023-12-01-preview").strip(),
    }


def azure_configured() -> bool:
    cfg = _azure_config()
    return bool(cfg["key"] and cfg["endpoint"] and cfg["deployment"])


def get_deployment_name() -> str:
    return _azure_config()["deployment"]


def _to_azure_messages(messages: list[Any]) -> list[dict[str, str]]:
    """Convert LangChain-style message objects (SystemMessage/HumanMessage/...)
    into the {"role": ..., "content": ...} shape Azure's Chat Completions API
    expects."""
    role_map = {"system": "system", "human": "user", "ai": "assistant"}
    out = []
    for m in messages:
        role = role_map.get(getattr(m, "type", "human"), "user")
        content = getattr(m, "content", None)
        out.append({"role": role, "content": content if isinstance(content, str) else str(content)})
    return out


def _call_azure_curl(
    messages: list[Any],
    temperature: float = 0.2,
    max_tokens: int = 256,
) -> str:
    cfg = _azure_config()
    if not azure_configured():
        raise RuntimeError(
            "Azure OpenAI not configured. Set AZURE_OPENAI_KEY, "
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT in .env"
        )

    url = (
        f"{cfg['endpoint']}/openai/deployments/{cfg['deployment']}"
        f"/chat/completions?api-version={cfg['api_version']}"
    )

    body = {
        "messages": _to_azure_messages(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Payload goes into a temp file (curl --data-binary @file) rather than
    # directly on the command line, mainly to avoid shell/length quirks
    # with large prompts; the api-key still has to go through -H since
    # curl has no other way to set a header value.
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            json.dump(body, tmp, ensure_ascii=False)
            tmp_path = tmp.name

        result = subprocess.run(
            [
                "curl",
                "-s",
                "-S",
                "--max-time",
                str(CURL_TIMEOUT_SECONDS),
                "-X",
                "POST",
                url,
                "-H",
                "Content-Type: application/json",
                "-H",
                f"api-key: {cfg['key']}",
                "--data-binary",
                f"@{tmp_path}",
            ],
            capture_output=True,
            text=True,
            timeout=CURL_TIMEOUT_SECONDS + 5,
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if result.returncode != 0:
        raise RuntimeError(
            f"curl failed (exit {result.returncode}): {result.stderr.strip() or 'no error output'}"
        )

    raw = (result.stdout or "").strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError(f"Azure OpenAI returned a non-JSON response: {raw[:300]}")

    if isinstance(payload, dict) and payload.get("error"):
        err = payload["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        raise RuntimeError(f"Azure OpenAI error: {msg}")

    try:
        return payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected Azure OpenAI response shape: {json.dumps(payload)[:300]}")


class _AzureAIMessage:
    """Minimal stand-in for a LangChain AIMessage — just enough surface
    (`.content`, `.additional_kwargs`) for agents/llm.py's message_text()."""

    def __init__(self, content: str):
        self.content = content
        self.additional_kwargs: dict[str, Any] = {}


class AzureCurlChat:
    """Drop-in replacement for langchain's ChatOpenAI, backed by curl.

    Exposes the same `.invoke(messages) -> message` surface used by
    agents/analyst.py and agents/helper.py, so those files don't need to
    know which provider is active.
    """

    def __init__(self, temperature: float = 0.2, max_tokens: int = 256):
        self.temperature = temperature
        self.max_tokens = max_tokens

    def invoke(self, messages: list[Any]) -> _AzureAIMessage:
        content = _call_azure_curl(messages, self.temperature, self.max_tokens)
        return _AzureAIMessage(content)
