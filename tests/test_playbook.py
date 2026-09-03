from valguard.client import ValGuardClient


def test_with_playbook_headers() -> None:
    client = ValGuardClient(
        api_key="vg_test",
        base_url="https://api.example.com",
        agent_slug="",
        flow_slug="invoice-processing",
    )
    headers = client.build_headers()
    assert headers["X-VG-Flow"] == "invoice-processing"
    assert "X-VG-Agent" not in headers


def test_mutually_exclusive_headers() -> None:
    client = ValGuardClient(
        api_key="vg_test",
        base_url="https://api.example.com",
        agent_slug="a",
        flow_slug="f",
    )
    try:
        client.build_headers()
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "mutually_exclusive_headers" in str(e)


if __name__ == "__main__":
    test_with_playbook_headers()
    test_mutually_exclusive_headers()
    print("test_playbook: ok")
