from valguard.webhook import (
    WEBHOOK_SIGNATURE_HEADER,
    sign_webhook_payload,
    verify_webhook_signature,
)

CONTRACT_SECRET = "contract-test-webhook-secret"
CONTRACT_BODY = b'{"event":"validation.block","request_id":"abc"}'
CONTRACT_SIG = sign_webhook_payload(CONTRACT_BODY, CONTRACT_SECRET, 1700000000)


def test_webhook_signature_contract() -> None:
    assert WEBHOOK_SIGNATURE_HEADER == "X-VG-Signature"
    assert CONTRACT_SIG.startswith("t=1700000000,v1=")
    assert verify_webhook_signature(CONTRACT_BODY, CONTRACT_SIG, CONTRACT_SECRET, max_age_seconds=None) is True
    assert verify_webhook_signature(CONTRACT_BODY.decode(), CONTRACT_SIG, CONTRACT_SECRET, max_age_seconds=None) is True
    assert verify_webhook_signature(CONTRACT_BODY, "sha256=bad", CONTRACT_SECRET) is False
    assert verify_webhook_signature(CONTRACT_BODY, CONTRACT_SIG, "") is False
    fresh = sign_webhook_payload("hello", CONTRACT_SECRET)
    assert verify_webhook_signature("hello", fresh, CONTRACT_SECRET) is True


if __name__ == "__main__":
    test_webhook_signature_contract()
    print("test_webhook: ok")
