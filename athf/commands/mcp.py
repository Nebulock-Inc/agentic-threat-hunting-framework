"""MCP server CLI command."""

import click


@click.group()
def mcp() -> None:
    """MCP server for AI assistant integration."""


@mcp.command()
@click.option("--workspace", default=None, help="Explicit workspace path (auto-detected if not set)")
def serve(workspace: str) -> None:
    """Start the ATHF MCP server (stdio transport).

    This exposes ATHF operations as MCP tools that AI assistants
    (Claude Code, Copilot, Cursor, etc.) can call directly.

    \b
    Configuration for Claude Code (~/.claude/mcp-servers.json):
      {
        "athf": {
          "command": "athf-mcp",
          "args": ["--workspace", "/path/to/hunts"]
        }
      }
    """
    try:
        from athf.mcp.server import main as mcp_main
    except ImportError:
        click.echo("Error: MCP dependencies not installed. Install with: pip install 'athf[mcp]'", err=True)
        raise SystemExit(1) from None

    mcp_main(workspace_path=workspace)
