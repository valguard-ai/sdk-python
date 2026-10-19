from valguard.errors import parse_valguard_error
from valguard.headers import parse_validation_headers


def test_parse_validation_headers() -> None:
    parsed = parse_validation_headers(
        {
            "X-VG-Validation-Status": "shadow",
            "X-VG-Shadow-Mode": "true",
            "X-VG-Latency-ms": "12",
            "X-VG-Request-Id": "abc-123",
        }
    )
    assert parsed.validation_status == "shadow"
    assert parsed.shadow_mode is True
    assert parsed.latency_ms == 12
    assert parsed.request_id == "abc-123"


def test_parse_orchestration_headers() -> None:
    parsed = parse_validation_headers(
        {
            "X-VG-Target-Type": "playbook",
            "X-VG-Orchestration-Path": "a,b,c",
            "X-VG-Orchestration-Validations-Used": "5",
            "X-VG-Requests-Remaining": "unlimited",
            "X-VG-Idempotency-Replayed": "true",
        }
    )
    assert parsed.target_type == "playbook"
    assert parsed.orchestration_path == "a,b,c"
    assert parsed.orchestration_validations_used == 5
    assert parsed.orchestration_executions_remaining == "unlimited"
    assert parsed.idempotency_replayed is True


def test_parse_repair_trace_and_run_headers() -> None:
    parsed = parse_validation_headers(
        {
            "X-VG-Validation-Status": "stream_passthrough",
            "X-VG-Healed": "true",
            "X-VG-Healed-Rules": "tier1:trim_whitespace,tier2:enum_normalize",
            "X-VG-Healed-Event-Count": "2",
            "X-VG-Healed-Trace": "tier1:trim_whitespace@_,tier2:enum_normalize@status",
            "X-VG-Cache": "cache_hit",
            "X-Trace-Id": "trace-1",
            "X-VG-Span-Id": "span-1",
            "X-VG-Parent-Span-Id": "parent-1",
            "X-VG-Agent-Id": "billing-agent",
            "X-VG-Run-Id": "run-1",
            "X-VG-Run-Status": "waiting_approval",
            "X-VG-Approval-Id": "appr-1",
            "X-VG-License-Status": "valid",
            "X-VG-License-Mode": "enforce",
        }
    )
    assert parsed.validation_status == "stream_passthrough"
    assert parsed.healed is True
    assert parsed.healed_rules == ("tier1:trim_whitespace", "tier2:enum_normalize")
    assert parsed.healed_event_count == 2
    assert parsed.healed_trace == ("tier1:trim_whitespace@_", "tier2:enum_normalize@status")
    assert parsed.cache_status == "cache_hit"
    assert parsed.trace_id == "trace-1"
    assert parsed.span_id == "span-1"
    assert parsed.parent_span_id == "parent-1"
    assert parsed.agent_id == "billing-agent"
    assert parsed.run_id == "run-1"
    assert parsed.run_status == "waiting_approval"
    assert parsed.approval_id == "appr-1"
    assert parsed.license_status == "valid"
    assert parsed.license_mode == "enforce"


def test_unknown_validation_status_is_dropped() -> None:
    parsed = parse_validation_headers({"X-VG-Validation-Status": "reasked_ok"})
    assert parsed.validation_status is None


def test_request_headers_for_approval_and_trace() -> None:
    from valguard.client import ValGuardClient

    client = ValGuardClient(
        api_key="vg_test",
        base_url="https://api.example.com",
        agent_slug="",
        flow_slug="invoice-processing",
        provider_key="sk-up",
    ).with_idempotency_key("idem-1").with_approval_mode("async").with_trace(
        traceparent="00-abc-def-01",
        parent_span_id="parent",
        agent_id="billing-agent",
    )
    headers = client.build_headers()
    assert headers["X-VG-Flow"] == "invoice-processing"
    assert "X-VG-Agent" not in headers
    assert headers["X-VG-Idempotency-Key"] == "idem-1"
    assert headers["X-VG-Approval-Mode"] == "async"
    assert headers["traceparent"] == "00-abc-def-01"
    assert headers["X-VG-Parent-Span-Id"] == "parent"
    assert headers["X-VG-Agent-Id"] == "billing-agent"
    assert headers["X-Provider-Key"] == "sk-up"
    openai = client.openai_client_kwargs()
    assert "Authorization" not in openai["default_headers"]
    assert openai["default_headers"]["X-VG-Approval-Mode"] == "async"
    assert openai["default_headers"]["X-Provider-Key"] == "sk-up"


def test_parse_soft_fail() -> None:
    info = parse_valguard_error(
        200,
        {"valid": False, "validation": {"status": "block", "failures": []}},
    )
    assert info is not None
    assert info.soft_fail is True


def test_parse_validation_block() -> None:
    info = parse_valguard_error(
        403,
        {"error": {"type": "validation_block", "reason": "required_fields", "message": "blocked"}},
    )
    assert info is not None
    assert info.type == "validation_block"


if __name__ == "__main__":
    test_parse_validation_headers()
    test_parse_orchestration_headers()
    test_parse_repair_trace_and_run_headers()
    test_unknown_validation_status_is_dropped()
    test_request_headers_for_approval_and_trace()
    test_parse_soft_fail()
    test_parse_validation_block()
    print("sdk-python tests: ok")
