"""Regression tests for ``athf hunt metrics gaps``.

The command shipped with two defects this file guards against:

1. It referenced ``find_hunt_directory`` without importing it in the ``gaps``
   function's scope, so any invocation raised ``NameError``.
2. It resolved hunts via a bare ``HuntManager()`` (cwd-relative) instead of
   ``find_hunt_directory()``, so it ignored ``ATHF_HUNT_DIR`` and disagreed
   with the ``metrics`` command about which hunts are in scope.
"""

from pathlib import Path

from click.testing import CliRunner

from athf.commands.hunt import hunt

_COMPLETE = """---
hunt_id: H-9001
title: Complete Hunt
status: completed
date: 2025-01-01
technology_domain: endpoint
hunt_type: hypothesis
data_sources_available: EDR process telemetry
completed_date: 2025-01-02
output_type: detection
output_criticality: high
---

# H-9001
"""

_GAPPY = """---
hunt_id: H-9002
title: Gappy Hunt
status: completed
date: 2025-01-01
---

# H-9002
"""


def _seed(tmp_path: Path) -> Path:
    prod = tmp_path / "hunts" / "production" / "2025" / "Q1"
    prod.mkdir(parents=True)
    (prod / "H-9001.md").write_text(_COMPLETE)
    (prod / "H-9002.md").write_text(_GAPPY)
    return tmp_path / "hunts" / "production"


class TestHuntMetricsGaps:
    def test_gaps_runs_and_honors_env_dir(self, tmp_path, monkeypatch):
        """Does not crash, and scans the ATHF_HUNT_DIR tree (not cwd)."""
        hunt_root = _seed(tmp_path)
        monkeypatch.setenv("ATHF_HUNT_DIR", str(hunt_root))

        result = CliRunner().invoke(hunt, ["metrics", "gaps"])

        assert "NameError" not in result.output, result.output
        # One of two hunts is complete -> 50% < 80% threshold -> exit 1.
        assert result.exit_code == 1, result.output
        assert "H-9002" in result.output  # the hunt with gaps is reported

    def test_gaps_strict_exits_nonzero_on_any_gap(self, tmp_path, monkeypatch):
        hunt_root = _seed(tmp_path)
        monkeypatch.setenv("ATHF_HUNT_DIR", str(hunt_root))

        result = CliRunner().invoke(hunt, ["metrics", "gaps", "--strict"])

        assert "NameError" not in result.output, result.output
        assert result.exit_code == 1, result.output

    def test_gaps_json_format_is_parseable(self, tmp_path, monkeypatch):
        import json

        hunt_root = _seed(tmp_path)
        monkeypatch.setenv("ATHF_HUNT_DIR", str(hunt_root))

        result = CliRunner().invoke(hunt, ["metrics", "gaps", "--format", "json"])

        assert "NameError" not in result.output, result.output
        payload = json.loads(result.output)
        assert payload  # non-empty JSON object/array
