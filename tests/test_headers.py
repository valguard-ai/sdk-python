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
            "X-VG-Orchestration-Executions-Remaining": "unlimited",
            "X-VG-Idempotency-Replayed": "true",
        }
    )
    assert parsed.target_type == "playbook"
    assert parsed.orchestration_path == "a,b,c"
    assert parsed.orchestration_validations_used == 5
    assert parsed.orchestration_executions_remaining == "unlimited"
    assert parsed.idempotency_replayed is True


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
    test_parse_soft_fail()
    test_parse_validation_block()
    print("sdk-python tests: ok")
