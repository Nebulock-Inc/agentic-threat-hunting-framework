"""
Tests for ATHF CLI commands using actual implementation.
"""

import os

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.hunt import hunt
from athf.commands.init import init


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace for testing."""
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)


class TestInitCommand:
    """Test suite for athf init command."""

    def test_init_creates_structure_non_interactive(self, runner, temp_workspace):
        """Test that init creates the correct directory structure in non-interactive mode."""
        result = runner.invoke(init, ["--non-interactive"])

        assert result.exit_code == 0
        assert (temp_workspace / "hunts").exists()
        assert (temp_workspace / "queries").exists()
        assert (temp_workspace / "runs").exists()
        assert (temp_workspace / "templates").exists()
        assert (temp_workspace / "knowledge").exists()
        assert (temp_workspace / "prompts").exists()
        assert (temp_workspace / "integrations").exists()
        assert (temp_workspace / "docs").exists()

    def test_init_creates_config_file(self, runner, temp_workspace):
        """Test that init creates a valid config file."""
        result = runner.invoke(init, ["--non-interactive"])

        assert result.exit_code == 0
        config_path = temp_workspace / "config" / ".athfconfig.yaml"
        assert config_path.exists()

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert "hunt_prefix" in config
        assert "siem" in config
        assert "edr" in config
        assert config["hunt_prefix"] == "H-"

    def test_init_creates_agents_file(self, runner, temp_workspace):
        """Test that init creates AGENTS.md."""
        result = runner.invoke(init, ["--non-interactive"])

        assert result.exit_code == 0
        agents_path = temp_workspace / "AGENTS.md"
        assert agents_path.exists()

        content = agents_path.read_text()
        assert "Data Sources" in content
        assert "Technology Stack" in content

    def test_init_creates_hunt_template(self, runner, temp_workspace):
        """Test that init creates hunt template."""
        result = runner.invoke(init, ["--non-interactive"])

        assert result.exit_code == 0
        template_path = temp_workspace / "templates" / "HUNT_LOCK.md"
        assert template_path.exists()

        content = template_path.read_text()
        assert "## LEARN" in content
        assert "## OBSERVE" in content
        assert "## CHECK" in content
        assert "## KEEP" in content

    def test_init_with_custom_path(self, runner, tmp_path):
        """Test init with custom path."""
        custom_path = tmp_path / "custom_workspace"
        custom_path.mkdir()

        result = runner.invoke(init, ["--path", str(custom_path), "--non-interactive"])

        assert result.exit_code == 0
        assert (custom_path / "hunts").exists()
        assert (custom_path / "config" / ".athfconfig.yaml").exists()


class TestHuntNewCommand:
    """Test suite for athf hunt new command."""

    def test_hunt_new_non_interactive(self, runner, temp_workspace):
        """Test creating a new hunt in non-interactive mode."""
        # First initialize
        runner.invoke(init, ["--non-interactive"])

        # Create hunt
        result = runner.invoke(
            hunt,
            [
                "new",
                "--technique",
                "T1003.001",
                "--title",
                "LSASS Memory Dumping",
                "--tactic",
                "credential-access",
                "--platform",
                "Windows",
                "--data-source",
                "EDR",
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0
        # Extract created hunt ID from output (init may copy sample hunts)
        import re

        match = re.search(r"Created (H-\d+)", result.output)
        assert match, f"Could not find hunt ID in output: {result.output}"
        hunt_id = match.group(1)

        # Check hunt file was created
        hunt_file = temp_workspace / "hunts" / f"{hunt_id}.md"
        assert hunt_file.exists()

        content = hunt_file.read_text()
        assert f"hunt_id: {hunt_id}" in content
        assert "LSASS Memory Dumping" in content
        assert "T1003.001" in content
        assert "## LEARN" in content

    def test_hunt_new_missing_title_non_interactive(self, runner, temp_workspace):
        """Test that hunt new fails without title in non-interactive mode."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["new", "--technique", "T1003.001", "--non-interactive"])

        assert result.exit_code == 0  # Click doesn't exit with error, just prints message
        assert "Error" in result.output or "required" in result.output.lower()

    def test_hunt_new_increments_id(self, runner, temp_workspace):
        """Test that hunt IDs increment correctly."""
        import re

        runner.invoke(init, ["--non-interactive"])

        # Create first hunt
        result1 = runner.invoke(hunt, ["new", "--title", "First Hunt", "--non-interactive"])
        match1 = re.search(r"Created (H-\d+)", result1.output)
        assert match1, f"Could not find hunt ID in output: {result1.output}"
        hunt_id_1 = match1.group(1)
        num1 = int(hunt_id_1.split("-")[1])

        # Create second hunt
        result2 = runner.invoke(hunt, ["new", "--title", "Second Hunt", "--non-interactive"])
        match2 = re.search(r"Created (H-\d+)", result2.output)
        assert match2, f"Could not find hunt ID in output: {result2.output}"
        hunt_id_2 = match2.group(1)
        num2 = int(hunt_id_2.split("-")[1])

        # Second hunt should have ID incremented by 1
        assert num2 == num1 + 1, f"Expected {hunt_id_2} to be one more than {hunt_id_1}"

    def test_hunt_new_with_multiple_tactics(self, runner, temp_workspace):
        """Test creating hunt with multiple tactics."""
        import re

        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(
            hunt,
            [
                "new",
                "--title",
                "Multi-Tactic Hunt",
                "--tactic",
                "persistence",
                "--tactic",
                "privilege-escalation",
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0
        # Extract created hunt ID from output
        match = re.search(r"Created (H-\d+)", result.output)
        assert match, f"Could not find hunt ID in output: {result.output}"
        hunt_id = match.group(1)

        hunt_file = temp_workspace / "hunts" / f"{hunt_id}.md"
        content = hunt_file.read_text()
        assert "persistence" in content
        assert "privilege-escalation" in content

    def test_hunt_new_with_rich_content(self, runner, temp_workspace):
        """Test creating hunt with rich content parameters (hypothesis, threat-context, ABLE framework)."""
        import re

        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(
            hunt,
            [
                "new",
                "--title",
                "Rich Content Hunt",
                "--technique",
                "T1003.001",
                "--tactic",
                "credential-access",
                "--platform",
                "Windows",
                "--data-source",
                "Sysmon",
                "--hypothesis",
                "Adversaries dump LSASS memory to extract credentials",
                "--threat-context",
                "APT29 and ransomware groups commonly use this technique",
                "--actor",
                "APT29, Ransomware operators",
                "--behavior",
                "Process access to lsass.exe with PROCESS_VM_READ",
                "--location",
                "Windows endpoints, Domain Controllers",
                "--evidence",
                "Sysmon Event ID 10, EDR process access events",
                "--hunter",
                "Test Hunter",
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0
        # Extract created hunt ID from output
        match = re.search(r"Created (H-\d+)", result.output)
        assert match, f"Could not find hunt ID in output: {result.output}"
        hunt_id = match.group(1)

        hunt_file = temp_workspace / "hunts" / f"{hunt_id}.md"
        content = hunt_file.read_text()

        # Verify YAML frontmatter
        assert f"hunt_id: {hunt_id}" in content
        assert "hunter: Test Hunter" in content

        # Verify hypothesis is populated
        assert "Adversaries dump LSASS memory to extract credentials" in content

        # Verify threat context is populated
        assert "APT29 and ransomware groups commonly use this technique" in content

        # Verify ABLE framework fields are populated
        assert "APT29, Ransomware operators" in content
        assert "Process access to lsass.exe with PROCESS_VM_READ" in content
        assert "Windows endpoints, Domain Controllers" in content
        assert "Sysmon Event ID 10, EDR process access events" in content

        # Verify it's not using default placeholders
        assert "[What behavior are you looking for?" not in content
        assert "[What threat actor/malware/TTP motivates this hunt?]" not in content
        assert "[Threat actor or malware family]" not in content


class TestHuntListCommand:
    """Test suite for athf hunt list command."""

    def setup_test_hunts(self, runner, temp_workspace):
        """Helper to create test hunts."""
        runner.invoke(init, ["--non-interactive"])

        # Create hunt 1
        runner.invoke(
            hunt,
            [
                "new",
                "--title",
                "Test Hunt 1",
                "--technique",
                "T1003.001",
                "--tactic",
                "credential-access",
                "--platform",
                "Windows",
                "--non-interactive",
            ],
        )

        # Create hunt 2
        runner.invoke(
            hunt,
            [
                "new",
                "--title",
                "Test Hunt 2",
                "--technique",
                "T1053.003",
                "--tactic",
                "persistence",
                "--platform",
                "Linux",
                "--non-interactive",
            ],
        )

    def test_hunt_list_all(self, runner, temp_workspace):
        """Test listing all hunts."""
        self.setup_test_hunts(runner, temp_workspace)

        result = runner.invoke(hunt, ["list"])

        assert result.exit_code == 0
        # Sample hunts may be copied, so just check our test hunts are listed
        assert "Test Hunt 1" in result.output
        assert "Test Hunt 2" in result.output

    def test_hunt_list_filter_by_status(self, runner, temp_workspace):
        """Test filtering hunts by status."""
        self.setup_test_hunts(runner, temp_workspace)

        result = runner.invoke(hunt, ["list", "--status", "planning"])

        assert result.exit_code == 0
        # Created test hunts should be in planning status by default
        # (sample hunts may have different statuses)
        assert "Test Hunt 1" in result.output or "Test Hunt 2" in result.output

    def test_hunt_list_filter_by_technique(self, runner, temp_workspace):
        """Test filtering hunts by technique."""
        self.setup_test_hunts(runner, temp_workspace)

        result = runner.invoke(hunt, ["list", "--technique", "T1003.001"])

        assert result.exit_code == 0
        assert "T1003.001" in result.output

    def test_hunt_list_json_output(self, runner, temp_workspace):
        """Test JSON output format."""
        self.setup_test_hunts(runner, temp_workspace)

        result = runner.invoke(hunt, ["list", "--output", "json"])

        assert result.exit_code == 0
        assert '"hunt_id"' in result.output or "hunt_id" in result.output

    def test_hunt_list_empty(self, runner, temp_workspace):
        """Test list with no user-created hunts (sample hunts may exist)."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["list"])

        # init may copy sample hunts, so this test just checks the command works
        # If no sample hunts exist, we'll see "No hunts found"
        # If sample hunts exist, we'll see the hunt catalog
        assert result.exit_code == 0
        assert "No hunts found" in result.output or "Hunt Catalog" in result.output or "H-" in result.output


class TestHuntValidateCommand:
    """Test suite for athf hunt validate command."""

    def test_validate_all_hunts(self, runner, temp_workspace):
        """Test validating all hunts."""
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(hunt, ["new", "--title", "Test Hunt", "--non-interactive"])

        result = runner.invoke(hunt, ["validate"])

        assert result.exit_code == 0

    def test_validate_specific_hunt(self, runner, temp_workspace):
        """Test validating a specific hunt."""
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(hunt, ["new", "--title", "Test Hunt", "--non-interactive"])

        result = runner.invoke(hunt, ["validate", "H-0001"])

        assert result.exit_code == 0

    def test_validate_nonexistent_hunt(self, runner, temp_workspace):
        """Test validating a hunt that doesn't exist."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["validate", "H-9999"])

        assert result.exit_code == 0  # Command runs but shows error message
        assert "not found" in result.output.lower()


class TestHuntStatsCommand:
    """Test suite for athf hunt stats command."""

    def test_hunt_stats_empty(self, runner, temp_workspace):
        """Test stats with no hunts."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["stats"])

        assert result.exit_code == 0
        assert "Statistics" in result.output or "stats" in result.output.lower()

    def test_hunt_stats_with_hunts(self, runner, temp_workspace):
        """Test stats with hunts created."""
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(hunt, ["new", "--title", "Test Hunt", "--non-interactive"])

        result = runner.invoke(hunt, ["stats"])

        assert result.exit_code == 0
        assert "Total Hunts" in result.output or "total" in result.output.lower()


class TestHuntSearchCommand:
    """Test suite for athf hunt search command."""

    def test_hunt_search(self, runner, temp_workspace):
        """Test searching for hunts."""
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(hunt, ["new", "--title", "Kerberoasting Detection", "--technique", "T1558.003", "--non-interactive"])

        result = runner.invoke(hunt, ["search", "Kerberoasting"])

        assert result.exit_code == 0

    def test_hunt_search_no_results(self, runner, temp_workspace):
        """Test search with no results."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No hunts found" in result.output or "found" in result.output.lower()


class TestHuntCoverageCommand:
    """Test suite for athf hunt coverage command."""

    def test_hunt_coverage(self, runner, temp_workspace):
        """Test ATT&CK coverage command."""
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(
            hunt,
            ["new", "--title", "Test Hunt", "--technique", "T1003.001", "--tactic", "credential-access", "--non-interactive"],
        )

        result = runner.invoke(hunt, ["coverage"])

        assert result.exit_code == 0

    def test_hunt_coverage_empty(self, runner, temp_workspace):
        """Test coverage with no hunts."""
        runner.invoke(init, ["--non-interactive"])

        result = runner.invoke(hunt, ["coverage"])

        assert result.exit_code == 0


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_full_workflow(self, runner, temp_workspace):
        """Test complete workflow: init -> new -> validate -> list -> stats."""
        import re

        # Step 1: Initialize
        result = runner.invoke(init, ["--non-interactive"])
        assert result.exit_code == 0

        # Step 2: Create new hunt
        result = runner.invoke(
            hunt,
            [
                "new",
                "--technique",
                "T1003.001",
                "--title",
                "LSASS Memory Dumping",
                "--tactic",
                "credential-access",
                "--platform",
                "Windows",
                "--non-interactive",
            ],
        )
        assert result.exit_code == 0
        # Extract created hunt ID from output
        match = re.search(r"Created (H-\d+)", result.output)
        assert match, f"Could not find hunt ID in output: {result.output}"
        hunt_id = match.group(1)

        # Step 3: Validate
        result = runner.invoke(hunt, ["validate", hunt_id])
        assert result.exit_code == 0

        # Step 4: List hunts
        result = runner.invoke(hunt, ["list"])
        assert result.exit_code == 0
        assert hunt_id in result.output

        # Step 5: Show stats
        result = runner.invoke(hunt, ["stats"])
        assert result.exit_code == 0

        # Step 6: Search
        result = runner.invoke(hunt, ["search", "LSASS"])
        assert result.exit_code == 0

    def test_multiple_hunts_workflow(self, runner, temp_workspace):
        """Test workflow with multiple hunts."""
        runner.invoke(init, ["--non-interactive"])

        # Create 3 hunts
        for i in range(1, 4):
            result = runner.invoke(hunt, ["new", "--title", f"Hunt {i}", "--technique", f"T100{i}.001", "--non-interactive"])
            assert result.exit_code == 0

        # List should show all 3
        result = runner.invoke(hunt, ["list"])
        assert result.exit_code == 0
        assert "H-0001" in result.output
        assert "H-0002" in result.output
        assert "H-0003" in result.output


class TestCLIErrorHandling:
    """Test suite for CLI error handling."""

    def test_hunt_commands_without_init(self, runner, temp_workspace):
        """Test that hunt commands handle missing initialization gracefully."""
        # Try to create hunt without init
        result = runner.invoke(hunt, ["new", "--title", "Test", "--non-interactive"])

        # Should still work, creating directories as needed
        assert result.exit_code == 0 or "error" in result.output.lower()

    def test_init_twice(self, runner, temp_workspace):
        """Test running init twice."""
        # First init
        result1 = runner.invoke(init, ["--non-interactive"])
        assert result1.exit_code == 0

        # Second init should ask for confirmation (but we're non-interactive)
        # In non-interactive mode, it might skip or proceed
        result2 = runner.invoke(init, ["--non-interactive"])
        # Should handle gracefully
        assert result2.exit_code == 0 or "already" in result2.output.lower()


# Run tests with: pytest tests/test_commands.py -v
