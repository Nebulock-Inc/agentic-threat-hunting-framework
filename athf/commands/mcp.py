"""MCP server CLI command."""

import click


@click.group()
def mcp() -> None:
    """MCP server for AI assistant integration."""


@mcp.command()
@click.option("--workspace", default=None, help="Explicit workspace path (auto-detected if not set)")
@click.option("--transport", default="stdio", type=click.Choice(["stdio", "sse", "streamable-http"]), help="Transport protocol")
@click.option("--port", default=3100, type=int, help="HTTP port for SSE transport")
def serve(workspace: str, transport: str, port: int) -> None:
    """Start the ATHF MCP server.

    This exposes ATHF operations as MCP tools that AI assistants
    (Claude Code, Copilot, Cursor, etc.) can call directly.

    \b
    Stdio (default, for Claude Code):
      athf mcp serve --workspace /path/to/hunts

    \b
    HTTP (for web UI integration):
      athf mcp serve --transport streamable-http --port 3100

    \b
    Configuration for Claude Code (~/.claude/mcp-servers.json):
      {
        "athf": {
          "command": "athf-mcp",
          "args": ["--workspace", "/path/to/hunts"]
        }
      }
    """
    # The mcp import happens lazily inside create_server(), so an
    # incompatible-version ImportError surfaces when mcp_main runs, not at the
    # import above. Wrap both to give one clear, version-aware message.
    try:
        from athf.mcp.server import main as mcp_main

        mcp_main(workspace_path=workspace, transport=transport, port=port)
    except ImportError as exc:
        click.echo(
            "Error starting the ATHF MCP server: {}\n"
            "This usually means the mcp package is missing or an incompatible "
            "version is installed (mcp 2.0.0 removed FastMCP). Install a supported "
            "version with: pip install 'athf[mcp]' (pins mcp[cli]>=1.0.0,<2.0.0).".format(exc),
            err=True,
        )
        raise SystemExit(1) from exc
