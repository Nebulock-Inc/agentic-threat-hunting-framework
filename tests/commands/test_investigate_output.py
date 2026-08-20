"""Tests for `athf investigate` user-facing output."""

from click.testing import CliRunner

from athf.commands.investigate import new as investigate_new


class TestInvestigateNewNextSteps:
    """The next-steps block must print a runnable command, not a template."""

    def test_promote_hint_contains_real_investigation_id(self, tmp_path):
        """Regression: this line lacked an f-prefix and printed the literal
        text "{investigation_id}", which is not a runnable command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                investigate_new,
                ["--title", "Odd PowerShell parent", "--non-interactive"],
            )

            assert result.exit_code == 0, result.output
            assert "athf investigate promote I-0001" in result.output
            assert "{investigation_id}" not in result.output
