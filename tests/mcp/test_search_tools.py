"""Tests for search MCP tools (similar, context)."""

import json
import pytest
from pathlib import Path

pytest.importorskip("mcp", reason="MCP optional dependency not installed")

from athf.mcp.server import create_server


def _setup_workspace(tmp_path):
    """Create workspace with hunts for search testing."""
    (tmp_path / ".athfconfig.yaml").write_text("workspace_name: test\n")
    hunts_dir = tmp_path / "hunts"
    hunts_dir.mkdir()
    (tmp_path / "research").mkdir()
    (tmp_path / "investigations").mkdir()

    hunt_content = """---
hunt_id: H-0001
title: "Credential Dumping via LSASS"
technique: T1003.001
tactics:
  - credential-access
platform:
  - Windows
status: completed
date: 2026-01-01
---

# H-0001: Credential Dumping via LSASS

## Learn
LSASS process memory contains credentials.
"""
    (hunts_dir / "H-0001.md").write_text(hunt_content)

    hunt2_content = """---
hunt_id: H-0002
title: "Lateral Movement via PsExec"
technique: T1570
tactics:
  - lateral-movement
platform:
  - Windows
status: active
date: 2026-01-02
---

# H-0002: Lateral Movement via PsExec

## Learn
PsExec enables remote command execution.
"""
    (hunts_dir / "H-0002.md").write_text(hunt2_content)

    # environment.md
    (tmp_path / "environment.md").write_text("# Environment\nSIEM: Splunk\nEDR: CrowdStrike\n")

    return tmp_path


@pytest.fixture
def workspace(tmp_path):
    return _setup_workspace(tmp_path)


@pytest.fixture
def server(workspace):
    return create_server(str(workspace))


def _call_tool(server, tool_name, arguments=None):
    import asyncio

    async def _run():
        result = await server.call_tool(tool_name, arguments or {})
        content_list = result[0] if isinstance(result, tuple) else result
        text = content_list[0].text if content_list else ""
        return json.loads(text)

    return asyncio.run(_run())


class TestSimilar:
    def test_similar_with_query(self, server):
        result = _call_tool(server, "athf_similar", {"query": "credential dumping LSASS"})
        assert result["count"] >= 1
        assert result["results"][0]["hunt_id"] == "H-0001"

    def test_similar_with_hunt_id(self, server):
        result = _call_tool(server, "athf_similar", {"hunt_id": "H-0001"})
        assert result["count"] >= 1

    def test_similar_no_params(self, server):
        result = _call_tool(server, "athf_similar")
        assert "error" in result

    def test_similar_threshold(self, server):
        result = _call_tool(server, "athf_similar", {"query": "credential dumping", "threshold": 0.9})
        # High threshold may filter out results
        assert "count" in result


class TestContext:
    def test_context_with_hunt_id(self, server):
        result = _call_tool(server, "athf_context", {"hunt_id": "H-0001"})
        assert "hunt" in result
        assert "environment" in result

    def test_context_with_tactic(self, server):
        result = _call_tool(server, "athf_context", {"tactic": "credential-access"})
        assert "hunts" in result
        assert result["hunt_count"] >= 1

    def test_context_no_params(self, server):
        result = _call_tool(server, "athf_context")
        assert "error" in result

    def test_context_includes_environment(self, server):
        result = _call_tool(server, "athf_context", {"hunt_id": "H-0001"})
        assert "Splunk" in result["environment"]
