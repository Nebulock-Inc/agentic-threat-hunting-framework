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


class MCPDependencyError(ImportError):
    """Raised when the optional MCP server dependencies are missing or an
    incompatible version is installed (e.g. mcp 2.0.0, which removed FastMCP).

    Subclasses ImportError so existing `except ImportError` handlers keep
    working, while giving callers a specific type to catch. The diagnostic
    message lives here so raise sites stay a one-liner (Ruff TRY003)."""

    def __init__(self, cause: BaseException) -> None:
        super().__init__(
            f"Could not import mcp.server.fastmcp.FastMCP ({cause}). This "
            "usually means either the mcp package is not installed, or an "
            "incompatible version is installed: mcp 2.0.0 removed FastMCP. "
            "Install a supported version with: pip install 'athf[mcp]' "
            "(which pins mcp[cli]>=1.9.4,<2.0.0)."
        )


def get_workspace() -> Path:
    """Return the current workspace path."""
    if _workspace is None:
        raise RuntimeError("ATHF MCP server not initialized. Call create_server() first.")
    return _workspace


def _json_result(data: Any) -> str:
    """Serialize a result to JSON string for MCP tool output."""
    return json.dumps(data, indent=2, default=str)


def _discover_plugin_tools() -> list:
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
    except ImportError as exc:
        raise MCPDependencyError(exc) from exc

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
    from athf.mcp.tools.attack_tools import register_attack_tools

    register_hunt_tools(mcp)
    register_search_tools(mcp)
    register_research_tools(mcp)
    register_investigate_tools(mcp)
    register_agent_tools(mcp)
    register_attack_tools(mcp)

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


DEFAULT_HOST = "127.0.0.1"

# Only these reach nothing beyond this machine. Everything else — a wildcard
# bind, a LAN address, a public address — is treated as exposed. The MCP server
# has no authentication and its tools read the full hunt corpus and can invoke
# LLM agents, so anything outside this set needs an explicit opt-in.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def is_exposed_host(host: str) -> bool:
    """Return True if `host` accepts connections from beyond this machine."""
    return host.strip().lower() not in LOOPBACK_HOSTS


def main(
    workspace_path: Optional[str] = None,
    transport: str = "stdio",
    port: int = 3100,
    host: str = DEFAULT_HOST,
) -> None:
    """Entry point for running the MCP server.

    For the HTTP transports the server binds to loopback by default. It serves
    unauthenticated tools over the whole workspace, so exposing it on a routable
    interface requires passing `host` explicitly and putting an authenticating
    proxy in front of it.
    """
    server = create_server(workspace_path)
    if transport in ("sse", "streamable-http"):
        if is_exposed_host(host):
            logger.warning(
                "ATHF MCP server binding to %s:%s — reachable from outside this "
                "machine. The server is UNAUTHENTICATED: anyone who can reach "
                "this port can read every hunt, investigation, and research "
                "document in the workspace and invoke LLM-backed tools at your "
                "expense. Bind to %s and use an authenticating proxy instead.",
                host,
                port,
                DEFAULT_HOST,
            )
        server.settings.host = host
        server.settings.port = port
    server.run(transport=transport)


def cli() -> None:
    """CLI entry point for athf-mcp standalone command."""
    import argparse

    parser = argparse.ArgumentParser(description="ATHF MCP Server")
    parser.add_argument("--workspace", default=None, help="Workspace path")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse", "streamable-http"])
    parser.add_argument("--port", type=int, default=3100, help="HTTP port for SSE/HTTP transport")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=(
            f"Bind address for SSE/HTTP transport (default: {DEFAULT_HOST}). "
            "The server is unauthenticated; only change this behind an "
            "authenticating proxy."
        ),
    )
    args = parser.parse_args()
    main(workspace_path=args.workspace, transport=args.transport, port=args.port, host=args.host)
