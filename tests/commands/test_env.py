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

    def test_env_group_exists(self, runner):
        """Test that env command group is callable."""
        result = runner.invoke(env, ["--help"])

        assert result.exit_code == 0
        assert "Manage Python virtual environment" in result.output

    def test_env_setup_help(self, runner):
        """Test env setup command help."""
        result = runner.invoke(env, ["setup", "--help"])

        assert result.exit_code == 0
        assert "Setup Python virtual environment" in result.output
        assert "--python" in result.output
        assert "--dev" in result.output
        assert "--clean" in result.output

    def test_env_info_help(self, runner):
        """Test env info command help."""
        result = runner.invoke(env, ["info", "--help"])

        assert result.exit_code == 0
        assert "Show virtual environment information" in result.output

    def test_env_clean_help(self, runner):
        """Test env clean command help."""
        result = runner.invoke(env, ["clean", "--help"])

        assert result.exit_code == 0
        assert "Remove virtual environment" in result.output

    def test_env_activate_help(self, runner):
        """Test env activate command help."""
        result = runner.invoke(env, ["activate", "--help"])

        assert result.exit_code == 0
        assert "Show command to activate virtual environment" in result.output

    def test_env_deactivate_help(self, runner):
        """Test env deactivate command help."""
        result = runner.invoke(env, ["deactivate", "--help"])

        assert result.exit_code == 0
        assert "Show command to deactivate virtual environment" in result.output

    def test_env_info_shows_info(self, runner):
        """Test that env info shows environment information."""
        result = runner.invoke(env, ["info"])

        assert result.exit_code == 0
        # Should show either environment info or missing venv message
        assert "Virtual Environment Info" in result.output or "No virtual environment" in result.output

    def test_env_activate_shows_command(self, runner):
        """Test that env activate shows activation command."""
        result = runner.invoke(env, ["activate"])

        assert result.exit_code == 0
        # Should show activation command or setup instructions
        assert "source" in result.output or "athf env setup" in result.output

    def test_env_deactivate_shows_command(self, runner):
        """Test that env deactivate shows deactivation command."""
        result = runner.invoke(env, ["deactivate"])

        assert result.exit_code == 0
        # Should show deactivation command
        assert "deactivate" in result.output

    # Note: We don't test actual setup/clean operations in unit tests
    # as they modify the filesystem and require subprocess execution.
    # These are better tested in integration tests or manually.
