"""Underlying-HTTP-attempt metering for provider-internal retries (docs 9.6 R3).

One upper-layer measurement must not masquerade as one HTTP request: key
rotation, Responses→chat fallback and parameter-compatibility retries each
issue another request. These tests assert the persisted ``attempts`` count on
selected entry points, against fake SDK clients and the real ledger.
"""

from __future__ import annotations

from types import SimpleNamespace as NS
from typing import Any

import pytest

from deeptutor.services.llm import metrics, usage_ledger
from deeptutor.services.llm.provider_core.openai_compat_provider import OpenAICompatProvider
from deeptutor.services.provider_registry import find_by_name


class _FakeHTTPError(Exception):
    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(body)
        self.status_code = status_code
        self.body = body


def _chat_result(content: str = "ok") -> NS:
    return NS(
        choices=[
            NS(
                message=NS(content=content, reasoning_content=None, reasoning=None, tool_calls=[]),
                finish_reason="stop",
            )
        ],
        usage=None,
    )


class _Collector:
    """Run one provider call under a turn collector and return its records."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    async def run(self, provider: OpenAICompatProvider, **kwargs: Any) -> Any:
        collector = metrics.TurnUsage(session_id="attempt-test", turn_id="attempt-turn")
        token = metrics.current_usage.set(collector)
        try:
            response = await provider.chat_with_retry(
                messages=[{"role": "user", "content": "hello"}], **kwargs
            )
        finally:
            metrics.current_usage.reset(token)
        self.records = list(collector.calls)
        return response

    def ledger_attempts(self) -> list[int]:
        records = usage_ledger.usage_records(0, 9999999999)
        return [
            call["attempts"]
            for record in records
            for call in record["summaries"][0]["call_details"]
        ]


@pytest.mark.asyncio
async def test_plain_call_records_exactly_one_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    from deeptutor.services.llm.provider_core import openai_compat_provider as provider_module

    class _Completions:
        async def create(self, **kwargs: Any) -> Any:
            return _chat_result()

    class _Client:
        def __init__(self, **_kwargs: Any) -> None:
            self.chat = NS(completions=_Completions())
            self.responses = NS()

    monkeypatch.setattr(provider_module, "AsyncOpenAI", _Client)
    provider = provider_module.OpenAICompatProvider(
        api_key="test-key",
        api_base="https://api.example.test/v1",
        default_model="gpt-4o-mini",
    )

    runner = _Collector()
    await runner.run(provider)
    assert [record["attempts"] for record in runner.records] == [1]
    assert runner.ledger_attempts() == [1]


@pytest.mark.asyncio
async def test_key_rotation_counts_every_underlying_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from deeptutor.services.llm.provider_core import openai_compat_provider as provider_module

    seen_auth: list[str] = []

    class _RateLimitError(Exception):
        status_code = 429

    class _Completions:
        async def create(self, **kwargs: Any) -> Any:
            seen_auth.append((kwargs.get("extra_headers") or {}).get("Authorization", ""))
            if len(seen_auth) < 3:
                raise _RateLimitError("429 rate limited")
            return _chat_result()

    class _Client:
        def __init__(self, **_kwargs: Any) -> None:
            self.chat = NS(completions=_Completions())
            self.responses = NS()

    monkeypatch.setattr(provider_module, "AsyncOpenAI", _Client)
    provider = provider_module.OpenAICompatProvider(
        api_key=["key-a", "key-b", "key-c"],
        api_base="https://api.example.test/v1",
        default_model="gpt-4o-mini",
    )

    runner = _Collector()
    response = await runner.run(provider)
    assert response.content == "ok"
    assert seen_auth == ["Bearer key-a", "Bearer key-b", "Bearer key-c"]
    # One upper-layer measurement, three real HTTP attempts, persisted.
    assert len(runner.records) == 1
    assert runner.records[0]["attempts"] == 3
    assert runner.ledger_attempts() == [3]


@pytest.mark.asyncio
async def test_responses_fallback_counts_both_attempts() -> None:
    class FailingResponses:
        async def create(self, **_kwargs: Any) -> Any:
            raise _FakeHTTPError(
                400,
                "The reasoning_text in the thinking mode must be passed back to the API.",
            )

    class SuccessfulChatCompletions:
        async def create(self, **_kwargs: Any) -> Any:
            return _chat_result("fallback answer")

    provider = OpenAICompatProvider(
        api_key="test-key",
        default_model="deepseek-v4-flash",
        spec=find_by_name("deepseek"),
        provider_name="deepseek",
        wire_api="auto",
    )
    provider._client = NS(
        responses=FailingResponses(),
        chat=NS(completions=SuccessfulChatCompletions()),
    )

    runner = _Collector()
    response = await runner.run(
        provider,
        model="deepseek-v4-flash",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ],
    )
    assert response.content == "fallback answer"
    assert runner.records[0]["attempts"] == 2
    assert runner.ledger_attempts() == [2]


@pytest.mark.asyncio
async def test_response_format_retry_counts_both_attempts() -> None:
    calls: list[Any] = []

    class _Completions:
        async def create(self, **kwargs: Any) -> Any:
            calls.append(kwargs.get("response_format"))
            if kwargs.get("response_format") is not None:
                raise _FakeHTTPError(
                    400,
                    "response_format 'json_object' is not supported by this model",
                )
            return _chat_result()

    provider = OpenAICompatProvider(
        api_key="test-key",
        default_model="attempt-meter-unique-model",
        spec=find_by_name("openai"),
        provider_name="openai",
        wire_api="chat_completions",
    )
    provider._client = NS(chat=NS(completions=_Completions()), responses=NS())

    runner = _Collector()
    response = await runner.run(
        provider, model="attempt-meter-unique-model", response_format={"type": "json_object"}
    )
    assert response.content == "ok"
    assert calls == [{"type": "json_object"}, None]
    assert runner.records[0]["attempts"] == 2
    assert runner.ledger_attempts() == [2]


@pytest.mark.asyncio
async def test_agentic_key_rotation_counts_underlying_requests() -> None:
    from deeptutor.runtime.agentic.client import _KeyRotatingCompletions
    from deeptutor.services.keypool import KeyPool

    class _RateLimitError(Exception):
        status_code = 429

    class _Inner:
        def __init__(self, fail: bool) -> None:
            self._fail = fail
            self.chat = NS(completions=NS(create=self._create))

        async def _create(self, **_kwargs: Any) -> Any:
            if self._fail:
                raise _RateLimitError("429 rate limited")
            return NS(
                usage={"prompt_tokens": 3, "completion_tokens": 2},
                choices=[NS(message=NS(content="ok"))],
            )

    clients = {"key-a": _Inner(fail=True), "key-b": _Inner(fail=False)}
    rotating = NS(
        chat=NS(completions=_KeyRotatingCompletions(KeyPool(["key-a", "key-b"]), clients))
    )
    client = metrics.instrument_client(rotating, model="gpt-4o", provider="rotation-test")

    result = await client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
    )
    assert result.usage == {"prompt_tokens": 3, "completion_tokens": 2}

    records = usage_ledger.usage_records(0, 9999999999)
    details = records[0]["summaries"][0]["call_details"]
    assert len(details) == 1  # one upper-layer measurement…
    assert details[0]["attempts"] == 2  # …two real HTTP attempts underneath
    assert details[0]["total_tokens"] == 5
