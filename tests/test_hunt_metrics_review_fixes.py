"""Regression tests for PR #78 review findings on ``athf hunt metrics``."""

from __future__ import annotations

import csv
import io
import json
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner

from athf.commands.hunt import hunt
from athf.core.hunt_guards import find_hunt_directory
from athf.core.hunt_metrics import calculate_metrics, format_metrics
from athf.core.hunt_metrics_enhanced import (
    drill_down_detections,
    drill_down_high_impact,
    format_drill_down,
)

WORKSPACE_CONFIG = """provenance:
  producers:
    analyst:
      capabilities:
        - clickhouse_query
        - host_forensics
"""

CONFIRMED_FINDING = (
    "findings:\n"
    "  - subject: web-prod-04\n"
    "    verdict: confirmed\n"
    "    evidence: OCSF process_activity\n"
    "    confirmation:\n"
    "      method: host_forensics\n"
    "      produced_by: analyst\n"
    "      attested_by: Sydney Marrone\n"
    "      detail: host triage recovered the crontab entry from disk\n"
)

Q1 = (date(2025, 1, 1), date(2025, 3, 31))


def _workspace(tmp_path: Path) -> Path:
    prod = tmp_path / "hunts" / "production"
    prod.mkdir(parents=True)
    (tmp_path / ".athfconfig.yaml").write_text(WORKSPACE_CONFIG, encoding="utf-8")
    return prod


def _hunt(prod: Path, hunt_id: str, body: str) -> None:
    text = f"---\nhunt_id: {hunt_id}\ntitle: {hunt_id} title\n{body}---\n\n# {hunt_id}\n"
    (prod / f"{hunt_id}.md").write_text(text, encoding="utf-8")


def _completed(extra: str = "", start: str = "2025-01-10", end: str = "2025-01-12") -> str:
    return f"status: completed\ndate: {start}\ncompleted_date: {end}\n{extra}"


class TestVerdictLadderIncidents:
    def test_confirmed_finding_counts_as_incident(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(CONFIRMED_FINDING))

        m = calculate_metrics(prod, *Q1, "2025-Q1")
        assert m.incidents_sourced == 1
        assert m.success_rate_pct == 100

    def test_legacy_true_positives_still_wins(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed("true_positives: 3\n" + CONFIRMED_FINDING))

        assert calculate_metrics(prod, *Q1, "2025-Q1").incidents_sourced == 3

    def test_top_performers_includes_ladder_hunt(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(CONFIRMED_FINDING))

        results = drill_down_high_impact(prod, *Q1, threshold=1)
        assert results == [("H-0001", "H-0001 title", 1)]


class TestBlankFields:
    def test_blank_template_fields_bucket_as_unknown(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed("output_type:\ntechnology_domain:\noutput_criticality:\n"))

        m = calculate_metrics(prod, *Q1, "2025-Q1")
        assert m.by_output_type == {"unknown": 1}
        assert m.by_technology == {"unknown": 1}
        assert m.by_criticality == {"unknown": 1}
        assert "1 hunts missing output_type" in format_metrics(m)

    @pytest.mark.parametrize("value", ['"false"', '"no"', '"False"', "false", "[]", "''"])
    def test_falsey_data_available_not_counted(self, tmp_path: Path, value: str) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(f"data_sources_available: {value}\n"))

        assert calculate_metrics(prod, *Q1, "2025-Q1").data_available_pct == 0

    @pytest.mark.parametrize("value", ["true", '"EDR process telemetry"', "[edr]"])
    def test_truthy_data_available_counted(self, tmp_path: Path, value: str) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(f"data_sources_available: {value}\n"))

        assert calculate_metrics(prod, *Q1, "2025-Q1").data_available_pct == 100

    def test_drill_downs_survive_null_values(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed("true_positives:\nrelated_detections:\n"))
        _hunt(prod, "H-0002", _completed("true_positives: 2\nrelated_detections: [D-1]\n"))
        hunt_file = prod / "H-0002.md"
        hunt_file.write_text(hunt_file.read_text().replace("title: H-0002 title", "title:"))

        impact = drill_down_high_impact(prod, *Q1, threshold=1)
        assert impact == [("H-0002", "Unknown", 2)]
        assert drill_down_detections(prod, *Q1) == [("H-0002", "Unknown", 1)]
        assert "H-0002" in format_drill_down("high_impact", impact, *Q1)


class TestExcludeFromMetrics:
    def test_drill_down_skips_excluded_hunts(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed("exclude_from_metrics: true\nrelated_detections: [D-1]\n"))
        _hunt(prod, "H-0002", _completed("related_detections: [D-2]\n"))

        assert [r[0] for r in drill_down_detections(prod, *Q1)] == ["H-0002"]
        assert calculate_metrics(prod, *Q1, "2025-Q1").detections_created == 1


class TestDuration:
    def test_same_day_hunts_count_toward_average(self, tmp_path: Path) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(end="2025-01-10"))
        _hunt(prod, "H-0002", _completed(end="2025-01-10"))
        _hunt(prod, "H-0003", _completed(end="2025-01-17"))

        m = calculate_metrics(prod, *Q1, "2025-Q1")
        assert m.avg_duration_days == pytest.approx(7 / 3)
        assert m.median_duration_days == 0


class TestHuntDirectory:
    def test_invalid_env_dir_raises_instead_of_falling_back(self, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "hunts" / "production").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ATHF_HUNT_DIR", str(tmp_path / "typo"))

        with pytest.raises(ValueError, match="ATHF_HUNT_DIR"):
            find_hunt_directory()

    def test_metrics_command_exits_nonzero_on_invalid_env_dir(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("ATHF_HUNT_DIR", str(tmp_path / "typo"))

        for args in (["metrics", "--period", "2025-Q1"], ["metrics", "gaps", "--strict"]):
            result = CliRunner().invoke(hunt, args)
            assert result.exit_code != 0, (args, result.output)
            assert "ATHF_HUNT_DIR" in result.output

    def test_missing_directory_exits_nonzero_with_real_paths(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("ATHF_HUNT_DIR", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "fakehome")

        result = CliRunner().invoke(hunt, ["metrics", "--period", "2025-Q1"])
        assert result.exit_code == 1
        assert "../hunt-vault/hunts/production" in result.output
        assert "agentic-threat-hunting-framework" not in result.output

    def test_invalid_period_exits_nonzero(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setenv("ATHF_HUNT_DIR", str(_workspace(tmp_path)))

        assert CliRunner().invoke(hunt, ["metrics", "--period", "2025-Q9"]).exit_code == 1


class TestMachineOutput:
    def test_year_csv_is_not_wrapped(self, tmp_path: Path, monkeypatch) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed())
        monkeypatch.setenv("ATHF_HUNT_DIR", str(prod))

        result = CliRunner().invoke(hunt, ["metrics", "--year", "2025", "--format", "csv"])
        assert result.exit_code == 0, result.output
        rows = list(csv.reader(io.StringIO(result.output)))
        assert len(rows) == 5
        assert all(len(r) == len(rows[0]) for r in rows)

    def test_period_csv_and_json_parse(self, tmp_path: Path, monkeypatch) -> None:
        prod = _workspace(tmp_path)
        _hunt(prod, "H-0001", _completed(CONFIRMED_FINDING))
        monkeypatch.setenv("ATHF_HUNT_DIR", str(prod))

        csv_out = CliRunner().invoke(hunt, ["metrics", "--period", "2025-Q1", "--format", "csv"]).output
        rows = list(csv.reader(io.StringIO(csv_out)))
        assert len(rows) == 2 and len(rows[0]) == len(rows[1])

        json_out = CliRunner().invoke(hunt, ["metrics", "--period", "2025-Q1", "--format", "json"]).output
        assert json.loads(json_out)["incidents_sourced"] == 1

        year_json = CliRunner().invoke(hunt, ["metrics", "--year", "2025", "--format", "json"]).output
        assert len(json.loads(year_json)["quarters"]) == 4


class TestGapsStatusAware:
    def test_planning_hunt_not_penalized_for_outcome_fields(self, tmp_path: Path, monkeypatch) -> None:
        prod = _workspace(tmp_path)
        _hunt(
            prod,
            "H-0001",
            "status: planning\ndate: 2025-01-10\ntechnology_domain: endpoint\nhunt_type: hypothesis\n"
            "data_sources_available: true\ncompleted_date:\noutput_type:\noutput_criticality:\n",
        )
        monkeypatch.setenv("ATHF_HUNT_DIR", str(prod))

        result = CliRunner().invoke(hunt, ["metrics", "gaps", "--strict", "--format", "json"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["incomplete_hunts"] == 0

    def test_completed_hunt_still_requires_outcome_fields(self, tmp_path: Path, monkeypatch) -> None:
        prod = _workspace(tmp_path)
        _hunt(
            prod,
            "H-0001",
            "status: completed\ndate: 2025-01-10\ntechnology_domain: endpoint\nhunt_type: hypothesis\n"
            "data_sources_available: true\n",
        )
        monkeypatch.setenv("ATHF_HUNT_DIR", str(prod))

        result = CliRunner().invoke(hunt, ["metrics", "gaps", "--format", "json"])
        payload = json.loads(result.output)
        assert payload["gaps"][0]["missing_fields"] == ["completed_date", "output_type", "output_criticality"]
