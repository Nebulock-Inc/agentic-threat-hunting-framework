"""Tests for ``athf metrics`` CLI subcommands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from athf.commands.metrics import metrics
from athf.core.metrics import EventStore, MetricEvent


def _seed_events(workspace: Path) -> None:
    """Drop a small but representative set of events into the workspace."""
    store = EventStore(workspace / "metrics" / "events.jsonl")
    store.append(
        MetricEvent(
            event_type="llm_call",
            hunt_id="H-0019",
            model="claude-sonnet-4",
            input_tokens=120,
            output_tokens=80,
            cost_usd=0.0042,
            duration_ms=400,
        )
    )
    store.append(
        MetricEvent(
            event_type="query",
            hunt_id="H-0019",
            duration_ms=15,
            rows_returned=42,
            status="success",
        )
    )
    store.append(
        MetricEvent(
            event_type="web_search",
            hunt_id="H-0019",
            duration_ms=900,
            custom={"query": "lsass dumping", "result_count": 5},
        )
    )
    store.append(
        MetricEvent(
            event_type="similarity_search",
            hunt_id="H-0019",
            duration_ms=8,
        )
    )
    store.append(
        MetricEvent(
            event_type="hunt_outcome",
            hunt_id="H-0019",
            outcome="tp",
        )
    )


@pytest.mark.unit
class TestMetricsExtract:
    def test_extract_writes_aggregates(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(metrics, ["extract", "--workspace", str(tmp_path)])

        assert result.exit_code == 0, result.output
        agg_path = tmp_path / "metrics" / "aggregates.json"
        assert agg_path.exists()
        payload = json.loads(agg_path.read_text(encoding="utf-8"))
        assert "H-0019" in payload["hunts"]
        assert payload["totals"]["llm_calls"] == 1
        assert payload["totals"]["queries"] == 1

    def test_extract_with_explicit_output(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)
        custom_out = tmp_path / "custom" / "agg.json"

        runner = CliRunner()
        result = runner.invoke(
            metrics,
            [
                "extract",
                "--workspace",
                str(tmp_path),
                "--output",
                str(custom_out),
            ],
        )

        assert result.exit_code == 0, result.output
        assert custom_out.exists()


@pytest.mark.unit
class TestMetricsShow:
    def test_show_table_for_known_hunt(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            metrics,
            ["show", "--hunt", "H-0019", "--workspace", str(tmp_path)],
        )

        assert result.exit_code == 0, result.output
        assert "H-0019" in result.output
        assert "LLM calls" in result.output

    def test_show_json(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            metrics,
            [
                "show",
                "--hunt",
                "H-0019",
                "--workspace",
                str(tmp_path),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["hunt_id"] == "H-0019"
        assert payload["llm_calls"] == 1

    def test_show_unknown_hunt_returns_nonzero_with_message(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            metrics,
            ["show", "--hunt", "H-9999", "--workspace", str(tmp_path)],
        )

        # Missing-hunt is an error path: shell automation must see a non-zero
        # status so missing IDs don't silently look like success.
        assert result.exit_code != 0
        assert "No metrics found" in result.output


@pytest.mark.unit
class TestMetricsSummary:
    def test_summary_table(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            metrics, ["summary", "--workspace", str(tmp_path)]
        )

        assert result.exit_code == 0, result.output
        assert "Workspace Totals" in result.output
        assert "Hunts tracked" in result.output

    def test_summary_json(self, tmp_path: Path) -> None:
        _seed_events(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            metrics,
            ["summary", "--workspace", str(tmp_path), "--format", "json"],
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["totals"]["hunts"] >= 1
        assert "rollups" in payload


@pytest.mark.unit
class TestMetricsRecord:
    def test_record_manual_event(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            metrics,
            [
                "record",
                "--type",
                "manual",
                "--hunt",
                "H-0042",
                "--workspace",
                str(tmp_path),
                "--field",
                "note=hello",
                "--field",
                "duration_ms=12",
            ],
        )

        assert result.exit_code == 0, result.output
        events_file = tmp_path / "metrics" / "events.jsonl"
        assert events_file.exists()
        line = events_file.read_text(encoding="utf-8").splitlines()[0]
        evt = json.loads(line)
        assert evt["event_type"] == "manual"
        assert evt["hunt_id"] == "H-0042"
        assert evt["duration_ms"] == 12
        assert evt["custom"]["note"] == "hello"

    def test_record_rejects_invalid_type(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            metrics,
            [
                "record",
                "--type",
                "not-an-event",
                "--workspace",
                str(tmp_path),
            ],
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output or "not-an-event" in result.output

    def test_record_rejects_malformed_field(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            metrics,
            [
                "record",
                "--type",
                "manual",
                "--workspace",
                str(tmp_path),
                "--field",
                "no_equals_sign",
            ],
        )

        assert result.exit_code != 0


@pytest.mark.unit
class TestMetricsRegistration:
    def test_metrics_appears_in_athf_help(self) -> None:
        from athf.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "metrics" in result.output

    def test_metrics_subcommands_registered(self) -> None:
        runner = CliRunner()
        result = runner.invoke(metrics, ["--help"])

        assert result.exit_code == 0
        for sub in ("show", "summary", "extract", "record"):
            assert sub in result.output
