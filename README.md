# valguard (Python SDK)

Thin Python helpers for the ValGuard OpenAI-compatible integrity layer. The import package is `valguard`.

Public GitHub: [github.com/valguard-ai/sdk-python](https://github.com/valguard-ai/sdk-python). Install from GitHub or a local checkout — this SDK is not the unrelated PyPI project named `valguard`.

Set `VG_PROXY` to your layer URL — see [valguard.ai/docs/quickstart](https://valguard.ai/docs/quickstart).

## Install

```bash
pip install "git+https://github.com/valguard-ai/sdk-python.git"
pip install openai   # optional, for OpenAI SDK bridge
```

## Environment

```bash
export VG_PROXY="https://api.valguard.ai"   # your layer base URL
export VG_API_KEY="vg_live_..."
export VG_AGENT="invoice_extraction_agent"
export VG_PROVIDER_KEY="sk-..."             # optional BYOK upstream key
```

## OpenAI SDK (recommended)

```python
from openai import OpenAI
from valguard import ValGuardClient

vg = ValGuardClient.from_env()
client = OpenAI(**vg.openai_client_kwargs())

raw = client.with_raw_response.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "Extract invoice JSON"}],
)

print(vg.parse_response_headers(dict(raw.http_response.headers)))
print(raw.parse())
```

## Stdlib-only HTTP

```python
from valguard import ValGuardClient

vg = ValGuardClient(
    api_key="vg_live_...",
    base_url="https://api.valguard.ai",
    agent_slug="default",
    provider_key="sk-...",
)

result = vg.chat_completions(
    model="openai/gpt-4o-mini",
    messages=[{"role": "user", "content": "hi"}],
)
print(result.validation)
print(result.data)
```

## RAG sources

```python
vg = ValGuardClient.from_env().with_rag_sources(
    [{"id": "doc-1", "text": "Acme revenue was $4.2M in Q3."}]
)
```

## Errors

```python
from valguard import ValGuardClient, ValGuardError

try:
    vg.chat_completions(model="openai/gpt-4o-mini", messages=[])
except ValGuardError as err:
    print(err.info.type)  # validation_block, input_validation, rate_limit_exceeded, ...
```

Soft-fail agents return HTTP 200 with `valid: false` — inspect `result.error.soft_fail` instead of exceptions.

## API surface

| Symbol | Purpose |
|--------|---------|
| `ValGuardClient` | Main client + `from_env()` |
| `openai_client_kwargs()` | Legacy functional helper |
| `parse_validation_headers()` | Read `X-VG-*` headers |
| `parse_valguard_error()` | Parse error / soft-fail JSON |
| `ValGuardError` | Raised on non-2xx responses |
