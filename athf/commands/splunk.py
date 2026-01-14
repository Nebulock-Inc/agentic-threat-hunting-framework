"""Splunk integration commands for ATHF.

This module provides CLI commands for interacting with Splunk via REST API.
"""

import json
import os
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from athf.core.splunk_client import SplunkClient

console = Console()


def get_client(host: Optional[str], token: Optional[str], verify_ssl: Optional[bool]) -> SplunkClient:
    """Get Splunk client from CLI args or environment variables.

    Args:
        host: Splunk host (from CLI)
        token: Auth token (from CLI)
        verify_ssl: Whether to verify SSL (None to read from env)

    Returns:
        Configured SplunkClient

    Raises:
        click.UsageError: If credentials are not provided
    """
    # Try CLI args first, fall back to environment
    if not host:
        host = os.getenv("SPLUNK_HOST")
    if not token:
        token = os.getenv("SPLUNK_TOKEN")

    # Read verify_ssl from environment if not provided via CLI
    if verify_ssl is None:
        env_verify = os.getenv("SPLUNK_VERIFY_SSL", "true")
        verify_ssl = env_verify.lower() in ("true", "1", "yes")

    if not host or not token:
        raise click.UsageError(
            "Splunk credentials required. Provide via:\n"
            "  • CLI: --host and --token flags\n"
            "  • Environment: SPLUNK_HOST and SPLUNK_TOKEN variables\n"
            "  • Config file: Create .env with credentials"
        )

    return SplunkClient(host=host, token=token, verify_ssl=verify_ssl)


@click.group()
def splunk() -> None:
    """Splunk REST API integration.

    \b
    Execute SPL queries and interact with Splunk directly from ATHF CLI.

    \b
    Setup:
      1. Create a Splunk authentication token:
         Settings → Tokens → New Token

      2. Set environment variables (recommended):
         export SPLUNK_HOST="splunk.example.com"
         export SPLUNK_TOKEN="your-token-here"

      3. Or use --host and --token flags with each command

    \b
    Examples:
      # Test connection
      athf splunk test

      # List available indexes
      athf splunk indexes

      # Execute a query
      athf splunk search 'index=main "Failed password" | head 10'

      # Query with time range
      athf splunk search 'index=* | stats count by sourcetype' \\
        --earliest "-7d" --latest "now" --count 100
    """


@splunk.command()
@click.option("--host", envvar="SPLUNK_HOST", help="Splunk host (e.g., splunk.example.com)")
@click.option("--token", envvar="SPLUNK_TOKEN", help="Splunk authentication token")
@click.option("--verify-ssl/--no-verify-ssl", default=None, help="Verify SSL certificates")
def test(host: Optional[str], token: Optional[str], verify_ssl: Optional[bool]) -> None:
    """Test Splunk connection and authentication.

    \b
    Validates that:
      • Host is reachable
      • Token is valid
      • API access is working

    \b
    Example:
      athf splunk test
    """
    try:
        client = get_client(host, token, verify_ssl)
        info = client.test_connection()

        console.print("\n[bold green]✓ Connection successful![/bold green]\n")

        # Display server info
        if "entry" in info and len(info["entry"]) > 0:
            content = info["entry"][0].get("content", {})
            console.print(f"[bold]Server:[/bold] {content.get('serverName', 'N/A')}")
            console.print(f"[bold]Version:[/bold] {content.get('version', 'N/A')}")
            console.print(f"[bold]Build:[/bold] {content.get('build', 'N/A')}")

    except Exception as e:
        console.print(f"\n[bold red]✗ Connection failed:[/bold red] {e}\n", style="red")
        raise click.Abort()


@splunk.command()
@click.option("--host", envvar="SPLUNK_HOST", help="Splunk host")
@click.option("--token", envvar="SPLUNK_TOKEN", help="Splunk authentication token")
@click.option("--verify-ssl/--no-verify-ssl", default=None, help="Verify SSL certificates")
@click.option("--format", "output_format", type=click.Choice(["table", "json", "list"]), default="list", help="Output format")
def indexes(host: Optional[str], token: Optional[str], verify_ssl: Optional[bool], output_format: str) -> None:
    """List available Splunk indexes.

    \b
    Shows all indexes accessible with current credentials.

    \b
    Example:
      athf splunk indexes
      athf splunk indexes --format json
    """
    try:
        client = get_client(host, token, verify_ssl)
        index_list = client.get_indexes()

        if not index_list:
            console.print("[yellow]No indexes found[/yellow]")
            return

        if output_format == "json":
            click.echo(json.dumps({"indexes": index_list}, indent=2))
        elif output_format == "table":
            table = Table(title=f"Splunk Indexes ({len(index_list)} total)")
            table.add_column("Index Name", style="cyan")
            for idx in sorted(index_list):
                table.add_row(idx)
            console.print(table)
        else:  # list
            console.print(f"\n[bold]Available Indexes ({len(index_list)}):[/bold]\n")
            for idx in sorted(index_list):
                console.print(f"  • {idx}")
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}", style="red")
        raise click.Abort()


@splunk.command()
@click.argument("query")
@click.option("--host", envvar="SPLUNK_HOST", help="Splunk host")
@click.option("--token", envvar="SPLUNK_TOKEN", help="Splunk authentication token")
@click.option("--verify-ssl/--no-verify-ssl", default=None, help="Verify SSL certificates")
@click.option("--earliest", default="-24h", help="Earliest time (e.g., '-24h', '2024-01-01T00:00:00')")
@click.option("--latest", default="now", help="Latest time (e.g., 'now', '2024-01-02T00:00:00')")
@click.option("--count", default=100, type=int, help="Maximum results to return")
@click.option("--format", "output_format", type=click.Choice(["json", "table", "raw"]), default="json", help="Output format")
@click.option("--async-search/--oneshot", "use_async", default=False, help="Use async search for long queries")
@click.option("--max-wait", default=300, type=int, help="Max wait time for async searches (seconds)")
def search(
    query: str,
    host: Optional[str],
    token: Optional[str],
    verify_ssl: Optional[bool],
    earliest: str,
    latest: str,
    count: int,
    output_format: str,
    use_async: bool,
    max_wait: int,
) -> None:
    """Execute a Splunk search query.

    \b
    Runs SPL (Splunk Processing Language) queries and returns results.

    \b
    Query Examples:
      'index=main "Failed password"'
      'index=* sourcetype=linux_secure | stats count by user'
      'index=web status>=400 | timechart count by status'

    \b
    Time Format Examples:
      --earliest "-1h"          (last hour)
      --earliest "-7d"          (last 7 days)
      --earliest "2024-01-01T00:00:00"  (absolute time)

    \b
    Examples:
      # Basic search
      athf splunk search 'index=main error'

      # With time range
      athf splunk search 'index=* | stats count by sourcetype' \\
        --earliest "-7d" --count 1000

      # JSON output for parsing
      athf splunk search 'index=main | head 10' --format json

      # Long-running query (async)
      athf splunk search 'index=* | rare limit=20 sourcetype' \\
        --async-search --max-wait 600
    """
    try:
        client = get_client(host, token, verify_ssl)

        console.print(f"\n[bold]Executing query:[/bold] {query}")
        console.print(f"[bold]Time range:[/bold] {earliest} to {latest}")
        console.print(f"[bold]Max results:[/bold] {count}\n")

        # Execute search
        if use_async:
            console.print("[dim]Using async search (for longer queries)...[/dim]")
            results = client.search_async(
                query=query, earliest_time=earliest, latest_time=latest, max_results=count, max_wait=max_wait
            )
        else:
            console.print("[dim]Using oneshot search (fast for small queries)...[/dim]")
            results = client.search(query=query, earliest_time=earliest, latest_time=latest, max_count=count)

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        console.print(f"[green]✓ Found {len(results)} results[/green]\n")

        # Output results
        if output_format == "json":
            click.echo(json.dumps(results, indent=2, default=str))
        elif output_format == "table":
            if not results:
                return

            # Extract all unique fields
            all_fields: set[str] = set()
            for result in results:
                all_fields.update(result.keys())

            # Create table
            table = Table(title=f"Search Results ({len(results)} events)")
            for field in sorted(all_fields):
                table.add_column(field, overflow="fold")

            # Add rows
            for result in results[:count]:  # Limit display
                row = [str(result.get(field, "")) for field in sorted(all_fields)]
                table.add_row(*row)

            console.print(table)
        else:  # raw
            for i, result in enumerate(results, 1):
                console.print(f"[bold cyan]Event {i}:[/bold cyan]")
                for key, value in result.items():
                    console.print(f"  {key}: {value}")
                console.print()

    except TimeoutError as e:
        console.print(f"\n[bold red]Timeout:[/bold red] {e}", style="red")
        console.print("[yellow]Try using --async-search for long queries[/yellow]")
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}", style="red")
        raise click.Abort()


@splunk.command()
@click.option("--host", envvar="SPLUNK_HOST", help="Splunk host")
@click.option("--token", envvar="SPLUNK_TOKEN", help="Splunk authentication token")
@click.option("--verify-ssl/--no-verify-ssl", default=None, help="Verify SSL certificates")
def config(host: Optional[str], token: Optional[str], verify_ssl: Optional[bool]) -> None:
    """Show current Splunk configuration.

    \b
    Displays configuration from environment variables and validates credentials.

    \b
    Example:
      athf splunk config
    """
    console.print("\n[bold]Splunk Configuration:[/bold]\n")

    # Check environment
    env_host = os.getenv("SPLUNK_HOST")
    env_token = os.getenv("SPLUNK_TOKEN")
    env_verify = os.getenv("SPLUNK_VERIFY_SSL", "true")

    console.print(f"[bold]SPLUNK_HOST:[/bold] {env_host or '[red]Not set[/red]'}")
    console.print(f"[bold]SPLUNK_TOKEN:[/bold] {'[green]Set[/green]' if env_token else '[red]Not set[/red]'}")
    console.print(f"[bold]SPLUNK_VERIFY_SSL:[/bold] {env_verify}")

    # Test connection if credentials available
    if (host or env_host) and (token or env_token):
        console.print("\n[dim]Testing connection...[/dim]")
        try:
            # get_client will read environment variable if verify_ssl is None
            client = get_client(host, token, verify_ssl)
            client.test_connection()
            console.print("[bold green]✓ Connection successful[/bold green]\n")
        except Exception as e:
            console.print(f"[bold red]✗ Connection failed:[/bold red] {e}\n")
    else:
        console.print("\n[yellow]⚠ Missing credentials - cannot test connection[/yellow]\n")
        console.print("[dim]Set SPLUNK_HOST and SPLUNK_TOKEN environment variables[/dim]\n")
