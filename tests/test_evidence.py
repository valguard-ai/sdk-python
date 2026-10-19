from valguard.evidence import EVIDENCE_TYP, verify_evidence, verify_proof

SECRET = "contract-test-evidence-secret"
KEY_ID = "org:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb:v1"
PAYLOAD = (
    '{"typ":"valguard-evidence/1","request_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",'
    '"org_id":"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","checked_at":"2026-03-15T08:30:00Z",'
    '"engine_version":"valguard-engine/1","policy_snapshot_hash":"policy-1",'
    '"request_digest":"sha256:758d61f26a44448384e5c4468a0dcb7a2abe456067b0f7b505bc28b9411fe931",'
    '"response_digest":"sha256:9795c5ff8937f23526ccb207a5684c1fc94a7854e19c021b39d944e51f5baef2",'
    '"verdicts":[]}'
)
SIGNATURE = "sha256=35b87328b2f2c94b34658646f15e993fe900e1a79fe75558b4b6140d55b3003a"


def test_verify_evidence_contract_vector() -> None:
    assert EVIDENCE_TYP == "valguard-evidence/1"
    assert verify_evidence(KEY_ID, PAYLOAD, SIGNATURE, SECRET) is True
    assert verify_evidence(KEY_ID, PAYLOAD, SIGNATURE + "x", SECRET) is False
    assert verify_evidence(KEY_ID, PAYLOAD[:-1] + "x", SIGNATURE, SECRET) is False
    assert verify_evidence(KEY_ID, PAYLOAD, SIGNATURE, "") is False


def test_verify_proof_json_and_mapping() -> None:
    record = {"key_id": KEY_ID, "payload": PAYLOAD, "signature": SIGNATURE}
    assert verify_proof(record, SECRET) is True
    assert verify_proof('{"key_id":"x"}', SECRET) is False
    assert verify_proof("{", SECRET) is False
