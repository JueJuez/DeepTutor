"""Task-local turn accounting at the LLM transport boundaries.

No prompts, credentials or responses are retained. Parallel child tasks share
one collector; different turns/users get different ContextVar bindings.
"""

from __future__ import annotations

from contextvars import ContextVar
import logging
import time
from typing import Any
import uuid

from .usage_estimation import estimate_prompt_tokens
from .usage_frame import usage_breakdown


class TurnUsage:
    def __init__(self, *, session_id: str = "", turn_id: str = "", source: str = "") -> None:
        self.session_id = session_id
        self.turn_id = turn_id or uuid.uuid4().hex
        self.source = source
        self.calls: list[dict[str, Any]] = []

    def summary(self) -> dict[str, Any] | None:
        if not self.calls:
            return None
        calls = self.calls
        totals = {
            key: sum(c.get(key, 0) or 0 for c in calls)
            for key in (
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "cache_read_input_tokens",
                "cache_creation_input_tokens",
                "reasoning_tokens",
                "duration_seconds",
            )
        }
        cache_calls = [c for c in calls if c.get("cache_read_input_tokens") is not None]
        cache_input = sum(c["prompt_tokens"] for c in cache_calls)
        timed = [c for c in calls if c.get("ttft_seconds") is not None]
        generated = [c for c in calls if c.get("generation_seconds") and not c["estimated"]]
        generation_seconds = sum(c["generation_seconds"] for c in generated)
        return {
            **totals,
            "total_calls": len(calls),
            "total_attempts": sum(max(1, c.get("attempts") or 1) for c in calls),
            "cache_reported_calls": len(cache_calls),
            "cache_input_tokens": cache_input,
            "cache_hit_rate": (
                totals["cache_read_input_tokens"] / cache_input if cache_input else None
            ),
            "ttft_seconds": (sum(c["ttft_seconds"] for c in timed) / len(timed) if timed else None),
            "ttft_calls": len(timed),
            "generation_seconds": generation_seconds,
            "timed_completion_tokens": sum(c["completion_tokens"] for c in generated),
            "tokens_per_second": (
                sum(c["completion_tokens"] for c in generated) / generation_seconds
                if generation_seconds
                else None
            ),
            "estimated_calls": sum(c["estimated"] for c in calls),
            "call_details": list(calls),
        }


current_usage: ContextVar[TurnUsage | None] = ContextVar("llm_turn_usage", default=None)
# Prevent native adapter and factory instrumentation from counting the same call twice.
measurement_active: ContextVar[bool] = ContextVar("llm_measurement_active", default=False)
# Task-local count of *underlying* HTTP attempts inside one measured call.
# Provider-internal compatibility retries (key rotation, Responses→chat
# fallback, parameter-compat retries) each issue another HTTP request while
# the upper layer sees a single measurement; they bump this counter so the
# persisted record can tell one request from several (docs 9.6 R3).
_http_attempts: ContextVar[int | None] = ContextVar("llm_http_attempts", default=None)


def note_llm_http_attempt() -> None:
    """Record one underlying HTTP attempt; no-op outside a measured call."""
    current = _http_attempts.get()
    if current is not None:
        _http_attempts.set(current + 1)


class CallMeasurement:
    def __init__(self, *, model: str = "", provider: str = "", messages: Any = None):
        self.enabled = not measurement_active.get()
        self.collector = current_usage.get() if self.enabled else None
        self.call_id = uuid.uuid4().hex
        self.started_at = time.time()
        self.ledger = None
        if self.enabled:
            from .usage_ledger import ledger_path

            try:
                self.ledger = ledger_path()
            except Exception:
                logging.getLogger(__name__).exception("Unable to resolve usage ledger")
        self.model, self.provider = model, provider
        self.started = time.perf_counter()
        self.first: float | None = None
        self.last: float | None = None
        self.output_chars = 0
        self.http_attempts = 0
        # Estimate only when the API does not report usage; never persist message text.
        self.estimated_prompt_tokens = estimate_prompt_tokens(messages) if self.enabled else 0
        self.usage: Any = None
        self.finished = False

    def delta(self, value: Any) -> None:
        if not value:
            return
        now = time.perf_counter()
        if self.first is None:
            self.first = now
        self.last = now
        self.output_chars += len(str(value))

    def chunk(self, chunk: Any) -> None:
        if usage := usage_breakdown(getattr(chunk, "usage", None)):
            self.usage = usage
        for choice in getattr(chunk, "choices", []) or []:
            delta = getattr(choice, "delta", None)
            if delta is not None:
                self.delta(getattr(delta, "content", None))
                self.delta(
                    getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
                )
                for tool in getattr(delta, "tool_calls", []) or []:
                    self.delta(getattr(getattr(tool, "function", None), "arguments", None))

    def finish(self, response: Any = None, *, status: str = "completed") -> dict[str, Any] | None:
        """Close the measurement; returns the record (or None when disabled).

        Returning the record lets a budget guard settle from the same numbers
        this meter just persisted, instead of re-deriving them.
        """
        if self.finished or not self.enabled:
            return None
        self.finished = True
        if response is not None:
            self.usage = getattr(response, "usage", None) or self.usage
        counts = usage_breakdown(self.usage)
        estimated = not bool(counts)
        if estimated:
            response_text = getattr(response, "content", "") or ""
            if not response_text:
                for choice in getattr(response, "choices", []) or []:
                    message = getattr(choice, "message", None)
                    response_text += str(getattr(message, "content", "") or "")
                    response_text += str(getattr(message, "reasoning_content", "") or "")
            output = self.output_chars or len(response_text)
            counts = {
                "prompt_tokens": self.estimated_prompt_tokens,
                "completion_tokens": int(output / 3.5),
            }
            counts["total_tokens"] = sum(counts.values())
        duration = time.perf_counter() - self.started
        # Use last model delta, excluding usage-only trailers and UI rendering.
        generation = self.last - self.first if self.first is not None and self.last else 0
        record = {
            "call_id": self.call_id,
            **counts,
            "model": self.model,
            "provider": self.provider,
            "status": status,
            "estimated": estimated,
            # Underlying HTTP attempts for this one measurement; providers that
            # never bump the counter still made the one visible attempt.
            "attempts": max(1, self.http_attempts),
            "duration_seconds": duration,
            "ttft_seconds": self.first - self.started if self.first is not None else None,
            "generation_seconds": generation if generation > 0 else None,
            "tokens_per_second": (
                counts["completion_tokens"] / generation
                if generation > 0 and not estimated
                else None
            ),
            "cache_hit_rate": (
                counts["cache_read_input_tokens"] / counts["prompt_tokens"]
                if "cache_read_input_tokens" in counts and counts["prompt_tokens"]
                else None
            ),
        }
        if self.collector is not None:
            self.collector.calls.append(record)
        if self.ledger is not None:
            from .usage_ledger import record_call

            try:
                record_call(
                    self.ledger,
                    record,
                    started_at=self.started_at,
                    session_id=self.collector.session_id if self.collector else "",
                    turn_id=self.collector.turn_id if self.collector else "",
                    source=self.collector.source if self.collector else "",
                )
            except Exception:
                logging.getLogger(__name__).exception("Unable to persist LLM usage")
        return record


async def measure_provider_call(call: Any, *, provider: str = "", **kwargs: Any) -> Any:
    """Measure each provider attempt, before callbacks are buffered by the factory."""
    meter = CallMeasurement(
        model=kwargs.get("model") or "", provider=provider, messages=kwargs.get("messages")
    )
    for key in ("on_content_delta", "on_reasoning_delta", "on_tool_args_delta"):
        callback = kwargs.get(key)
        if callback is not None:

            def wrap(original: Any) -> Any:
                async def measured(*args: Any, **kw: Any) -> Any:
                    meter.delta(args[-1] if args else None)
                    return await original(*args, **kw)

                return measured

            kwargs[key] = wrap(callback)
    token = measurement_active.set(True)
    attempts_token = _http_attempts.set(0)
    try:
        response = await call(**kwargs)
        meter.http_attempts = _http_attempts.get() or 0
        meter.finish(
            response, status="failed" if response.finish_reason == "error" else "completed"
        )
        return response
    except BaseException:
        meter.http_attempts = _http_attempts.get() or 0
        meter.finish(status="interrupted")
        raise
    finally:
        _http_attempts.reset(attempts_token)
        measurement_active.reset(token)


class MeasuredStream:
    def __init__(self, stream: Any, meter: CallMeasurement, budget: Any = None):
        self.stream, self.meter, self.budget = stream, meter, budget
        self.iterator: Any = None

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)

    def __aiter__(self) -> Any:
        return self

    async def __anext__(self) -> Any:
        token = measurement_active.set(True)
        try:
            if self.iterator is None:
                self.iterator = self.stream.__aiter__()
            chunk = await self.iterator.__anext__()
            self.meter.chunk(chunk)
            return chunk
        except StopAsyncIteration:
            record = self.meter.finish()
            if self.budget is not None:
                self.budget.settle(record, status="completed")
            raise
        except BaseException:
            self.meter.finish(status="interrupted")
            if self.budget is not None:
                self.budget.settle(status="interrupted")
            raise
        finally:
            measurement_active.reset(token)

    async def close(self) -> None:
        self.meter.finish(status="interrupted")
        if self.budget is not None and not self.budget.settled:
            self.budget.settle(status="interrupted")
        close = getattr(self.stream, "close", None) or getattr(self.stream, "aclose", None)
        if close:
            await close()

    async def aclose(self) -> None:
        await self.close()

    async def __aenter__(self) -> Any:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


def instrument_client(client: Any, *, model: str = "", provider: str = "") -> Any:
    create = client.chat.completions.create

    async def measured_create(**kwargs: Any) -> Any:
        from .budget import budget_call, current_source
        from .exceptions import LLMBudgetError

        resolved_model = str(kwargs.get("model") or model)
        meter = CallMeasurement(
            model=resolved_model, provider=provider, messages=kwargs.get("messages")
        )
        token = measurement_active.set(True)
        attempts_token = _http_attempts.set(0)
        budget = None
        try:
            budget = budget_call(
                model=resolved_model,
                provider=provider,
                source=current_source("agentic"),
                messages=kwargs.get("messages"),
                max_output_tokens=kwargs.get("max_tokens"),
            )
            if budget is not None:
                # A rejection here must not be metered as a provider failure:
                # no provider traffic happened.
                budget.reserve()
            result = await create(**kwargs)
            meter.http_attempts = _http_attempts.get() or 0
            if kwargs.get("stream"):
                return MeasuredStream(result, meter, budget)
            record = meter.finish(result)
            if budget is not None:
                budget.settle(
                    record if record is not None else getattr(result, "usage", None),
                    status="completed",
                )
            return result
        except LLMBudgetError:
            raise
        except BaseException:
            meter.http_attempts = _http_attempts.get() or 0
            meter.finish(status="failed")
            if budget is not None:
                budget.settle(status="interrupted")
            raise
        finally:
            _http_attempts.reset(attempts_token)
            measurement_active.reset(token)

    client.chat.completions.create = measured_create
    return client
