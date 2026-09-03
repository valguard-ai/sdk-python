"""Parse ValGuard observability headers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

ValidationStatus = Literal["pass", "warn", "block", "shadow"]


@dataclass(frozen=True)
class ValidationHeaders:
    validation_status: ValidationStatus | None
    shadow_mode: bool
    latency_ms: int | None
    request_id: str | None
    input_validation_shadow: bool
    validation_phase: Literal["input"] | None
    overage: bool
    target_type: str | None
    orchestration_path: str | None
    orchestration_validations_used: int | None
    orchestration_executions_remaining: int | Literal["unlimited"] | None
    idempotency_replayed: bool


def _header_get(headers: Mapping[str, str], name: str) -> str | None:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return value
    return None


def parse_validation_headers(headers: Mapping[str, str]) -> ValidationHeaders:
    latency_raw = _header_get(headers, "x-vg-latency-ms")
    latency_ms: int | None
    try:
        latency_ms = int(latency_raw) if latency_raw is not None else None
    except ValueError:
        latency_ms = None

    status = _header_get(headers, "x-vg-validation-status")
    validation_status: ValidationStatus | None
    if status in ("pass", "warn", "block", "shadow"):
        validation_status = status
    else:
        validation_status = None

    phase = _header_get(headers, "x-vg-validation-phase")
    validation_phase: Literal["input"] | None = "input" if phase == "input" else None

    remaining_raw = _header_get(headers, "x-vg-orchestration-executions-remaining")
    orchestration_executions_remaining: int | Literal["unlimited"] | None
    if remaining_raw is None:
        orchestration_executions_remaining = None
    elif remaining_raw == "unlimited":
        orchestration_executions_remaining = "unlimited"
    else:
        try:
            orchestration_executions_remaining = int(remaining_raw)
        except ValueError:
            orchestration_executions_remaining = None

    validations_used_raw = _header_get(headers, "x-vg-orchestration-validations-used")
    orchestration_validations_used: int | None
    try:
        orchestration_validations_used = int(validations_used_raw) if validations_used_raw is not None else None
    except ValueError:
        orchestration_validations_used = None

    return ValidationHeaders(
        validation_status=validation_status,
        shadow_mode=_header_get(headers, "x-vg-shadow-mode") == "true",
        latency_ms=latency_ms,
        request_id=_header_get(headers, "x-vg-request-id"),
        input_validation_shadow=_header_get(headers, "x-vg-input-validation") == "shadow",
        validation_phase=validation_phase,
        overage=_header_get(headers, "x-vg-overage") == "true",
        target_type=_header_get(headers, "x-vg-target-type"),
        orchestration_path=_header_get(headers, "x-vg-orchestration-path"),
        orchestration_validations_used=orchestration_validations_used,
        orchestration_executions_remaining=orchestration_executions_remaining,
        idempotency_replayed=_header_get(headers, "x-vg-idempotency-replayed") == "true",
    )
