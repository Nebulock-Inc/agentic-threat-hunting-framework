"""Integration test: verify plugin MCP tools are discovered by the server.

This test requires hunt-vault and detect-vault to be installed in the same venv.
Skip if they are not available.
"""

import asyncio
import pytest

pytest.importorskip("mcp", reason="MCP optional dependency not installed")


def _has_plugin(group: str, name: str) -> bool:
    import sys
    if sys.version_info >= (3, 10):
        from importlib.metadata import entry_points
        eps = entry_points(group=group)
    else:
        from importlib.metadata import entry_points
        eps = entry_points().get(group, [])
    return any(ep.name == name for ep in eps)


@pytest.mark.skipif(
    not _has_plugin("athf.mcp_tools", "hunt-vault"),
    reason="hunt-vault not installed with athf.mcp_tools entry point",
)
class TestHuntVaultPluginIntegration:
    def test_hunt_vault_tools_registered(self, tmp_path):
        (tmp_path / ".athfconfig.yaml").write_text("workspace_name: test\n")
        (tmp_path / "hunts").mkdir()
        (tmp_path / "research").mkdir()
        (tmp_path / "investigations").mkdir()
        (tmp_path / "queries").mkdir()

        from athf.mcp.server import create_server
        server = create_server(str(tmp_path))

        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]

        assert "athf_hunt_list" in tool_names

        assert "hv_clickhouse_query" in tool_names
        assert "hv_query_list" in tool_names
        assert "hv_session_start" in tool_names
        assert "hv_baseline_detect" in tool_names
        assert "hv_signals_scan" in tool_names
        assert "hv_metrics_summary" in tool_names
        assert "hv_deliverable_generate" in tool_names


@pytest.mark.skipif(
    not _has_plugin("athf.mcp_tools", "detect-vault"),
    reason="detect-vault not installed with athf.mcp_tools entry point",
)
class TestDetectVaultPluginIntegration:
    def test_detect_vault_tools_registered(self, tmp_path):
        (tmp_path / ".athfconfig.yaml").write_text("workspace_name: test\n")
        (tmp_path / "hunts").mkdir()
        (tmp_path / "research").mkdir()
        (tmp_path / "investigations").mkdir()

        from athf.mcp.server import create_server
        server = create_server(str(tmp_path))

        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]

        assert "dv_detect_list" in tool_names
        assert "dv_detect_show" in tool_names
        assert "dv_detect_search" in tool_names
        assert "dv_detect_performance" in tool_names
