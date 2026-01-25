"""Centralized metrics tracking for hunt execution.

Auto-captures ClickHouse query times and Bedrock LLM token usage,
associating metrics with active hunt sessions when available.
"""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ClickHouseQueryMetric:
    """Metric for a single ClickHouse query execution."""

    id: str
    timestamp: str
    sql_hash: str  # SHA256 of SQL for grouping (privacy)
    duration_ms: int
    rows_returned: int
    status: str  # success | error | timeout


@dataclass
class BedrockCallMetric:
    """Metric for a single Bedrock LLM call."""

    id: str
    timestamp: str
    agent: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int


@dataclass
class SessionMetrics:
    """Metrics for a single hunt session."""

    session_id: str
    hunt_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    clickhouse_queries: List[ClickHouseQueryMetric] = field(default_factory=list)
    bedrock_calls: List[BedrockCallMetric] = field(default_factory=list)

    @property
    def clickhouse_totals(self) -> Dict[str, Any]:
        """Calculate ClickHouse totals for this session."""
        return {
            "query_count": len(self.clickhouse_queries),
            "total_duration_ms": sum(q.duration_ms for q in self.clickhouse_queries),
            "total_rows_returned": sum(q.rows_returned for q in self.clickhouse_queries),
        }

    @property
    def bedrock_totals(self) -> Dict[str, Any]:
        """Calculate Bedrock totals for this session."""
        return {
            "call_count": len(self.bedrock_calls),
            "total_input_tokens": sum(c.input_tokens for c in self.bedrock_calls),
            "total_output_tokens": sum(c.output_tokens for c in self.bedrock_calls),
            "total_cost_usd": round(sum(c.cost_usd for c in self.bedrock_calls), 4),
        }


class MetricsTracker:
    """Singleton tracker for execution metrics.

    Auto-captures ClickHouse query times and Bedrock LLM usage.
    Persists to metrics/execution_metrics.json.

    Usage:
        tracker = MetricsTracker.get_instance()
        tracker.log_clickhouse_query(sql, duration_ms, rows, "success")
        tracker.log_bedrock_call("hypothesis-generator", model_id, in_tok, out_tok, cost, dur)
    """

    _instance: Optional["MetricsTracker"] = None
    _metrics_file: Path = Path("metrics/execution_metrics.json")
    _data: Optional[Dict[str, Any]] = None

    def __new__(cls) -> "MetricsTracker":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MetricsTracker":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _hash_sql(self, sql: str) -> str:
        """Create SHA256 hash of SQL query for grouping."""
        return hashlib.sha256(sql.encode()).hexdigest()[:16]

    def _get_current_context(self) -> tuple[Optional[str], Optional[str]]:
        """Get current hunt_id and session_id from active session.

        Returns:
            Tuple of (hunt_id, session_id), both None if no active session.
        """
        try:
            # Lazy import to avoid circular dependencies
            from athf.core.session_manager import SessionManager

            manager = SessionManager.get_instance()
            session = manager.get_active_session()
            if session:
                return session.hunt_id, session.session_id
        except Exception:
            pass  # No active session or import failed
        return None, None

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from file or create empty structure."""
        if self._data is not None:
            return self._data

        if self._metrics_file.exists():
            try:
                with open(self._metrics_file, "r") as f:
                    self._data = json.load(f)
                    return self._data
            except (json.JSONDecodeError, IOError):
                pass  # Fall through to create new

        # Create empty structure
        self._data = {
            "version": "1.0.0",
            "last_updated": self._now_iso(),
            "hunts": {},
            "sessions": {},
            "no_session": {"clickhouse_queries": [], "bedrock_calls": []},
        }
        return self._data

    def _save_metrics(self) -> None:
        """Save metrics to file with atomic write."""
        if self._data is None:
            return

        self._data["last_updated"] = self._now_iso()

        # Ensure directory exists
        self._metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file then rename
        try:
            fd, tmp_path = tempfile.mkstemp(dir=self._metrics_file.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(self._data, f, indent=2)
                os.rename(tmp_path, self._metrics_file)
            except Exception:
                # Clean up temp file on error
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except Exception:
            # If atomic write fails, try direct write
            with open(self._metrics_file, "w") as f:
                json.dump(self._data, f, indent=2)

    def _ensure_session_entry(self, hunt_id: str, session_id: str) -> Dict[str, Any]:
        """Ensure session entry exists in data structure."""
        data = self._load_metrics()

        # Ensure hunt entry
        if hunt_id not in data["hunts"]:
            data["hunts"][hunt_id] = {
                "hunt_id": hunt_id,
                "sessions": [],
                "totals": {
                    "clickhouse": {
                        "query_count": 0,
                        "total_duration_ms": 0,
                        "total_rows_returned": 0,
                    },
                    "bedrock": {
                        "call_count": 0,
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_cost_usd": 0.0,
                    },
                },
            }

        # Ensure session entry
        if session_id not in data["sessions"]:
            data["sessions"][session_id] = {
                "session_id": session_id,
                "hunt_id": hunt_id,
                "start_time": self._now_iso(),
                "clickhouse_queries": [],
                "bedrock_calls": [],
            }
            # Add session to hunt's session list
            if session_id not in data["hunts"][hunt_id]["sessions"]:
                data["hunts"][hunt_id]["sessions"].append(session_id)

        session_data: dict[str, Any] = data["sessions"][session_id]
        return session_data

    def _update_hunt_totals(self, hunt_id: str) -> None:
        """Recalculate hunt totals from all sessions."""
        data = self._load_metrics()
        if hunt_id not in data["hunts"]:
            return

        hunt = data["hunts"][hunt_id]
        ch_totals = {"query_count": 0, "total_duration_ms": 0, "total_rows_returned": 0}
        br_totals = {
            "call_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
        }

        for session_id in hunt.get("sessions", []):
            if session_id in data["sessions"]:
                session = data["sessions"][session_id]

                # ClickHouse totals
                for q in session.get("clickhouse_queries", []):
                    ch_totals["query_count"] += 1
                    ch_totals["total_duration_ms"] += q.get("duration_ms", 0)
                    ch_totals["total_rows_returned"] += q.get("rows_returned", 0)

                # Bedrock totals
                for c in session.get("bedrock_calls", []):
                    br_totals["call_count"] += 1
                    br_totals["total_input_tokens"] += c.get("input_tokens", 0)
                    br_totals["total_output_tokens"] += c.get("output_tokens", 0)
                    br_totals["total_cost_usd"] += c.get("cost_usd", 0.0)

        br_totals["total_cost_usd"] = round(br_totals["total_cost_usd"], 4)
        hunt["totals"] = {"clickhouse": ch_totals, "bedrock": br_totals}

    def log_clickhouse_query(
        self,
        sql: str,
        duration_ms: int,
        rows: int,
        status: str = "success",
    ) -> None:
        """Log a ClickHouse query execution.

        Args:
            sql: SQL query executed (hashed for storage)
            duration_ms: Query execution time in milliseconds
            rows: Number of rows returned
            status: Query status (success, error, timeout)
        """
        hunt_id, session_id = self._get_current_context()
        data = self._load_metrics()

        # Create metric entry
        if session_id and hunt_id:
            session = self._ensure_session_entry(hunt_id, session_id)
            query_num = len(session.get("clickhouse_queries", [])) + 1
            metric_id = f"ch-{query_num:03d}"
            target = session.setdefault("clickhouse_queries", [])
        else:
            query_num = len(data["no_session"].get("clickhouse_queries", [])) + 1
            metric_id = f"ch-nosess-{query_num:03d}"
            target = data["no_session"].setdefault("clickhouse_queries", [])

        metric = {
            "id": metric_id,
            "timestamp": self._now_iso(),
            "sql_hash": self._hash_sql(sql),
            "duration_ms": duration_ms,
            "rows_returned": rows,
            "status": status,
        }
        target.append(metric)

        # Update hunt totals if we have a hunt context
        if hunt_id:
            self._update_hunt_totals(hunt_id)

        self._save_metrics()

    def log_bedrock_call(
        self,
        agent: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
    ) -> None:
        """Log a Bedrock LLM call.

        Args:
            agent: Agent name (e.g., "hypothesis-generator")
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Estimated cost in USD
            duration_ms: Call duration in milliseconds
        """
        hunt_id, session_id = self._get_current_context()
        data = self._load_metrics()

        # Create metric entry
        if session_id and hunt_id:
            session = self._ensure_session_entry(hunt_id, session_id)
            call_num = len(session.get("bedrock_calls", [])) + 1
            metric_id = f"br-{call_num:03d}"
            target = session.setdefault("bedrock_calls", [])
        else:
            call_num = len(data["no_session"].get("bedrock_calls", [])) + 1
            metric_id = f"br-nosess-{call_num:03d}"
            target = data["no_session"].setdefault("bedrock_calls", [])

        metric = {
            "id": metric_id,
            "timestamp": self._now_iso(),
            "agent": agent,
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 4),
            "duration_ms": duration_ms,
        }
        target.append(metric)

        # Update hunt totals if we have a hunt context
        if hunt_id:
            self._update_hunt_totals(hunt_id)

        self._save_metrics()

    def get_hunt_metrics(self, hunt_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific hunt.

        Args:
            hunt_id: Hunt identifier (e.g., "H-0019")

        Returns:
            Hunt metrics dict or None if not found
        """
        data = self._load_metrics()
        result: Optional[Dict[str, Any]] = data["hunts"].get(hunt_id)
        return result

    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific session.

        Args:
            session_id: Session identifier (e.g., "H-0019-2025-12-30")

        Returns:
            Session metrics dict or None if not found
        """
        data = self._load_metrics()
        result: Optional[Dict[str, Any]] = data["sessions"].get(session_id)
        return result

    def get_aggregate_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregate metrics summary.

        Args:
            days: Number of days to include (0 for all time)

        Returns:
            Aggregate metrics dict
        """
        data = self._load_metrics()

        # Calculate totals across all hunts
        ch_totals = {"query_count": 0, "total_duration_ms": 0, "total_rows_returned": 0}
        br_totals = {
            "call_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
        }

        for hunt in data.get("hunts", {}).values():
            totals = hunt.get("totals", {})
            ch = totals.get("clickhouse", {})
            br = totals.get("bedrock", {})

            ch_totals["query_count"] += ch.get("query_count", 0)
            ch_totals["total_duration_ms"] += ch.get("total_duration_ms", 0)
            ch_totals["total_rows_returned"] += ch.get("total_rows_returned", 0)

            br_totals["call_count"] += br.get("call_count", 0)
            br_totals["total_input_tokens"] += br.get("total_input_tokens", 0)
            br_totals["total_output_tokens"] += br.get("total_output_tokens", 0)
            br_totals["total_cost_usd"] += br.get("total_cost_usd", 0.0)

        # Include no-session metrics
        no_sess = data.get("no_session", {})
        ch_totals["query_count"] += len(no_sess.get("clickhouse_queries", []))
        for q in no_sess.get("clickhouse_queries", []):
            ch_totals["total_duration_ms"] += q.get("duration_ms", 0)
            ch_totals["total_rows_returned"] += q.get("rows_returned", 0)

        br_totals["call_count"] += len(no_sess.get("bedrock_calls", []))
        for c in no_sess.get("bedrock_calls", []):
            br_totals["total_input_tokens"] += c.get("input_tokens", 0)
            br_totals["total_output_tokens"] += c.get("output_tokens", 0)
            br_totals["total_cost_usd"] += c.get("cost_usd", 0.0)

        br_totals["total_cost_usd"] = round(br_totals["total_cost_usd"], 4)

        return {
            "hunt_count": len(data.get("hunts", {})),
            "session_count": len(data.get("sessions", {})),
            "clickhouse": ch_totals,
            "bedrock": br_totals,
            "last_updated": data.get("last_updated"),
        }

    def get_metrics_in_time_window(
        self,
        session_id: str,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        """Get session metrics including no_session calls within time window.

        This captures Bedrock calls that occurred during the session time window
        but were logged before the session started (e.g., hypothesis generation
        that ran before 'athf session start').

        Args:
            session_id: Session identifier (e.g., "H-0019-2025-12-30")
            start_time: Session start time in ISO format
            end_time: Session end time in ISO format

        Returns:
            Dict with combined metrics:
            {
                "clickhouse": {"query_count": N, "total_duration_ms": N, ...},
                "bedrock": {"call_count": N, "total_input_tokens": N, ...},
            }
        """
        from datetime import datetime

        data = self._load_metrics()

        # Initialize totals
        ch_totals = {"query_count": 0, "total_duration_ms": 0, "total_rows_returned": 0}
        br_totals = {
            "call_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0,
        }

        # Parse time window
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # If time parsing fails, return empty metrics
            return {"clickhouse": ch_totals, "bedrock": br_totals}

        # Get session-specific metrics
        session_metrics = data.get("sessions", {}).get(session_id, {})

        for q in session_metrics.get("clickhouse_queries", []):
            ch_totals["query_count"] += 1
            ch_totals["total_duration_ms"] += q.get("duration_ms", 0)
            ch_totals["total_rows_returned"] += q.get("rows_returned", 0)

        for c in session_metrics.get("bedrock_calls", []):
            br_totals["call_count"] += 1
            br_totals["total_input_tokens"] += c.get("input_tokens", 0)
            br_totals["total_output_tokens"] += c.get("output_tokens", 0)
            br_totals["total_cost_usd"] += c.get("cost_usd", 0.0)

        # Also include no_session metrics within the time window
        no_sess = data.get("no_session", {})

        for q in no_sess.get("clickhouse_queries", []):
            try:
                q_time = datetime.fromisoformat(q.get("timestamp", "").replace("Z", "+00:00"))
                if start_dt <= q_time <= end_dt:
                    ch_totals["query_count"] += 1
                    ch_totals["total_duration_ms"] += q.get("duration_ms", 0)
                    ch_totals["total_rows_returned"] += q.get("rows_returned", 0)
            except (ValueError, AttributeError):
                continue

        for c in no_sess.get("bedrock_calls", []):
            try:
                c_time = datetime.fromisoformat(c.get("timestamp", "").replace("Z", "+00:00"))
                if start_dt <= c_time <= end_dt:
                    br_totals["call_count"] += 1
                    br_totals["total_input_tokens"] += c.get("input_tokens", 0)
                    br_totals["total_output_tokens"] += c.get("output_tokens", 0)
                    br_totals["total_cost_usd"] += c.get("cost_usd", 0.0)
            except (ValueError, AttributeError):
                continue

        br_totals["total_cost_usd"] = round(br_totals["total_cost_usd"], 4)

        return {"clickhouse": ch_totals, "bedrock": br_totals}
