"""Hunt management commands."""

import json
import random
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from athf.core.attack_matrix import get_technique
from athf.core.hunt_manager import HuntManager
from athf.core.hunt_parser import validate_hunt_file
from athf.core.template_engine import render_hunt_template
from athf.utils.validation import validate_hunt_id, validate_research_id

console = Console()


def _default_tactics_for_technique(technique_id: str) -> List[str]:
    """Best-effort tactic auto-derivation from an ATT&CK technique ID.

    Looks up the technique in the active ATT&CK data provider and returns
    its tactic shortnames. Returns an empty list if the technique isn't
    found or the active provider is the hardcoded fallback (which doesn't
    carry per-technique metadata) — callers should treat that as "no
    derivation available" and fall back to their own default.
    """
    if not technique_id:
        return []
    info = get_technique(technique_id)
    if info:
        return list(info.get("tactic_shortnames") or [])
    return []


def get_hunt_directory(is_test: bool = False) -> Path:
    """Calculate hunt directory based on current date.

    Args:
        is_test: If True, creates in test/ directory, otherwise production/

    Returns:
        Path to hunt directory (hunts/{environment}/{YYYY}/{QX}/)
    """
    now = datetime.now()
    year = now.year
    quarter = f"Q{(now.month - 1) // 3 + 1}"

    environment = "test" if is_test else "production"

    return Path("hunts") / environment / str(year) / quarter


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

  # Link research document to hunt
  athf hunt new --research R-0001 --title "Hunt Title" --non-interactive

  # List hunts with filters
  athf hunt list --status completed --tactic credential-access

  # Search hunts for keywords
  athf hunt search "kerberoasting"

  # Get JSON output for scripting
  athf hunt list --format json

  # Show coverage gaps
  athf hunt coverage

  # Filter coverage by tactic
  athf hunt coverage --tactic credential-access

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
@click.option("--test", is_flag=True, help="Create as test hunt (hunts/test/...) instead of production")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
@click.option("--hypothesis", help="Full hypothesis statement")
@click.option("--threat-context", help="Threat intel or context motivating the hunt")
@click.option("--actor", help="Threat actor (for ABLE framework)")
@click.option("--behavior", help="Behavior description (for ABLE framework)")
@click.option("--location", help="Location/scope (for ABLE framework)")
@click.option("--evidence", help="Evidence description (for ABLE framework)")
@click.option("--hunter", help="Hunter name", default="AI Assistant")
@click.option("--research", help="Research document ID (e.g., R-0001) this hunt is based on")
@click.option(
    "--hypothesis-duration",
    type=float,
    default=None,
    help="Hypothesis generation duration in minutes (from athf agent run output)",
)
def new(
    technique: Optional[str],
    title: Optional[str],
    tactic: Tuple[str, ...],
    platform: Tuple[str, ...],
    data_source: Tuple[str, ...],
    test: bool,
    non_interactive: bool,
    hypothesis: Optional[str],
    threat_context: Optional[str],
    actor: Optional[str],
    behavior: Optional[str],
    location: Optional[str],
    evidence: Optional[str],
    hunter: Optional[str],
    research: Optional[str],
    hypothesis_duration: Optional[float],
) -> None:
    """Create a new hunt hypothesis with LOCK structure.

    \b
    Creates a hunt file with:
    • Auto-generated hunt ID (H-XXXX format)
    • YAML frontmatter with metadata
    • LOCK pattern sections (Learn, Observe, Check, Keep)
    • MITRE ATT&CK mapping
    • Optional link to research document

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
    With research document:
      Link a pre-hunt research document to the hunt.
      Example: athf hunt new --research R-0001 --title "Hunt Title" --non-interactive

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

    # Validate research document if provided
    if research:
        # Validate research ID format
        if not validate_research_id(research):
            console.print(f"[red]Error: Invalid research ID format: {research}[/red]")
            console.print("[yellow]Expected format: R-0001[/yellow]")
            return

        research_file = Path("research") / f"{research}.md"

        # Validate path is within research directory (Python 3.8 compatible)
        try:
            research_file.resolve().relative_to(Path("research").resolve())
        except (ValueError, OSError):
            console.print("[red]Error: Invalid research path[/red]")
            return

        if not research_file.exists():
            console.print(f"[yellow]Warning: Research document {research} not found at {research_file}[/yellow]")
            console.print("[yellow]Hunt will still be created, but research link may be broken.[/yellow]\n")

    # Gather hunt details
    if non_interactive:
        if not title:
            console.print("[red]Error: --title required in non-interactive mode[/red]")
            return
        hunt_title = title
        hunt_technique = technique or "T1005"
        if tactic:
            hunt_tactics = list(tactic)
        else:
            derived = _default_tactics_for_technique(hunt_technique)
            hunt_tactics = derived if derived else ["collection"]
        hunt_platforms = list(platform) if platform else ["Windows"]
        hunt_data_sources = list(data_source) if data_source else ["SIEM", "EDR"]
    else:
        # Interactive prompts
        console.print("\n[bold]🔍 Let's build your hypothesis:[/bold]")

        # Technique
        hunt_technique = Prompt.ask("1. MITRE ATT&CK Technique (e.g., T1003.001)", default=technique or "")

        # Title
        hunt_title = Prompt.ask("2. Hunt Title", default=title or f"Hunt for {hunt_technique}")

        # Tactics — auto-derive from technique when possible, otherwise prompt
        # with a generic default the user is likely to override anyway.
        console.print("\n3. Primary Tactic(s) (comma-separated):")
        console.print("   Common: [cyan]persistence, credential-access, collection, lateral-movement[/cyan]")
        if tactic:
            tactic_default = ",".join(tactic)
        else:
            derived = _default_tactics_for_technique(hunt_technique)
            tactic_default = ",".join(derived) if derived else "collection"
        tactic_input = Prompt.ask("   Tactics", default=tactic_default)
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
        spawned_from=research,
        hypothesis_duration_minutes=hypothesis_duration,
    )

    # Write hunt file using hierarchical directory structure
    hunt_dir = get_hunt_directory(is_test=test)
    hunt_dir.mkdir(parents=True, exist_ok=True)
    hunt_file = hunt_dir / f"{hunt_id}.md"

    # Validate path is within hunts directory (Python 3.8 compatible)
    try:
        hunt_file.resolve().relative_to(Path("hunts").resolve())
    except (ValueError, OSError):
        console.print("[red]Error: Invalid hunt file path[/red]")
        return

    with open(hunt_file, "w", encoding="utf-8") as f:
        f.write(hunt_content)

    console.print(f"\n[bold green]✅ Created {hunt_id}: {hunt_title}[/bold green]")

    # Link hunt back to research document (issue #14)
    if research:
        try:
            from athf.core.research_manager import ResearchManager

            research_mgr = ResearchManager()
            if research_mgr.link_hunt_to_research(research, hunt_id):
                console.print(f"[dim]Linked {hunt_id} to research {research}[/dim]")
            else:
                console.print(f"[yellow]Warning: Could not link {hunt_id} to research {research}[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not update research document: {e}[/yellow]")

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
@click.option("--directory", type=click.Choice(["test", "production"]), help="Filter by environment directory")
@click.option("--output", type=click.Choice(["table", "json", "yaml"]), default="table", help="Output format")
def list_hunts(status: str, tactic: str, technique: str, platform: str, directory: str, output: str) -> None:
    """List all hunts with filtering and formatting options.

    \b
    Displays hunt catalog with:
    • Hunt ID and title
    • Current status
    • Environment directory (test/production)
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

      # Filter by environment directory
      athf hunt list --directory test

      # Combine filters
      athf hunt list --tactic persistence --platform Linux --directory production

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
    hunts = manager.list_hunts(status=status, tactic=tactic, technique=technique, platform=platform, directory=directory)

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
    table.add_column("Title", style="white", no_wrap=True, max_width=30)
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Status", style="yellow", no_wrap=True)
    table.add_column("Env", style="blue", no_wrap=True)
    table.add_column("Technique", style="magenta", no_wrap=True)
    table.add_column("Findings", style="green", no_wrap=True)

    for hunt in hunts:
        hunt_id = hunt.get("hunt_id", "")
        title_full = hunt.get("title") or ""
        title = title_full[:30] + ("..." if len(title_full) > 30 else "")
        date_val = hunt.get("date") or "-"
        date_str = str(date_val) if date_val != "-" else "-"
        status_val = hunt.get("status", "")
        environment = hunt.get("environment", "-")
        env_display = environment if environment else "-"
        techniques = hunt.get("techniques", [])
        technique_str = techniques[0] if techniques else "-"

        tp = hunt.get("true_positives", 0)
        fp = hunt.get("false_positives", 0)
        findings_str = f"{tp + fp} ({tp} TP)" if (tp + fp) > 0 else "-"

        table.add_row(hunt_id, title, date_str, status_val, env_display, technique_str, findings_str)

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
        # Validate hunt ID format
        if not validate_hunt_id(hunt_id):
            console.print(f"[red]Error: Invalid hunt ID format: {hunt_id}[/red]")
            console.print("[yellow]Expected format: H-0001[/yellow]")
            return

        # Validate specific hunt - search recursively for backward compatibility
        hunts_dir = Path("hunts")
        hunt_file = hunts_dir / f"{hunt_id}.md"

        # If not found in flat structure, search recursively
        if not hunt_file.exists():
            matching_files = list(hunts_dir.rglob(f"{hunt_id}.md"))
            if not matching_files:
                console.print(f"[red]Hunt not found: {hunt_id}[/red]")
                return
            hunt_file = matching_files[0]  # Use first match

        # Validate path is within hunts directory
        try:
            hunt_file.resolve().relative_to(hunts_dir.resolve())
        except (ValueError, OSError):
            console.print("[red]Error: Invalid hunt file path[/red]")
            return

        _validate_single_hunt(hunt_file)
    else:
        # Validate all hunts
        console.print("\n[bold]🔍 Validating all hunts...[/bold]\n")

        hunts_dir = Path("hunts")
        if not hunts_dir.exists():
            console.print("[yellow]No hunts directory found.[/yellow]")
            return

        hunt_files = HuntManager(hunts_dir).find_all_hunt_files()

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
@click.option("--directory", type=click.Choice(["test", "production"]), help="Filter by environment directory")
def search(query: str, directory: str) -> None:
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

      # Filter by environment directory
      athf hunt search "credential" --directory test

    \b
    Use this to:
    • Avoid duplicate hunts
    • Find related past work
    • Reference lessons learned
    • Check if a TTP has been hunted before
    """
    manager = HuntManager()
    results = manager.search_hunts(query, directory=directory)

    if not results:
        console.print(f"[yellow]No hunts found matching '{query}'[/yellow]")
        return

    console.print(f"\n[bold]🔍 Search results for '{query}' ({len(results)} found)[/bold]\n")

    for result in results:
        environment = result.get("environment", "-")
        env_display = f" | Env: {environment}" if environment else ""
        console.print(f"[cyan]{result['hunt_id']}[/cyan]: {result['title']}")
        console.print(f"  Status: {result['status']}{env_display} | File: {result['file_path']}")
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
@click.option("--tactic", help="Filter by specific tactic (or 'all' for all tactics)")
@click.option("--detailed", is_flag=True, help="Show detailed technique coverage with hunt references")
def coverage(tactic: Optional[str], detailed: bool) -> None:
    """Show MITRE ATT&CK technique coverage across hunts.

    \b
    Analyzes and displays:
    • Hunt count per tactic across all 14 ATT&CK tactics
    • Technique count per tactic (with caveats - see note below)
    • Overall unique technique coverage across all hunts
    • Detailed technique-to-hunt mapping (with --detailed)

    \b
    Examples:
      # Show coverage overview for all tactics
      athf hunt coverage

      # Show all tactics explicitly
      athf hunt coverage --tactic all

      # Show coverage for a specific tactic
      athf hunt coverage --tactic credential-access

      # Show detailed technique mapping for execution tactic
      athf hunt coverage --tactic execution --detailed

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

    # Determine which tactics to display
    tactics_to_display = []
    if tactic and tactic.lower() != "all":
        # Validate tactic exists
        if tactic not in ATTACK_TACTICS:
            console.print(f"[red]Error: Unknown tactic '{tactic}'[/red]")
            console.print("\n[bold]Valid tactics:[/bold]")
            for tactic_key in get_sorted_tactics():
                console.print(f"  • {tactic_key}")
            return
        tactics_to_display = [tactic]
    else:
        # Show all tactics
        tactics_to_display = get_sorted_tactics()

    # Display title
    if tactic and tactic.lower() != "all":
        tactic_display_name = ATTACK_TACTICS[tactic]["name"]
        console.print(f"\n[bold]MITRE ATT&CK Coverage - {tactic_display_name}[/bold]")
    else:
        console.print("\n[bold]MITRE ATT&CK Coverage[/bold]")
    console.print("─" * 60 + "\n")

    # Display selected tactics in ATT&CK order with hunt counts
    for tactic_key in tactics_to_display:
        data = by_tactic.get(tactic_key, {})
        tactic_name = ATTACK_TACTICS[tactic_key]["name"]

        hunt_count = data.get("hunt_count", 0)
        techniques_covered = data.get("techniques_covered", 0)

        # Format: "Tactic Name          2 hunts, 7 techniques"
        if hunt_count > 0:
            console.print(f"{tactic_name:<24} {hunt_count} hunts, {techniques_covered} techniques")
        else:
            console.print(f"{tactic_name:<24} [dim]no coverage[/dim]")

    # Display overall coverage only if showing all tactics
    if not tactic or tactic.lower() == "all":
        console.print(
            f"\n[bold]Overall: {summary['unique_techniques']}/{summary['total_techniques']} techniques ({summary['overall_coverage_pct']:.0f}%)[/bold]\n"
        )
    else:
        console.print()

    # Display detailed technique coverage if requested
    if detailed:
        console.print("\n[bold cyan]🔍 Detailed Technique Coverage[/bold cyan]\n")

        for tactic_key in tactics_to_display:
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


@hunt.command(name="promote")
@click.argument("hunt_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def promote_hunt(hunt_id: str, yes: bool) -> None:
    """Promote a hunt from test to production.

    \b
    Moves a hunt file from hunts/test/... to hunts/production/...
    while preserving its hunt ID and updating the file path.

    \b
    Examples:
      # Promote a test hunt to production
      athf hunt promote H-0042

      # Skip confirmation
      athf hunt promote H-0042 --yes

    \b
    After promotion:
      • Hunt file moved to production directory
      • Original test file removed
      • Hunt ID preserved (no renumbering)
    """
    import shutil

    if not validate_hunt_id(hunt_id):
        console.print(f"[red]Error: Invalid hunt ID format: {hunt_id}[/red]")
        console.print("[yellow]Expected format: H-0001[/yellow]")
        return

    manager = HuntManager()
    hunt_file = manager.find_hunt_file(hunt_id)

    if not hunt_file:
        console.print(f"[red]Error: Hunt not found: {hunt_id}[/red]")
        return

    # Check hunt is in test directory
    if "test" not in hunt_file.parts:
        if "production" in hunt_file.parts:
            console.print(f"[yellow]{hunt_id} is already in production: {hunt_file}[/yellow]")
        else:
            console.print(f"[yellow]{hunt_id} is not in a test directory: {hunt_file}[/yellow]")
        return

    # Calculate production destination
    prod_dir = get_hunt_directory(is_test=False)
    prod_file = prod_dir / f"{hunt_id}.md"

    console.print(f"\n[bold cyan]🔄 Promoting {hunt_id} to production[/bold cyan]\n")
    console.print(f"  [dim]From:[/dim] {hunt_file}")
    console.print(f"  [dim]To:  [/dim] {prod_file}\n")

    if prod_file.exists():
        console.print(f"[red]Error: Destination already exists: {prod_file}[/red]")
        return

    if not yes:
        confirm = Prompt.ask("Proceed with promotion?", choices=["y", "n"], default="y")
        if confirm != "y":
            console.print("[dim]Promotion cancelled.[/dim]")
            return

    # Move the file
    prod_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(hunt_file), str(prod_file))

    console.print(f"[bold green]✅ Promoted {hunt_id} to production[/bold green]")
    console.print(f"  [dim]{prod_file}[/dim]\n")


def _load_linked_research(research_id: str, research_dir: Path) -> Optional[Dict[str, Any]]:
    """Load a linked research document by ID.

    Args:
        research_id: Research ID (e.g., R-0008)
        research_dir: Path to research directory

    Returns:
        Dict with research frontmatter and sections, or None if not found
    """
    research_file = research_dir / f"{research_id}.md"
    if not research_file.exists():
        return None

    try:
        from athf.core.research_manager import parse_research_file

        research_data = parse_research_file(research_file)
        frontmatter = research_data.get("frontmatter", {})

        return {
            "research_id": frontmatter.get("research_id"),
            "topic": frontmatter.get("topic"),
            "mitre_techniques": frontmatter.get("mitre_techniques", []),
            "status": frontmatter.get("status"),
            "depth": frontmatter.get("depth"),
            "duration_minutes": frontmatter.get("duration_minutes"),
            "data_source_availability": frontmatter.get("data_source_availability", {}),
            "estimated_hunt_complexity": frontmatter.get("estimated_hunt_complexity"),
            "created_date": frontmatter.get("created_date"),
            "sections": research_data.get("sections", {}),
            "file_path": str(research_file),
        }
    except Exception:
        return None


def _json_serializer(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def _load_sessions_for_hunt(hunt_id: str, sessions_dir: Path) -> List[Dict[str, Any]]:
    """Load all session data for a hunt from the sessions directory.

    Reads session.yaml, decisions.yaml, findings.yaml, and queries.yaml
    from each matching session directory.

    Args:
        hunt_id: Hunt ID to find sessions for (e.g., H-0027)
        sessions_dir: Path to sessions directory

    Returns:
        List of session dicts with all available data
    """
    sessions: List[Dict[str, Any]] = []

    if not sessions_dir.exists():
        return sessions

    for session_dir in sorted(sessions_dir.iterdir()):
        if not session_dir.is_dir() or session_dir.name.startswith("."):
            continue

        session_file = session_dir / "session.yaml"
        if not session_file.exists():
            continue

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = yaml.safe_load(f) or {}

            if session_data.get("hunt_id") != hunt_id:
                continue

            # Load optional YAML files
            for yaml_name in ("decisions", "findings", "queries"):
                yaml_file = session_dir / f"{yaml_name}.yaml"
                if yaml_file.exists():
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        extra_data = yaml.safe_load(f) or {}
                    session_data[yaml_name] = extra_data.get(yaml_name, [])

            sessions.append(session_data)
        except Exception:
            continue

    return sessions


@hunt.command(name="export")
@click.argument("hunt_id", required=False)
@click.option("--all", "export_all", is_flag=True, help="Export all hunts")
@click.option("--output", "output_file", type=click.Path(), help="Write to file instead of stdout")
@click.option("--include-content", is_flag=True, help="Include raw markdown content in output")
@click.option("--no-sessions", is_flag=True, help="Exclude session data from export")
@click.option("--status", help="Filter by status when using --all (planning, active, completed)")
def export_hunt(
    hunt_id: Optional[str],
    export_all: bool,
    output_file: Optional[str],
    include_content: bool,
    no_sessions: bool,
    status: Optional[str],
) -> None:
    """Export hunt data as structured JSON.

    \b
    Exports full hunt data including frontmatter, LOCK sections,
    and associated session data (decisions, findings, queries).

    \b
    Examples:
      # Export a single hunt
      athf hunt export H-0027

      # Export all hunts
      athf hunt export --all

      # Export to file
      athf hunt export H-0027 --output hunt-0027.json

      # Export with raw markdown content
      athf hunt export H-0027 --include-content

      # Export without session data
      athf hunt export H-0027 --no-sessions

      # Export all completed hunts
      athf hunt export --all --status completed

    \b
    Use this to:
      • Feed hunt data into external tools and dashboards
      • Create machine-readable hunt reports
      • Power graph databases and analytics pipelines
      • Archive hunts in structured format
    """
    if not hunt_id and not export_all:
        console.print("[red]Error: Provide a hunt ID or use --all[/red]")
        console.print("[dim]Example: athf hunt export H-0027[/dim]")
        console.print("[dim]         athf hunt export --all[/dim]")
        raise click.Abort()

    manager = HuntManager()
    sessions_dir = Path("sessions")

    if export_all:
        hunts = manager.list_hunts(status=status)
        if not hunts:
            console.print("[yellow]No hunts found.[/yellow]")
            return

        export_data: List[Dict[str, Any]] = []
        for hunt_summary in hunts:
            hid = hunt_summary.get("hunt_id")
            if not hid:
                continue
            hunt_data = manager.get_hunt(hid)
            if not hunt_data:
                continue
            export_data.append(_build_export_dict(hunt_data, sessions_dir, include_content, no_sessions))

        result = json.dumps(export_data, indent=2, default=_json_serializer)

    else:
        if not validate_hunt_id(hunt_id):  # type: ignore[arg-type]
            console.print(f"[red]Error: Invalid hunt ID format: {hunt_id}[/red]")
            console.print("[yellow]Expected format: H-0001[/yellow]")
            raise click.Abort()

        hunt_data = manager.get_hunt(hunt_id)  # type: ignore[arg-type]
        if not hunt_data:
            console.print(f"[red]Error: Hunt not found: {hunt_id}[/red]")
            raise click.Abort()

        export_dict = _build_export_dict(hunt_data, sessions_dir, include_content, no_sessions)
        result = json.dumps(export_dict, indent=2, default=_json_serializer)

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
            f.write("\n")
        console.print(f"[green]Exported to {output_path}[/green]")
    else:
        click.echo(result)


def _build_export_dict(
    hunt_data: Dict[str, Any],
    sessions_dir: Path,
    include_content: bool,
    no_sessions: bool,
) -> Dict[str, Any]:
    """Build the export dictionary for a single hunt.

    Args:
        hunt_data: Parsed hunt data from HuntParser
        sessions_dir: Path to sessions directory
        include_content: Whether to include raw markdown
        no_sessions: Whether to exclude sessions

    Returns:
        Dict ready for JSON serialization
    """
    frontmatter = hunt_data.get("frontmatter", {})
    hunt_id = frontmatter.get("hunt_id", "")

    export: Dict[str, Any] = {
        "hunt_id": hunt_id,
        "title": frontmatter.get("title"),
        "status": frontmatter.get("status"),
        "date": frontmatter.get("date"),
        "hunter": frontmatter.get("hunter"),
        "platform": frontmatter.get("platform", []),
        "tactics": frontmatter.get("tactics", []),
        "techniques": frontmatter.get("techniques", []),
        "data_sources": frontmatter.get("data_sources", []),
        "related_hunts": frontmatter.get("related_hunts", []),
        "spawned_from": frontmatter.get("spawned_from"),
        "findings_count": frontmatter.get("findings_count", 0),
        "true_positives": frontmatter.get("true_positives", 0),
        "false_positives": frontmatter.get("false_positives", 0),
        "events_scanned": frontmatter.get("events_scanned"),
        "tags": frontmatter.get("tags", []),
        "lock_sections": hunt_data.get("lock_sections", {}),
        "file_path": hunt_data.get("file_path"),
    }

    if include_content:
        export["content"] = hunt_data.get("content", "")

    # Load linked research document
    spawned_from = frontmatter.get("spawned_from")
    if spawned_from:
        research_dir = Path("research")
        research = _load_linked_research(spawned_from, research_dir)
        if research:
            export["research"] = research

    if not no_sessions:
        export["sessions"] = _load_sessions_for_hunt(hunt_id, sessions_dir)

    return export
