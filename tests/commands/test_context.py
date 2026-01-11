"""Tests for context command."""

import json

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.context import context


class TestContextCommand:
    """Tests for context command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_context_requires_filter(self, runner):
        """Test that context requires at least one filter option."""
        result = runner.invoke(context, [])

        assert result.exit_code != 0
        assert "Must specify at least one of" in result.output

    def test_context_allows_combined_filters(self, runner, tmp_path):
        """Test that context allows combining tactic and platform filters."""
        output_file = tmp_path / "context.json"
        result = runner.invoke(
            context,
            ["--tactic", "persistence", "--platform", "linux", "--format", "json", "--output", str(output_file)],
        )

        assert result.exit_code == 0

        output_data = json.loads(output_file.read_text())
        assert output_data["metadata"]["filters"]["tactic"] == "persistence"
        assert output_data["metadata"]["filters"]["platform"] == "linux"

        # Verify hunts match both filters (if any exist)
        for hunt in output_data["hunts"]:
            assert hunt["hunt_id"]  # Should have valid hunt IDs

    def test_context_full_rejects_other_filters(self, runner):
        """Test that --full flag cannot be combined with other filters."""
        result = runner.invoke(context, ["--full", "--tactic", "persistence"])

        assert result.exit_code != 0
        assert "cannot be combined" in result.output

    def test_context_hunt_json_output(self, runner, tmp_path):
        """Test context export for specific hunt with JSON output."""
        output_file = tmp_path / "context.json"
        result = runner.invoke(context, ["--hunt", "H-0001", "--format", "json", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()

        # Parse JSON from file
        output_data = json.loads(output_file.read_text())

        assert "metadata" in output_data
        assert output_data["metadata"]["filters"]["hunt"] == "H-0001"
        assert "environment" in output_data
        assert "hunt_index" in output_data
        assert "hunts" in output_data

    def test_context_hunt_markdown_output(self, runner):
        """Test context export with markdown output."""
        result = runner.invoke(context, ["--hunt", "H-0001", "--format", "markdown"])

        assert result.exit_code == 0
        assert "# ATHF Context Export" in result.output
        # In an isolated test environment without hunts/environment files,
        # only the header and filters will be present
        assert "Filters:" in result.output

    def test_context_hunt_yaml_output(self, runner):
        """Test context export with YAML output."""
        result = runner.invoke(context, ["--hunt", "H-0001", "--format", "yaml"])

        assert result.exit_code == 0

        # Parse YAML output
        output_data = yaml.safe_load(result.output)

        assert "metadata" in output_data
        assert output_data["metadata"]["filters"]["hunt"] == "H-0001"

    def test_context_tactic_filter(self, runner, tmp_path):
        """Test context export filtered by tactic."""
        output_file = tmp_path / "context.json"
        result = runner.invoke(context, ["--tactic", "execution", "--format", "json", "--output", str(output_file)])

        assert result.exit_code == 0

        output_data = json.loads(output_file.read_text())
        assert output_data["metadata"]["filters"]["tactic"] == "execution"

    def test_context_platform_filter(self, runner, tmp_path):
        """Test context export filtered by platform."""
        output_file = tmp_path / "context.json"
        result = runner.invoke(context, ["--platform", "linux", "--format", "json", "--output", str(output_file)])

        assert result.exit_code == 0

        output_data = json.loads(output_file.read_text())
        assert output_data["metadata"]["filters"]["platform"] == "linux"

    def test_context_output_to_file(self, runner, tmp_path):
        """Test context export to file."""
        output_file = tmp_path / "context.json"

        result = runner.invoke(
            context,
            ["--hunt", "H-0001", "--format", "json", "--output", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Verify file content
        output_data = json.loads(output_file.read_text())
        assert output_data["metadata"]["filters"]["hunt"] == "H-0001"

    def test_context_nonexistent_hunt(self, runner, tmp_path):
        """Test context with nonexistent hunt ID."""
        output_file = tmp_path / "context.json"
        result = runner.invoke(context, ["--hunt", "H-9999", "--format", "json", "--output", str(output_file)])

        # Should succeed but have empty hunts list
        assert result.exit_code == 0

        output_data = json.loads(output_file.read_text())
        assert len(output_data["hunts"]) == 0
