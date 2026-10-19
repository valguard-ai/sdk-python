"""Parse ValGuard observability headers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

ValidationStatus = Literal["pass", "warn", "block", "shadow", "stream_passthrough", "fail"]

_VALIDATION_STATUSES = {"pass", "warn", "block", "shadow", "stream_passthrough", "fail"}


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
    healed: bool
    healed_rules: tuple[str, ...]
    healed_event_count: int | None
    healed_trace: tuple[str, ...]
    cache_status: str | None
    trace_id: str | None
    span_id: str | None
    parent_span_id: str | None
    agent_id: str | None
    idempotent_run_id: str | None
    run_id: str | None
    run_status: str | None
    approval_id: str | None
    license_status: str | None
    license_mode: str | None


def _header_get(headers: Mapping[str, str], name: str) -> str | None:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            if value is None or value == "":
                return None
            return value
    return None


def _split_csv(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _parse_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_validation_headers(headers: Mapping[str, str]) -> ValidationHeaders:
    status = _header_get(headers, "x-vg-validation-status")
    if status is not None:
        status = status.lower()
    validation_status: ValidationStatus | None
    if status in _VALIDATION_STATUSES:
        validation_status = status  # type: ignore[assignment]
    else:
        validation_status = None

    phase = _header_get(headers, "x-vg-validation-phase")
    validation_phase: Literal["input"] | None = "input" if phase == "input" else None

    remaining_raw = _header_get(headers, "x-vg-requests-remaining")
    orchestration_executions_remaining: int | Literal["unlimited"] | None
    if remaining_raw is None:
        orchestration_executions_remaining = None
    elif remaining_raw == "unlimited":
        orchestration_executions_remaining = "unlimited"
    else:
        orchestration_executions_remaining = _parse_int(remaining_raw)

    return ValidationHeaders(
        validation_status=validation_status,
        shadow_mode=_header_get(headers, "x-vg-shadow-mode") == "true",
        latency_ms=_parse_int(_header_get(headers, "x-vg-latency-ms")),
        request_id=_header_get(headers, "x-vg-request-id"),
        input_validation_shadow=_header_get(headers, "x-vg-input-validation") == "shadow",
        validation_phase=validation_phase,
        overage=_header_get(headers, "x-vg-overage") == "true",
        target_type=_header_get(headers, "x-vg-target-type"),
        orchestration_path=_header_get(headers, "x-vg-orchestration-path"),
        orchestration_validations_used=_parse_int(_header_get(headers, "x-vg-orchestration-validations-used")),
        orchestration_executions_remaining=orchestration_executions_remaining,
        idempotency_replayed=_header_get(headers, "x-vg-idempotency-replayed") == "true",
        healed=_header_get(headers, "x-vg-healed") == "true",
        healed_rules=_split_csv(_header_get(headers, "x-vg-healed-rules")),
        healed_event_count=_parse_int(_header_get(headers, "x-vg-healed-event-count")),
        healed_trace=_split_csv(_header_get(headers, "x-vg-healed-trace")),
        cache_status=_header_get(headers, "x-vg-cache"),
        trace_id=_header_get(headers, "x-trace-id"),
        span_id=_header_get(headers, "x-vg-span-id"),
        parent_span_id=_header_get(headers, "x-vg-parent-span-id"),
        agent_id=_header_get(headers, "x-vg-agent-id"),
        idempotent_run_id=_header_get(headers, "x-vg-idempotent-run-id"),
        run_id=_header_get(headers, "x-vg-run-id"),
        run_status=_header_get(headers, "x-vg-run-status"),
        approval_id=_header_get(headers, "x-vg-approval-id"),
        license_status=_header_get(headers, "x-vg-license-status"),
        license_mode=_header_get(headers, "x-vg-license-mode"),
    )
