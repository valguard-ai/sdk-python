"""ValGuard client — OpenAI-compatible layer helpers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterator, Mapping, Sequence, Union

from .errors import ValGuardError, ValGuardErrorInfo, parse_valguard_error
from .headers import ValidationHeaders, parse_validation_headers
from .stream import iter_chat_completion_stream

RAGSource = Union[str, Dict[str, str]]


@dataclass
class ChatCompletionResult:
    status: int
    data: Any
    validation: ValidationHeaders
    error: ValGuardErrorInfo | None


@dataclass
class TestValidatorsResult:
    status: int
    data: Any
    validation: ValidationHeaders
    error: ValGuardErrorInfo | None


@dataclass
class ChatCompletionStreamResult:
    status: int
    validation: ValidationHeaders
    stream: Iterator[dict[str, Any]]
    error: ValGuardErrorInfo | None = None


@dataclass
class ValGuardClient:
    api_key: str
    base_url: str
    agent_slug: str = "default"
    flow_slug: str | None = None
    provider_key: str | None = None
    request_id: str | None = None
    rag_sources: Sequence[RAGSource] = field(default_factory=list)
    internal_secret: str | None = None
    project_id: str | None = None
    idempotency_key: str | None = None
    approval_mode: str | None = None
    traceparent: str | None = None
    parent_span_id: str | None = None
    agent_id: str | None = None

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> ValGuardClient:
        env = dict(os.environ if environ is None else environ)
        api_key = env.get("VG_API_KEY") or env.get("VALGUARD_API_KEY")
        base_url = env.get("VG_PROXY") or env.get("VALGUARD_BASE_URL")
        agent_slug = env.get("VG_AGENT") or env.get("VALGUARD_AGENT") or "default"
        provider_key = env.get("VG_PROVIDER_KEY") or env.get("OPENAI_API_KEY")
        internal_secret = env.get("INTERNAL_PROXY_SECRET") or env.get("VG_INTERNAL_SECRET")
        project_id = env.get("VG_PROJECT_ID") or env.get("VG_TEST_PROJECT_ID")

        if not api_key and not (internal_secret and project_id):
            raise ValueError(
                "Missing VG_API_KEY (or INTERNAL_PROXY_SECRET + VG_PROJECT_ID for internal test endpoints)"
            )
        if not base_url:
            raise ValueError("Missing VG_PROXY (layer base URL)")

        return cls(
            api_key=api_key or "",
            base_url=base_url,
            agent_slug=agent_slug,
            provider_key=provider_key,
            internal_secret=internal_secret,
            project_id=project_id,
        )

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/v1/chat/completions"

    @property
    def test_validators_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/internal/test-validators"

    def _build_internal_test_headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.internal_secret:
            headers["X-VG-Internal-Secret"] = self.internal_secret
        if self.project_id:
            headers["X-VG-Project-Id"] = self.project_id
        if not headers.get("Authorization") and not (self.internal_secret and self.project_id):
            raise ValueError(
                "test_validators requires api_key or both internal_secret and project_id"
            )
        if extra:
            headers.update(extra)
        return headers

    def test_validators(
        self,
        *,
        output: str,
        agent_slug: str,
        input_text: str = "",
        rag_sources: Sequence[RAGSource] | None = None,
        reask_attempt: int | None = None,
        extra_headers: Mapping[str, str] | None = None,
        timeout: float = 60.0,
    ) -> TestValidatorsResult:
        if not output or not agent_slug:
            raise ValueError("test_validators requires output and agent_slug")

        body: dict[str, Any] = {
            "output": output,
            "agent_slug": agent_slug,
        }
        if input_text:
            body["input_text"] = input_text
        if rag_sources:
            body["rag_sources"] = list(rag_sources)
        if reask_attempt is not None:
            body["reask_attempt"] = reask_attempt

        payload = json.dumps(body).encode("utf-8")
        headers = self._build_internal_test_headers(
            {"Content-Type": "application/json", **dict(extra_headers or {})}
        )

        request = urllib.request.Request(
            self.test_validators_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                raw = response.read().decode("utf-8")
                response_headers = {k: v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8")
            response_headers = {k: v for k, v in exc.headers.items()}

        data: Any
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
        else:
            data = None

        validation = parse_validation_headers(response_headers)
        error = parse_valguard_error(status, data)

        if error and status >= 400:
            raise ValGuardError(status, error)

        return TestValidatorsResult(status=status, data=data, validation=validation, error=error)

    def openai_client_kwargs(self) -> dict[str, Any]:
        default_headers = self.build_headers()
        default_headers.pop("Authorization", None)
        return {
            "api_key": self.api_key,
            "base_url": f"{self.base_url.rstrip('/')}/v1",
            "default_headers": default_headers,
        }

    def _assert_mutually_exclusive(self) -> None:
        if self.flow_slug and self.agent_slug:
            raise ValueError("mutually_exclusive_headers: use either with_agent or with_playbook, not both")

    def build_headers(self, extra: Mapping[str, str] | None = None) -> dict[str, str]:
        self._assert_mutually_exclusive()
        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.flow_slug:
            headers["X-VG-Flow"] = self.flow_slug
        else:
            headers["X-VG-Agent"] = self.agent_slug
        if self.provider_key:
            headers["X-Provider-Key"] = self.provider_key
        if self.request_id:
            headers["X-Request-Id"] = self.request_id
        if self.rag_sources:
            headers["X-VG-Sources"] = json.dumps(list(self.rag_sources))
        if self.idempotency_key:
            headers["X-VG-Idempotency-Key"] = self.idempotency_key
        if self.approval_mode:
            headers["X-VG-Approval-Mode"] = self.approval_mode
        if self.traceparent:
            headers["traceparent"] = self.traceparent
        if self.parent_span_id:
            headers["X-VG-Parent-Span-Id"] = self.parent_span_id
        if self.agent_id:
            headers["X-VG-Agent-Id"] = self.agent_id
        if extra:
            headers.update(extra)
        return headers

    def with_agent(self, agent_slug: str) -> ValGuardClient:
        return replace(self, agent_slug=agent_slug, flow_slug=None)

    def with_playbook(self, flow_slug: str) -> ValGuardClient:
        return replace(self, flow_slug=flow_slug, agent_slug="")

    def with_provider_key(self, provider_key: str) -> ValGuardClient:
        return replace(self, provider_key=provider_key)

    def with_rag_sources(self, sources: Sequence[RAGSource]) -> ValGuardClient:
        return replace(self, rag_sources=list(sources))

    def with_idempotency_key(self, key: str) -> ValGuardClient:
        return replace(self, idempotency_key=key)

    def with_approval_mode(self, mode: str) -> ValGuardClient:
        return replace(self, approval_mode=mode)

    def with_trace(
        self,
        *,
        traceparent: str | None = None,
        parent_span_id: str | None = None,
        agent_id: str | None = None,
    ) -> ValGuardClient:
        return replace(
            self,
            traceparent=traceparent,
            parent_span_id=parent_span_id,
            agent_id=agent_id,
        )

    def parse_response_headers(self, headers: Mapping[str, str]) -> ValidationHeaders:
        return parse_validation_headers(headers)

    def chat_completions(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        stream: bool = False,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream_options: Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        extra_headers: Mapping[str, str] | None = None,
        timeout: float = 60.0,
    ) -> ChatCompletionResult:
        body: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": stream,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stream_options is not None:
            body["stream_options"] = dict(stream_options)
        if response_format is not None:
            body["response_format"] = dict(response_format)

        payload = json.dumps(body).encode("utf-8")
        headers = self.build_headers({"Content-Type": "application/json", **dict(extra_headers or {})})

        request = urllib.request.Request(
            self.chat_completions_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.status
                raw = response.read().decode("utf-8")
                response_headers = {k: v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8")
            response_headers = {k: v for k, v in exc.headers.items()}

        data: Any
        if raw:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
        else:
            data = None

        validation = parse_validation_headers(response_headers)
        error = parse_valguard_error(status, data)

        if error and not error.soft_fail and status >= 400:
            raise ValGuardError(status, error)

        return ChatCompletionResult(status=status, data=data, validation=validation, error=error)

    def chat_completions_stream(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream_options: Mapping[str, Any] | None = None,
        response_format: Mapping[str, Any] | None = None,
        tools: Any | None = None,
        tool_choice: Any | None = None,
        extra_headers: Mapping[str, str] | None = None,
        timeout: float = 300.0,
    ) -> ChatCompletionStreamResult:
        """POST /v1/chat/completions with stream=true and yield parsed SSE events."""
        body: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": True,
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if stream_options is not None:
            body["stream_options"] = dict(stream_options)
        if response_format is not None:
            body["response_format"] = dict(response_format)
        if tools is not None:
            body["tools"] = tools
        if tool_choice is not None:
            body["tool_choice"] = tool_choice

        payload = json.dumps(body).encode("utf-8")
        headers = self.build_headers(
            {
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                **dict(extra_headers or {}),
            }
        )

        request = urllib.request.Request(
            self.chat_completions_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            response = urllib.request.urlopen(request, timeout=timeout)
            status = response.status
            response_headers = {k: v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8")
            response_headers = {k: v for k, v in exc.headers.items()}
            data: Any
            if raw:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = raw
            else:
                data = None
            validation = parse_validation_headers(response_headers)
            error = parse_valguard_error(status, data)
            if error and not error.soft_fail and status >= 400:
                raise ValGuardError(status, error)

            def empty() -> Iterator[dict[str, Any]]:
                return iter(())

            return ChatCompletionStreamResult(
                status=status,
                validation=validation,
                stream=empty(),
                error=error,
            )

        validation = parse_validation_headers(response_headers)

        def chunk_text() -> Iterator[str]:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                yield chunk.decode("utf-8", errors="replace")

        return ChatCompletionStreamResult(
            status=status,
            validation=validation,
            stream=iter_chat_completion_stream(chunk_text()),
            error=None,
        )
