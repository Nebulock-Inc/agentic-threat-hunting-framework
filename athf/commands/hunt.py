"""Hunt management commands."""

import click
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import box
from athf.core.hunt_manager import HuntManager
from athf.core.template_engine import render_hunt_template
from athf.core.hunt_parser import validate_hunt_file

console = Console()


def get_config_path():
    """Get config file path, checking new location first, then falling back to root."""
    new_location = Path("config/.athfconfig.yaml")
    old_location = Path(".athfconfig.yaml")

    if new_location.exists():
        return new_location
    elif old_location.exists():
        return old_location
    else:
        return new_location  # Default to new location for creation


@click.group()
def hunt():
    """Manage threat hunts."""
    pass


@hunt.command()
@click.option("--technique", help="MITRE ATT&CK technique (e.g., T1003.001)")
@click.option("--title", help="Hunt title")
@click.option("--tactic", multiple=True, help="MITRE tactics (can specify multiple)")
@click.option("--platform", multiple=True, help="Target platforms (can specify multiple)")
@click.option("--data-source", multiple=True, help="Data sources (can specify multiple)")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
def new(technique, title, tactic, platform, data_source, non_interactive):
    """Create a new hunt.

    Interactive mode guides you through creating a hunt with proper structure.
    """
    console.print("\n[bold cyan]🎯 Creating new hunt[/bold cyan]\n")

    # Load config
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
    else:
        config = {"hunt_prefix": "H-"}

    hunt_prefix = config.get("hunt_prefix", "H-")

    # Get next hunt ID
    manager = HuntManager()
    hunt_id = manager.get_next_hunt_id(prefix=hunt_prefix)

    console.print(f"[bold]Hunt ID:[/bold] {hunt_id}")

    # Gather hunt details
    if non_interactive:
        if not title:
            console.print("[red]Error: --title required in non-interactive mode[/red]")
            return
        hunt_title = title
        hunt_technique = technique or "T1005"
        hunt_tactics = list(tactic) if tactic else ["collection"]
        hunt_platforms = list(platform) if platform else ["Windows"]
        hunt_data_sources = list(data_source) if data_source else ["SIEM", "EDR"]
    else:
        # Interactive prompts
        console.print("\n[bold]🔍 Let's build your hypothesis:[/bold]")

        # Technique
        hunt_technique = Prompt.ask(
            "1. MITRE ATT&CK Technique (e.g., T1003.001)",
            default=technique or ""
        )

        # Title
        hunt_title = Prompt.ask(
            "2. Hunt Title",
            default=title or f"Hunt for {hunt_technique}"
        )

        # Tactics
        console.print("\n3. Primary Tactic(s) (comma-separated):")
        console.print("   Common: [cyan]persistence, credential-access, collection, lateral-movement[/cyan]")
        tactic_input = Prompt.ask("   Tactics", default=",".join(tactic) if tactic else "collection")
        hunt_tactics = [t.strip() for t in tactic_input.split(",")]

        # Platform
        console.print("\n4. Target Platform(s) (comma-separated):")
        console.print("   Options: [cyan]Windows, Linux, macOS, Cloud, Network[/cyan]")
        platform_input = Prompt.ask("   Platforms", default=",".join(platform) if platform else "Windows")
        hunt_platforms = [p.strip() for p in platform_input.split(",")]

        # Data sources
        console.print("\n5. Data Sources (comma-separated):")
        console.print(f"   Examples: [cyan]{config.get('siem', 'SIEM')}, {config.get('edr', 'EDR')}, Network Logs[/cyan]")
        ds_input = Prompt.ask("   Data Sources", default=",".join(data_source) if data_source else f"{config.get('siem', 'SIEM')}, {config.get('edr', 'EDR')}")
        hunt_data_sources = [ds.strip() for ds in ds_input.split(",")]

    # Render template
    hunt_content = render_hunt_template(
        hunt_id=hunt_id,
        title=hunt_title,
        technique=hunt_technique,
        tactics=hunt_tactics,
        platform=hunt_platforms,
        data_sources=hunt_data_sources
    )

    # Write hunt file
    hunt_file = Path("hunts") / f"{hunt_id}.md"
    hunt_file.parent.mkdir(exist_ok=True)

    with open(hunt_file, "w") as f:
        f.write(hunt_content)

    console.print(f"\n[bold green]✅ Created {hunt_id}: {hunt_title}[/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{hunt_file}[/cyan] to flesh out your hypothesis")
    console.print("  2. Document your hunt using the LOCK pattern")
    console.print("  3. View all hunts: [cyan]athf hunt list[/cyan]")


@hunt.command()
@click.option("--status", help="Filter by status (planning, active, completed)")
@click.option("--tactic", help="Filter by MITRE tactic")
@click.option("--technique", help="Filter by MITRE technique (e.g., T1003.001)")
@click.option("--platform", help="Filter by platform")
@click.option("--format", type=click.Choice(["table", "json", "yaml"]), default="table", help="Output format")
def list(status, tactic, technique, platform, format):
    """List all hunts.

    Shows hunt catalog with optional filters.
    """
    manager = HuntManager()
    hunts = manager.list_hunts(
        status=status,
        tactic=tactic,
        technique=technique,
        platform=platform
    )

    if not hunts:
        console.print("[yellow]No hunts found.[/yellow]")
        console.print("\nCreate your first hunt: [cyan]athf hunt new[/cyan]")
        return

    if format == "json":
        import json
        console.print(json.dumps(hunts, indent=2))
        return

    if format == "yaml":
        console.print(yaml.dump(hunts, default_flow_style=False))
        return

    # Table format
    console.print(f"\n[bold]📋 Hunt Catalog ({len(hunts)} total)[/bold]\n")

    table = Table(box=box.ROUNDED)
    table.add_column("Hunt ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Technique", style="magenta")
    table.add_column("Findings", style="green")

    for hunt in hunts:
        hunt_id = hunt.get("hunt_id", "")
        title_full = hunt.get("title") or ""
        title = title_full[:30] + ("..." if len(title_full) > 30 else "")
        status_val = hunt.get("status", "")
        techniques = hunt.get("techniques", [])
        technique_str = techniques[0] if techniques else "-"

        tp = hunt.get("true_positives", 0)
        fp = hunt.get("false_positives", 0)
        findings_str = f"{tp + fp} ({tp} TP)" if (tp + fp) > 0 else "-"

        table.add_row(hunt_id, title, status_val, technique_str, findings_str)

    console.print(table)
    console.print()


@hunt.command()
@click.argument("hunt_id", required=False)
def validate(hunt_id):
    """Validate hunt structure.

    Checks YAML frontmatter, required fields, and LOCK sections.
    """
    if hunt_id:
        # Validate specific hunt
        hunt_file = Path("hunts") / f"{hunt_id}.md"
        if not hunt_file.exists():
            console.print(f"[red]Hunt not found: {hunt_id}[/red]")
            return

        _validate_single_hunt(hunt_file)
    else:
        # Validate all hunts
        console.print("\n[bold]🔍 Validating all hunts...[/bold]\n")

        hunt_files = list(Path("hunts").glob("*.md"))

        if not hunt_files:
            console.print("[yellow]No hunt files found.[/yellow]")
            return

        valid_count = 0
        invalid_count = 0

        for hunt_file in hunt_files:
            is_valid, errors = validate_hunt_file(hunt_file)

            if is_valid:
                valid_count += 1
                console.print(f"[green]✓[/green] {hunt_file.name}")
            else:
                invalid_count += 1
                console.print(f"[red]✗[/red] {hunt_file.name}")
                for error in errors:
                    console.print(f"    - {error}")

        console.print(f"\n[bold]Results:[/bold] {valid_count} valid, {invalid_count} invalid")


def _validate_single_hunt(hunt_file: Path):
    """Validate a single hunt file."""
    console.print(f"\n[bold]🔍 Validating {hunt_file.name}...[/bold]\n")

    is_valid, errors = validate_hunt_file(hunt_file)

    if is_valid:
        console.print("[green]✅ Hunt is valid![/green]")
    else:
        console.print("[red]❌ Hunt has validation errors:[/red]\n")
        for error in errors:
            console.print(f"  - {error}")


@hunt.command()
def stats():
    """Show hunt program statistics.

    Displays success rates, TP/FP ratios, and coverage metrics.
    """
    manager = HuntManager()
    stats = manager.calculate_stats()

    console.print("\n[bold cyan]📊 Hunt Program Statistics[/bold cyan]\n")

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")

    table.add_row("Total Hunts", str(stats["total_hunts"]))
    table.add_row("Completed Hunts", str(stats["completed_hunts"]))
    table.add_row("Total Findings", str(stats["total_findings"]))
    table.add_row("True Positives", str(stats["true_positives"]))
    table.add_row("False Positives", str(stats["false_positives"]))
    table.add_row("Success Rate", f"{stats['success_rate']}%")
    table.add_row("TP/FP Ratio", str(stats["tp_fp_ratio"]))

    console.print(table)
    console.print()


@hunt.command()
@click.argument("query")
def search(query):
    """Full-text search across all hunts.

    Example: athf hunt search "kerberoasting"
    """
    manager = HuntManager()
    results = manager.search_hunts(query)

    if not results:
        console.print(f"[yellow]No hunts found matching '{query}'[/yellow]")
        return

    console.print(f"\n[bold]🔍 Search results for '{query}' ({len(results)} found)[/bold]\n")

    for result in results:
        console.print(f"[cyan]{result['hunt_id']}[/cyan]: {result['title']}")
        console.print(f"  Status: {result['status']} | File: {result['file_path']}")
        console.print()


@hunt.command()
def coverage():
    """Show MITRE ATT&CK technique coverage.

    Displays which techniques you've hunted for, organized by tactic.
    """
    manager = HuntManager()
    coverage = manager.calculate_attack_coverage()

    if not coverage:
        console.print("[yellow]No hunt coverage data available.[/yellow]")
        return

    console.print("\n[bold cyan]🎯 MITRE ATT&CK Coverage[/bold cyan]\n")

    for tactic, techniques in sorted(coverage.items()):
        console.print(f"[bold]{tactic.title()}[/bold] ({len(techniques)} techniques)")
        for technique in techniques:
            console.print(f"  • {technique}")
        console.print()
