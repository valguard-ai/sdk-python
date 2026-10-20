"""ValGuard integration helpers for the OpenAI-compatible layer."""

from valguard.client import (
    ChatCompletionResult,
    ChatCompletionStreamResult,
    TestValidatorsResult,
    ValGuardClient,
)
from valguard.stream import iter_chat_completion_stream, parse_chat_completion_stream
from valguard.errors import ValGuardError, ValGuardErrorInfo, parse_valguard_error
from valguard.evidence import EVIDENCE_TYP, verify_evidence, verify_proof
from valguard.headers import ValidationHeaders, parse_validation_headers
from valguard.webhook import (
    WEBHOOK_SIGNATURE_HEADER,
    sign_webhook_payload,
    verify_webhook_signature,
)


def openai_client_kwargs(
    api_key: str,
    base_url: str,
    agent_slug: str,
    provider_key: str | None = None,
) -> dict:
    """Backward-compatible helper — prefer ValGuardClient.openai_client_kwargs().

    Pass provider_key so the OpenAI client sends X-Provider-Key (BYOK).
    """
    return ValGuardClient(
        api_key=api_key,
        base_url=base_url,
        agent_slug=agent_slug,
        provider_key=provider_key,
    ).openai_client_kwargs()


__all__ = [
    "ChatCompletionResult",
    "ChatCompletionStreamResult",
    "EVIDENCE_TYP",
    "iter_chat_completion_stream",
    "parse_chat_completion_stream",
    "TestValidatorsResult",
    "ValGuardClient",
    "ValGuardError",
    "ValGuardErrorInfo",
    "ValidationHeaders",
    "WEBHOOK_SIGNATURE_HEADER",
    "openai_client_kwargs",
    "parse_response_headers",
    "parse_valguard_error",
    "parse_validation_headers",
    "sign_webhook_payload",
    "verify_evidence",
    "verify_proof",
    "verify_webhook_signature",
]

# Alias for symmetry with the Node SDK
parse_response_headers = parse_validation_headers
