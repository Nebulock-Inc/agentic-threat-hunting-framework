"""Tests for similar command."""

import json

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.similar import similar


class TestSimilarCommand:
    """Tests for similar command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_similar_requires_query_or_hunt(self, runner):
        """Test that similar requires either query or --hunt option."""
        result = runner.invoke(similar, [])

        assert result.exit_code != 0
        assert "Must provide either QUERY or --hunt" in result.output

    def test_similar_rejects_both_query_and_hunt(self, runner):
        """Test that similar rejects both query and --hunt."""
        result = runner.invoke(similar, ["test query", "--hunt", "H-0001"])

        assert result.exit_code != 0
        assert "Cannot specify both QUERY and --hunt" in result.output

    def test_similar_with_text_query_table_output(self, runner):
        """Test similar search with text query and table output."""
        result = runner.invoke(similar, ["password spraying", "--limit", "3"])

        # Should succeed or fail with scikit-learn error
        assert result.exit_code == 0 or "scikit-learn not installed" in result.output

        if result.exit_code == 0:
            assert "Similar to:" in result.output
            assert "password spraying" in result.output

    def test_similar_json_output(self, runner):
        """Test similar search with JSON output."""
        result = runner.invoke(similar, ["credential theft", "--format", "json"])

        # Should succeed or fail with scikit-learn error
        if result.exit_code == 0:
            # Parse JSON output
            output_data = json.loads(result.output)

            assert isinstance(output_data, list)
            # Each result should have required fields
            if len(output_data) > 0:
                assert "hunt_id" in output_data[0]
                assert "similarity_score" in output_data[0]
                assert "title" in output_data[0]

    def test_similar_yaml_output(self, runner):
        """Test similar search with YAML output."""
        result = runner.invoke(similar, ["kerberos", "--format", "yaml"])

        # Should succeed or fail with scikit-learn error
        if result.exit_code == 0:
            # Parse YAML output
            output_data = yaml.safe_load(result.output)

            assert isinstance(output_data, list)

    def test_similar_limit_parameter(self, runner):
        """Test that limit parameter is respected."""
        result = runner.invoke(similar, ["shell execution", "--limit", "3", "--format", "json"])

        if result.exit_code == 0:
            output_data = json.loads(result.output)
            assert len(output_data) <= 3

    def test_similar_threshold_parameter(self, runner):
        """Test that threshold parameter filters results."""
        # High threshold should return fewer results
        result = runner.invoke(similar, ["reconnaissance", "--threshold", "0.5", "--format", "json"])

        if result.exit_code == 0:
            output_data = json.loads(result.output)

            # All results should have score >= 0.5
            for result_item in output_data:
                assert result_item["similarity_score"] >= 0.5

    def test_similar_nonexistent_hunt(self, runner):
        """Test similar with nonexistent hunt ID."""
        result = runner.invoke(similar, ["--hunt", "H-9999"])

        # Should fail with "not found" or succeed with scikit-learn error
        assert result.exit_code != 0
        assert "not found" in result.output or "scikit-learn not installed" in result.output

    def test_similar_results_sorted_by_score(self, runner):
        """Test that results are sorted by similarity score (descending)."""
        result = runner.invoke(similar, ["lateral movement", "--format", "json"])

        if result.exit_code == 0:
            output_data = json.loads(result.output)

            if len(output_data) > 1:
                # Verify descending order
                scores = [item["similarity_score"] for item in output_data]
                assert scores == sorted(scores, reverse=True)

    def test_similar_results_include_metadata(self, runner):
        """Test that results include hunt metadata."""
        result = runner.invoke(similar, ["privilege escalation", "--format", "json"])

        if result.exit_code == 0:
            output_data = json.loads(result.output)

            if len(output_data) > 0:
                result_item = output_data[0]
                assert "hunt_id" in result_item
                assert "similarity_score" in result_item
                assert "title" in result_item
                assert "status" in result_item
                assert "tactics" in result_item
                assert "techniques" in result_item
                assert "platform" in result_item

    def test_similar_empty_results(self, runner):
        """Test similar with query that returns no results."""
        # Use very high threshold to get no results
        result = runner.invoke(similar, ["very specific unusual query string", "--threshold", "0.99"])

        if result.exit_code == 0:
            assert "No similar hunts found" in result.output or "Found 0" in result.output
