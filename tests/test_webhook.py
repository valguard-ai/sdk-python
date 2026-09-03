from valguard.webhook import (
    WEBHOOK_SIGNATURE_HEADER,
    sign_webhook_payload,
    verify_webhook_signature,
)

CONTRACT_SECRET = "contract-test-webhook-secret"
CONTRACT_BODY = b'{"event":"validation.block","request_id":"abc"}'
CONTRACT_SIG = "sha256=6ef400c3c929c837d90cd6e99f082815966aee86cf10ac5f884e0f06cbcfd879"


def test_webhook_signature_contract() -> None:
    assert WEBHOOK_SIGNATURE_HEADER == "X-VG-Signature"
    assert sign_webhook_payload(CONTRACT_BODY, CONTRACT_SECRET) == CONTRACT_SIG
    assert verify_webhook_signature(CONTRACT_BODY, CONTRACT_SIG, CONTRACT_SECRET) is True
    assert verify_webhook_signature(CONTRACT_BODY, "sha256=bad", CONTRACT_SECRET) is False
    assert verify_webhook_signature(CONTRACT_BODY, CONTRACT_SIG, "") is False


if __name__ == "__main__":
    test_webhook_signature_contract()
    print("test_webhook: ok")
