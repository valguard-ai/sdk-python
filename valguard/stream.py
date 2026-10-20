"""Parse OpenAI-style chat completion SSE streams."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from typing import Any


def _parse_sse_part(part: str) -> dict[str, Any] | None:
    data_line = ""
    for line in part.split("\n"):
        if line.startswith("data:"):
            data_line += line[5:].lstrip()
    payload = data_line.strip()
    if not payload:
        return None
    if payload == "[DONE]":
        return {"type": "done"}
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return {"type": "raw", "raw": payload}
    choice = (parsed.get("choices") or [{}])[0]
    delta = choice.get("delta") or {}
    return {
        "type": "chunk",
        "id": parsed.get("id"),
        "model": parsed.get("model"),
        "delta": {
            "role": delta.get("role"),
            "content": delta.get("content"),
            "tool_calls": delta.get("tool_calls"),
        },
        "finish_reason": choice.get("finish_reason"),
        "usage": parsed.get("usage"),
    }


def iter_chat_completion_stream(lines: Iterator[str]) -> Iterator[dict[str, Any]]:
    """Iterate parsed events from newline-delimited SSE text (tests / sync callers)."""
    buffer = ""
    for chunk in lines:
        buffer += chunk
        while "\n\n" in buffer:
            part, buffer = buffer.split("\n\n", 1)
            event = _parse_sse_part(part)
            if event:
                yield event
    if buffer.strip():
        event = _parse_sse_part(buffer)
        if event:
            yield event


async def parse_chat_completion_stream(body: Any) -> AsyncIterator[dict[str, Any]]:
    """Async iterator over parsed SSE events from an httpx/ aiohttp stream body."""
    buffer = ""
    async for chunk in body:
        if isinstance(chunk, bytes):
            text = chunk.decode("utf-8", errors="replace")
        else:
            text = str(chunk)
        buffer += text
        while "\n\n" in buffer:
            part, buffer = buffer.split("\n\n", 1)
            event = _parse_sse_part(part)
            if event:
                yield event
    if buffer.strip():
        event = _parse_sse_part(buffer)
        if event:
            yield event
