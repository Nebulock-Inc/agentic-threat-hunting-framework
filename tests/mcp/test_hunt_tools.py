"""Tests for hunt MCP tools."""

import json
import pytest
from pathlib import Path

pytest.importorskip("mcp", reason="MCP optional dependency not installed")

from athf.mcp.server import create_server


def _setup_workspace(tmp_path):
    """Create a minimal workspace with sample hunts."""
    (tmp_path / ".athfconfig.yaml").write_text("workspace_name: test\nhunt_prefix: H-\n")
    hunts_dir = tmp_path / "hunts"
    hunts_dir.mkdir()
    (tmp_path / "research").mkdir()
    (tmp_path / "investigations").mkdir()

    # Create sample hunt
    hunt_content = """---
hunt_id: H-0001
title: "Kerberoasting Detection"
technique: T1558.003
tactics:
  - credential-access
platform:
  - Windows
status: completed
result: true_positive
date: 2026-01-01
---

# H-0001: Kerberoasting Detection

## Learn
Kerberoasting allows attackers to request service tickets.

## Observe
Hypothesis: Adversaries request TGS tickets for service accounts.

## Check
Query: index=security EventCode=4769 TicketEncryptionType=0x17

## Keep
Found 3 service accounts with RC4 tickets.
"""
    (hunts_dir / "H-0001.md").write_text(hunt_content)

    hunt2_content = """---
hunt_id: H-0002
title: "Pass-the-Hash Detection"
technique: T1550.002
tactics:
  - lateral-movement
platform:
  - Windows
status: active
date: 2026-01-02
---

# H-0002: Pass-the-Hash Detection

## Learn
Pass-the-Hash uses stolen NTLM hashes.
"""
    (hunts_dir / "H-0002.md").write_text(hunt2_content)
    return tmp_path


@pytest.fixture
def workspace(tmp_path):
    return _setup_workspace(tmp_path)


@pytest.fixture
def server(workspace):
    return create_server(str(workspace))


def _call_tool(server, tool_name, arguments=None):
    """Synchronously call an MCP tool and return parsed JSON."""
    import asyncio

    async def _run():
        result = await server.call_tool(tool_name, arguments or {})
        # call_tool returns (content_list, metadata_dict)
        content_list = result[0] if isinstance(result, tuple) else result
        text = content_list[0].text if content_list else ""
        return json.loads(text)

    return asyncio.run(_run())


class TestHuntList:
    def test_lists_all_hunts(self, server):
        result = _call_tool(server, "athf_hunt_list")
        assert result["count"] == 2

    def test_filter_by_status(self, server):
        result = _call_tool(server, "athf_hunt_list", {"status": "completed"})
        assert result["count"] == 1
        assert result["hunts"][0]["hunt_id"] == "H-0001"

    def test_filter_by_tactic(self, server):
        result = _call_tool(server, "athf_hunt_list", {"tactic": "lateral-movement"})
        assert result["count"] == 1
        assert result["hunts"][0]["hunt_id"] == "H-0002"


class TestHuntSearch:
    def test_search_finds_match(self, server):
        result = _call_tool(server, "athf_hunt_search", {"query": "Kerberoasting"})
        assert result["count"] >= 1

    def test_search_no_match(self, server):
        result = _call_tool(server, "athf_hunt_search", {"query": "zzz_nonexistent_zzz"})
        assert result["count"] == 0


class TestHuntGet:
    def test_get_existing_hunt(self, server):
        result = _call_tool(server, "athf_hunt_get", {"hunt_id": "H-0001"})
        assert result["hunt_id"] == "H-0001"
        assert "frontmatter" in result

    def test_get_nonexistent_hunt(self, server):
        result = _call_tool(server, "athf_hunt_get", {"hunt_id": "H-9999"})
        assert "error" in result


class TestHuntStats:
    def test_returns_stats(self, server):
        result = _call_tool(server, "athf_hunt_stats")
        assert "total_hunts" in result
        assert result["total_hunts"] == 2


class TestHuntCoverage:
    def test_returns_coverage(self, server):
        result = _call_tool(server, "athf_hunt_coverage")
        assert "by_tactic" in result
        assert "summary" in result
        assert result["summary"]["total_techniques"] > 0
        assert len(result["by_tactic"]) == 14

    def test_filter_by_tactic(self, server):
        result = _call_tool(server, "athf_hunt_coverage", {"tactic": "credential-access"})
        assert "error" not in result
        assert "total_techniques" in result


class TestHuntValidate:
    def test_validate_valid_hunt(self, server):
        result = _call_tool(server, "athf_hunt_validate", {"hunt_id": "H-0001"})
        assert result["valid"] is True

    def test_validate_nonexistent(self, server):
        result = _call_tool(server, "athf_hunt_validate", {"hunt_id": "H-9999"})
        assert result["valid"] is False


class TestHuntNew:
    def test_creates_hunt(self, server, workspace):
        result = _call_tool(server, "athf_hunt_new", {
            "title": "Test Hunt Creation",
            "technique": "T1059.001",
        })
        assert "hunt_id" in result
        assert result["technique"] == "T1059.001"
        # Verify file exists
        hunt_file = Path(result["file_path"])
        assert hunt_file.exists()
