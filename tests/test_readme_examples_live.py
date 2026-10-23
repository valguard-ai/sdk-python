"""Live README examples against the default agent (optional CI job with secrets)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

import pytest

PROMPT = "Return JSON with name Ada Lovelace and email ada@example.com for a demo contact."


def _skip_unless_live() -> None:
    if not (os.environ.get("VG_API_KEY") or os.environ.get("VALGUARD_API_KEY")):
        pytest.skip("VG_API_KEY not set")
    if not os.environ.get("VG_PROVIDER_KEY"):
        pytest.skip("VG_PROVIDER_KEY not set")


def _post(payload: dict) -> None:
    base = (os.environ.get("VG_PROXY") or os.environ.get("VALGUARD_BASE_URL") or "https://api.valguard.ai").rstrip(
        "/"
    )
    api_key = os.environ.get("VG_API_KEY") or os.environ.get("VALGUARD_API_KEY") or ""
    provider_key = os.environ.get("VG_PROVIDER_KEY") or ""
    agent = os.environ.get("VG_AGENT") or "default"
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-VG-Agent": agent,
            "X-Provider-Key": provider_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            assert resp.status == 200
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        pytest.fail(f"HTTP {exc.code}: {body}")


def test_readme_non_stream_example() -> None:
    _skip_unless_live()
    _post(
        {
            "model": "groq/openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": PROMPT}],
        }
    )


def test_readme_stream_example() -> None:
    _skip_unless_live()
    _post(
        {
            "model": "groq/openai/gpt-oss-20b",
            "stream": True,
            "messages": [{"role": "user", "content": PROMPT}],
        }
    )
