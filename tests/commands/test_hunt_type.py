"""`hunt_type` — the controlled-vocabulary hunt category behind issue #60.

Covers the field end to end: written by `athf hunt new`, surfaced by
`athf hunt list`, aggregated by `athf hunt stats --by hunt_type`, rolled up by
`athf metrics summary`, and warned about (never failed) by `athf hunt validate`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.hunt import hunt
from athf.commands.init import init
from athf.commands.metrics import metrics
from athf.core.hunt_manager import HuntManager
from athf.core.hunt_parser import HuntParser, hunt_file_warnings
from athf.core.hunt_types import (
    DEFAULT_HUNT_TYPE,
    HUNT_TYPES,
    UNCATEGORIZED_LABEL,
    is_valid_hunt_type,
    normalize_hunt_type,
)
from athf.core.metrics import Aggregator
from athf.core.template_engine import render_hunt_template


def _hunt_path(hunt_id: str) -> Path:
    return next(Path("hunts").rglob(f"{hunt_id}.md"))


def _frontmatter(hunt_id: str) -> dict:
    text = _hunt_path(hunt_id).read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


def _set_frontmatter(hunt_id: str, **changes: object) -> None:
    """Rewrite selected frontmatter keys in place; ``None`` deletes a key."""
    path = _hunt_path(hunt_id)
    _, fm_text, body = path.read_text(encoding="utf-8").split("---", 2)
    fm = yaml.safe_load(fm_text)
    for key, value in changes.items():
        if value is None:
            fm.pop(key, None)
        else:
            fm[key] = value
    path.write_text(f"---\n{yaml.safe_dump(fm, sort_keys=False)}---{body}", encoding="utf-8")


def _new(runner: CliRunner, title: str, *args: str) -> None:
    result = runner.invoke(hunt, ["new", "--title", title, "--non-interactive", *args])
    assert result.exit_code == 0, result.output


@pytest.fixture
def workspace(tmp_path):
    """A fresh workspace with NO hunts, so counts in tests are exact.

    ``athf init`` may seed example hunts; they are removed here because the
    assertions below depend on knowing precisely which hunts exist.
    """
    # Other test modules leave a cached ATT&CK provider behind; `hunt new`
    # consults it for tactic derivation, so start from a clean resolution.
    from athf.core import attack_matrix

    previous_provider = attack_matrix._provider
    attack_matrix.reset_provider(None)

    runner = CliRunner()
    try:
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(init, ["--non-interactive"])
            hunts_dir = Path("hunts")
            for path in hunts_dir.rglob("H-*.md"):
                path.unlink()
            yield runner
    finally:
        attack_matrix.reset_provider(previous_provider)


@pytest.fixture
def mixed_workspace(workspace):
    """Four hunts: 2 hypothesis (one completed), 1 baseline, 1 uncategorized."""
    _new(workspace, "Hyp A")  # default hunt_type -> hypothesis
    _new(workspace, "Hyp B", "--hunt-type", "hypothesis")
    _new(workspace, "Base A", "--hunt-type", "baseline")
    _new(workspace, "Legacy", "--hunt-type", "model-assisted")
    _set_frontmatter("H-0002", status="completed")
    _set_frontmatter("H-0004", hunt_type=None)  # legacy hunt predating the field
    return workspace


# ---------------------------------------------------------------------------
# Vocabulary helpers
# ---------------------------------------------------------------------------


class TestVocabulary:
    def test_vocabulary_is_the_three_methodologies(self):
        assert HUNT_TYPES == ("hypothesis", "baseline", "model-assisted")
        assert DEFAULT_HUNT_TYPE in HUNT_TYPES

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("hypothesis", "hypothesis"),
            ("Baseline", "baseline"),
            ("Model_Assisted", "model-assisted"),
            ("model assisted", "model-assisted"),
            ("  baseline ", "baseline"),
            ("anomaly", None),
            ("", None),
            (None, None),
            (42, None),
        ],
    )
    def test_normalize(self, raw, expected):
        assert normalize_hunt_type(raw) == expected

    def test_is_valid_is_strict(self):
        assert is_valid_hunt_type("baseline")
        assert not is_valid_hunt_type("Baseline")
        assert not is_valid_hunt_type(None)


# ---------------------------------------------------------------------------
# Template / hunt new
# ---------------------------------------------------------------------------


class TestHuntNewWritesHuntType:
    def test_template_renders_field_when_given(self):
        out = render_hunt_template(hunt_id="H-0001", title="t", hunt_type="baseline")
        assert "\nhunt_type: baseline\n" in out

    def test_template_omits_field_when_absent(self):
        out = render_hunt_template(hunt_id="H-0001", title="t")
        assert "hunt_type" not in out

    def test_non_interactive_defaults_to_hypothesis(self, workspace):
        _new(workspace, "Default")
        assert _frontmatter("H-0001")["hunt_type"] == "hypothesis"

    @pytest.mark.parametrize("value", HUNT_TYPES)
    def test_flag_sets_each_vocabulary_value(self, workspace, value):
        _new(workspace, f"Typed {value}", "--hunt-type", value)
        assert _frontmatter("H-0001")["hunt_type"] == value

    def test_flag_rejects_unknown_value(self, workspace):
        result = workspace.invoke(hunt, ["new", "--title", "x", "--hunt-type", "anomaly", "--non-interactive"])
        assert result.exit_code != 0
        assert "anomaly" in result.output

    def test_legacy_custom_template_still_gets_hunt_type(self, workspace):
        """A workspace template snapshotted before hunt_type existed must not drop the value."""
        legacy = Path("templates") / "HUNT_TEMPLATE.j2"
        legacy.parent.mkdir(exist_ok=True)
        legacy.write_text(
            "---\nhunt_id: {{ hunt_id }}\ntitle: {{ title }}\nstatus: {{ status }}\ndate: {{ date }}\n"
            "hunter: {{ hunter }}\nplatform: {{ platform }}\ntactics: {{ tactics }}\ntechniques: {{ techniques }}\n"
            "data_sources: {{ data_sources }}\nfindings: []\nruled_out: []\ntags: {{ tags }}\n---\n\n"
            "# {{ hunt_id }}\n\n## LEARN\n\n## OBSERVE\n\n## CHECK\n\n## KEEP\n",
            encoding="utf-8",
        )
        _new(workspace, "Legacy template", "--hunt-type", "baseline")
        fm = _frontmatter("H-0001")
        assert fm["hunt_type"] == "baseline"
        assert fm["hunter"]  # neighbouring fields intact
        assert HuntManager().list_hunts()[0]["hunt_type"] == "baseline"

    def test_injection_respects_template_that_already_emits_field(self):
        from athf.core.template_engine import _ensure_frontmatter_field

        rendered = "---\nhunt_id: H-0001\nhunt_type: baseline\n---\nbody"
        assert _ensure_frontmatter_field(rendered, "hunt_type", "hypothesis") == rendered

    def test_injection_appends_when_no_hunter_line(self):
        from athf.core.template_engine import _ensure_frontmatter_field

        rendered = "---\nhunt_id: H-0001\n---\nbody"
        out = _ensure_frontmatter_field(rendered, "hunt_type", "baseline")
        assert yaml.safe_load(out.split("---", 2)[1]) == {"hunt_id": "H-0001", "hunt_type": "baseline"}
        assert out.endswith("---\nbody")


# ---------------------------------------------------------------------------
# hunt list
# ---------------------------------------------------------------------------


class TestHuntListShowsHuntType:
    def test_json_summary_carries_hunt_type(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["list", "--output", "json"])
        assert result.exit_code == 0, result.output
        by_id = {h["hunt_id"]: h for h in json.loads(result.output)}
        assert by_id["H-0001"]["hunt_type"] == "hypothesis"
        assert by_id["H-0003"]["hunt_type"] == "baseline"
        assert by_id["H-0004"]["hunt_type"] is None

    def test_table_has_type_column(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["list"])
        assert result.exit_code == 0
        assert "Type" in result.output
        assert "baseline" in result.output

    def test_filter_by_hunt_type(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["list", "--hunt-type", "baseline", "--output", "json"])
        ids = [h["hunt_id"] for h in json.loads(result.output)]
        assert ids == ["H-0003"]

    def test_filter_uncategorized_finds_legacy_hunts(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["list", "--hunt-type", "uncategorized", "--output", "json"])
        ids = [h["hunt_id"] for h in json.loads(result.output)]
        assert ids == ["H-0004"]

    def test_filter_rejects_unknown_value(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["list", "--hunt-type", "anomaly"])
        assert result.exit_code != 0

    def test_manager_filter_unknown_value_matches_nothing(self, mixed_workspace):
        """An out-of-vocabulary filter must not alias to the uncategorized bucket."""
        assert HuntManager().list_hunts(hunt_type="anomaly") == []
        assert [h["hunt_id"] for h in HuntManager().list_hunts(hunt_type="uncategorized")] == ["H-0004"]

    def test_manager_filter_accepts_non_canonical_spelling(self, mixed_workspace):
        assert [h["hunt_id"] for h in HuntManager().list_hunts(hunt_type="Baseline")] == ["H-0003"]


# ---------------------------------------------------------------------------
# HuntManager.calculate_breakdown / hunt stats
# ---------------------------------------------------------------------------


class TestBreakdown:
    def test_counts_and_percentages(self, mixed_workspace):
        breakdown = HuntManager().calculate_breakdown(by="hunt_type")
        assert breakdown["total"] == 4
        assert breakdown["counts"] == {
            "hypothesis": 2,
            "baseline": 1,
            "model-assisted": 0,
            UNCATEGORIZED_LABEL: 1,
        }
        assert breakdown["percentages"]["hypothesis"] == 50.0
        assert sum(breakdown["counts"].values()) == breakdown["total"]

    def test_vocabulary_values_always_present_even_at_zero(self, workspace):
        _new(workspace, "only one")
        counts = HuntManager().calculate_breakdown(by="hunt_type")["counts"]
        assert set(HUNT_TYPES) <= set(counts)
        assert UNCATEGORIZED_LABEL not in counts  # nothing uncategorized -> row hidden

    def test_status_filter_scopes_the_denominator(self, mixed_workspace):
        breakdown = HuntManager().calculate_breakdown(by="hunt_type", status="completed")
        assert breakdown["total"] == 1
        assert breakdown["counts"]["hypothesis"] == 1
        assert breakdown["percentages"]["hypothesis"] == 100.0
        assert breakdown["filters"] == {"status": "completed"}

    def test_group_by_status(self, mixed_workspace):
        breakdown = HuntManager().calculate_breakdown(by="status")
        assert breakdown["counts"] == {"planning": 3, "completed": 1}

    def test_unknown_field_is_refused(self, mixed_workspace):
        with pytest.raises(ValueError):
            HuntManager().calculate_breakdown(by="hunter")

    def test_normalizes_non_canonical_values(self, mixed_workspace):
        _set_frontmatter("H-0004", hunt_type="Model_Assisted")
        counts = HuntManager().calculate_breakdown(by="hunt_type")["counts"]
        assert counts["model-assisted"] == 1
        assert UNCATEGORIZED_LABEL not in counts

    def test_calculate_stats_includes_by_hunt_type(self, mixed_workspace):
        stats = HuntManager().calculate_stats()
        assert stats["by_hunt_type"]["hypothesis"] == 2
        assert stats["by_hunt_type"][UNCATEGORIZED_LABEL] == 1

    def test_calculate_stats_empty_workspace_has_zeroed_breakdown(self, workspace):
        stats = HuntManager().calculate_stats()
        assert stats["total_hunts"] == 0
        assert stats["by_hunt_type"] == {name: 0 for name in HUNT_TYPES}


class TestHuntStatsCommand:
    def test_default_view_includes_hunts_by_type(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats"])
        assert result.exit_code == 0, result.output
        assert "Total Hunts" in result.output
        assert "Hunts by type" in result.output
        assert "baseline" in result.output

    def test_by_hunt_type_table(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type"])
        assert result.exit_code == 0, result.output
        for label in ("Hunt Type", "Count", "%", "hypothesis", "baseline", "model-assisted", "(uncategorized)", "Total"):
            assert label in result.output
        assert "50.0%" in result.output
        assert "100.0%" in result.output

    def test_by_hunt_type_json_matches_issue_shape(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type", "--output", "json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["total"] == 4
        assert payload["by_hunt_type"] == {
            "hypothesis": 2,
            "baseline": 1,
            "model-assisted": 0,
            "uncategorized": 1,
        }
        assert payload["percentages"]["uncategorized"] == 25.0

    def test_format_is_an_alias_for_output(self, mixed_workspace):
        via_output = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type", "--output", "json"])
        via_format = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type", "--format", "json"])
        assert via_format.exit_code == 0, via_format.output
        assert json.loads(via_format.output) == json.loads(via_output.output)

    def test_yaml_output(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type", "--output", "yaml"])
        assert result.exit_code == 0, result.output
        data = yaml.safe_load(result.output)
        assert data["by"] == "hunt_type"
        assert data["counts"]["baseline"] == 1

    def test_status_filter(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "hunt_type", "--status", "completed", "--output", "json"])
        payload = json.loads(result.output)
        assert payload["total"] == 1
        assert payload["filters"] == {"status": "completed"}
        assert payload["by_hunt_type"]["hypothesis"] == 1

    def test_full_stats_json_carries_by_hunt_type(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--output", "json"])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["total_hunts"] == 4
        assert payload["by_hunt_type"]["baseline"] == 1

    def test_by_other_field(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "status", "--output", "json"])
        payload = json.loads(result.output)
        assert payload["by_status"] == {"planning": 3, "completed": 1}

    def test_by_rejects_unknown_field(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["stats", "--by", "hunter"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# validate: warn, never fail
# ---------------------------------------------------------------------------


class TestValidateWarnsOnHuntType:
    def test_missing_hunt_type_warns_but_exits_zero(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["validate", "H-0004"])
        assert result.exit_code == 0, result.output
        assert "Hunt is valid" in result.output
        assert "Missing hunt_type" in result.output

    def test_present_hunt_type_has_no_warning(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["validate", "H-0003"])
        assert result.exit_code == 0
        assert "hunt_type" not in result.output

    def test_unknown_hunt_type_warns_but_exits_zero(self, mixed_workspace):
        _set_frontmatter("H-0004", hunt_type="anomaly")
        result = mixed_workspace.invoke(hunt, ["validate", "H-0004"])
        assert result.exit_code == 0, result.output
        assert "Unknown hunt_type" in result.output

    def test_validate_all_counts_warnings_in_summary(self, mixed_workspace):
        result = mixed_workspace.invoke(hunt, ["validate"])
        assert result.exit_code == 0, result.output
        assert "4 valid, 0 invalid, 1 with warnings" in result.output

    def test_parser_validate_is_unaffected(self, mixed_workspace):
        parser = HuntParser(_hunt_path("H-0004"))
        parser.parse()
        is_valid, errors = parser.validate()
        assert is_valid and errors == []
        assert any("hunt_type" in w for w in parser.warnings())

    def test_non_canonical_value_gets_a_nudge(self, mixed_workspace):
        _set_frontmatter("H-0004", hunt_type="Baseline")
        warnings = hunt_file_warnings(_hunt_path("H-0004"))
        assert warnings and "use 'baseline'" in warnings[0]


# ---------------------------------------------------------------------------
# metrics summary rollup
# ---------------------------------------------------------------------------


class TestMetricsRollup:
    def test_extract_from_hunt_file_normalizes_hunt_type(self):
        content = "---\nhunt_id: H-0001\ntitle: t\nhunt_type: Baseline\n---\n"
        assert Aggregator.extract_from_hunt_file(content)["hunt_type"] == "baseline"

    def test_extract_from_hunt_file_defaults_to_uncategorized(self):
        content = "---\nhunt_id: H-0001\ntitle: t\n---\n"
        assert Aggregator.extract_from_hunt_file(content)["hunt_type"] == UNCATEGORIZED_LABEL

    def test_metrics_summary_json_has_by_hunt_type_rollup(self, mixed_workspace):
        result = mixed_workspace.invoke(metrics, ["summary", "--format", "json"])
        assert result.exit_code == 0, result.output
        rollup = json.loads(result.output)["rollups"]["by_hunt_type"]
        assert rollup == {"hypothesis": 2, "baseline": 1, UNCATEGORIZED_LABEL: 1}

    def test_metrics_summary_table_renders_hunt_type_section(self, mixed_workspace):
        result = mixed_workspace.invoke(metrics, ["summary"])
        assert result.exit_code == 0, result.output
        assert "By hunt type" in result.output

    def test_metrics_summary_refreshes_aggregates_missing_the_rollup(self, mixed_workspace):
        """aggregates.json written before by_hunt_type existed must be re-extracted, not rendered stale."""
        first = mixed_workspace.invoke(metrics, ["extract"])
        assert first.exit_code == 0, first.output
        agg_path = Path("metrics") / "aggregates.json"
        payload = json.loads(agg_path.read_text(encoding="utf-8"))
        payload["rollups"].pop("by_hunt_type")
        agg_path.write_text(json.dumps(payload), encoding="utf-8")

        result = mixed_workspace.invoke(metrics, ["summary", "--format", "json"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["rollups"]["by_hunt_type"]["baseline"] == 1
        table = mixed_workspace.invoke(metrics, ["summary"])
        assert "By hunt type" in table.output


# ---------------------------------------------------------------------------
# bundled example hunts are backfilled
# ---------------------------------------------------------------------------


def test_bundled_example_hunts_carry_hunt_type():
    repo = Path(__file__).resolve().parents[2]
    examples = list((repo / "athf" / "data" / "hunts").rglob("H-*.md"))
    assert examples, "expected bundled example hunts"
    for path in examples:
        fm = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
        assert is_valid_hunt_type(fm.get("hunt_type")), f"{path.name} is missing hunt_type"
