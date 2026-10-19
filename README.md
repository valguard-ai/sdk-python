# valguard-sdk (Python)

Thin Python helpers for the ValGuard OpenAI-compatible integrity layer.

**Package name: `valguard-sdk`.** `pip install valguard` installs an unrelated third-party project. Import this SDK as `valguard`.

Public GitHub: [github.com/valguard-ai/sdk-python](https://github.com/valguard-ai/sdk-python).

Set `VG_PROXY` to your layer URL — see [valguard.ai/docs/quickstart](https://valguard.ai/docs/quickstart).

## Install

```bash
pip install valguard-sdk
# or, from this repo: pip install "git+https://github.com/valguard-ai/sdk-python.git"
pip install openai   # optional, for OpenAI SDK bridge
```

## Environment

```bash
export VG_PROXY="https://api.valguard.ai"   # your layer base URL
export VG_API_KEY="vg_live_..."
export VG_AGENT="invoice_extraction_agent"
export VG_PROVIDER_KEY="sk-..."             # optional BYOK upstream key
```

## with_agent and with_playbook

`with_agent` sets `X-VG-Agent`. `with_playbook` sets `X-VG-Flow`. Pass `provider_key` (or `VG_PROVIDER_KEY` via `from_env`) so `openai_client_kwargs()` includes `X-Provider-Key`.

```python
vg = ValGuardClient.from_env().with_playbook("invoice-processing")
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
| `parse_validation_headers()` | Read `X-VG-*` headers, including repair, cache, trace, and approval |
| `verify_proof()` / `verify_evidence()` | Offline HMAC check of a Proof download (`valguard-evidence/1`) |
| `parse_valguard_error()` | Parse error / soft-fail JSON |
| `ValGuardError` | Raised on non-2xx responses |

`with_approval_mode("async")` sends `X-VG-Approval-Mode`. `with_idempotency_key` sends `X-VG-Idempotency-Key`. `with_trace` sends `traceparent`, `X-VG-Parent-Span-Id`, and `X-VG-Agent-Id`. Response repair is reported with `X-VG-Healed`, `X-VG-Healed-Rules`, `X-VG-Healed-Event-Count`, and `X-VG-Healed-Trace`. Presets are agent settings.
