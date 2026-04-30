"""Tests for env command."""

import pytest
from click.testing import CliRunner

from athf.commands.env import env


class TestEnvCommand:
    """Tests for env command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_env_info_shows_info(self, runner):
        """Test that env info shows environment information."""
        result = runner.invoke(env, ["info"])

        assert result.exit_code == 0
        # Should show either environment info or missing venv message
        assert "Virtual Environment Info" in result.output or "No .venv directory found" in result.output

    def test_env_activate_shows_command(self, runner):
        """Test that env activate shows activation command."""
        result = runner.invoke(env, ["activate"])

        # Exit code 1 when no venv exists (click.Abort), 0 when venv exists
        assert result.exit_code in (0, 1)
        # Should show activation command or setup instructions
        assert "source" in result.output or "athf env setup" in result.output or "No .venv directory found" in result.output

    def test_env_deactivate_shows_command(self, runner):
        """Test that env deactivate shows deactivation command."""
        result = runner.invoke(env, ["deactivate"])

        assert result.exit_code == 0
        # Should show deactivation command
        assert "deactivate" in result.output

    # Note: We don't test actual setup/clean operations in unit tests
    # as they modify the filesystem and require subprocess execution.
    # These are better tested in integration tests or manually.
