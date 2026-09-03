"""Parse ValGuard layer errors and soft-fail envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValGuardErrorInfo:
    type: str
    code: str | None
    message: str | None
    reason: str | None
    details: Any
    soft_fail: bool
    body: Any


class ValGuardError(Exception):
    def __init__(self, status: int, info: ValGuardErrorInfo) -> None:
        super().__init__(info.message or info.reason or f"ValGuard request failed ({status})")
        self.status = status
        self.info = info


def parse_valguard_error(status: int, body: Any) -> ValGuardErrorInfo | None:
    if not isinstance(body, dict):
        return None

    if body.get("valid") is False and body.get("validation") is not None:
        return ValGuardErrorInfo(
            type="validation_soft_fail",
            code=None,
            message="response failed validation (http 200 envelope)",
            reason=None,
            details=body.get("validation"),
            soft_fail=True,
            body=body,
        )

    error = body.get("error")
    if not isinstance(error, dict):
        return None

    err_type = error.get("type")
    return ValGuardErrorInfo(
        type=str(err_type) if err_type is not None else "unknown",
        code=error.get("code") if isinstance(error.get("code"), str) else None,
        message=error.get("message") if isinstance(error.get("message"), str) else None,
        reason=error.get("reason") if isinstance(error.get("reason"), str) else None,
        details=error.get("details"),
        soft_fail=False,
        body=body,
    )
