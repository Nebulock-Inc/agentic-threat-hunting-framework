"""ATHF MCP Server — expose threat hunting operations as MCP tools.

Usage:
    athf mcp serve                    # auto-detect workspace
    athf mcp serve --workspace /path  # explicit workspace
    athf-mcp                          # standalone entry point
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Global workspace path — set during server startup
_workspace: Optional[Path] = None


def get_workspace() -> Path:
    """Return the current workspace path."""
    if _workspace is None:
        raise RuntimeError("ATHF MCP server not initialized. Call create_server() first.")
    return _workspace


def _json_result(data: Any) -> str:
    """Serialize a result to JSON string for MCP tool output."""
    return json.dumps(data, indent=2, default=str)


def _discover_plugin_tools():
    """Discover MCP tool registration functions from installed plugins."""
    if sys.version_info >= (3, 10):
        from importlib.metadata import entry_points
        return list(entry_points(group="athf.mcp_tools"))
    else:
        from importlib.metadata import entry_points
        return list(entry_points().get("athf.mcp_tools", []))


def create_server(workspace_path: Optional[str] = None) -> "FastMCP":  # type: ignore[name-defined]  # noqa: F821
    """Create and configure the ATHF MCP server.

    Args:
        workspace_path: Explicit workspace path (optional).

    Returns:
        Configured FastMCP server instance.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        raise ImportError(
            "MCP dependencies not installed. Install with: pip install 'athf[mcp]'"
        ) from None

    from athf.mcp.utils import find_workspace, load_workspace_config

    global _workspace
    _workspace = find_workspace(workspace_path)
    load_workspace_config(_workspace)

    mcp = FastMCP(
        name="athf",
        instructions=(
            "ATHF (Agentic Threat Hunting Framework) server. "
            "Provides threat hunting operations: search hunts, check ATT&CK coverage, "
            "find similar hunts, create new hunts, run AI-powered research, and more. "
            f"Workspace: {_workspace}"
        ),
    )

    # Register all tool modules
    from athf.mcp.tools.hunt_tools import register_hunt_tools
    from athf.mcp.tools.search_tools import register_search_tools
    from athf.mcp.tools.research_tools import register_research_tools
    from athf.mcp.tools.investigate_tools import register_investigate_tools
    from athf.mcp.tools.agent_tools import register_agent_tools

    register_hunt_tools(mcp)
    register_search_tools(mcp)
    register_research_tools(mcp)
    register_investigate_tools(mcp)
    register_agent_tools(mcp)

    for ep in _discover_plugin_tools():
        try:
            register_fn = ep.load()
            register_fn(mcp, _workspace)
            logger.info("Loaded MCP tools from plugin: %s", ep.name)
        except Exception:
            logger.warning("Failed to load MCP tools from plugin: %s", ep.name, exc_info=True)

    logger.info("ATHF MCP server initialized with workspace: %s", _workspace)
    return mcp


def reset_server() -> None:
    """Reset global server state (for testing)."""
    global _workspace
    _workspace = None


def main(workspace_path: Optional[str] = None) -> None:
    """Entry point for running the MCP server via stdio."""
    server = create_server(workspace_path)
    server.run(transport="stdio")
