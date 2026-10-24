"""Persistent pre-call budget gate for LLM requests (docs 9.6 R2).

Every gated call reserves budget *before* the provider is touched and settles
*durable* usage *after* it ends. State lives in the owner's ``usage.sqlite3``
beside the ledger, so one backup covers both and the gate survives restarts.

Counting model for one window epoch::

    usage = settled rows (actual or estimated, audit-complete)
          + active reservations (reserve-time upper bounds)

Settlement rules (conservative by contract — unknown is never free):

* completed with provider usage -> exact tokens;
* completed without usage        -> prompt estimate + chars/3.5 output estimate;
* failed / interrupted           -> prompt estimate + reserved output bound;
* crashed (process died, TTL or window sweep) -> the reservation's own bounds.

Only identifiers, timestamps and numeric measurements are stored — no prompts,
responses, credentials or endpoint URLs. The gate is off unless the
``llm_budget`` settings file enables it.
"""

from __future__ import annotations

from contextlib import closing, suppress
import logging
import sqlite3
import time
from typing import Any
import uuid

from deeptutor.services.llm.exceptions import LLMBudgetError, LLMBudgetExceededError
from deeptutor.services.llm.usage_estimation import estimate_prompt_tokens
from deeptutor.services.llm.usage_frame import usage_breakdown

logger = logging.getLogger(__name__)

DEFAULT_RESERVED_OUTPUT_TOKENS = 4096
_WINDOW_SECONDS_PER_DAY = 86400.0


def _now() -> float:
    return time.time()


def _load_settings() -> dict[str, Any]:
    from deeptutor.services.config.runtime_settings import load_llm_budget_settings

    return load_llm_budget_settings()


def _store_path():
    """Resolve the owner-scoped store through the ledger (test-isolated)."""
    from deeptutor.services.llm import usage_ledger

    return usage_ledger.ledger_path()


def current_source(default: str = "") -> str:
    """Best-effort call source from the active turn collector, if any."""
    from deeptutor.services.llm.metrics import current_usage

    collector = current_usage.get()
    if collector is not None and collector.source:
        return collector.source
    return default


def _pricing(model: str) -> dict[str, float]:
    from deeptutor.logging.stats.llm_stats import get_pricing

    try:
        return get_pricing(model, fallback=False)
    except Exception:
        logger.exception("budget pricing lookup failed")
        return {}


def _cost_for(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    pricing = _pricing(model)
    if not pricing:
        return None
    return (prompt_tokens / 1000.0) * pricing["input"] + (completion_tokens / 1000.0) * pricing[
        "output"
    ]


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS budget_window (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        epoch INTEGER NOT NULL,
        window_started_at REAL NOT NULL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS budget_reservations (
        reservation_id TEXT PRIMARY KEY,
        epoch INTEGER NOT NULL,
        created_at REAL NOT NULL,
        model TEXT NOT NULL,
        provider TEXT NOT NULL,
        source TEXT NOT NULL,
        estimated_prompt_tokens INTEGER NOT NULL,
        reserved_output_tokens INTEGER NOT NULL,
        estimated_cost_usd REAL)""")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_budget_reservations_epoch ON budget_reservations(epoch)"
    )
    conn.execute("""CREATE TABLE IF NOT EXISTS budget_settled (
        reservation_id TEXT PRIMARY KEY,
        epoch INTEGER NOT NULL,
        created_at REAL NOT NULL,
        settled_at REAL NOT NULL,
        model TEXT NOT NULL,
        provider TEXT NOT NULL,
        source TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        estimated INTEGER NOT NULL,
        cost_usd REAL,
        status TEXT NOT NULL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_budget_settled_epoch ON budget_settled(epoch)")


def _connect(path) -> sqlite3.Connection:
    from deeptutor.utils.secret_files import ensure_private_directory, ensure_private_file

    ensure_private_directory(path.parent)
    conn = sqlite3.connect(path, timeout=5, isolation_level=None)
    try:
        _ensure_schema(conn)
        ensure_private_file(path)
    except BaseException:
        conn.close()
        raise
    return conn


class _WindowUsage:
    __slots__ = ("requests", "total_tokens", "cost_usd", "cost_known", "active")

    def __init__(self) -> None:
        self.requests = 0
        self.total_tokens = 0
        self.cost_usd = 0.0
        self.cost_known = True
        self.active = 0


def _usage_in_epoch(conn: sqlite3.Connection, epoch: int) -> _WindowUsage:
    usage = _WindowUsage()
    settled_requests, settled_tokens, settled_cost, settled_null = conn.execute(
        """SELECT COUNT(*), COALESCE(SUM(total_tokens), 0), SUM(cost_usd),
                  SUM(cost_usd IS NULL)
           FROM budget_settled WHERE epoch = ?""",
        (epoch,),
    ).fetchone()
    active_requests, active_tokens, active_cost, active_null = conn.execute(
        """SELECT COUNT(*),
                  COALESCE(SUM(estimated_prompt_tokens + reserved_output_tokens), 0),
                  SUM(estimated_cost_usd),
                  SUM(estimated_cost_usd IS NULL)
           FROM budget_reservations WHERE epoch = ?""",
        (epoch,),
    ).fetchone()
    usage.requests = int(settled_requests or 0) + int(active_requests or 0)
    usage.total_tokens = int(settled_tokens or 0) + int(active_tokens or 0)
    usage.cost_usd = float(settled_cost or 0.0) + float(active_cost or 0.0)
    # A NULL cost row (unpriced model, or history from before a cost cap was
    # configured) makes the window total unknowable — never silently zero.
    usage.cost_known = not settled_null and not active_null
    usage.active = int(active_requests or 0)
    return usage


def _settle_reservation_row(
    conn: sqlite3.Connection,
    row: tuple,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    estimated: bool,
    cost_usd: float | None,
    status: str,
    settled_at: float,
) -> None:
    (reservation_id, epoch, created_at, model, provider, source) = row
    conn.execute(
        """INSERT OR IGNORE INTO budget_settled (
               reservation_id, epoch, created_at, settled_at, model, provider, source,
               prompt_tokens, completion_tokens, total_tokens, estimated, cost_usd, status
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            reservation_id,
            epoch,
            created_at,
            settled_at,
            model,
            provider,
            source,
            prompt_tokens,
            completion_tokens,
            prompt_tokens + completion_tokens,
            1 if estimated else 0,
            cost_usd,
            status,
        ),
    )
    conn.execute("DELETE FROM budget_reservations WHERE reservation_id = ?", (reservation_id,))


def _sweep_actives(
    conn: sqlite3.Connection, *, epoch: int, cutoff: float | None, settled_at: float
) -> int:
    """Settle stale reservations of ``epoch`` as crashed; they keep counting.

    ``cutoff`` limits the sweep to reservations created before that timestamp
    (TTL sweep); ``None`` sweeps every remaining active of the epoch (window
    rollover / explicit reset).
    """
    if cutoff is None:
        rows = conn.execute(
            """SELECT reservation_id, epoch, created_at, model, provider, source,
                      estimated_prompt_tokens, reserved_output_tokens, estimated_cost_usd
               FROM budget_reservations WHERE epoch = ?""",
            (epoch,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT reservation_id, epoch, created_at, model, provider, source,
                      estimated_prompt_tokens, reserved_output_tokens, estimated_cost_usd
               FROM budget_reservations WHERE epoch = ? AND created_at < ?""",
            (epoch, cutoff),
        ).fetchall()
    for full_row in rows:
        head, est_prompt, reserved_output, est_cost = (
            full_row[:6],
            full_row[6],
            full_row[7],
            full_row[8],
        )
        _settle_reservation_row(
            conn,
            head,
            prompt_tokens=est_prompt,
            completion_tokens=reserved_output,
            estimated=True,
            cost_usd=est_cost,
            status="crashed",
            settled_at=settled_at,
        )
    return len(rows)


def _current_window(conn: sqlite3.Connection, *, window_days: int, now: float) -> int:
    """Return the active epoch, rolling the window over when it expired."""
    row = conn.execute("SELECT epoch, window_started_at FROM budget_window WHERE id = 1").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO budget_window (id, epoch, window_started_at) VALUES (1, 1, ?)", (now,)
        )
        return 1
    epoch, started_at = int(row[0]), float(row[1])
    if now - started_at >= window_days * _WINDOW_SECONDS_PER_DAY:
        # The old window's leftovers (if any process died mid-flight) are
        # settled as crashed inside their own epoch; the new epoch starts at 0.
        _sweep_actives(conn, epoch=epoch, cutoff=None, settled_at=now)
        conn.execute(
            "UPDATE budget_window SET epoch = ?, window_started_at = ? WHERE id = 1",
            (epoch + 1, now),
        )
        return epoch + 1
    return epoch


def reset_budget_window() -> dict[str, Any]:
    """Start a fresh window epoch immediately (operator action).

    Active reservations are settled as crashed in the old epoch, so a broken
    in-flight call can never keep gating the new window.
    """
    settings = _load_settings()
    path = _store_path()
    now = _now()
    with closing(_connect(path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT epoch FROM budget_window WHERE id = 1").fetchone()
            epoch = int(row[0]) if row else 0
            if row is None:
                conn.execute(
                    "INSERT INTO budget_window (id, epoch, window_started_at) VALUES (1, 1, ?)",
                    (now,),
                )
                new_epoch = 1
            else:
                _sweep_actives(conn, epoch=epoch, cutoff=None, settled_at=now)
                new_epoch = epoch + 1
                conn.execute(
                    "UPDATE budget_window SET epoch = ?, window_started_at = ? WHERE id = 1",
                    (new_epoch, now),
                )
            conn.execute("COMMIT")
            return {"epoch": new_epoch, "window_started_at": now}
        except BaseException:
            with suppress(sqlite3.Error):
                conn.execute("ROLLBACK")
            raise


class BudgetCall:
    """One gated logical LLM call: reserve before, settle after."""

    def __init__(
        self,
        *,
        settings: dict[str, Any],
        model: str,
        provider: str,
        source: str,
        estimated_prompt_tokens: int,
        reserved_output_tokens: int,
    ) -> None:
        self.settings = settings
        self.model = model
        self.provider = provider
        self.source = source
        self.estimated_prompt_tokens = max(0, int(estimated_prompt_tokens))
        self.reserved_output_tokens = max(1, int(reserved_output_tokens))
        self.reservation_id = uuid.uuid4().hex
        self.created_at = _now()
        self.settled = False
        self._estimated_cost_usd: float | None = None

    # -- reserve ---------------------------------------------------------

    def reserve(self) -> None:
        if self.settled:
            raise RuntimeError("budget call reserved twice")
        max_requests = int(self.settings.get("max_requests") or 0)
        max_tokens = int(self.settings.get("max_total_tokens") or 0)
        max_cost = float(self.settings.get("max_cost_usd") or 0.0)
        estimated_cost = _cost_for(
            self.model, self.estimated_prompt_tokens, self.reserved_output_tokens
        )
        try:
            path = _store_path()
            now = _now()
            with closing(_connect(path)) as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    epoch = _current_window(
                        conn,
                        window_days=int(self.settings.get("window_days") or 30),
                        now=now,
                    )
                    ttl = float(self.settings.get("reservation_ttl_minutes") or 120) * 60.0
                    _sweep_actives(conn, epoch=epoch, cutoff=now - ttl, settled_at=now)
                    usage = _usage_in_epoch(conn, epoch)
                    self._check_caps(
                        usage,
                        max_requests=max_requests,
                        max_tokens=max_tokens,
                        max_cost=max_cost,
                        estimated_cost=estimated_cost,
                    )
                    conn.execute(
                        """INSERT INTO budget_reservations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            self.reservation_id,
                            epoch,
                            now,
                            self.model,
                            self.provider,
                            self.source,
                            self.estimated_prompt_tokens,
                            self.reserved_output_tokens,
                            estimated_cost,
                        ),
                    )
                    self._estimated_cost_usd = estimated_cost
                    conn.execute("COMMIT")
                except BaseException:
                    with suppress(sqlite3.Error):
                        conn.execute("ROLLBACK")
                    raise
        except LLMBudgetError:
            raise
        except Exception as exc:
            # Fail closed: an unreadable store cannot verify the caps, so a
            # call must not slip through while the budget gate is enabled.
            raise LLMBudgetError(
                "LLM budget store unavailable; calls are blocked while the budget gate is enabled.",
                provider=self.provider,
            ) from exc

    def _check_caps(
        self,
        usage: _WindowUsage,
        *,
        max_requests: int,
        max_tokens: int,
        max_cost: float,
        estimated_cost: float | None,
    ) -> None:
        call_tokens = self.estimated_prompt_tokens + self.reserved_output_tokens
        if max_requests > 0 and usage.requests + 1 > max_requests:
            raise LLMBudgetExceededError(
                f"LLM budget request cap reached for this window "
                f"({usage.requests} used, cap {max_requests}).",
                reason="requests",
                usage={"requests": usage.requests, "active": usage.active},
                limit=max_requests,
                model=self.model,
            )
        if max_tokens > 0 and usage.total_tokens + call_tokens > max_tokens:
            raise LLMBudgetExceededError(
                f"LLM budget token cap reached for this window "
                f"({usage.total_tokens} settled/reserved, this call would add "
                f"~{call_tokens}, cap {max_tokens}).",
                reason="tokens",
                usage={"total_tokens": usage.total_tokens, "active": usage.active},
                limit=max_tokens,
                model=self.model,
            )
        if max_cost > 0:
            if not usage.cost_known:
                raise LLMBudgetExceededError(
                    "LLM budget cost cap is set but this window already contains "
                    "usage with an unknown price; new calls are blocked until the "
                    "window resets or the cap is removed.",
                    reason="unknown_history_cost",
                    usage={"cost_usd_known_part": usage.cost_usd, "active": usage.active},
                    limit=max_cost,
                    model=self.model,
                )
            if estimated_cost is None:
                raise LLMBudgetExceededError(
                    f"LLM budget cost cap is set but model '{self.model}' has no "
                    "price entry; unknown prices are not treated as free.",
                    reason="unknown_price",
                    usage={},
                    limit=max_cost,
                    model=self.model,
                )
            if usage.cost_usd + estimated_cost > max_cost:
                raise LLMBudgetExceededError(
                    f"LLM budget cost cap reached for this window "
                    f"(~{usage.cost_usd:.4f} USD used, this call would add "
                    f"~{estimated_cost:.4f} USD, cap {max_cost:.4f}).",
                    reason="cost",
                    usage={"cost_usd": usage.cost_usd, "active": usage.active},
                    limit=max_cost,
                    model=self.model,
                )

    # -- settle ----------------------------------------------------------

    def settle(
        self,
        usage: Any = None,
        *,
        status: str = "completed",
        output_chars: int = 0,
    ) -> None:
        """Settle this call durably; safe to call again (no-op).

        Post-call persistence must never discard an answer the user already
        received: store failures are logged and the reservation stays active,
        so the TTL sweep still settles it conservatively instead of losing it.
        """
        if self.settled:
            return
        prompt_tokens = self.estimated_prompt_tokens
        completion_tokens = self.reserved_output_tokens
        estimated = True
        if status == "completed":
            counts = usage_breakdown(usage) if usage is not None else {}
            if counts:
                prompt_tokens = int(counts["prompt_tokens"])
                completion_tokens = int(counts["completion_tokens"])
                estimated = bool(usage.get("estimated")) if isinstance(usage, dict) else False
            elif output_chars:
                completion_tokens = int(output_chars / 3.5)
        cost_usd = _cost_for(self.model, prompt_tokens, completion_tokens)
        try:
            path = _store_path()
            now = _now()
            with closing(_connect(path)) as conn:
                conn.execute("BEGIN IMMEDIATE")
                try:
                    row = conn.execute(
                        """SELECT reservation_id, epoch, created_at, model, provider, source
                           FROM budget_reservations WHERE reservation_id = ?""",
                        (self.reservation_id,),
                    ).fetchone()
                    if row is None:
                        # Already swept (TTL/window rollover) — the crashed row
                        # already counts this call conservatively.
                        self.settled = True
                        conn.execute("COMMIT")
                        return
                    _settle_reservation_row(
                        conn,
                        row,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        estimated=estimated,
                        cost_usd=cost_usd,
                        status=status,
                        settled_at=now,
                    )
                    conn.execute("COMMIT")
                    self.settled = True
                except BaseException:
                    with suppress(sqlite3.Error):
                        conn.execute("ROLLBACK")
                    raise
        except sqlite3.Error:
            logger.exception(
                "budget settle failed; reservation %s stays active until swept",
                self.reservation_id,
            )


def budget_call(
    *,
    model: str,
    provider: str = "",
    source: str = "",
    messages: Any = None,
    estimated_prompt_tokens: int | None = None,
    max_output_tokens: int | None = None,
) -> BudgetCall | None:
    """Open a budget guard for one logical LLM call, or ``None`` when off.

    ``max_output_tokens`` should be the caller's requested output bound; it is
    reserved as the conservative completion amount for unknown-usage outcomes.
    """
    settings = _load_settings()
    if not settings.get("enabled"):
        return None
    if estimated_prompt_tokens is None:
        estimated_prompt_tokens = estimate_prompt_tokens(messages) if messages is not None else 0
    reserved_output = int(max_output_tokens or 0)
    if reserved_output <= 0:
        reserved_output = DEFAULT_RESERVED_OUTPUT_TOKENS
    return BudgetCall(
        settings=settings,
        model=model,
        provider=provider,
        source=source,
        estimated_prompt_tokens=estimated_prompt_tokens,
        reserved_output_tokens=reserved_output,
    )


def budget_status() -> dict[str, Any]:
    """Read-only window/usage snapshot for diagnostics and tests."""
    settings = _load_settings()
    if not settings.get("enabled"):
        return {"enabled": False}
    path = _store_path()
    now = _now()
    if not path.exists():
        return {"enabled": True, "epoch": 0, "usage": _empty_usage()}
    with closing(sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=5)) as conn:
        try:
            row = conn.execute(
                "SELECT epoch, window_started_at FROM budget_window WHERE id = 1"
            ).fetchone()
        except sqlite3.OperationalError:
            return {"enabled": True, "epoch": 0, "usage": _empty_usage()}
        if row is None:
            return {"enabled": True, "epoch": 0, "usage": _empty_usage()}
        epoch = int(row[0])
        usage = _usage_in_epoch(conn, epoch)
        return {
            "enabled": True,
            "epoch": epoch,
            "window_started_at": float(row[1]),
            "window_days": int(settings.get("window_days") or 30),
            "caps": {
                "max_requests": int(settings.get("max_requests") or 0),
                "max_total_tokens": int(settings.get("max_total_tokens") or 0),
                "max_cost_usd": float(settings.get("max_cost_usd") or 0.0),
            },
            "usage": {
                "requests": usage.requests,
                "total_tokens": usage.total_tokens,
                "cost_usd": usage.cost_usd if usage.cost_known else None,
                "cost_known": usage.cost_known,
                "active_reservations": usage.active,
            },
            "now": now,
        }


def _empty_usage() -> dict[str, Any]:
    return {
        "requests": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "cost_known": True,
        "active_reservations": 0,
    }


__all__ = [
    "BudgetCall",
    "DEFAULT_RESERVED_OUTPUT_TOKENS",
    "LLMBudgetError",
    "LLMBudgetExceededError",
    "budget_call",
    "budget_status",
    "current_source",
    "reset_budget_window",
]
