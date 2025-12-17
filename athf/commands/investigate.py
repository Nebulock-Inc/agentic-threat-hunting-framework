"""Investigation management commands."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import click
import yaml
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from athf.core.investigation_parser import get_all_investigations, get_next_investigation_id, validate_investigation_file

console = Console()


INVESTIGATION_EPILOG = """
\b
Examples:
  # Interactive investigation creation
  athf investigate new

  # Non-interactive with all options
  athf investigate new --title "Alert Triage - PowerShell" --type finding --non-interactive

  # List investigations with filters
  athf investigate list --type finding

  # Search investigations for keywords
  athf investigate search "PowerShell"

  # Validate investigation structure
  athf investigate validate I-0042

\b
Workflow:
  1. Create investigation → athf investigate new
  2. Edit investigation file → investigations/I-XXXX.md
  3. Document findings and analysis
  4. Optionally promote to formal hunt → athf investigate promote I-XXXX

\b
Learn more: See investigations/README.md for full documentation
"""


@click.group(epilog=INVESTIGATION_EPILOG)
def investigate() -> None:
    """Manage security investigations and exploratory work.

    \b
    Investigation commands help you:
    • Triage alerts and findings
    • Baseline new data sources
    • Explore and sandbox queries
    • Document ad-hoc analysis work
    • Promote investigations to formal hunts

    \b
    Note: Investigations are NOT tracked in metrics.
    They won't contribute to hunt success rates or cost tracking.
    """


@investigate.command()
@click.option("--title", help="Investigation title")
@click.option(
    "--type",
    "investigation_type",
    type=click.Choice(["finding", "baseline", "exploratory", "other"]),
    help="Investigation type",
)
@click.option("--tags", help="Comma-separated tags (e.g., alert-triage,powershell)")
@click.option("--data-source", multiple=True, help="Data sources (can specify multiple)")
@click.option("--related-hunt", multiple=True, help="Related hunt IDs (e.g., H-0013)")
@click.option("--investigator", help="Investigator name", default="ATHF")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
def new(
    title: Optional[str],
    investigation_type: Optional[str],
    tags: Optional[str],
    data_source: Tuple[str, ...],
    related_hunt: Tuple[str, ...],
    investigator: Optional[str],
    non_interactive: bool,
) -> None:
    """Create a new investigation file.

    \b
    Creates an investigation file with:
    • Auto-generated investigation ID (I-XXXX format)
    • Minimal YAML frontmatter
    • Optional LOCK structure for flexible documentation

    \b
    Interactive mode (default):
      Guides you through investigation creation with prompts.
      Example: athf investigate new

    \b
    Non-interactive mode:
      Provide all details via options for scripting.
      Example: athf investigate new --title "Alert Triage" \\
               --type finding --tags alert-triage --non-interactive

    \b
    After creation:
      1. Edit investigations/I-XXXX.md to document your investigation
      2. Use LOCK pattern sections (optional/flexible)
      3. Optionally promote to hunt: athf investigate promote I-XXXX
    """
    console.print("\n[bold cyan]🔍 Creating new investigation[/bold cyan]\n")

    # Get investigations directory
    investigations_dir = Path("investigations")
    investigations_dir.mkdir(exist_ok=True)

    # Get next investigation ID
    investigation_id = get_next_investigation_id(investigations_dir)
    console.print(f"[bold]Investigation ID:[/bold] {investigation_id}")

    # Gather investigation details
    if non_interactive:
        if not title:
            console.print("[red]Error: --title required in non-interactive mode[/red]")
            return
        inv_title = title
        inv_type = investigation_type or "exploratory"
        inv_tags = [t.strip() for t in tags.split(",")] if tags else []
        inv_data_sources = list(data_source) if data_source else []
        inv_related_hunts = list(related_hunt) if related_hunt else []
    else:
        # Interactive prompts
        console.print("\n[bold]📋 Let's set up your investigation:[/bold]")

        # Title
        inv_title = Prompt.ask("1. Investigation Title", default=title or "")

        # Type
        console.print("\n2. Investigation Type:")
        console.print("   [cyan]finding[/cyan]     - Alert triage or specific finding investigation")
        console.print("   [cyan]baseline[/cyan]    - Data source baselining or normal behavior analysis")
        console.print("   [cyan]exploratory[/cyan] - Ad-hoc exploration or query sandbox")
        console.print("   [cyan]other[/cyan]       - Miscellaneous investigation")
        inv_type = Prompt.ask(
            "   Type",
            default=investigation_type or "exploratory",
            choices=["finding", "baseline", "exploratory", "other"],
        )

        # Tags
        console.print("\n3. Tags (comma-separated, optional):")
        console.print("   Examples: [cyan]alert-triage, powershell, customer-x[/cyan]")
        tags_input = Prompt.ask("   Tags", default=tags or "")
        inv_tags = [t.strip() for t in tags_input.split(",")] if tags_input else []

        # Data sources
        console.print("\n4. Data Sources (comma-separated, optional):")
        console.print("   Examples: [cyan]ClickHouse, EDR, CloudTrail[/cyan]")
        ds_input = Prompt.ask("   Data Sources", default="")
        inv_data_sources = [ds.strip() for ds in ds_input.split(",")] if ds_input else []

        # Related hunts
        console.print("\n5. Related Hunts (comma-separated IDs, optional):")
        console.print("   Examples: [cyan]H-0013, H-0042[/cyan]")
        hunts_input = Prompt.ask("   Related Hunts", default="")
        inv_related_hunts = [h.strip() for h in hunts_input.split(",")] if hunts_input else []

    # Render investigation template
    investigation_content = _render_investigation_template(
        investigation_id=investigation_id,
        title=inv_title,
        investigator=investigator or "ATHF",
        investigation_type=inv_type,
        tags=inv_tags,
        data_sources=inv_data_sources,
        related_hunts=inv_related_hunts,
    )

    # Write investigation file
    investigation_file = investigations_dir / f"{investigation_id}.md"

    with open(investigation_file, "w", encoding="utf-8") as f:
        f.write(investigation_content)

    console.print(f"\n[bold green]✅ Created {investigation_id}: {inv_title}[/bold green]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{investigation_file}[/cyan] to document your investigation")
    console.print("  2. Use LOCK pattern sections (optional/flexible)")
    console.print("  3. View all investigations: [cyan]athf investigate list[/cyan]")
    console.print("  4. Promote to hunt if valuable: [cyan]athf investigate promote {investigation_id}[/cyan]")


def _render_investigation_template(
    investigation_id: str,
    title: str,
    investigator: str,
    investigation_type: str,
    tags: List[str],
    data_sources: List[str],
    related_hunts: List[str],
) -> str:
    """Render investigation template with provided values.

    Args:
        investigation_id: Investigation ID (e.g., I-0001)
        title: Investigation title
        investigator: Investigator name
        investigation_type: Type (finding, baseline, exploratory, other)
        tags: List of tags
        data_sources: List of data sources
        related_hunts: List of related hunt IDs

    Returns:
        Rendered investigation content
    """
    today = datetime.now().strftime("%Y-%m-%d")

    # YAML frontmatter
    frontmatter = {
        "investigation_id": investigation_id,
        "title": title,
        "date": today,
        "investigator": investigator,
        "type": investigation_type,
        "related_hunts": related_hunts,
        "data_sources": data_sources,
        "tags": tags,
    }

    # Convert to YAML
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Build investigation content
    content = f"""---
{yaml_content}---

# {investigation_id}: {title}

**Investigation Metadata**

- **Date:** {today}
- **Investigator:** {investigator}
- **Type:** {investigation_type.title()}

---

## LEARN: Context & Background

### Investigation Context

[Why are you investigating this? What prompted the investigation?]

- **Trigger:** [Alert, customer report, anomaly, data quality check, etc.]
- **Initial Observations:** [What was initially noticed?]
- **Scope:** [What are you investigating? Time range? Specific systems?]

### Related Context

- **Related Hunts:** {', '.join(related_hunts) if related_hunts else '[None]'}
- **Past Investigations:** [Reference any related investigations]
- **Threat Intel/CTI:** [Any relevant threat intelligence or context]

---

## OBSERVE: Initial Analysis

### What You're Looking For

[Describe what patterns, behaviors, or anomalies you're investigating]

### Data Sources

- **Index/Data Source:** {', '.join(data_sources) if data_sources else '[Specify data sources]'}
- **Time Range:** [Start datetime] to [End datetime]
- **Key Fields:** [process.name, user, source_ip, etc.]

### Expected vs Observed

**Normal Behavior:**
- [What should normal activity look like?]
- [Common false positives to watch for]

**Suspicious/Anomalous Behavior:**
- [What anomalies are you seeing?]
- [What makes this suspicious or worth investigating?]

---

## CHECK: Investigation Queries & Analysis

### Initial Query

```[language: sql, kql, spl, etc.]
[Your initial investigation query]
```

**Query Results:**

- **Events Found:** [Count]
- **Time to Execute:** [X.X seconds]
- **Initial Findings:** [Brief summary of what was found]

### Refined Analysis

```[language]
[Follow-up queries or refined analysis]
```

**Additional Findings:**

- [Key observations from refined analysis]
- [Patterns or correlations discovered]
- [Anomalies identified]

### Pivots & Follow-ups

[Document any pivots you made during the investigation]

- **Pivot 1:** [What did you investigate next and why?]
- **Pivot 2:** [Additional follow-up investigation]

---

## KEEP: Findings & Next Steps

### Summary

[3-5 sentence summary of the investigation outcome]

- **Verdict:** [Benign | Suspicious | Malicious | Inconclusive | Data Quality Issue]
- **Confidence:** [High | Medium | Low]

### Key Findings

| **Finding** | **Evidence** | **Assessment** |
|-------------|-------------|----------------|
| [Finding 1] | [Supporting evidence] | [Benign/Suspicious/Malicious] |
| [Finding 2] | [Supporting evidence] | [Benign/Suspicious/Malicious] |

### Lessons Learned

**What Worked Well:**

- [Effective investigation strategies]
- [Useful queries or data sources]
- [Tools or techniques that helped]

**What Could Be Improved:**

- [Data gaps or blind spots identified]
- [Better approaches for next time]
- [Telemetry or visibility improvements needed]

### Next Steps

- [ ] [Escalate to incident response if malicious]
- [ ] [Create detection rule if repeatable pattern]
- [ ] [Promote to formal hunt if hypothesis emerges]
- [ ] [Document exceptions or false positive filters]
- [ ] [Address telemetry gaps]
- [ ] [Follow-up investigation if needed]

---

**Investigation Completed:** [Date or "Ongoing"]
**Status:** [Closed|In Progress|Escalated|Promoted to Hunt]
"""

    return content


@investigate.command(name="list")
@click.option("--type", "investigation_type", help="Filter by type (finding, baseline, exploratory, other)")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--output", type=click.Choice(["table", "json", "yaml"]), default="table", help="Output format")
def list_investigations(
    investigation_type: Optional[str],
    tags: Optional[str],
    output: str,
) -> None:
    """List all investigations with filtering options.

    \b
    Displays investigation catalog with:
    • Investigation ID and title
    • Type (finding, baseline, exploratory, other)
    • Tags and related hunts

    \b
    Examples:
      # List all investigations
      athf investigate list

      # Show only finding investigations
      athf investigate list --type finding

      # Filter by tags
      athf investigate list --tags alert-triage

      # JSON output for scripting
      athf investigate list --output json
    """
    investigations_dir = Path("investigations")
    investigations = get_all_investigations(investigations_dir)

    if not investigations:
        console.print("[yellow]No investigations found.[/yellow]")
        console.print("\nCreate your first investigation: [cyan]athf investigate new[/cyan]")
        return

    # Apply filters
    filtered_investigations = investigations
    if investigation_type:
        filtered_investigations = [
            inv for inv in filtered_investigations if inv.get("frontmatter", {}).get("type") == investigation_type
        ]

    if tags:
        filter_tags = {t.strip() for t in tags.split(",")}
        filtered_investigations = [
            inv for inv in filtered_investigations if filter_tags.intersection(inv.get("frontmatter", {}).get("tags", []))
        ]

    if not filtered_investigations:
        console.print("[yellow]No investigations match the filters.[/yellow]")
        return

    # Output format
    if output == "json":
        console.print(json.dumps(filtered_investigations, indent=2))
        return

    if output == "yaml":
        console.print(yaml.dump(filtered_investigations, default_flow_style=False))
        return

    # Table output (default)
    table = Table(title="Investigations", box=box.ROUNDED, show_header=True, header_style="bold cyan")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Tags", style="dim")
    table.add_column("Date", style="dim")

    for investigation in filtered_investigations:
        frontmatter = investigation.get("frontmatter", {})
        inv_id = frontmatter.get("investigation_id", "N/A")
        title = frontmatter.get("title", "Untitled")
        inv_type = frontmatter.get("type", "unknown")
        inv_tags = frontmatter.get("tags", [])
        date = frontmatter.get("date", "N/A")

        tags_str = ", ".join(inv_tags[:3]) if inv_tags else "-"
        if len(inv_tags) > 3:
            tags_str += f" (+{len(inv_tags) - 3})"

        table.add_row(inv_id, title, inv_type, tags_str, date)

    console.print(table)
    console.print(f"\n[dim]Total: {len(filtered_investigations)} investigations[/dim]")


@investigate.command()
@click.argument("query")
def search(query: str) -> None:
    """Search investigation files for keywords.

    \b
    Performs full-text search across all investigation files.

    \b
    Examples:
      # Search for PowerShell
      athf investigate search "PowerShell"

      # Search for customer-specific findings
      athf investigate search "customer-x"

      # Search for baseline work
      athf investigate search "baseline CloudTrail"
    """
    investigations_dir = Path("investigations")
    investigation_files = sorted(investigations_dir.glob("I-*.md"))

    if not investigation_files:
        console.print("[yellow]No investigation files found.[/yellow]")
        return

    matches = []
    for file_path in investigation_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if query.lower() in content.lower():
                matches.append(file_path)

    if not matches:
        console.print(f'[yellow]No matches found for "{query}"[/yellow]')
        return

    console.print(f'\n[bold]Found {len(matches)} investigation(s) matching "{query}":[/bold]\n')

    for file_path in matches:
        # Extract investigation ID and title from filename
        investigation_id = file_path.stem

        # Try to get title from frontmatter
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                frontmatter_match = yaml.safe_load(content.split("---")[1])
                title = frontmatter_match.get("title", "Untitled")
        except Exception:
            title = "Untitled"

        console.print(f"[cyan]{investigation_id}[/cyan]: {title}")
        console.print(f"  [dim]{file_path}[/dim]\n")


@investigate.command()
@click.argument("investigation_id")
def validate(investigation_id: str) -> None:
    """Validate investigation file structure.

    \b
    Checks:
    • YAML frontmatter is valid
    • Required fields exist (investigation_id, title, date)
    • Investigation ID format (I-XXXX)
    • File name matches investigation ID

    \b
    Examples:
      # Validate a specific investigation
      athf investigate validate I-0042

      # Validate after editing
      athf investigate validate I-0001
    """
    investigations_dir = Path("investigations")
    investigation_file = investigations_dir / f"{investigation_id}.md"

    if not investigation_file.exists():
        console.print(f"[red]Error: Investigation file not found: {investigation_file}[/red]")
        return

    is_valid, errors = validate_investigation_file(investigation_file)

    if is_valid:
        console.print(f"[bold green]✅ {investigation_id} is valid[/bold green]")
    else:
        console.print(f"[bold red]❌ {investigation_id} has validation errors:[/bold red]\n")
        for error in errors:
            console.print(f"  • {error}")


@investigate.command()
@click.argument("investigation_id")
@click.option("--technique", help="MITRE ATT&CK technique (required for hunt)")
@click.option("--tactic", multiple=True, help="MITRE tactics (can specify multiple)")
@click.option("--platform", multiple=True, help="Target platforms (can specify multiple)")
@click.option("--status", default="in-progress", help="Hunt status (default: in-progress)")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
def promote(
    investigation_id: str,
    technique: Optional[str],
    tactic: Tuple[str, ...],
    platform: Tuple[str, ...],
    status: str,
    non_interactive: bool,
) -> None:
    """Promote investigation to formal hunt.

    \b
    Creates a hunt file (H-XXXX) from an investigation, adding:
    • Hunt-required metadata (tactics, techniques, platform)
    • Hunt status and tracking fields
    • Findings count and TP/FP fields (default: 0)
    • Reference to original investigation (spawned_from)

    \b
    Examples:
      # Interactive promotion (prompts for details)
      athf investigate promote I-0042

      # Non-interactive with all options
      athf investigate promote I-0042 \\
        --technique T1059.001 \\
        --tactic execution \\
        --platform Windows \\
        --non-interactive

    \b
    After promotion:
      • Hunt file created in hunts/ directory
      • Investigation remains in investigations/ directory
      • Both files cross-reference each other
    """
    from athf.core.hunt_manager import HuntManager
    from athf.core.investigation_parser import InvestigationParser

    console.print("\n[bold cyan]🔄 Promoting investigation to hunt[/bold cyan]\n")

    # Check investigation file exists
    investigations_dir = Path("investigations")
    investigation_file = investigations_dir / f"{investigation_id}.md"

    if not investigation_file.exists():
        console.print(f"[red]Error: Investigation file not found: {investigation_file}[/red]")
        return

    # Parse investigation file
    try:
        parser = InvestigationParser(investigation_file)
        investigation_data = parser.parse()
        inv_frontmatter = investigation_data.get("frontmatter", {})
        inv_content = investigation_data.get("content", "")
    except Exception as e:
        console.print(f"[red]Error parsing investigation file: {e}[/red]")
        return

    # Get investigation details
    inv_title = inv_frontmatter.get("title", "Untitled")
    inv_investigator = inv_frontmatter.get("investigator", "Unknown")
    inv_data_sources = inv_frontmatter.get("data_sources", [])
    inv_related_hunts = inv_frontmatter.get("related_hunts", [])
    inv_tags = inv_frontmatter.get("tags", [])

    console.print(f"[bold]Investigation:[/bold] {investigation_id} - {inv_title}")

    # Gather hunt-required metadata
    if non_interactive:
        if not technique:
            console.print("[red]Error: --technique required in non-interactive mode[/red]")
            return
        hunt_technique = technique
        hunt_tactics = list(tactic) if tactic else []
        hunt_platforms = list(platform) if platform else []
        hunt_status = status
    else:
        # Interactive prompts
        console.print("\n[bold]📋 Let's add hunt-required metadata:[/bold]")

        # Technique (required)
        console.print("\n1. MITRE ATT&CK Technique (required for hunts):")
        console.print("   Examples: [cyan]T1003.001, T1059.001, T1078[/cyan]")
        hunt_technique = Prompt.ask("   Technique", default=technique or "")

        # Tactics
        console.print("\n2. MITRE Tactics (comma-separated):")
        console.print("   Examples: [cyan]initial-access, execution, persistence, credential-access[/cyan]")
        tactics_input = Prompt.ask("   Tactics", default=",".join(tactic) if tactic else "")
        hunt_tactics = [t.strip() for t in tactics_input.split(",")] if tactics_input else []

        # Platforms
        console.print("\n3. Target Platforms (comma-separated):")
        console.print("   Examples: [cyan]Windows, Linux, macOS, Cloud[/cyan]")
        platforms_input = Prompt.ask("   Platforms", default=",".join(platform) if platform else "")
        hunt_platforms = [p.strip() for p in platforms_input.split(",")] if platforms_input else []

        # Status
        console.print("\n4. Hunt Status:")
        hunt_status = Prompt.ask(
            "   Status",
            default=status,
            choices=["planning", "in-progress", "completed", "archived"],
        )

    # Get next hunt ID
    hunt_manager = HuntManager()
    hunt_id = hunt_manager.get_next_hunt_id()

    console.print(f"\n[bold]Hunt ID:[/bold] {hunt_id}")

    # Create hunt frontmatter
    today = datetime.now().strftime("%Y-%m-%d")
    hunt_frontmatter = {
        "hunt_id": hunt_id,
        "title": inv_title,
        "status": hunt_status,
        "date": today,
        "hunter": inv_investigator,
        "platform": hunt_platforms,
        "tactics": hunt_tactics,
        "techniques": [hunt_technique],
        "data_sources": inv_data_sources,
        "related_hunts": inv_related_hunts,
        "spawned_from": investigation_id,  # Reference investigation
        "findings_count": 0,
        "true_positives": 0,
        "false_positives": 0,
        "customer_deliverables": [],
        "tags": inv_tags,
    }

    # Convert to YAML
    yaml_content = yaml.dump(hunt_frontmatter, default_flow_style=False, sort_keys=False)

    # Build hunt content (preserve investigation content structure)
    hunt_content = f"""---
{yaml_content}---

# {hunt_id}: {inv_title}

**Hunt Metadata**

- **Date:** {today}
- **Hunter:** {inv_investigator}
- **Status:** {hunt_status.title()}
- **Promoted From:** {investigation_id}

---

{inv_content}
"""

    # Write hunt file
    hunts_dir = Path("hunts")
    hunts_dir.mkdir(exist_ok=True)
    hunt_file = hunts_dir / f"{hunt_id}.md"

    with open(hunt_file, "w", encoding="utf-8") as f:
        f.write(hunt_content)

    console.print(f"\n[bold green]✅ Promoted {investigation_id} to {hunt_id}[/bold green]")

    # Update investigation with promotion note
    promotion_note = f"\n\n---\n\n**Promoted to Hunt:** {hunt_id} on {today}\n"

    with open(investigation_file, "a", encoding="utf-8") as f:
        f.write(promotion_note)

    console.print(f"[dim]Updated {investigation_file} with promotion note[/dim]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  1. Edit [cyan]{hunt_file}[/cyan] to refine hunt hypothesis")
    console.print("  2. Add MITRE ATT&CK coverage if needed")
    console.print(f"  3. Validate hunt: [cyan]athf hunt validate {hunt_id}[/cyan]")
    console.print(f"  4. View hunt: [cyan]athf hunt list --status {hunt_status}[/cyan]\n")
