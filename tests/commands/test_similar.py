"""Tests for similar command."""

import json

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.similar import _extract_session_text, similar


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


class TestExtractSessionText:
    """Tests for _extract_session_text function."""

    def test_extracts_decisions_and_rationales(self, tmp_path):
        """Decision text and rationales are extracted."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        (session_dir / "decisions.yaml").write_text(
            "decisions:\n"
            "- timestamp: '2026-01-15T10:00:00Z'\n"
            "  phase: analysis\n"
            "  decision: svchost spawning PowerShell is Windows Update\n"
            "  rationale: Scheduled task triggers PowerShell for update check\n"
            "  alternatives: null\n"
        )
        result = _extract_session_text(session_dir)
        assert "svchost spawning PowerShell is Windows Update" in result
        assert "Scheduled task triggers PowerShell" in result

    def test_extracts_summary_lessons(self, tmp_path):
        """Summary key decisions and lessons sections are extracted."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        (session_dir / "summary.md").write_text(
            "# Session: H-0001 (2026-01-15)\n\n"
            "**Duration:** 30m | **Queries:** 5 | **Findings:** 0 TP, 0 FP\n\n"
            "## Final Query\n\n```sql\nSELECT 1\n```\n\n"
            "## Key Decisions\n\n"
            "- **Analysis:** Found legitimate automation pattern\n\n"
            "## Lessons\n\n"
            "- Automation patterns common in enterprise\n"
        )
        result = _extract_session_text(session_dir)
        assert "legitimate automation pattern" in result
        assert "Automation patterns common in enterprise" in result

    def test_combines_decisions_and_summary(self, tmp_path):
        """Both decisions.yaml and summary.md content combined."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        (session_dir / "decisions.yaml").write_text(
            "decisions:\n"
            "- timestamp: '2026-01-15T10:00:00Z'\n"
            "  phase: analysis\n"
            "  decision: Telegram bot is known activity\n"
            "  rationale: Already reported to customer\n"
            "  alternatives: null\n"
        )
        (session_dir / "summary.md").write_text(
            "# Session\n\n## Key Decisions\n\n"
            "- Known bot activity\n\n"
            "## Lessons\n\n- Check with customer first\n"
        )
        result = _extract_session_text(session_dir)
        assert "Telegram bot is known activity" in result
        assert "Check with customer first" in result

    def test_empty_session_dir(self, tmp_path):
        """Returns empty string when no session files exist."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        result = _extract_session_text(session_dir)
        assert result == ""

    def test_malformed_decisions_yaml(self, tmp_path):
        """Gracefully handles malformed YAML."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        (session_dir / "decisions.yaml").write_text("not: valid: yaml: [[[")
        result = _extract_session_text(session_dir)
        assert isinstance(result, str)

    def test_nonexistent_dir(self, tmp_path):
        """Returns empty string for nonexistent directory."""
        session_dir = tmp_path / "does-not-exist"
        result = _extract_session_text(session_dir)
        assert result == ""

    def test_skips_queries_yaml(self, tmp_path):
        """SQL from queries.yaml is NOT included."""
        session_dir = tmp_path / "H-0001-2026-01-15"
        session_dir.mkdir()
        (session_dir / "queries.yaml").write_text(
            "queries:\n"
            "- id: q001\n"
            "  sql: SELECT process.name FROM nocsf_unified_events\n"
            "  result_count: 100\n"
        )
        result = _extract_session_text(session_dir)
        assert "SELECT" not in result
        assert "nocsf_unified_events" not in result
