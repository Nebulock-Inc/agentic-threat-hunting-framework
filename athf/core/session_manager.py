"""Hunt session management for capturing execution context."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class SessionError(Exception):
    """Session management error."""

    pass


@dataclass
class QueryLog:
    """Log entry for a query execution."""

    id: str
    timestamp: str
    sql: str
    result_count: int
    duration_ms: int
    outcome: str  # success | refined | abandoned
    note: Optional[str] = None


@dataclass
class DecisionLog:
    """Log entry for a decision point."""

    timestamp: str
    phase: str  # hypothesis | analysis | pivot
    decision: str
    rationale: Optional[str] = None
    alternatives: Optional[List[str]] = None


@dataclass
class FindingLog:
    """Log entry for a finding."""

    timestamp: str
    finding_type: str  # tp | fp | pattern | suspicious
    description: str
    count: int = 1
    escalated: bool = False


@dataclass
class Session:
    """Hunt execution session."""

    hunt_id: str
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_min: Optional[int] = None
    queries: List[QueryLog] = field(default_factory=list)
    decisions: List[DecisionLog] = field(default_factory=list)
    findings: List[FindingLog] = field(default_factory=list)

    @property
    def query_count(self) -> int:
        """Get total number of queries."""
        return len(self.queries)

    @property
    def finding_count(self) -> int:
        """Get total number of findings."""
        return len(self.findings)

    @property
    def tp_count(self) -> int:
        """Get count of true positive findings."""
        return len([f for f in self.findings if f.finding_type == "tp"])

    @property
    def fp_count(self) -> int:
        """Get count of false positive findings."""
        return len([f for f in self.findings if f.finding_type == "fp"])

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert to metadata dict for session.yaml (committed)."""
        return {
            "hunt_id": self.hunt_id,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_min": self.duration_min,
            "query_count": self.query_count,
            "finding_count": self.finding_count,
            "tp_count": self.tp_count,
            "fp_count": self.fp_count,
        }


class SessionManager:
    """Singleton manager for hunt sessions.

    Handles session lifecycle:
    - start_session(): Create new session
    - log_query(): Record query execution
    - log_decision(): Record decision point
    - log_finding(): Record finding
    - end_session(): Close session, generate summary
    """

    _instance: Optional["SessionManager"] = None
    _active_session: Optional[Session] = None
    _sessions_dir: Path = Path("sessions")

    def __new__(cls) -> "SessionManager":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "SessionManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_active_file(self) -> Path:
        """Get path to .active file."""
        return self._sessions_dir / ".active"

    def _get_session_dir(self, session_id: str) -> Path:
        """Get path to session directory."""
        return self._sessions_dir / session_id

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _today_str(self) -> str:
        """Get today's date as string."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def get_active_session(self) -> Optional[Session]:
        """Get currently active session, if any."""
        if self._active_session:
            return self._active_session

        # Try to load from .active file
        active_file = self._get_active_file()
        if active_file.exists():
            try:
                session_id = active_file.read_text().strip()
                if session_id:
                    return self._load_session(session_id)
            except Exception:
                pass

        return None

    def _load_session(self, session_id: str) -> Optional[Session]:
        """Load session from disk."""
        session_dir = self._get_session_dir(session_id)
        session_file = session_dir / "session.yaml"

        if not session_file.exists():
            return None

        try:
            with open(session_file, "r") as f:
                data = yaml.safe_load(f)

            session = Session(
                hunt_id=data["hunt_id"],
                session_id=data["session_id"],
                start_time=data["start_time"],
                end_time=data.get("end_time"),
                duration_min=data.get("duration_min"),
            )

            # Load queries
            queries_file = session_dir / "queries.yaml"
            if queries_file.exists():
                with open(queries_file, "r") as f:
                    queries_data = yaml.safe_load(f) or {}
                    for q in queries_data.get("queries", []):
                        session.queries.append(
                            QueryLog(
                                id=q["id"],
                                timestamp=q["timestamp"],
                                sql=q["sql"],
                                result_count=q["result_count"],
                                duration_ms=q["duration_ms"],
                                outcome=q["outcome"],
                                note=q.get("note"),
                            )
                        )

            # Load decisions
            decisions_file = session_dir / "decisions.yaml"
            if decisions_file.exists():
                with open(decisions_file, "r") as f:
                    decisions_data = yaml.safe_load(f) or {}
                    for d in decisions_data.get("decisions", []):
                        session.decisions.append(
                            DecisionLog(
                                timestamp=d["timestamp"],
                                phase=d["phase"],
                                decision=d["decision"],
                                rationale=d.get("rationale"),
                                alternatives=d.get("alternatives"),
                            )
                        )

            # Load findings
            findings_file = session_dir / "findings.yaml"
            if findings_file.exists():
                with open(findings_file, "r") as f:
                    findings_data = yaml.safe_load(f) or {}
                    for f_item in findings_data.get("findings", []):
                        session.findings.append(
                            FindingLog(
                                timestamp=f_item["timestamp"],
                                finding_type=f_item["type"],
                                description=f_item["description"],
                                count=f_item.get("count", 1),
                                escalated=f_item.get("escalated", False),
                            )
                        )

            self._active_session = session
            return session

        except Exception as e:
            raise SessionError(f"Failed to load session {session_id}: {e}")

    def start_session(self, hunt_id: str) -> Session:
        """Start a new hunt session.

        Args:
            hunt_id: Hunt identifier (e.g., H-0025)

        Returns:
            New Session instance

        Raises:
            SessionError: If session already active or creation fails
        """
        # Check for existing active session
        existing = self.get_active_session()
        if existing:
            raise SessionError(f"Session already active: {existing.session_id}. " f"End it with 'athf session end' first.")

        # Create session ID
        session_id = f"{hunt_id}-{self._today_str()}"

        # Handle multiple sessions on same day
        session_dir = self._get_session_dir(session_id)
        counter = 1
        while session_dir.exists():
            counter += 1
            session_id = f"{hunt_id}-{self._today_str()}-{counter}"
            session_dir = self._get_session_dir(session_id)

        # Create session directory
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create session
        session = Session(
            hunt_id=hunt_id,
            session_id=session_id,
            start_time=self._now_iso(),
        )

        # Write session.yaml
        self._save_session_metadata(session)

        # Write .active pointer
        self._get_active_file().write_text(session_id)

        self._active_session = session
        return session

    def _save_session_metadata(self, session: Session) -> None:
        """Save session metadata to session.yaml."""
        session_dir = self._get_session_dir(session.session_id)
        session_file = session_dir / "session.yaml"

        # Get base metadata
        metadata = session.to_metadata_dict()

        # Add LLM metrics if session has ended (has end_time)
        if session.end_time:
            llm_metrics = self._get_session_llm_metrics(session)
            metadata["llm_calls"] = llm_metrics.get("call_count", 0)
            metadata["llm_total_tokens"] = llm_metrics.get("total_input_tokens", 0) + llm_metrics.get("total_output_tokens", 0)
            metadata["llm_cost_usd"] = llm_metrics.get("total_cost_usd", 0.0)

        with open(session_file, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    def log_query(
        self,
        sql: str,
        result_count: int,
        duration_ms: int = 0,
        outcome: str = "success",
        note: Optional[str] = None,
    ) -> QueryLog:
        """Log a query execution.

        Args:
            sql: SQL query executed
            result_count: Number of rows returned
            duration_ms: Query execution time in milliseconds
            outcome: Query outcome (success, refined, abandoned)
            note: Optional note about the query

        Returns:
            QueryLog entry

        Raises:
            SessionError: If no active session
        """
        session = self.get_active_session()
        if not session:
            raise SessionError("No active session. Start one with 'athf session start --hunt H-XXXX'")

        # Generate query ID
        query_id = f"q{len(session.queries) + 1:03d}"

        query_log = QueryLog(
            id=query_id,
            timestamp=self._now_iso(),
            sql=sql,
            result_count=result_count,
            duration_ms=duration_ms,
            outcome=outcome,
            note=note,
        )

        session.queries.append(query_log)
        self._save_queries(session)
        self._save_session_metadata(session)

        return query_log

    def _save_queries(self, session: Session) -> None:
        """Save queries to queries.yaml."""
        session_dir = self._get_session_dir(session.session_id)
        queries_file = session_dir / "queries.yaml"

        queries_data = {
            "queries": [
                {
                    "id": q.id,
                    "timestamp": q.timestamp,
                    "sql": q.sql,
                    "result_count": q.result_count,
                    "duration_ms": q.duration_ms,
                    "outcome": q.outcome,
                    "note": q.note,
                }
                for q in session.queries
            ]
        }

        with open(queries_file, "w") as f:
            yaml.dump(queries_data, f, default_flow_style=False, sort_keys=False)

    def log_decision(
        self,
        phase: str,
        decision: str,
        rationale: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
    ) -> DecisionLog:
        """Log a decision point.

        Args:
            phase: Decision phase (hypothesis, analysis, pivot)
            decision: The decision made
            rationale: Why this decision was made
            alternatives: Alternative options considered

        Returns:
            DecisionLog entry

        Raises:
            SessionError: If no active session
        """
        session = self.get_active_session()
        if not session:
            raise SessionError("No active session. Start one with 'athf session start --hunt H-XXXX'")

        decision_log = DecisionLog(
            timestamp=self._now_iso(),
            phase=phase,
            decision=decision,
            rationale=rationale,
            alternatives=alternatives,
        )

        session.decisions.append(decision_log)
        self._save_decisions(session)

        return decision_log

    def _save_decisions(self, session: Session) -> None:
        """Save decisions to decisions.yaml."""
        session_dir = self._get_session_dir(session.session_id)
        decisions_file = session_dir / "decisions.yaml"

        decisions_data = {
            "decisions": [
                {
                    "timestamp": d.timestamp,
                    "phase": d.phase,
                    "decision": d.decision,
                    "rationale": d.rationale,
                    "alternatives": d.alternatives,
                }
                for d in session.decisions
            ]
        }

        with open(decisions_file, "w") as f:
            yaml.dump(decisions_data, f, default_flow_style=False, sort_keys=False)

    def log_finding(
        self,
        finding_type: str,
        description: str,
        count: int = 1,
        escalated: bool = False,
    ) -> FindingLog:
        """Log a finding.

        Args:
            finding_type: Type of finding (tp, fp, pattern, suspicious)
            description: Description of the finding
            count: Number of instances found
            escalated: Whether finding was escalated

        Returns:
            FindingLog entry

        Raises:
            SessionError: If no active session
        """
        session = self.get_active_session()
        if not session:
            raise SessionError("No active session. Start one with 'athf session start --hunt H-XXXX'")

        finding_log = FindingLog(
            timestamp=self._now_iso(),
            finding_type=finding_type,
            description=description,
            count=count,
            escalated=escalated,
        )

        session.findings.append(finding_log)
        self._save_findings(session)
        self._save_session_metadata(session)

        return finding_log

    def _save_findings(self, session: Session) -> None:
        """Save findings to findings.yaml."""
        session_dir = self._get_session_dir(session.session_id)
        findings_file = session_dir / "findings.yaml"

        findings_data = {
            "findings": [
                {
                    "timestamp": f.timestamp,
                    "type": f.finding_type,
                    "description": f.description,
                    "count": f.count,
                    "escalated": f.escalated,
                }
                for f in session.findings
            ]
        }

        with open(findings_file, "w") as f:
            yaml.dump(findings_data, f, default_flow_style=False, sort_keys=False)

    def end_session(self, generate_summary: bool = True) -> Session:
        """End the active session.

        Args:
            generate_summary: Whether to generate summary.md

        Returns:
            Completed Session

        Raises:
            SessionError: If no active session
        """
        session = self.get_active_session()
        if not session:
            raise SessionError("No active session to end.")

        # Set end time and calculate duration
        session.end_time = self._now_iso()

        start = datetime.fromisoformat(session.start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(session.end_time.replace("Z", "+00:00"))
        session.duration_min = int((end - start).total_seconds() / 60)

        # Save final metadata
        self._save_session_metadata(session)

        # Generate summary
        if generate_summary:
            self._generate_summary(session)

        # Clear active pointer
        active_file = self._get_active_file()
        if active_file.exists():
            active_file.unlink()

        self._active_session = None

        return session

    def _get_session_llm_metrics(self, session: Session) -> Dict[str, Any]:
        """Get LLM metrics for session, including no_session calls in time window.

        Extends the start time 30 minutes backwards to capture LLM calls
        that occurred before the session started (e.g., hypothesis generation
        that ran before 'athf session start').

        Args:
            session: Session to get metrics for

        Returns:
            Dict with LLM metrics:
            {
                "call_count": N,
                "total_input_tokens": N,
                "total_output_tokens": N,
                "total_cost_usd": N.NNNN,
            }
        """
        try:
            from datetime import timedelta

            from athf.core.metrics_tracker import MetricsTracker

            tracker = MetricsTracker.get_instance()

            # Extend start time 30 min backwards to capture pre-session LLM calls
            # (e.g., hypothesis generation that ran before 'athf session start')
            start_dt = datetime.fromisoformat(session.start_time.replace("Z", "+00:00"))
            extended_start = (start_dt - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

            metrics = tracker.get_metrics_in_time_window(
                session.session_id,
                extended_start,
                session.end_time or self._now_iso(),
            )
            bedrock_metrics: dict[str, Any] = metrics.get("bedrock", {})
            return bedrock_metrics
        except Exception:
            return {
                "call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
            }

    def _generate_summary(self, session: Session) -> None:
        """Generate summary.md for the session."""
        session_dir = self._get_session_dir(session.session_id)
        summary_file = session_dir / "summary.md"

        # Format duration
        if session.duration_min is not None:
            if session.duration_min == 0:
                duration_str = "< 1m"
            else:
                hours = session.duration_min // 60
                mins = session.duration_min % 60
                if hours > 0:
                    duration_str = f"{hours}h {mins}m"
                else:
                    duration_str = f"{mins}m"
        else:
            duration_str = "Unknown"

        # Extract date from session_id (e.g., H-TEST-2025-12-29 -> 2025-12-29)
        parts = session.session_id.split("-")
        if len(parts) >= 4:
            # Format: H-XXXX-YYYY-MM-DD or H-TEST-YYYY-MM-DD
            date_str = "-".join(parts[-3:])  # Last 3 parts are the date
        else:
            date_str = session.session_id

        # Get LLM metrics for the session
        llm_metrics = self._get_session_llm_metrics(session)
        llm_cost = llm_metrics.get("total_cost_usd", 0.0)
        llm_calls = llm_metrics.get("call_count", 0)
        llm_input_tokens = llm_metrics.get("total_input_tokens", 0)
        llm_output_tokens = llm_metrics.get("total_output_tokens", 0)

        # Build header with LLM cost if any
        header_parts = [
            f"**Duration:** {duration_str}",
            f"**Queries:** {session.query_count}",
            f"**Findings:** {session.tp_count} TP, {session.fp_count} FP",
        ]
        if llm_cost > 0:
            header_parts.append(f"**LLM Cost:** ${llm_cost:.4f}")

        # Build summary
        lines = [
            f"# Session: {session.hunt_id} ({date_str})",
            "",
            " | ".join(header_parts),
            "",
        ]

        # Final successful query
        successful_queries = [q for q in session.queries if q.outcome == "success"]
        if successful_queries:
            final_query = successful_queries[-1]
            lines.extend(
                [
                    "## Final Query",
                    "",
                    "```sql",
                    final_query.sql.strip(),
                    "```",
                    "",
                ]
            )

        # Key decisions
        if session.decisions:
            lines.extend(
                [
                    "## Key Decisions",
                    "",
                ]
            )
            for d in session.decisions:
                lines.append(f"- **{d.phase.title()}:** {d.decision}")
                if d.rationale:
                    lines.append(f"  - Rationale: {d.rationale}")
            lines.append("")

        # Findings
        if session.findings:
            lines.extend(
                [
                    "## Findings",
                    "",
                ]
            )
            for finding in session.findings:
                prefix = finding.finding_type.upper()
                escalated = " (escalated)" if finding.escalated else ""
                lines.append(f"- **{prefix}:** {finding.description} ({finding.count} instances){escalated}")
            lines.append("")

        # Lessons (extracted from decisions with rationale)
        lessons = [d for d in session.decisions if d.rationale]
        if lessons:
            lines.extend(
                [
                    "## Lessons",
                    "",
                ]
            )
            for d in lessons:
                lines.append(f"- {d.rationale}")
            lines.append("")

        # Calculate query execution metrics
        total_query_time_ms = sum(q.duration_ms for q in session.queries if q.duration_ms)
        avg_query_time_ms = (
            total_query_time_ms // session.query_count if session.query_count > 0 else 0
        )

        # Execution Metrics section
        if llm_calls > 0 or session.query_count > 0:
            lines.extend(
                [
                    "## Execution Metrics",
                    "",
                    "| Resource | Metric | Value |",
                    "|----------|--------|-------|",
                ]
            )

            # Query metrics (if any queries executed)
            if session.query_count > 0:
                total_query_time_sec = total_query_time_ms / 1000
                lines.append(f"| ClickHouse | Queries | {session.query_count} |")
                lines.append(f"| ClickHouse | Total Time | {total_query_time_sec:.1f}s |")
                lines.append(f"| ClickHouse | Avg Time | {avg_query_time_ms}ms |")

            # LLM metrics (if any LLM calls)
            if llm_calls > 0:
                lines.append(f"| LLM | Calls | {llm_calls} |")
                lines.append(f"| LLM | Input Tokens | {llm_input_tokens:,} |")
                lines.append(f"| LLM | Output Tokens | {llm_output_tokens:,} |")
                lines.append(f"| LLM | Cost | ${llm_cost:.4f} |")

            lines.append("")

        with open(summary_file, "w") as f:
            f.write("\n".join(lines))

    def list_sessions(self, hunt_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sessions, optionally filtered by hunt.

        Args:
            hunt_id: Optional hunt ID to filter by

        Returns:
            List of session metadata dicts
        """
        sessions = []

        for session_dir in self._sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            if session_dir.name.startswith("."):
                continue

            session_file = session_dir / "session.yaml"
            if not session_file.exists():
                continue

            try:
                with open(session_file, "r") as f:
                    data = yaml.safe_load(f)

                if hunt_id and data.get("hunt_id") != hunt_id:
                    continue

                sessions.append(data)
            except Exception:
                continue

        # Sort by start_time descending (most recent first)
        sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)

        return sessions

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a specific session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session if found, None otherwise
        """
        return self._load_session(session_id)
