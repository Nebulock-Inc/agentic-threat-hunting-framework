"""Hunting metrics: event schema, JSONL storage, and aggregator.

This is the canonical, vault-agnostic metrics core for ATHF. It defines:

- ``MetricEvent`` — a single immutable event record (LLM call, query,
  web search, similarity search, hunt outcome, or generic).
- ``EventStore`` — append-only JSONL writer at ``metrics/events.jsonl``
  with concurrency-safe appends (``fcntl.flock`` on POSIX, atomic-rename
  fallback elsewhere).
- ``Aggregator`` — scans ``events.jsonl`` plus the workspace's hunt files
  and produces ``metrics/aggregates.json`` with per-hunt and workspace
  rollups.

The public recording API lives in :mod:`athf.metrics`. This module
provides the primitives those helpers compose.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

EVENT_TYPES = (
    "llm_call",
    "query",
    "web_search",
    "similarity_search",
    "hunt_outcome",
    "manual",
)

DEFAULT_EVENTS_PATH = Path("metrics/events.jsonl")
DEFAULT_AGGREGATES_PATH = Path("metrics/aggregates.json")
SCHEMA_VERSION = "1.0.0"


def _now_iso() -> str:
    """Return current UTC time as RFC3339 with millisecond precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"


@dataclass(frozen=True)
class MetricEvent:
    """A single metric event.

    Fields are kept flat so events stream naturally into JSONL. Anything
    that doesn't fit the canonical fields goes into ``custom``.
    """

    event_type: str
    timestamp: str = field(default_factory=_now_iso)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])

    organization_id: Optional[str] = None
    hunt_id: Optional[str] = None
    session_id: Optional[str] = None
    agent: Optional[str] = None
    model: Optional[str] = None

    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    duration_ms: Optional[int] = None

    query_count: Optional[int] = None
    events_analyzed: Optional[int] = None
    rows_returned: Optional[int] = None
    status: Optional[str] = None  # success | error | timeout | inconclusive

    outcome: Optional[str] = None  # TP | FP | inconclusive (for hunt_outcome)

    custom: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.event_type not in EVENT_TYPES:
            raise ValueError(
                "event_type must be one of {}; got {!r}".format(
                    ", ".join(EVENT_TYPES), self.event_type
                )
            )

    def to_dict(self) -> Dict[str, Any]:
        """Render to a plain dict, dropping ``None`` fields except event_type."""
        raw = asdict(self)
        keep = {"event_type", "timestamp", "event_id", "custom"}
        return {k: v for k, v in raw.items() if k in keep or v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricEvent":
        """Build a MetricEvent from a dict, ignoring unknown keys.

        Raises ``ValueError`` for malformed payloads (wrong shape, bad
        ``custom`` type) so ``EventStore.read_all()`` can skip them
        without aborting the whole replay.
        """
        if not isinstance(data, dict):
            raise ValueError("event payload must be a JSON object")
        known = set(cls.__dataclass_fields__)
        kwargs = {k: v for k, v in data.items() if k in known}
        raw_custom = kwargs.get("custom")
        if raw_custom is None:
            custom: Dict[str, Any] = {}
        elif isinstance(raw_custom, dict):
            custom = dict(raw_custom)
        else:
            raise ValueError("custom must be an object")
        # Keep extra fields under custom for round-trip safety.
        for k, v in data.items():
            if k not in known and k != "custom":
                custom[k] = v
        kwargs["custom"] = custom
        try:
            return cls(**kwargs)
        except TypeError as exc:
            raise ValueError("invalid metric event payload") from exc


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


class EventStore:
    """Append-only JSONL event store.

    Concurrency:
        On POSIX systems each append acquires an exclusive ``fcntl.flock``
        on the open file descriptor before writing the line. On platforms
        without ``fcntl`` (Windows), we fall back to a process-local
        lock plus a write-then-rename pattern, which is safe within a
        single process and best-effort across processes.

    Storage layout:
        Each line is a single JSON object — one ``MetricEvent.to_dict()``.
        Files are created lazily on first write.
    """

    _PROCESS_LOCK = threading.Lock()

    def __init__(self, path: Union[str, Path] = DEFAULT_EVENTS_PATH) -> None:
        self.path = Path(path)

    # -- writes ------------------------------------------------------------

    def append(self, event: MetricEvent) -> None:
        """Append a single event. Never raises on serialization-safe input."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.to_dict(), separators=(",", ":")) + "\n"

        if _has_fcntl():
            self._append_flock(line)
        else:
            with EventStore._PROCESS_LOCK:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(line)

    def _append_flock(self, line: str) -> None:
        import fcntl

        with open(self.path, "a", encoding="utf-8") as fh:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
                fh.write(line)
                fh.flush()
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    # -- reads -------------------------------------------------------------

    def read_all(self) -> Iterator[MetricEvent]:
        """Yield every event in insertion order. Skips malformed lines."""
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield MetricEvent.from_dict(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue

    def __iter__(self) -> Iterator[MetricEvent]:  # convenience
        return self.read_all()


def _has_fcntl() -> bool:
    return sys.platform != "win32"


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------


# Body regexes for the LOCK hunt template, used as a fallback so that
# `athf metrics extract` works on any ATHF workspace. We ALWAYS prefer
# YAML frontmatter when present; the body regexes are fallback only.
_HUNT_BODY_QUERY_RE = re.compile(r"\*\*Total Queries Executed:\*\*\s*(\d+)")
_HUNT_BODY_QUERY_FRAC_RE = re.compile(r"Queries Executed:\s*(\d+)/(\d+)")
_HUNT_BODY_TIME_RE = re.compile(r"\*\*Total Query Execution Time:\*\*\s*([\d.]+)s")
_HUNT_BODY_EVENTS_RE = re.compile(r"\*\*Events Analyzed:\*\*\s*~?([\d.]+)([MK]?)\+?")
_HUNT_BODY_TP_RE = re.compile(r"\*\*True Positives:\*\*\s*(\d+)")
_HUNT_BODY_FP_RE = re.compile(r"\*\*False Positives:\*\*\s*(\d+)")
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

_NUMERIC_FRONTMATTER_FIELDS = (
    "events_analyzed",
    "total_queries",
    "execution_time_seconds",
    "execution_time_minutes",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "input_cost",
    "output_cost",
    "total_cost",
    "true_positives",
    "false_positives",
    "findings_count",
)


class Aggregator:
    """Combine ``events.jsonl`` with hunt files into ``aggregates.json``.

    The output is a derived, regenerable view — never the source of truth.
    Run :meth:`extract` to refresh it.
    """

    def __init__(
        self,
        workspace: Union[str, Path] = ".",
        events_path: Optional[Union[str, Path]] = None,
        aggregates_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.events_path = (
            Path(events_path) if events_path else self.workspace / DEFAULT_EVENTS_PATH
        )
        self.aggregates_path = (
            Path(aggregates_path)
            if aggregates_path
            else self.workspace / DEFAULT_AGGREGATES_PATH
        )

    # -- public ------------------------------------------------------------

    def extract(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Compute the aggregate dict and write it to ``aggregates.json``.

        If ``organization_id`` is supplied, only events with a matching
        ``organization_id`` (or no ``organization_id`` at all, treated as
        unscoped legacy data) are considered. Without it, the aggregator
        merges every event in the log — appropriate for single-tenant
        workspaces only.
        """
        per_hunt = self._scan_events(organization_id=organization_id)
        for hunt_id, file_metrics in self._scan_hunt_files().items():
            bucket = per_hunt.setdefault(hunt_id, _empty_hunt_bucket())
            # Normalize hunt-file frontmatter keys onto bucket totals when the
            # event store had nothing to contribute. Without this, hunt-file-only
            # data (queries / runtime / cost recorded in the hunt's frontmatter)
            # never reaches workspace totals because aggregation reads the
            # canonical keys (queries, query_duration_ms, cost_usd).
            if "total_queries" in file_metrics and bucket.get("queries", 0) == 0:
                bucket["queries"] = int(file_metrics["total_queries"] or 0)
            if (
                "execution_time_seconds" in file_metrics
                and bucket.get("query_duration_ms", 0) == 0
            ):
                bucket["query_duration_ms"] = int(
                    float(file_metrics["execution_time_seconds"] or 0) * 1000
                )
            if "total_cost" in file_metrics and bucket.get("cost_usd", 0.0) == 0.0:
                bucket["cost_usd"] = float(file_metrics["total_cost"] or 0.0)
            for k, v in file_metrics.items():
                if k not in bucket or bucket[k] in (None, 0):
                    bucket[k] = v

        workspace_totals = _aggregate_workspace(per_hunt)
        rollups = _aggregate_rollups(per_hunt)

        result = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _now_iso(),
            "workspace": str(self.workspace.resolve()),
            "totals": workspace_totals,
            "rollups": rollups,
            "hunts": per_hunt,
        }

        self.aggregates_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(self.aggregates_path, json.dumps(result, indent=2))
        return result

    def load(self) -> Optional[Dict[str, Any]]:
        """Return the last-written aggregates, or ``None`` if missing."""
        if not self.aggregates_path.exists():
            return None
        try:
            data: Any = json.loads(self.aggregates_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    # -- internal ----------------------------------------------------------

    def _scan_events(
        self, organization_id: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Group ``events.jsonl`` rows by hunt_id.

        Events without a ``hunt_id`` are workspace-level (manual records,
        ad-hoc CLI use). They get accumulated into a separate bucket and
        excluded from per-hunt aggregates and the hunt count.

        If ``organization_id`` is provided, events whose ``organization_id``
        is set and does not match are skipped. Events with no
        ``organization_id`` are always included (legacy/unscoped data).
        """
        per_hunt: Dict[str, Dict[str, Any]] = {}
        workspace_bucket = _empty_hunt_bucket()
        store = EventStore(self.events_path)
        for evt in store.read_all():
            if (
                organization_id is not None
                and evt.organization_id is not None
                and evt.organization_id != organization_id
            ):
                continue
            if evt.hunt_id:
                bucket = per_hunt.setdefault(evt.hunt_id, _empty_hunt_bucket())
            else:
                bucket = workspace_bucket
            _accumulate(bucket, evt)
        if workspace_bucket["events"]:
            per_hunt["_workspace"] = workspace_bucket
        return per_hunt

    def _scan_hunt_files(self) -> Dict[str, Dict[str, Any]]:
        """Walk ``hunts/`` and extract per-hunt metrics from frontmatter+body."""
        result: Dict[str, Dict[str, Any]] = {}
        hunts_dir = self.workspace / "hunts"
        if not hunts_dir.exists():
            return result

        for hunt_file in sorted(hunts_dir.rglob("H-*.md")):
            if "TEMPLATE" in hunt_file.name or "CUSTOMER" in hunt_file.name:
                continue
            if "investigations" in hunt_file.parts:
                continue
            try:
                content = hunt_file.read_text(encoding="utf-8")
            except OSError:
                continue

            metrics = self.extract_from_hunt_file(content)
            hunt_id = metrics.get("hunt_id") or hunt_file.stem
            metrics.pop("hunt_id", None)
            result[str(hunt_id)] = metrics
        return result

    @staticmethod
    def extract_from_hunt_file(content: str) -> Dict[str, Any]:
        """Pull metrics from a hunt markdown file.

        Frontmatter (YAML) wins over body regexes when both are present.
        """
        out: Dict[str, Any] = {}
        frontmatter = _parse_frontmatter(content)

        for key in (
            "hunt_id",
            "title",
            "status",
            "platform",
            "tactics",
            "techniques",
            "data_sources",
        ):
            if frontmatter.get(key):
                out[key] = frontmatter[key]

        for field_name in _NUMERIC_FRONTMATTER_FIELDS:
            if field_name in frontmatter:
                value = _coerce_number(frontmatter[field_name])
                if value is not None:
                    out[field_name] = value

        if "execution_time_minutes" in out and "execution_time_seconds" not in out:
            out["execution_time_seconds"] = out["execution_time_minutes"] * 60

        # Body fallbacks
        if "total_queries" not in out:
            m = _HUNT_BODY_QUERY_RE.search(content) or _HUNT_BODY_QUERY_FRAC_RE.search(content)
            if m:
                out["total_queries"] = int(m.group(1))

        if "execution_time_seconds" not in out:
            m = _HUNT_BODY_TIME_RE.search(content)
            if m:
                out["execution_time_seconds"] = float(m.group(1))

        if "events_analyzed" not in out:
            m = _HUNT_BODY_EVENTS_RE.search(content)
            if m:
                num = float(m.group(1))
                unit = m.group(2)
                if unit == "M":
                    num *= 1_000_000
                elif unit == "K":
                    num *= 1_000
                out["events_analyzed"] = int(num)

        if "true_positives" not in out:
            m = _HUNT_BODY_TP_RE.search(content)
            if m:
                out["true_positives"] = int(m.group(1))
        if "false_positives" not in out:
            m = _HUNT_BODY_FP_RE.search(content)
            if m:
                out["false_positives"] = int(m.group(1))

        # Derived
        tp = out.get("true_positives")
        fp = out.get("false_positives")
        if tp is not None and fp is not None:
            total = tp + fp
            if total > 0:
                out["precision"] = round(tp / total, 4)

        return out


def _empty_hunt_bucket() -> Dict[str, Any]:
    return {
        "llm_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "queries": 0,
        "query_duration_ms": 0,
        "rows_returned": 0,
        "web_searches": 0,
        "web_search_duration_ms": 0,
        "similarity_searches": 0,
        "true_positives": 0,
        "false_positives": 0,
        "events": [],
        "outcomes": [],
    }


def _accumulate(bucket: Dict[str, Any], evt: MetricEvent) -> None:
    if evt.event_type == "llm_call":
        bucket["llm_calls"] += 1
        bucket["input_tokens"] += evt.input_tokens or 0
        bucket["output_tokens"] += evt.output_tokens or 0
        bucket["cost_usd"] = round((bucket["cost_usd"] + (evt.cost_usd or 0.0)), 6)
    elif evt.event_type == "query":
        bucket["queries"] += 1
        bucket["query_duration_ms"] += evt.duration_ms or 0
        bucket["rows_returned"] += evt.rows_returned or 0
    elif evt.event_type == "web_search":
        bucket["web_searches"] += 1
        bucket["web_search_duration_ms"] += evt.duration_ms or 0
    elif evt.event_type == "similarity_search":
        bucket["similarity_searches"] += 1
    elif evt.event_type == "hunt_outcome":
        if evt.outcome:
            bucket["outcomes"].append(evt.outcome)
            normalized = evt.outcome.strip().upper()
            if normalized == "TP":
                bucket["true_positives"] += 1
            elif normalized == "FP":
                bucket["false_positives"] += 1
    bucket["events"].append({"id": evt.event_id, "type": evt.event_type, "ts": evt.timestamp})


def _aggregate_workspace(per_hunt: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    # ``_workspace`` is the synthetic bucket for events with no hunt_id;
    # exclude it from the hunt count so workspace-level activity doesn't
    # masquerade as a real hunt.
    totals = {
        "hunts": sum(1 for k in per_hunt if k != "_workspace"),
        "llm_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0,
        "queries": 0,
        "query_duration_ms": 0,
        "events_analyzed": 0,
        "web_searches": 0,
        "similarity_searches": 0,
        "true_positives": 0,
        "false_positives": 0,
    }
    for bucket in per_hunt.values():
        for k in (
            "llm_calls",
            "input_tokens",
            "output_tokens",
            "queries",
            "query_duration_ms",
            "web_searches",
            "similarity_searches",
        ):
            totals[k] += int(bucket.get(k, 0) or 0)
        totals["cost_usd"] = round(totals["cost_usd"] + float(bucket.get("cost_usd", 0.0) or 0.0), 6)
        totals["events_analyzed"] += int(bucket.get("events_analyzed", 0) or 0)
        totals["true_positives"] += int(bucket.get("true_positives", 0) or 0)
        totals["false_positives"] += int(bucket.get("false_positives", 0) or 0)
    return totals


def _aggregate_rollups(per_hunt: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Roll up cost + query counts by tactic / technique / data-source / platform."""
    rollups: Dict[str, Dict[str, int]] = {
        "by_platform": {},
        "by_tactic": {},
        "by_technique": {},
        "by_data_source": {},
    }
    for bucket in per_hunt.values():
        for label_field, key in (
            ("platform", "by_platform"),
            ("tactics", "by_tactic"),
            ("techniques", "by_technique"),
            ("data_sources", "by_data_source"),
        ):
            value = bucket.get(label_field)
            if not value:
                continue
            for label in _flatten_label(value):
                rollups[key][label] = rollups[key].get(label, 0) + 1
    return rollups


def _flatten_label(value: Any) -> Iterable[str]:
    if isinstance(value, list):
        for item in value:
            yield str(item)
    elif isinstance(value, str):
        # Allow comma-separated lists from frontmatter.
        for item in value.split(","):
            item = item.strip().strip("'").strip('"')
            if item:
                yield item


def _parse_frontmatter(content: str) -> Dict[str, Any]:
    match = _FRONTMATTER_RE.search(content)
    if not match:
        return {}
    try:
        import yaml  # local import; pyyaml is a hard dep

        data = yaml.safe_load(match.group(1)) or {}
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    # Permissive line-by-line fallback.
    out: Dict[str, Any] = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def _coerce_number(value: Any) -> Optional[Union[int, float]]:
    if isinstance(value, (int, float)):
        return value
    if not isinstance(value, str):
        return None
    raw = value.strip().strip("'").strip('"')
    if not raw:
        return None
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return None


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` via temp-file + rename for atomicity."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


__all__ = [
    "EVENT_TYPES",
    "DEFAULT_EVENTS_PATH",
    "DEFAULT_AGGREGATES_PATH",
    "SCHEMA_VERSION",
    "MetricEvent",
    "EventStore",
    "Aggregator",
]
