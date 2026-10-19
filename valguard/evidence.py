"""Offline HMAC verification for ValGuard evidence envelopes.

Matches `valguard-cli verify-proof` and the proxy signer: org key is
HMAC-SHA256(secret, key_id), signature is `sha256=` + HMAC-SHA256(org key, payload).
The payload string is verified as stored. Do not re-serialize the envelope.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Mapping

EVIDENCE_TYP = "valguard-evidence/1"


def verify_evidence(key_id: str, payload: str, signature: str, secret: str) -> bool:
    """Return true when `signature` matches HMAC over the exact payload bytes."""
    if not key_id or not payload or not signature or not secret:
        return False
    org_key = hmac.new(secret.encode(), key_id.encode(), hashlib.sha256).digest()
    expected = "sha256=" + hmac.new(org_key, payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def verify_proof(envelope: str | Mapping[str, Any], secret: str) -> bool:
    """Verify a downloaded envelope object or its JSON text.

    Requires `key_id`, `payload`, and `signature`. The caller supplies the
    deployment secret (`EVIDENCE_HMAC_SECRET`, or the webhook secret when that
    is the fallback). This does not call the API.
    """
    record: Any
    if isinstance(envelope, str):
        try:
            record = json.loads(envelope)
        except json.JSONDecodeError:
            return False
    else:
        record = envelope
    if not isinstance(record, Mapping):
        return False
    return verify_evidence(
        str(record.get("key_id") or ""),
        str(record.get("payload") or ""),
        str(record.get("signature") or ""),
        secret,
    )
