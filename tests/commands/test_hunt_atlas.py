"""Tests for ATLAS support in `athf hunt new`, list and export."""

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.hunt import hunt
from athf.commands.init import init


def _frontmatter(hunt_id: str) -> dict:
    path = next(Path("hunts").rglob(f"{hunt_id}.md"))
    return yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])


@pytest.fixture
def workspace(tmp_path):
    from athf.core import atlas_matrix, attack_matrix

    prev_attack, prev_atlas = attack_matrix._provider, atlas_matrix._provider
    attack_matrix.reset_provider(None)
    atlas_matrix.reset_atlas_provider(None)
    runner = CliRunner()
    try:
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(init, ["--non-interactive"])
            for path in Path("hunts").rglob("H-*.md"):
                path.unlink()
            yield runner
    finally:
        attack_matrix.reset_provider(prev_attack)
        atlas_matrix.reset_atlas_provider(prev_atlas)


def _new(runner, *args):
    return runner.invoke(hunt, ["new", "--title", "AI hunt", "--non-interactive", *args])


@pytest.mark.unit
class TestHuntNewAtlas:
    def test_flags_write_fields(self, workspace):
        result = _new(
            workspace, "--technique", "T1567",
            "--atlas-technique", "AML.T0051", "--atlas-technique", "AML.T0057",
            "--atlas-tactic", "AML.TA0005",
        )
        assert result.exit_code == 0, result.output
        fm = _frontmatter("H-0001")
        assert fm["techniques"] == ["T1567"]
        assert fm["atlas_techniques"] == ["AML.T0051", "AML.T0057"]
        assert fm["atlas_tactics"] == ["AML.TA0005"]

    def test_duplicates_collapse_in_order(self, workspace):
        _new(workspace, "--atlas-technique", "AML.T0057", "--atlas-technique", "AML.T0051",
             "--atlas-technique", "AML.T0057")
        assert _frontmatter("H-0001")["atlas_techniques"] == ["AML.T0057", "AML.T0051"]

    def test_no_flags_no_fields(self, workspace):
        assert _new(workspace).exit_code == 0
        fm = _frontmatter("H-0001")
        assert "atlas_techniques" not in fm and "atlas_tactics" not in fm

    @pytest.mark.parametrize("flag,bad", [
        ("--atlas-technique", "T1059"),
        ("--atlas-technique", "aml.t0051"),
        ("--atlas-tactic", "execution"),
    ])
    def test_malformed_ids_rejected_before_writing(self, workspace, flag, bad):
        result = _new(workspace, flag, bad)
        assert result.exit_code == 2  # click usage error, same as --hunt-type
        assert bad in result.output
        assert not list(Path("hunts").rglob("H-*.md"))

    def test_created_hunt_validates(self, workspace):
        _new(workspace, "--atlas-technique", "AML.T0051")
        result = workspace.invoke(hunt, ["validate", "H-0001"])
        assert result.exit_code == 0, result.output
