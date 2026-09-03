from valguard.client import ValGuardClient


def test_build_internal_test_headers_api_key() -> None:
    client = ValGuardClient(api_key="vg_test", base_url="https://api.example.com")
    headers = client._build_internal_test_headers()
    assert headers["Authorization"] == "Bearer vg_test"


def test_build_internal_test_headers_secret() -> None:
    client = ValGuardClient(
        api_key="",
        base_url="https://api.example.com",
        internal_secret="secret",
        project_id="proj-1",
    )
    headers = client._build_internal_test_headers()
    assert headers["X-VG-Internal-Secret"] == "secret"
    assert headers["X-VG-Project-Id"] == "proj-1"
    assert "Authorization" not in headers


if __name__ == "__main__":
    test_build_internal_test_headers_api_key()
    test_build_internal_test_headers_secret()
    print("test_internal: ok")
