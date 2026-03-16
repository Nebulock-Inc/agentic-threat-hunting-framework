"""Tests for athf.commands.attack - ATT&CK CLI commands."""

import pytest
from click.testing import CliRunner

from athf.commands.attack import attack


@pytest.mark.unit
class TestAttackStatus:
    """Test 'athf attack status' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_status_shows_provider(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Provider" in result.output
        assert "Fallback" in result.output or "STIX" in result.output

    def test_status_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Version" in result.output

    def test_status_shows_tactic_count(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Tactics" in result.output


@pytest.mark.unit
class TestAttackLookup:
    """Test 'athf attack lookup' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_lookup_without_stix_shows_message(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["lookup", "T1003"])
        assert result.exit_code == 0
        assert "not available" in result.output.lower() or "requires" in result.output.lower()


@pytest.mark.unit
class TestAttackTechniques:
    """Test 'athf attack techniques' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_techniques_without_stix_shows_message(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["techniques", "credential-access"])
        assert result.exit_code == 0
        assert "not available" in result.output.lower() or "requires" in result.output.lower()


@pytest.mark.unit
class TestAttackUpdate:
    """Test 'athf attack update' command."""

    def test_update_without_mitreattack_installed(self, monkeypatch):
        """update should error gracefully when mitreattack-python is not installed."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("mitreattack"):
                raise ImportError("mocked: no mitreattack")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        runner = CliRunner()
        result = runner.invoke(attack, ["update"])
        # Should abort (exit code 1) with helpful message
        assert result.exit_code != 0 or "not installed" in result.output.lower()
