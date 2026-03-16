"""Tests for ResearchManager.extract_research_context() and find_by_technique()."""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from athf.agents.llm.hypothesis_generator import ResearchContext
from athf.core.research_manager import ResearchManager


SAMPLE_RESEARCH_CONTENT = textwrap.dedent("""\
    ---
    research_id: R-0008
    topic: Rare parent-child process relationships for behavioral detection
    mitre_techniques:
    - T1055
    status: completed
    depth: basic
    duration_minutes: 0.7
    linked_hunts: []
    data_source_availability:
      process_execution: true
      file_operations: true
      network_connections: false
      registry_events: false
    estimated_hunt_complexity: high
    created_date: '2026-02-11'
    ---

    # R-0008: Research

    ## 1. System Research: How It Works

    ### Summary
    Parent-child process relationships define the hierarchical spawning patterns between processes.

    ### Key Findings
    - Legitimate system processes follow predictable parent-child patterns
    - Rare or suspicious relationships include office applications spawning scripting engines

    ---

    ## 2. Adversary Tradecraft: Attack Techniques

    ### Summary
    Adversaries abuse process injection by injecting malicious code into legitimate processes.

    ### Key Findings
    - Office applications spawning command-line interpreters indicates macro-based malware
    - System processes creating unexpected child processes suggests process hollowing

    ---

    ## 3. Telemetry Mapping: OCSF Fields

    ### Summary
    T1055 exhibits rare parent-child process relationships when malicious code spawns unexpected processes.

    ### Key Fields
    - process.parent.name (98%+ populated): Critical for detecting abnormal parent processes
    - process.name (98%+ populated): Identifies suspicious child processes

    ---

    ## 4. Related Work: Past Hunts

    ### Summary
    No related hunts found

    ---

    ## 5. Research Synthesis

    ### Executive Summary
    Process injection creates detectable behavioral anomalies.

    ### Recommended Hypothesis
    > Adversaries use process injection to create rare parent-child relationships to evade detection

    ### Gaps Identified
    - No baseline of legitimate rare-but-benign parent-child relationships exists
    - Cross-platform detection coverage is undefined
    - Telemetry shows process.parent.file.signature.value at only ~70% population

    ### Key Findings
    - Hypothesis: Adversaries use process injection to create rare parent-child relationships
""")


@pytest.fixture
def research_dir(tmp_path):
    """Create a temp research directory with a sample file."""
    research_path = tmp_path / "research"
    research_path.mkdir()
    (research_path / "R-0008.md").write_text(SAMPLE_RESEARCH_CONTENT)
    return research_path


@pytest.fixture
def research_manager(research_dir):
    """Create a ResearchManager with the temp directory."""
    return ResearchManager(research_dir)


class TestExtractResearchContext:
    """Tests for extract_research_context()."""

    def test_extracts_frontmatter_fields(self, research_manager):
        """Test that frontmatter fields are extracted correctly."""
        doc = research_manager.get_research("R-0008")
        assert doc is not None

        ctx = research_manager.extract_research_context(doc)

        assert isinstance(ctx, ResearchContext)
        assert ctx.research_id == "R-0008"
        assert ctx.topic == "Rare parent-child process relationships for behavioral detection"
        assert ctx.mitre_techniques == ["T1055"]
        assert ctx.estimated_hunt_complexity == "high"
        assert ctx.data_source_availability["process_execution"] is True
        assert ctx.data_source_availability["network_connections"] is False

    def test_extracts_recommended_hypothesis(self, research_manager):
        """Test that recommended_hypothesis is extracted from blockquote."""
        doc = research_manager.get_research("R-0008")
        ctx = research_manager.extract_research_context(doc)

        assert ctx.recommended_hypothesis is not None
        assert "process injection" in ctx.recommended_hypothesis.lower()

    def test_extracts_gaps_identified(self, research_manager):
        """Test that gaps are extracted from bullet list."""
        doc = research_manager.get_research("R-0008")
        ctx = research_manager.extract_research_context(doc)

        assert len(ctx.gaps_identified) == 3
        assert "baseline" in ctx.gaps_identified[0].lower()

    def test_extracts_adversary_tradecraft_findings(self, research_manager):
        """Test that adversary tradecraft findings are extracted."""
        doc = research_manager.get_research("R-0008")
        ctx = research_manager.extract_research_context(doc)

        assert len(ctx.adversary_tradecraft_findings) >= 2
        assert "Office" in ctx.adversary_tradecraft_findings[0]

    def test_extracts_telemetry_mapping_findings_from_key_fields(self, research_manager):
        """Test that telemetry findings work with 'Key Fields' heading."""
        doc = research_manager.get_research("R-0008")
        ctx = research_manager.extract_research_context(doc)

        assert len(ctx.telemetry_mapping_findings) >= 2
        assert "process.parent.name" in ctx.telemetry_mapping_findings[0]

    def test_extracts_summaries(self, research_manager):
        """Test that section summaries are extracted."""
        doc = research_manager.get_research("R-0008")
        ctx = research_manager.extract_research_context(doc)

        assert "parent-child" in ctx.system_research_summary.lower()
        assert "process injection" in ctx.adversary_tradecraft_summary.lower()
        assert "T1055" in ctx.telemetry_mapping_summary

    def test_missing_sections_return_defaults(self, research_dir):
        """Test that missing sections produce empty defaults."""
        minimal_content = textwrap.dedent("""\
            ---
            research_id: R-0099
            topic: Minimal research
            mitre_techniques:
            - T9999
            status: completed
            created_date: '2026-01-01'
            ---

            # R-0099: Minimal
        """)
        (research_dir / "R-0099.md").write_text(minimal_content)

        mgr = ResearchManager(research_dir)
        doc = mgr.get_research("R-0099")
        ctx = mgr.extract_research_context(doc)

        assert ctx.research_id == "R-0099"
        assert ctx.recommended_hypothesis is None
        assert ctx.gaps_identified == []
        assert ctx.adversary_tradecraft_findings == []
        assert ctx.telemetry_mapping_findings == []
        assert ctx.system_research_summary == ""
        assert ctx.adversary_tradecraft_summary == ""
        assert ctx.telemetry_mapping_summary == ""


class TestFindByTechnique:
    """Tests for find_by_technique()."""

    def test_finds_matching_research(self, research_manager):
        """Test finding research by technique ID."""
        doc = research_manager.find_by_technique("T1055")

        assert doc is not None
        assert doc["frontmatter"]["research_id"] == "R-0008"

    def test_returns_none_for_no_match(self, research_manager):
        """Test that no match returns None."""
        doc = research_manager.find_by_technique("T9999")

        assert doc is None

    def test_returns_most_recent_when_multiple(self, research_dir):
        """Test that most recent match is returned."""
        older_content = textwrap.dedent("""\
            ---
            research_id: R-0001
            topic: Older research
            mitre_techniques:
            - T1055
            status: completed
            created_date: '2025-01-01'
            ---

            # Older
        """)
        (research_dir / "R-0001.md").write_text(older_content)

        mgr = ResearchManager(research_dir)
        doc = mgr.find_by_technique("T1055")

        assert doc is not None
        # R-0008 has created_date 2026-02-11, R-0001 has 2025-01-01
        assert doc["frontmatter"]["research_id"] == "R-0008"


class TestHelperMethods:
    """Tests for static helper methods."""

    def test_extract_blockquote(self):
        """Test blockquote extraction."""
        text = "### Hypothesis\n> My hypothesis here\n\nMore text"
        result = ResearchManager._extract_markdown_blockquote(text)
        assert result == "My hypothesis here"

    def test_extract_blockquote_none(self):
        """Test blockquote returns None when missing."""
        result = ResearchManager._extract_markdown_blockquote("No blockquote here")
        assert result is None

    def test_extract_list_under_heading(self):
        """Test list extraction under heading."""
        text = "### Gaps Identified\n- Gap one\n- Gap two\n\n### Next Section"
        result = ResearchManager._extract_markdown_list_under_heading(text, "Gaps Identified")
        assert result == ["Gap one", "Gap two"]

    def test_extract_list_empty_when_missing(self):
        """Test list returns empty when heading missing."""
        result = ResearchManager._extract_markdown_list_under_heading("No heading", "Missing")
        assert result == []

    def test_extract_paragraph_under_heading(self):
        """Test paragraph extraction under heading."""
        text = "### Summary\nThis is the summary paragraph.\n\n### Next"
        result = ResearchManager._extract_markdown_paragraph_under_heading(text, "Summary")
        assert result == "This is the summary paragraph."

    def test_extract_paragraph_empty_when_missing(self):
        """Test paragraph returns empty string when heading missing."""
        result = ResearchManager._extract_markdown_paragraph_under_heading("No heading", "Missing")
        assert result == ""
