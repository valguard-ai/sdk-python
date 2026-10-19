"""Verify inbound ValGuard webhook HMAC signatures."""

from __future__ import annotations

import hashlib
import hmac
import time

WEBHOOK_SIGNATURE_HEADER = "X-VG-Signature"


def _as_bytes(raw_body: bytes | str) -> bytes:
    if isinstance(raw_body, str):
        return raw_body.encode("utf-8")
    if isinstance(raw_body, (bytes, bytearray)):
        return bytes(raw_body)
    raise TypeError("raw_body must be str or bytes")


def sign_webhook_payload(raw_body: bytes | str, secret: str, unix: int | None = None) -> str:
    """Return `t=<unix>,v1=<hex>` HMAC-SHA256 over `<unix>.<raw body>`."""
    body = _as_bytes(raw_body)
    ts = int(time.time()) if unix is None else int(unix)
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256)
    return f"t={ts},v1={mac.hexdigest()}"


def verify_webhook_signature(
    raw_body: bytes | str,
    signature_header: str | None,
    secret: str,
    max_age_seconds: int | None = 300,
) -> bool:
    """Verify `X-VG-Signature`. Accepts str or bytes bodies and legacy `sha256=` signatures."""
    if not signature_header or not secret:
        return False
    try:
        body = _as_bytes(raw_body)
    except TypeError:
        return False
    header = signature_header.strip()
    if header.startswith("t=") and ",v1=" in header:
        try:
            stamp, hex_sig = header.split(",v1=", 1)
            unix = int(stamp[2:])
        except ValueError:
            return False
        if max_age_seconds is not None and abs(int(time.time()) - unix) > max_age_seconds:
            return False
        expected = sign_webhook_payload(body, secret, unix)
        return hmac.compare_digest(expected, f"t={unix},v1={hex_sig}")
    if header.startswith("sha256="):
        mac = hmac.new(secret.encode(), body, hashlib.sha256)
        expected = f"sha256={mac.hexdigest()}"
        return hmac.compare_digest(expected, header)
    return False
