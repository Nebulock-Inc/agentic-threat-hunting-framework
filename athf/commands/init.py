"""Initialize ATHF directory structure."""

import shutil
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

from athf.data import get_data_path

console = Console()


@click.command()
@click.option("--path", default=".", help="Directory to initialize ATHF in")
@click.option("--non-interactive", is_flag=True, help="Skip interactive prompts")
def init(path: str, non_interactive: bool) -> None:
    """Initialize a new ATHF threat hunting workspace.

    \b
    Creates directory structure:
      config/         Configuration files
      hunts/          Hunt hypothesis cards
      queries/        Reusable query library
      runs/           Hunt execution results
      templates/      Hunt templates (LOCK pattern)
      knowledge/      Domain expertise and frameworks
      prompts/        AI workflow prompts
      integrations/   Tool integration configs
      docs/           Documentation

    \b
    Generates files:
      • config/.athfconfig.yaml (workspace configuration)
      • AGENTS.md (AI assistant context)
      • templates/HUNT_LOCK.md (hunt template)

    \b
    Examples:
      # Interactive setup (recommended for first time)
      athf init

      # Non-interactive with defaults
      athf init --non-interactive

      # Initialize in specific directory
      athf init --path /path/to/workspace

    \b
    Interactive setup will ask you:
      1. Workspace name (default: directory name)
      2. SIEM platform (Splunk, Sentinel, Elastic, etc.)
      3. EDR platform (CrowdStrike, SentinelOne, etc.)
      4. Hunt ID prefix (default: H-)
      5. Hunt retention period (default: 365 days)

    \b
    After initialization:
      1. Customize AGENTS.md with your environment details
      2. Add data sources to config/.athfconfig.yaml
      3. Create your first hunt: athf hunt new
    """
    base_path = Path(path).resolve()

    # Check if already initialized (check both old and new locations)
    old_config_path = base_path / ".athfconfig.yaml"
    new_config_path = base_path / "config" / ".athfconfig.yaml"

    if (old_config_path.exists() or new_config_path.exists()) and not Confirm.ask(
        f"ATHF already initialized in {base_path}. Reinitialize?", default=False
    ):
        console.print("[yellow]Initialization cancelled.[/yellow]")
        return

    config_path = new_config_path

    console.print("\n[bold cyan]🎯 Initializing Agentic Threat Hunting Framework[/bold cyan]\n")

    # Gather configuration
    if non_interactive:
        config = _default_config(base_path)
    else:
        config = _interactive_config(base_path)

    # Create directory structure
    directories = ["config", "hunts", "queries", "runs", "templates", "knowledge", "prompts", "integrations", "docs"]

    console.print("\n[bold]Creating directory structure...[/bold]")
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(exist_ok=True)
        console.print(f"  ✓ Created [cyan]{dir_name}/[/cyan]")

    # Save configuration
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    console.print("  ✓ Created [cyan]config/.athfconfig.yaml[/cyan]")

    # Create AGENTS.md if it doesn't exist
    agents_path = base_path / "AGENTS.md"
    if not agents_path.exists():
        _create_agents_file(agents_path, config)
        console.print("  ✓ Created [cyan]AGENTS.md[/cyan]")

    # Copy templates if they don't exist
    templates_path = base_path / "templates"
    if not (templates_path / "HUNT_LOCK.md").exists():
        _create_hunt_template(templates_path / "HUNT_LOCK.md")
        console.print("  ✓ Created [cyan]templates/HUNT_LOCK.md[/cyan]")

    # Create customizable Jinja2 template for athf hunt new
    if not (templates_path / "HUNT_TEMPLATE.j2").exists():
        _create_jinja2_hunt_template(templates_path / "HUNT_TEMPLATE.j2")
        console.print("  ✓ Created [cyan]templates/HUNT_TEMPLATE.j2[/cyan] (customizable hunt template)")

    # Copy reference files from package data
    _copy_reference_files(base_path)

    console.print("\n[bold green]✅ ATHF initialized successfully![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Customize [cyan]AGENTS.md[/cyan] with your environment details")
    console.print("  2. Create your first hunt: [cyan]athf hunt new[/cyan]")
    console.print("  3. Check out the docs at [cyan]docs/getting-started.md[/cyan]")


def _default_config(base_path: Path) -> dict:
    """Return default configuration."""
    return {
        "workspace_name": base_path.name,
        "hunt_prefix": "H-",
        "siem": "Splunk",
        "edr": "CrowdStrike",
        "query_language": "SPL",
        "hunt_retention_days": 365,
    }


def _interactive_config(base_path: Path) -> dict:
    """Gather configuration interactively."""
    console.print("[bold]📋 Quick setup questions:[/bold]")

    config: dict = {}

    # Workspace name
    workspace_name = Prompt.ask(
        "1. Workspace name (e.g., 'Production Hunts', 'Client-Acme', 'SOC Team')", default=base_path.name
    )
    config["workspace_name"] = workspace_name

    # SIEM
    siem = Prompt.ask(
        "2. What SIEM do you use?", choices=["Splunk", "Sentinel", "Elastic", "Chronicle", "Other"], default="Splunk"
    )
    config["siem"] = siem

    # Query language mapping
    query_lang_map = {"Splunk": "SPL", "Sentinel": "KQL", "Elastic": "Lucene", "Chronicle": "YARA-L", "Other": "Custom"}
    config["query_language"] = query_lang_map.get(siem, "SPL")

    # EDR
    edr = Prompt.ask(
        "3. What's your primary EDR?",
        choices=["CrowdStrike", "SentinelOne", "Defender", "Carbon Black", "Other"],
        default="CrowdStrike",
    )
    config["edr"] = edr

    # Hunt prefix
    hunt_prefix = Prompt.ask("4. Hunt ID prefix (e.g., H-, HUNT-)", default="H-")
    config["hunt_prefix"] = hunt_prefix

    # Retention
    retention = Prompt.ask("5. Hunt retention (days)", default="365")
    config["hunt_retention_days"] = int(retention) if isinstance(retention, str) else retention

    return config


def _create_agents_file(path: Path, config: dict) -> None:
    """Create AGENTS.md file with configuration."""
    content = f"""# ATHF Agent Context

**Workspace:** {config['workspace_name']}

This file provides context to AI assistants about your threat hunting environment.

## Data Sources

### SIEM / Log Aggregation
- **Platform:** {config['siem']}
- **Query Language:** {config['query_language']}
- **Indexes:** [Add your indexes here]
- **Retention:** 90 days
- **Access:** [Add access method]

### EDR / Endpoint Security
- **Platform:** {config['edr']}
- **Telemetry:** Process execution, network connections, file modifications
- **Query Access:** [Add query method]

### Other Data Sources
[Add additional data sources]

## Technology Stack

### Security Tools
- SIEM: {config['siem']}
- EDR: {config['edr']}
- [Add more tools]

### Cloud Platforms
[Add cloud platforms if applicable]

## Known Visibility Gaps

Document what you can't see:
- [Add visibility gaps]

## Hunt Numbering Convention

- **Prefix:** {config['hunt_prefix']}
- **Format:** {config['hunt_prefix']}XXXX (e.g., {config['hunt_prefix']}0001)
- **Retention:** {config['hunt_retention_days']} days

## Team Context

[Add information about your team, shift coverage, escalation procedures]
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_hunt_template(path: Path) -> None:
    """Create hunt template file."""
    content = """---
hunt_id: H-XXXX
title: [Hunt Title]
status: planning
date: YYYY-MM-DD
hunter: [Your Name]
platform: [Windows/Linux/macOS/Cloud]
tactics: [persistence, credential-access, etc.]
techniques: [T1003.001, T1005, etc.]
data_sources: [SIEM, EDR, etc.]
related_hunts: []
findings_count: 0
findings: []
ruled_out: []
# Legacy counters, kept for hunts predating the ladder. Leave commented out: an
# explicit value overrides the counts derived from findings/ruled_out above.
# true_positives: 0
# false_positives: 0
customer_deliverables: []
tags: []
---

# H-XXXX: [Hunt Title]

**Hunt Metadata**

- **Date:** YYYY-MM-DD
- **Hunter:** [Your Name]
- **Status:** Planning
- **MITRE ATT&CK:** [Primary Technique]

---

## LEARN: Prepare the Hunt

### Hypothesis Statement

[What behavior are you looking for? What will you observe if the hypothesis is true?]

### Threat Context

[What threat actor/malware/TTP motivates this hunt?]

### ABLE Scoping

| **Field**   | **Your Input** |
|-------------|----------------|
| **Actor** *(Optional)* | [Threat actor or malware family] |
| **Behavior** | [TTP or behavior pattern] |
| **Location** | [Systems, networks, or environments to hunt] |
| **Evidence** | [Data sources and key fields to examine] |

### Threat Intel & Research

- **MITRE ATT&CK Techniques:** [List relevant techniques]
- **CTI Sources & References:** [Links to reports, blogs, etc.]

### Related Tickets

| **Team** | **Ticket/Details** |
|----------|-------------------|
| **SOC/IR** | [Ticket numbers or N/A] |

---

## OBSERVE: Expected Behaviors

### What Normal Looks Like

[Describe legitimate activity that should not trigger alerts]

### What Suspicious Looks Like

[Describe adversary behavior patterns to hunt for]

### Expected Observables

- **Processes:** [Process names, command lines]
- **Network:** [Connections, protocols, domains]
- **Files:** [File paths, extensions, sizes]
- **Registry:** [Registry keys if applicable]
- **Authentication:** [Login patterns if applicable]

---

## CHECK: Execute & Analyze

### Data Source Information

- **Index/Data Source:** [SIEM index or data source]
- **Time Range:** [Date range for hunt]
- **Events Analyzed:** [Approximate count]
- **Data Quality:** [Assessment of data completeness]

### Hunting Queries

#### Initial Query

```
[Your initial query]
```

**Query Notes:**
- [What did this query return?]
- [What worked? What didn't?]

#### Refined Query

```
[Your refined query after iterations]
```

**Refinement Rationale:**
- [Why did you change the query?]
- [What improvements were made?]

### Visualization & Analytics

[Describe any visualizations, timelines, or statistical analysis]

### Query Performance

**What Worked Well:**
- [Effective filters or techniques]

**What Didn't Work:**
- [Challenges or limitations]

**Iterations Made:**
- [Document query evolution]

---

## KEEP: Findings & Response

### Executive Summary

[Concise summary of hunt results and key findings]

### Findings

Things you're reporting as malicious. Only `confirmed` and `suspected` belong here.

| **Verdict** | **Subject** | **Ticket** | **Evidence** | **Independent Confirmation** |
|-------------|-------------|-----------|--------------|------------------------------|
| `confirmed` | [Host, account, or resource] | [INC-####] | [Telemetry that surfaced it] | [What established root cause outside the logs] |
| `suspected` | [Host, account, or resource] | [INC-####] | [Telemetry that surfaced it] | None — telemetry only |

**The evidence gate:** `confirmed` requires telemetry **plus** something from outside the log
corpus — controlled reproduction, host forensics, or configuration review. Telemetry alone never
reaches `confirmed`. If you couldn't confirm, the verdict is `suspected`.

### Ruled Out

Results that closed the question. `attempted_not_vulnerable` is often the most valuable row in a
customer-facing report.

| **Verdict** | **Subject** | **What Closed It** |
|-------------|-------------|--------------------|
| `attempted_not_vulnerable` | [Host, account, or resource] | [Name the control that held and how you verified it] |
| `benign` | [Host, account, or resource] | [The legitimate activity that explains it] |
| `inconclusive` | [Host, account, or resource] | [Which telemetry was missing or too sparse] |

**Counts:** `confirmed` [N] · `suspected` [N] · `attempted_not_vulnerable` [N] · `benign` [N] · `inconclusive` [N]

### Detection Logic

**Automation Opportunity:**

[Can this hunt become an automated detection rule?]

**Proposed Detection:**

```
[Detection rule if applicable]
```

### Lessons Learned

**What Worked Well:**
- [Successes]

**What Could Be Improved:**
- [Areas for improvement]

**Telemetry Gaps Identified:**
- [Missing data sources or visibility gaps]

### Follow-up Actions

- [ ] [Action item 1]
- [ ] [Action item 2]

### Follow-up Hunts

- [Related hunt ideas for future investigation]

---

**Hunt Completed:** YYYY-MM-DD
**Next Review:** [Date for recurring hunt if applicable]
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _create_jinja2_hunt_template(path: Path) -> None:
    """Create customizable Jinja2 hunt template for athf hunt new.

    This template is used by `athf hunt new` to generate hunt files.
    Users can modify it to customize the structure of new hunts.
    """
    from athf.core.template_engine import HUNT_TEMPLATE

    header = (
        "{#- Customizable Jinja2 template for 'athf hunt new' -#}\n"
        "{#- Edit this file to change the structure of new hunt files -#}\n"
        "{#- Available variables: hunt_id, title, status, date, hunter, platform, -#}\n"
        "{#-   tactics, techniques, data_sources, tags, hypothesis, threat_context, -#}\n"
        "{#-   actor, behavior, location, evidence, spawned_from -#}\n"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(HUNT_TEMPLATE)


def _copy_reference_files(base_path: Path) -> None:
    """Copy reference files from package data to workspace.

    Copies knowledge base, prompts, example hunts, docs, and integrations
    from the installed package to the user's workspace.
    """
    try:
        data_path = get_data_path()
    except Exception:
        # Package data not available (e.g., development mode)
        console.print("  [dim]Skipping reference file copy (package data not available)[/dim]")
        return

    # Directories to copy from package to workspace
    copy_dirs = ["knowledge", "prompts", "hunts", "docs", "integrations"]

    for dir_name in copy_dirs:
        src_dir = data_path / dir_name
        dst_dir = base_path / dir_name

        if src_dir.exists() and src_dir.is_dir():
            try:
                # Copy files, don't overwrite existing
                for src_file in src_dir.rglob("*"):
                    if src_file.is_file():
                        # Calculate relative path and destination
                        rel_path = src_file.relative_to(src_dir)
                        dst_file = dst_dir / rel_path

                        # Only copy if destination doesn't exist
                        if not dst_file.exists():
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)

                console.print(f"  ✓ Copied reference files to [cyan]{dir_name}/[/cyan]")
            except Exception as e:
                console.print(f"  [yellow]Warning: Could not copy {dir_name}/: {e}[/yellow]")
