"""Public recording API for ATHF hunting metrics.

This is the **stability surface** that vaults, plugins, and AI assistants
should call when they want a metric event written. The helpers here build
``MetricEvent``s and append them to the workspace's append-only event log.

Storage paths (relative to the workspace root):

- ``metrics/events.jsonl`` — append-only event log (canonical)
- ``metrics/aggregates.json`` — derived view, refreshed by
  ``athf metrics extract`` or :class:`athf.core.metrics.Aggregator`

Typical use::

    import athf.metrics as m

    m.record_llm_call(
        model="claude-sonnet-4",
        input_tokens=120,
        output_tokens=80,
        duration_ms=420,
        agent="hypothesis-generator",
    )

    m.record_query(sql="SELECT 1", duration_ms=15, rows=1)
    m.record_web_search(query="lsass dumping", duration_ms=900)
    m.record_similarity_search(query="kerberoast", duration_ms=12)
    m.record_hunt_outcome(hunt_id="H-0001", outcome="TP")

Each helper takes optional explicit ``hunt_id`` / ``session_id``. If
omitted, they look up the current active session via
:class:`SessionManager` (lazy import to avoid cycles); when there's no
active session, the event is still recorded with those fields unset.

All helpers are best-effort: serialization or filesystem failures are
caught and silently dropped so metrics never break the calling code path.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from athf.core.cost_tracker import estimate_cost
from athf.core.metrics import (
    DEFAULT_EVENTS_PATH,
    EVENT_TYPES,
    EventStore,
    MetricEvent,
)

logger = logging.getLogger(__name__)


# A context provider may return either:
#   (hunt_id, session_id)                      — legacy 2-tuple, no org scope
#   (hunt_id, session_id, organization_id)     — current 3-tuple, tenant-scoped
# Both shapes are accepted so existing plugins keep working; tenant-scoped
# storage requires the 3-tuple form.
ContextTuple = Union[
    tuple[Optional[str], Optional[str]],
    tuple[Optional[str], Optional[str], Optional[str]],
]

_context_provider: Optional[Callable[[], ContextTuple]] = None


def register_context_provider(provider: Callable[[], ContextTuple]) -> None:
    """Register a callable returning ``(hunt_id, session_id[, organization_id])``.

    Plugins (vault extensions) call this once at import time to plug in their
    own session manager. ATHF core ships no provider, so without one
    registered, ``_resolve_active_context`` returns ``(None, None, None)`` and
    callers must pass ``hunt_id`` / ``session_id`` / ``organization_id``
    explicitly. The 2-tuple shape is accepted for backwards compatibility
    and treated as having no organization scope.
    """
    global _context_provider
    _context_provider = provider


def _resolve_active_context() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Best-effort lookup of (hunt_id, session_id, organization_id).

    Returns (None, None, None) if no provider is registered, no active
    session, or the provider raises for any reason. A legacy 2-tuple
    provider is normalized to ``(hunt, session, None)``.
    """
    provider = _context_provider
    if provider is None:
        return None, None, None
    try:
        result = provider()
    except Exception:
        return None, None, None
    if not isinstance(result, tuple):
        return None, None, None
    if len(result) == 2:
        return result[0], result[1], None
    if len(result) == 3:
        return result[0], result[1], result[2]
    return None, None, None


def _fill_context(
    hunt_id: Optional[str],
    session_id: Optional[str],
    organization_id: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Backfill missing hunt_id / session_id / organization_id from the provider."""
    if hunt_id is not None and session_id is not None and organization_id is not None:
        return hunt_id, session_id, organization_id
    ctx_hunt, ctx_session, ctx_org = _resolve_active_context()
    return (
        hunt_id or ctx_hunt,
        session_id or ctx_session,
        organization_id or ctx_org,
    )


def _store_for(workspace: Optional[Union[str, Path]] = None) -> EventStore:
    """Return an EventStore rooted at the workspace (cwd by default)."""
    if workspace is None:
        return EventStore(DEFAULT_EVENTS_PATH)
    return EventStore(Path(workspace) / DEFAULT_EVENTS_PATH)


def _append_safely(store: EventStore, event: MetricEvent) -> None:
    """Append while swallowing any exception: metrics must never break callers."""
    try:
        store.append(event)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("metrics append failed (%s): %s", type(exc).__name__, exc)


# ---------------------------------------------------------------------------
# Recording helpers
# ---------------------------------------------------------------------------


def record_llm_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    *,
    agent: Optional[str] = None,
    cost_usd: Optional[float] = None,
    hunt_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a single LLM API call.

    Cost is computed via :func:`athf.core.cost_tracker.estimate_cost` when
    ``cost_usd`` is not supplied, so callers can pass token counts and let
    ATHF do the pricing math. Pass ``cost_usd=0`` to record a zero-cost
    event explicitly (e.g. local model).
    """
    if cost_usd is None:
        cost_usd = estimate_cost(model, input_tokens, output_tokens)
    hunt_id, session_id, organization_id = _fill_context(
        hunt_id, session_id, organization_id
    )

    evt = MetricEvent(
        event_type="llm_call",
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        agent=agent,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
        custom=custom or {},
    )
    _append_safely(_store_for(workspace), evt)


def record_query(
    *,
    duration_ms: int,
    rows: Optional[int] = None,
    sql: Optional[str] = None,
    status: str = "success",
    hunt_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a single data-source query (Splunk, Elasticsearch, Athena, etc.).

    The SQL itself is **not** stored — only a hash, so query patterns can
    be grouped without leaking data.
    """
    hunt_id, session_id, organization_id = _fill_context(
        hunt_id, session_id, organization_id
    )

    custom_dict = dict(custom or {})
    if sql is not None:
        import hashlib

        custom_dict.setdefault("sql_hash", hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16])

    evt = MetricEvent(
        event_type="query",
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        duration_ms=duration_ms,
        rows_returned=rows,
        status=status,
        custom=custom_dict,
    )
    _append_safely(_store_for(workspace), evt)


def _hash_query(query: str) -> str:
    """Truncated SHA-256 of a query string. Lets us group repeats without storing text."""
    import hashlib

    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def record_web_search(
    *,
    query: str,
    duration_ms: int,
    result_count: Optional[int] = None,
    hunt_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a web search call (Tavily etc.). No cost field — by design.

    Search text is hashed (not persisted verbatim) so the metrics log
    doesn't leak hunt content, IOCs, or other sensitive user input. Pass
    ``custom={"query": ...}`` explicitly if a caller has already
    sanitized the text and wants to keep it.
    """
    hunt_id, session_id, organization_id = _fill_context(
        hunt_id, session_id, organization_id
    )

    custom_dict = dict(custom or {})
    custom_dict.setdefault("query_hash", _hash_query(query))
    if result_count is not None:
        custom_dict.setdefault("result_count", result_count)

    evt = MetricEvent(
        event_type="web_search",
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        duration_ms=duration_ms,
        custom=custom_dict,
    )
    _append_safely(_store_for(workspace), evt)


def record_similarity_search(
    *,
    duration_ms: int,
    query: Optional[str] = None,
    result_count: Optional[int] = None,
    hunt_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a similarity (TF-IDF) search.

    The raw query text is hashed before persisting (same approach as
    :func:`record_query`) so the metrics log never holds search prose.
    """
    hunt_id, session_id, organization_id = _fill_context(
        hunt_id, session_id, organization_id
    )

    custom_dict = dict(custom or {})
    if query is not None:
        custom_dict.setdefault("query_hash", _hash_query(query))
    if result_count is not None:
        custom_dict.setdefault("result_count", result_count)

    evt = MetricEvent(
        event_type="similarity_search",
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        duration_ms=duration_ms,
        custom=custom_dict,
    )
    _append_safely(_store_for(workspace), evt)


def record_hunt_outcome(
    *,
    hunt_id: str,
    outcome: str,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    custom: Optional[Dict[str, Any]] = None,
) -> None:
    """Record a hunt outcome (TP / FP / inconclusive).

    ``outcome`` is canonicalized to lowercase. Anything other than
    ``tp``, ``fp``, or ``inconclusive`` raises ``ValueError``.
    """
    canonical = outcome.strip().lower()
    if canonical not in {"tp", "fp", "inconclusive"}:
        raise ValueError(
            "outcome must be one of 'TP', 'FP', 'inconclusive'; got {!r}".format(outcome)
        )

    if session_id is None or organization_id is None:
        _, ctx_session, ctx_org = _resolve_active_context()
        if session_id is None:
            session_id = ctx_session
        if organization_id is None:
            organization_id = ctx_org

    evt = MetricEvent(
        event_type="hunt_outcome",
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        outcome=canonical,
        custom=dict(custom or {}),
    )
    _append_safely(_store_for(workspace), evt)


def record(
    event_type: str,
    *,
    hunt_id: Optional[str] = None,
    session_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    workspace: Optional[Union[str, Path]] = None,
    **fields: Any,
) -> None:
    """Generic recording escape hatch.

    Builds a :class:`MetricEvent` with arbitrary fields. Use the typed
    helpers above when one fits — this exists for plugins and ad-hoc
    scripting.
    """
    if event_type not in EVENT_TYPES:
        raise ValueError(
            "event_type must be one of {}; got {!r}".format(", ".join(EVENT_TYPES), event_type)
        )

    hunt_id, session_id, organization_id = _fill_context(
        hunt_id, session_id, organization_id
    )

    known_kwargs: Dict[str, Any] = {}
    custom: Dict[str, Any] = {}
    for k, v in fields.items():
        if k in {"event_type", "hunt_id", "session_id", "organization_id"}:
            # These are passed as explicit parameters; ignore duplicates in fields
            # to avoid TypeError "got multiple values for keyword argument".
            continue
        if k == "custom":
            if isinstance(v, dict):
                custom.update(v)
            continue
        if k in MetricEvent.__dataclass_fields__:
            known_kwargs[k] = v
        else:
            custom[k] = v

    evt = MetricEvent(
        event_type=event_type,
        organization_id=organization_id,
        hunt_id=hunt_id,
        session_id=session_id,
        custom=custom,
        **known_kwargs,
    )
    _append_safely(_store_for(workspace), evt)


__all__ = [
    "record_llm_call",
    "record_query",
    "record_web_search",
    "record_similarity_search",
    "record_hunt_outcome",
    "record",
    "register_context_provider",
]
