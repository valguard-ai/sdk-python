"""Verify inbound ValGuard webhook HMAC signatures."""

from __future__ import annotations

import hashlib
import hmac

WEBHOOK_SIGNATURE_HEADER = "X-VG-Signature"


def sign_webhook_payload(raw_body: bytes, secret: str) -> str:
    """Return `sha256=<hex>` HMAC-SHA256 over the raw request body bytes."""
    mac = hmac.new(secret.encode(), raw_body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def verify_webhook_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify `X-VG-Signature` on an inbound ValGuard webhook delivery."""
    if not signature_header or not secret:
        return False
    expected = sign_webhook_payload(raw_body, secret)
    return hmac.compare_digest(expected, signature_header)
