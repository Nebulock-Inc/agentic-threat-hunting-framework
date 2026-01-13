"""Hunt management commands."""

import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import click
import yaml
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from athf.core.hunt_manager import HuntManager
from athf.core.hunt_parser import validate_hunt_file
from athf.core.template_engine import render_hunt_template

console = Console()


def get_config_path() -> Path:
    """Get config file path, checking new location first, then falling back to root."""
    new_location = Path("config/.athfconfig.yaml")
    old_location = Path(".athfconfig.yaml")

    if new_location.exists():
        return new_location
    if old_location.exists():
        return old_location
    return new_location  # Default to new location for creation


HUNT_EPILOG = """
\b
Examples:
  # Interactive hunt creation (guided prompts)
  athf hunt new

  # Non-interactive with all options
  athf hunt new --technique T1003.001 --title "LSASS Dumping" --non-interactive

  # List hunts with filters
  athf hunt list --status completed --tactic credential-access

  # Search hunts for keywords
  athf hunt search "kerberoasting"

  # Get JSON output for scripting
  athf hunt list --format json

  # Show coverage gaps
  athf hunt coverage

  # Validate hunt structure
  athf hunt validate H-0042

\b
Workflow:
  1. Create hunt → athf hunt new
  2. Edit hunt file → hunts/H-XXXX.md (use LOCK pattern)
  3. Create query → queries/H-XXXX.spl
  4. Execute hunt → document findings in runs/H-XXXX_YYYY-MM-DD.md
  5. Track results → athf hunt stats

\b
Learn more: https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/blob/main/docs/CLI_REFERENCE.md
"""


@click.group(epilog=HUNT_EPILOG)
def hunt() -> None:
    """Manage threat hunting activities and track program metrics.

    \b
    Hunt commands help you:
    • Create structured hunt hypotheses
    • Track hunts across your program
    • Search past work to avoid duplication
    • Calculate success rates and coverage
    • Validate hunt file structure
    """


@hunt.command()
@click.option("--technique", help="MITRE ATT&CK technique (e.g., T1003.001)")
@click.option("--title", help="Hunt title")
@click.option("--tactic", multiple=True, help="MITRE tactics (can specify multiple)")
@click.option("--platform", multiple=True, help="Target platforms (can specify multiple)")
@click.option("--data-source", multiple=True, help="Data sources (can specify multiple)")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
@click.option("--hypothesis", help="Full hypothesis statement")
@click.option("--threat-context", help="Threat intel or context motivating the hunt")
@click.option("--actor", help="Threat actor (for ABLE framework)")
@click.option("--behavior", help="Behavior description (for ABLE framework)")
@click.option("--location", help="Location/scope (for ABLE framework)")
@click.option("--evidence", help="Evidence description (for ABLE framework)")
@click.option("--hunter", help="Hunter name", default="AI Assistant")
def new(
    technique: Optional[str],
    title: Optional[str],
    tactic: Tuple[str, ...],
    platform: Tuple[str, ...],
    data_source: Tuple[str, ...],
    non_interactive: bool,
    hypothesis: Optional[str],
    threat_context: Optional[str],
    actor: Optional[str],
    behavior: Optional[str],
    location: Optional[str],
    evidence: Optional[str],
    hunter: Optional[str],
) -> None:
    """Create a new hunt hypothesis with LOCK structure.

    \b
    Creates a hunt file with:
    • Auto-generated hunt ID (H-XXXX format)
    • YAML frontmatter with metadata
    • LOCK pattern sections (Learn, Observe, Check, Keep)
    • MITRE ATT&CK mapping

    \b
    Interactive mode (default):
      Guides you through hunt creation with prompts and suggestions.
      Example: athf hunt new

    \b
    Non-interactive mode:
      Provide all details via options for scripting.
      Example: athf hunt new --technique T1003.001 --title "LSASS Dumping" \\
               --tactic credential-access --platform Windows --non-interactive

    \b
    After creation:
      1. Edit hunts/H-XXXX.md to flesh out your hypothesis
      2. Create query in queries/H-XXXX.spl
      3. Execute hunt and document in runs/H-XXXX_YYYY-MM-DD.md
    """
    console.print("\n[bold cyan]🎯 Creating new hunt[/bold cyan]\n")

    # Load config
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
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
        hunt_technique = Prompt.ask("1. MITRE ATT&CK Technique (e.g., T1003.001)", default=technique or "")

        # Title
        hunt_title = Prompt.ask("2. Hunt Title", default=title or f"Hunt for {hunt_technique}")

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
        default_sources = ",".join(data_source) if data_source else f"{config.get('siem', 'SIEM')}, {config.get('edr', 'EDR')}"
        ds_input = Prompt.ask("   Data Sources", default=default_sources)
        hunt_data_sources = [ds.strip() for ds in ds_input.split(",")]

    # Render template
    hunt_content = render_hunt_template(
        hunt_id=hunt_id,
        title=hunt_title,
        technique=hunt_technique,
        tactics=hunt_tactics,
        platform=hunt_platforms,
        data_sources=hunt_data_sources,
        hunter=hunter or "AI Assistant",
        hypothesis=hypothesis,
        threat_context=threat_context,
        actor=actor,
        behavior=behavior,
        location=location,
        evidence=evidence,
    )

    # Write hunt file
    hunt_file = Path("hunts") / f"{hunt_id}.md"
    hunt_file.parent.mkdir(exist_ok=True)

    with open(hunt_file, "w", encoding="utf-8") as f:
        f.write(hunt_content)

    console.print(f"\n[bold green]✅ Created {hunt_id}: {hunt_title}[/bold green]")

    # Easter egg: Hunt #100 milestone
    if hunt_id.endswith("0100"):
        console.print("\n[bold yellow]✨ Milestone Achievement: Hunt #100 ✨[/bold yellow]\n")
        console.print("[italic]You've built serious hunting muscle memory.")
        console.print("This is where threat hunting programs transform from reactive to proactive.")
        console.print("Keep building that institutional knowledge.[/italic]\n")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{hunt_file}[/cyan] to flesh out your hypothesis")
    console.print("  2. Document your hunt using the LOCK pattern")
    console.print("  3. View all hunts: [cyan]athf hunt list[/cyan]")


@hunt.command(name="list")
@click.option("--status", help="Filter by status (planning, active, completed)")
@click.option("--tactic", help="Filter by MITRE tactic")
@click.option("--technique", help="Filter by MITRE technique (e.g., T1003.001)")
@click.option("--platform", help="Filter by platform")
@click.option("--output", type=click.Choice(["table", "json", "yaml"]), default="table", help="Output format")
def list_hunts(status: str, tactic: str, technique: str, platform: str, output: str) -> None:
    """List all hunts with filtering and formatting options.

    \b
    Displays hunt catalog with:
    • Hunt ID and title
    • Current status
    • MITRE ATT&CK techniques
    • True/False positive counts

    \b
    Examples:
      # List all hunts
      athf hunt list

      # Show only completed hunts
      athf hunt list --status completed

      # Filter by tactic
      athf hunt list --tactic credential-access

      # Combine filters
      athf hunt list --tactic persistence --platform Linux

      # JSON output for scripting
      athf hunt list --output json

    \b
    Output formats:
      • table (default): Human-readable table with colors
      • json: Machine-readable for scripts and automation
      • yaml: Structured format for configuration management

    Note: Use --output instead of --format for specifying output format.
    """
    manager = HuntManager()
    hunts = manager.list_hunts(status=status, tactic=tactic, technique=technique, platform=platform)

    if not hunts:
        console.print("[yellow]No hunts found.[/yellow]")
        console.print("\nCreate your first hunt: [cyan]athf hunt new[/cyan]")
        return

    if output == "json":
        import json

        console.print(json.dumps(hunts, indent=2))
        return

    if output == "yaml":
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
def validate(hunt_id: str) -> None:
    """Validate hunt file structure and metadata.

    \b
    Validates:
    • YAML frontmatter syntax
    • Required metadata fields
    • LOCK section structure
    • MITRE ATT&CK technique format
    • File naming conventions

    \b
    Examples:
      # Validate specific hunt
      athf hunt validate H-0042

      # Validate all hunts
      athf hunt validate

    \b
    Use this to:
    • Catch formatting errors before committing
    • Ensure consistency across hunt documentation
    • Verify hunt files are AI-assistant readable
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

        hunts_dir = Path("hunts")
        if not hunts_dir.exists():
            console.print("[yellow]No hunts directory found.[/yellow]")
            return

        hunt_files = list(hunts_dir.glob("*.md"))

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


def _validate_single_hunt(hunt_file: Path) -> None:
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
def stats() -> None:
    """Show hunt program statistics and success metrics.

    \b
    Calculates and displays:
    • Total hunts vs completed hunts
    • Total findings (True Positives + False Positives)
    • Success rate (hunts with TPs / completed hunts)
    • TP/FP ratio (quality of detections)
    • Hunt velocity metrics

    \b
    Example:
      athf hunt stats

    \b
    Use this to:
    • Track hunting program effectiveness over time
    • Identify areas for improvement
    • Demonstrate hunting value to leadership
    • Set quarterly goals and OKRs
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

    # Easter egg: First True Positive milestone
    if stats["true_positives"] == 1 and stats["completed_hunts"] > 0:
        console.print("[bold yellow]🎯 First True Positive Detected![/bold yellow]\n")
        console.print(
            "[italic]Every expert threat hunter started here. This confirms your hypothesis was testable, your data was sufficient, and your analytical instincts were sound. Document what worked.[/italic]\n"
        )


@hunt.command()
@click.argument("query")
def search(query: str) -> None:
    """Full-text search across all hunt files.

    \b
    Searches through:
    • Hunt titles and descriptions
    • YAML frontmatter metadata
    • LOCK section content
    • Lessons learned
    • Query comments

    \b
    Examples:
      # Search for specific TTP
      athf hunt search "kerberoasting"

      # Search for technology
      athf hunt search "powershell"

      # Search by hunt ID
      athf hunt search "H-0042"

      # Search for data source
      athf hunt search "sysmon"

    \b
    Use this to:
    • Avoid duplicate hunts
    • Find related past work
    • Reference lessons learned
    • Check if a TTP has been hunted before
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


def _render_progress_bar(covered: int, total: int, width: int = 20) -> str:
    """Render a visual progress bar with filled and empty blocks.

    Args:
        covered: Number of covered techniques
        total: Total number of techniques
        width: Width of the progress bar in characters

    Returns:
        ASCII progress bar string using simple characters
    """
    if total == 0:
        return "·" * width

    # Cap percentage at 100% for visual display
    percentage = min(covered / total, 1.0)
    filled = int(percentage * width)
    empty = width - filled

    # Use simple characters that render reliably
    filled_char = "■"
    empty_char = "·"

    return filled_char * filled + empty_char * empty


@hunt.command()
@click.option("--detailed", is_flag=True, help="Show detailed technique coverage with hunt references")
def coverage(detailed: bool) -> None:
    """Show MITRE ATT&CK technique coverage across hunts.

    \b
    Analyzes and displays:
    • Hunt count per tactic across all 14 ATT&CK tactics
    • Technique count per tactic (with caveats - see note below)
    • Overall unique technique coverage across all hunts
    • Detailed technique-to-hunt mapping (with --detailed)

    \b
    Examples:
      # Show coverage overview
      athf hunt coverage

      # Show detailed technique mapping
      athf hunt coverage --detailed

    \b
    Note on technique counts:
      Per-tactic technique counts may include duplicates if hunts cover
      multiple tactics. The overall unique technique count (bottom) is accurate.

    \b
    Use this to:
    • Identify blind spots in your hunting program
    • Prioritize future hunt topics
    • Demonstrate coverage to stakeholders
    • Align hunting with threat intelligence priorities
    • Balance hunt portfolio across tactics

    \b
    Pro tip:
      Focus on tactics with no coverage that align with your threat model.
      Use --detailed to see which specific techniques each hunt covers.
    """
    from athf.core.attack_matrix import ATTACK_TACTICS, get_sorted_tactics

    manager = HuntManager()
    coverage = manager.calculate_attack_coverage()

    if not coverage or not coverage.get("by_tactic"):
        console.print("[yellow]No hunt coverage data available.[/yellow]")
        return

    summary = coverage["summary"]
    by_tactic = coverage["by_tactic"]

    # Display title
    console.print("\n[bold]MITRE ATT&CK Coverage[/bold]")
    console.print("─" * 60 + "\n")

    # Display all tactics in ATT&CK order with hunt counts
    for tactic_key in get_sorted_tactics():
        data = by_tactic.get(tactic_key, {})
        tactic_name = ATTACK_TACTICS[tactic_key]["name"]

        hunt_count = data.get("hunt_count", 0)
        techniques_covered = data.get("techniques_covered", 0)

        # Format: "Tactic Name          2 hunts, 7 techniques"
        if hunt_count > 0:
            console.print(f"{tactic_name:<24} {hunt_count} hunts, {techniques_covered} techniques")
        else:
            console.print(f"{tactic_name:<24} [dim]no coverage[/dim]")

    # Display overall coverage
    console.print(
        f"\n[bold]Overall: {summary['unique_techniques']}/{summary['total_techniques']} techniques ({summary['overall_coverage_pct']:.0f}%)[/bold]\n"
    )

    # Display detailed technique coverage if requested
    if detailed:
        console.print("\n[bold cyan]🔍 Detailed Technique Coverage[/bold cyan]\n")

        for tactic_key in get_sorted_tactics():
            data = by_tactic.get(tactic_key, {})
            if data.get("hunt_count", 0) == 0:
                continue  # Skip tactics with no hunts in detailed view

            tactic_name = ATTACK_TACTICS[tactic_key]["name"]
            console.print(
                f"\n[bold]{tactic_name}[/bold] ({data['hunt_count']} hunts, {len(data['techniques'])} unique techniques)"
            )

            # Show techniques with hunt references
            for technique, hunt_ids in sorted(data["techniques"].items()):
                hunt_refs = ", ".join(sorted(set(hunt_ids)))  # Remove duplicates and sort
                console.print(f"  • [yellow]{technique}[/yellow] - {hunt_refs}")

    console.print()


@hunt.command(hidden=True)
def coffee() -> None:
    """Check your caffeine levels (critical for threat hunting)."""
    now = datetime.now()
    hour = now.hour

    # Random caffeine level
    caffeine_level = random.randint(0, 100)

    # Time-aware status
    if 3 <= hour < 5:
        status = "Incident Response Mode"
        time_message = "Running on pure incident response adrenaline."
    elif 0 <= hour < 6:
        status = "Night Hunter"
        time_message = "The real threat hunting happens in the dark."
    elif 6 <= hour < 9:
        status = "Early Bird"
        time_message = "Morning hunts catch the adversaries."
    elif 18 <= hour < 24:
        status = "Evening Detective"
        time_message = "Picking up where the day shift left off."
    else:
        status = "Operational"
        time_message = "Sustainable hunting pace detected."

    # Caffeine-level specific recommendations
    if caffeine_level < 30:
        recommendation = "Consider refueling. Even the best hunters need breaks."
    elif caffeine_level > 90:
        recommendation = "Peak operational capacity. Time to chase that hypothesis."
    else:
        recommendation = time_message

    console.print("\n[bold]☕ Threat Hunter Caffeine Check[/bold]\n")
    console.print(f"Current Level: [cyan]{caffeine_level}%[/cyan]")
    console.print(f"Status: [yellow]{status}[/yellow]")
    console.print(f"Recommendation: [italic]{recommendation}[/italic]\n")

    # Random wisdom quote
    wisdom_quotes = [
        "The best hunts are fueled by curiosity, not just caffeine.",
        "Caffeine enables the hunt. Rigor validates the findings.",
        "Stay sharp, stay curious, stay caffeinated.",
        "Coffee: because threat actors don't work business hours.",
        "Fuel your hypotheses with coffee. Validate them with data.",
    ]
    console.print(f"[dim italic]{random.choice(wisdom_quotes)}[/dim italic]\n")
