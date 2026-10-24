"""Offline contract tests for the persistent LLM budget gate (docs 9.6 R2).

Fake providers and real temporary SQLite only — no network, no real model.
These verify gate mechanics (caps, reservation atomicity, conservative
settlement, restart persistence), not model or pricing accuracy.
"""

import asyncio
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace as NS

import pytest

from deeptutor.services.llm import budget, factory, metrics, usage_ledger
from deeptutor.services.llm.config import LLMConfig
from deeptutor.services.llm.exceptions import LLMBudgetExceededError
from deeptutor.services.llm.provider_core.base import LLMProvider, LLMResponse


class CountingProvider(LLMProvider):
    provider_name = "budget-test"

    def __init__(self, *, usage=None, content="answer", error=None, delay=0.0):
        super().__init__()
        self.calls = 0
        self.usage = dict(usage or {})
        self.content = content
        self.error = error
        self.delay = delay

    async def chat(self, **kwargs):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        return LLMResponse(content=self.content, usage=dict(self.usage))

    async def chat_stream(self, *, on_content_delta=None, **kwargs):
        self.calls += 1
        if on_content_delta and self.content:
            await on_content_delta(self.content)
        return LLMResponse(content=self.content, usage=dict(self.usage))

    def get_default_model(self):
        return "budget-test-model"


def enable_budget(monkeypatch, **overrides):
    settings = {
        "version": 1,
        "enabled": True,
        "window_days": 30,
        "max_requests": 0,
        "max_total_tokens": 0,
        "max_cost_usd": 0.0,
        "reservation_ttl_minutes": 120,
    }
    settings.update(overrides)
    monkeypatch.setattr(budget, "_load_settings", lambda: settings)
    return settings


def wire_factory(monkeypatch, provider, *, model="gpt-4o"):
    config = LLMConfig(model=model, api_key="test", binding="openai", provider_name="openai")
    monkeypatch.setattr(factory, "get_llm_config", lambda: config)
    monkeypatch.setattr(factory, "get_runtime_provider", lambda _: provider)
    return config


def settled_rows() -> list[tuple]:
    path = usage_ledger.ledger_path()
    with sqlite3.connect(path) as conn:
        return conn.execute(
            "SELECT status, prompt_tokens, completion_tokens, estimated FROM budget_settled "
            "ORDER BY settled_at"
        ).fetchall()


@pytest.mark.asyncio
async def test_gate_off_by_default_touches_no_store(monkeypatch):
    provider = CountingProvider(usage={"prompt_tokens": 10, "completion_tokens": 5})
    wire_factory(monkeypatch, provider)
    assert await factory.complete("hi") == "answer"
    assert budget.budget_call(model="gpt-4o") is None
    assert budget.budget_status() == {"enabled": False}
    with sqlite3.connect(usage_ledger.ledger_path()) as conn:
        tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert not any(name.startswith("budget_") for name in tables)


@pytest.mark.asyncio
async def test_request_cap_rejects_new_calls_before_provider(monkeypatch):
    enable_budget(monkeypatch, max_requests=2)
    provider = CountingProvider(usage={"prompt_tokens": 10, "completion_tokens": 5})
    wire_factory(monkeypatch, provider)

    assert await factory.complete("hi") == "answer"
    assert await factory.complete("hi again") == "answer"
    with pytest.raises(LLMBudgetExceededError) as caught:
        await factory.complete("third")
    assert caught.value.reason == "requests"
    assert provider.calls == 2
    status = budget.budget_status()
    assert status["usage"]["requests"] == 2
    assert status["usage"]["active_reservations"] == 0


@pytest.mark.asyncio
async def test_concurrent_overload_only_budgeted_calls_reach_provider(monkeypatch):
    enable_budget(monkeypatch, max_requests=3)
    provider = CountingProvider(usage={"prompt_tokens": 10, "completion_tokens": 5}, delay=0.05)
    wire_factory(monkeypatch, provider)

    results = await asyncio.gather(
        *(factory.complete(f"msg {i}") for i in range(8)), return_exceptions=True
    )
    rejected = [r for r in results if isinstance(r, LLMBudgetExceededError)]
    answered = [r for r in results if r == "answer"]
    assert provider.calls == 3
    assert len(answered) == 3
    assert len(rejected) == 5
    assert budget.budget_status()["usage"]["requests"] == 3


@pytest.mark.asyncio
async def test_token_cap_counts_settled_usage_against_new_reservations(monkeypatch):
    enable_budget(monkeypatch, max_total_tokens=90)
    provider = CountingProvider(usage={"prompt_tokens": 40, "completion_tokens": 20})
    wire_factory(monkeypatch, provider)

    assert await factory.complete("hi", max_tokens=30) == "answer"
    with pytest.raises(LLMBudgetExceededError) as caught:
        await factory.complete("hi again", max_tokens=30)
    assert caught.value.reason == "tokens"
    assert provider.calls == 1
    usage = budget.budget_status()["usage"]
    assert usage["total_tokens"] == 60
    assert usage["active_reservations"] == 0


@pytest.mark.asyncio
async def test_unknown_usage_and_failures_settle_conservatively_not_free(monkeypatch):
    enable_budget(monkeypatch, max_total_tokens=10000)
    silent = CountingProvider()  # returns no usage at all
    wire_factory(monkeypatch, silent)
    assert await factory.complete("hi", max_tokens=25) == "answer"
    (status, prompt, completion, estimated) = settled_rows()[0]
    assert status == "completed"
    assert estimated == 1
    assert prompt > 0 and completion > 0

    failing = CountingProvider(error=TimeoutError("provider timed out"))
    wire_factory(monkeypatch, failing)
    with pytest.raises(Exception):
        await factory.complete("hi", max_tokens=25, max_retries=0)
    (status, prompt, completion, estimated) = settled_rows()[1]
    # A timed-out call may still be billed for the full request: settle the
    # reserved upper bound instead of zero.
    assert status == "failed"
    assert estimated == 1
    assert completion == 25
    assert prompt > 0

    # The conservative tokens now gate a fresh call under a tighter cap.
    spent = sum(row[1] + row[2] for row in settled_rows())
    enable_budget(monkeypatch, max_total_tokens=spent + 5)
    fresh = CountingProvider()
    wire_factory(monkeypatch, fresh)
    with pytest.raises(LLMBudgetExceededError) as caught:
        await factory.complete("hi", max_tokens=25, max_retries=0)
    assert caught.value.reason == "tokens"
    assert fresh.calls == 0


@pytest.mark.asyncio
async def test_cost_cap_rejects_unpriced_models_instead_of_free_rides(monkeypatch):
    enable_budget(monkeypatch, max_cost_usd=0.0105)
    provider = CountingProvider(usage={"prompt_tokens": 100, "completion_tokens": 50})
    config = wire_factory(monkeypatch, provider, model="gpt-4o")

    assert await factory.complete("hi", max_tokens=1000) == "answer"
    assert config.model == "gpt-4o"
    mystery = wire_factory(monkeypatch, provider, model="mystery-unpriced-model")
    assert mystery.model == "mystery-unpriced-model"
    with pytest.raises(LLMBudgetExceededError) as caught:
        await factory.complete("hi", max_tokens=1000)
    assert caught.value.reason == "unknown_price"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_cost_cap_blocks_when_history_contains_unknown_cost(monkeypatch):
    enable_budget(monkeypatch, max_total_tokens=10000)
    provider = CountingProvider()
    wire_factory(monkeypatch, provider, model="mystery-unpriced-model")
    assert await factory.complete("hi", max_tokens=10) == "answer"
    assert budget.budget_status()["usage"]["cost_known"] is False

    enable_budget(monkeypatch, max_total_tokens=10000, max_cost_usd=1.0)
    wire_factory(monkeypatch, provider, model="gpt-4o")
    with pytest.raises(LLMBudgetExceededError) as caught:
        await factory.complete("hi", max_tokens=10)
    assert caught.value.reason == "unknown_history_cost"
    assert provider.calls == 1


@pytest.mark.asyncio
async def test_settle_store_failure_keeps_answer_and_reservation(monkeypatch):
    enable_budget(monkeypatch, max_requests=5)
    provider = CountingProvider(usage={"prompt_tokens": 10, "completion_tokens": 5})
    wire_factory(monkeypatch, provider)

    def broken_settle(*args, **kwargs):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(budget, "_settle_reservation_row", broken_settle)
    # The answer the model already produced must still reach the caller, and
    # the model must not be called again to "fix" the books.
    assert await factory.complete("hi") == "answer"
    assert provider.calls == 1
    status = budget.budget_status()
    assert status["usage"]["active_reservations"] == 1
    assert status["usage"]["requests"] == 1


@pytest.mark.asyncio
async def test_window_rollover_resets_usage(monkeypatch):
    enable_budget(monkeypatch, max_requests=1)
    provider = CountingProvider(usage={"prompt_tokens": 10, "completion_tokens": 5})
    wire_factory(monkeypatch, provider)

    assert await factory.complete("hi") == "answer"
    with pytest.raises(LLMBudgetExceededError):
        await factory.complete("hi again")

    real_now = budget._now
    monkeypatch.setattr(budget, "_now", lambda: real_now() + 31 * 86400)
    assert await factory.complete("new window") == "answer"
    status = budget.budget_status()
    assert status["epoch"] == 2
    assert status["usage"]["requests"] == 1
    assert status["usage"]["active_reservations"] == 0


@pytest.mark.asyncio
async def test_stream_settles_once_with_final_usage(monkeypatch):
    enable_budget(monkeypatch, max_requests=2)
    provider = CountingProvider(usage={"prompt_tokens": 12, "completion_tokens": 7})
    wire_factory(monkeypatch, provider)

    chunks = [part async for part in factory.stream("hi")]
    assert "".join(chunks) == "answer"
    usage = budget.budget_status()["usage"]
    assert usage["requests"] == 1
    assert usage["total_tokens"] == 19
    assert usage["active_reservations"] == 0
    (status, *_rest) = settled_rows()[0]
    assert status == "completed"


def _budget_worker() -> None:
    """Separate interpreter: reserve and die without settling (crash sim)."""
    store = Path(sys.argv[1])
    settings = json.loads(sys.argv[2])
    from deeptutor.services.llm import budget

    budget._load_settings = lambda: settings
    budget._store_path = lambda: store
    call = budget.budget_call(
        model="gpt-4o",
        provider="budget-test",
        source="crash-sim",
        estimated_prompt_tokens=50,
        max_output_tokens=100,
    )
    assert call is not None
    call.reserve()


def test_crashed_reservation_from_dead_process_still_counts(monkeypatch, tmp_path):
    """A reservation left by a crashed process is never treated as free.

    Uses a real child interpreter so the durable-state claim covers a genuine
    restart, not just a second object in the same process.
    """
    settings = enable_budget(monkeypatch, max_total_tokens=10000)
    store = usage_ledger.ledger_path()

    result = subprocess.run(
        [sys.executable, Path(__file__).resolve(), str(store), json.dumps(settings)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    status = budget.budget_status()
    assert status["usage"]["active_reservations"] == 1
    assert status["usage"]["requests"] == 1
    assert status["usage"]["total_tokens"] == 150

    # The leftover reservation still gates fresh calls under a tight cap.
    enable_budget(monkeypatch, max_total_tokens=140)
    provider = CountingProvider()
    wire_factory(monkeypatch, provider)
    with pytest.raises(LLMBudgetExceededError) as caught:
        asyncio.run(factory.complete("hi", max_tokens=30))
    assert caught.value.reason == "tokens"
    assert provider.calls == 0

    # After the TTL the sweep converts it to a crashed settlement — still
    # counted, never free, and no longer blocking as "in flight".
    enable_budget(monkeypatch, max_total_tokens=10000, reservation_ttl_minutes=60)
    real_now = budget._now
    monkeypatch.setattr(budget, "_now", lambda: real_now() + 2 * 3600)
    assert asyncio.run(factory.complete("hi", max_tokens=30)) == "answer"
    rows = settled_rows()
    assert [row[0] for row in rows] == ["crashed", "completed"]
    usage = budget.budget_status()["usage"]
    assert usage["active_reservations"] == 0
    assert usage["requests"] == 2


@pytest.mark.asyncio
async def test_agentic_client_create_is_gated_and_settled(monkeypatch):
    enable_budget(monkeypatch, max_requests=2)

    calls = {"create": 0}

    async def create(**kwargs):
        calls["create"] += 1
        if kwargs.get("stream"):

            async def gen():
                yield NS(
                    usage={"prompt_tokens": 9, "completion_tokens": 4},
                    choices=[NS(delta=NS(content="chunk"))],
                )

            return gen()
        return NS(
            usage={"prompt_tokens": 9, "completion_tokens": 4},
            choices=[NS(message=NS(content="answer"))],
        )

    client = metrics.instrument_client(
        NS(chat=NS(completions=NS(create=create))), model="gpt-4o", provider="agentic-test"
    )

    result = await client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
    )
    assert result.usage == {"prompt_tokens": 9, "completion_tokens": 4}
    assert calls["create"] == 1

    stream = await client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": "hi"}], stream=True
    )
    collected = [chunk async for chunk in stream]
    assert collected and calls["create"] == 2

    with pytest.raises(LLMBudgetExceededError):
        await client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": "hi"}]
        )
    assert calls["create"] == 2

    usage = budget.budget_status()["usage"]
    assert usage["requests"] == 2
    assert usage["total_tokens"] == 26
    assert usage["active_reservations"] == 0
    assert [row[0] for row in settled_rows()] == ["completed", "completed"]


def test_llm_budget_settings_normalizer(tmp_path):
    from deeptutor.services.config.runtime_settings import RuntimeSettingsService

    service = RuntimeSettingsService.get_instance(tmp_path / "settings", process_env={})
    saved = service.save_llm_budget(
        {"enabled": "yes", "window_days": 0, "max_requests": -5, "max_cost_usd": "junk"}
    )
    assert saved["enabled"] is True
    assert saved["window_days"] == 1  # clamped to the minimum, not dropped
    assert saved["max_requests"] == 0
    assert saved["max_cost_usd"] == 0.0
    assert service.load_llm_budget() == saved


if __name__ == "__main__":
    _budget_worker()
