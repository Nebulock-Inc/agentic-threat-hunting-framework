"""End-to-end: investigate commands must handle nested investigation files."""

from pathlib import Path

from click.testing import CliRunner

from athf.commands.investigate import new as investigate_new
from athf.commands.investigate import promote as investigate_promote
from athf.commands.investigate import validate as investigate_validate


def _nest(investigation_id: str) -> Path:
    """Move a freshly created investigation into a subdirectory."""
    src = Path("investigations") / f"{investigation_id}.md"
    dest_dir = Path("investigations") / "2026" / "Q3"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.rename(dest)
    return dest


class TestNestedInvestigationCommands:
    """Regression: these resolved investigations/I-XXXX.md directly and failed
    with "Investigation file not found" once a file lived in a subdirectory."""

    def test_validate_finds_nested_investigation(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(investigate_new, ["--title", "Nested", "--non-interactive"])
            _nest("I-0001")

            result = runner.invoke(investigate_validate, ["I-0001"])

            assert result.exit_code == 0, result.output
            assert "not found" not in result.output
            assert "I-0001 is valid" in result.output

    def test_promote_finds_nested_investigation(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(investigate_new, ["--title", "Nested", "--non-interactive"])
            _nest("I-0001")

            result = runner.invoke(
                investigate_promote,
                ["I-0001", "--technique", "T1059.001", "--non-interactive"],
            )

            assert result.exit_code == 0, result.output
            assert "not found" not in result.output
            assert "Promoted I-0001" in result.output
