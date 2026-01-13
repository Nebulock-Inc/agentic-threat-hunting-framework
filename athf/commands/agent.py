"""Agent management commands."""

import json
from typing import Any, List, Optional

import click
from rich.console import Console

console = Console()

AGENT_EPILOG = """
\b
Examples:
  # List all available agents
  athf agent list

  # Get information about an agent
  athf agent info hypothesis-generator

  # Run hypothesis generator agent
  athf agent run hypothesis-generator --threat-intel "APT29 targeting SaaS applications"

\b
Agent Types:
  • LLM Agents - AI-powered agents using Claude API via AWS Bedrock

\b
Why Agents:
  • Standardized interfaces for hunt operations
  • Composable building blocks for workflows
  • Consistent error handling and result formats
  • Foundation for AI orchestration
"""


@click.group(epilog=AGENT_EPILOG)
def agent() -> None:
    """Manage ATHF agents.

    Agents provide modular capabilities for threat hunting operations.
    LLM agents use Claude API for creative and analytical tasks.

    \b
    Agent Execution Modes:
    • INTERACTIVE (default): Step-by-step execution with user approval
    • AUTONOMOUS (--auto): Runs all steps without check-ins
    """
    pass


@agent.command()
def list() -> None:
    """List all available agents.

    Displays registered agents with their type, status, and description.
    """
    from rich.table import Table

    agents = [
        {
            "name": "hypothesis-generator",
            "type": "LLM (Claude)",
            "status": "available",
            "description": "Generates creative hunt hypotheses using threat intelligence",
        },
        {
            "name": "hunt-researcher",
            "type": "LLM (Claude)",
            "status": "available",
            "description": "Conducts thorough pre-hunt research using 5-skill methodology",
        },
    ]

    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Agent Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="yellow", no_wrap=True, width=15)
    table.add_column("Status", style="green", no_wrap=True, width=12)
    table.add_column("Description", style="white")

    for agent_info in agents:
        name = agent_info["name"]
        agent_type = agent_info["type"]
        status = agent_info["status"]
        description = agent_info["description"]

        # Status emoji
        status_display = f"✅ {status}"
        table.add_row(name, agent_type, status_display, description)

    console.print("\n[bold]Available Agents:[/bold]\n")
    console.print(table)
    console.print()


@agent.command()
@click.argument("agent_name")
def info(agent_name: str) -> None:
    """Show detailed information about an agent.

    \b
    Example:
      athf agent info hypothesis-generator
      athf agent info hunt-researcher
    """
    if agent_name == "hypothesis-generator":
        # Display agent info
        console.print("\n[bold cyan]Agent:[/bold cyan] hypothesis-generator")
        console.print("[bold]Type:[/bold] LLM (Claude)")
        console.print("[bold]Status:[/bold] available")
        console.print("\n[bold]Description:[/bold]")
        console.print("  Generates creative hunt hypotheses using threat intelligence")

        console.print("\n[bold]Capabilities:[/bold]")
        capabilities = [
            "LOCK format generation",
            "ATT&CK mapping",
            "Environment validation",
            "Past hunt deduplication",
            "Fallback to template generation",
            "Cost tracking",
        ]
        for cap in capabilities:
            console.print(f"  • {cap}")

        console.print("\n[bold]Usage:[/bold]")
        console.print('  athf agent run hypothesis-generator --threat-intel "APT29 targeting SaaS"')
        console.print()

    elif agent_name == "hunt-researcher":
        console.print("\n[bold cyan]Agent:[/bold cyan] hunt-researcher")
        console.print("[bold]Type:[/bold] LLM (Claude)")
        console.print("[bold]Status:[/bold] available")
        console.print("\n[bold]Description:[/bold]")
        console.print("  Conducts thorough pre-hunt research using 5-skill methodology")

        console.print("\n[bold]Capabilities:[/bold]")
        capabilities = [
            "System internals research (how it normally works)",
            "Adversary tradecraft research via web search",
            "Telemetry mapping to OCSF fields",
            "Related past hunt discovery",
            "Research synthesis with gaps identification",
            "Recommended hypothesis generation",
            "Cost tracking and metrics",
        ]
        for cap in capabilities:
            console.print(f"  • {cap}")

        console.print("\n[bold]Research Skills:[/bold]")
        console.print("  1. System Research - How technology normally works")
        console.print("  2. Adversary Tradecraft - Attack techniques (web search)")
        console.print("  3. Telemetry Mapping - OCSF field availability")
        console.print("  4. Related Work - Past hunt correlation")
        console.print("  5. Synthesis - Key findings and gaps")

        console.print("\n[bold]Usage:[/bold]")
        console.print('  athf agent run hunt-researcher --topic "LSASS dumping"')
        console.print('  athf agent run hunt-researcher --topic "Pass-the-Hash" --technique T1003.002 --depth basic')
        console.print()

    else:
        console.print(f"[red]Error: Agent '{agent_name}' not found[/red]")
        console.print("\n[dim]Available agents:[/dim]")
        console.print("  • hypothesis-generator")
        console.print("  • hunt-researcher")
        raise click.Abort()


@agent.command()
@click.argument("agent_name")
@click.option("--threat-intel", help="Threat intelligence context (for hypothesis-generator)")
@click.option("--topic", help="Research topic (for hunt-researcher)")
@click.option("--technique", help="MITRE ATT&CK technique (for hunt-researcher)")
@click.option(
    "--depth",
    type=click.Choice(["basic", "advanced"]),
    default="advanced",
    help="Research depth: basic (5 min) or advanced (15-20 min) (for hunt-researcher)",
)
@click.option("--no-web-search", is_flag=True, help="Skip web search - offline mode (for hunt-researcher)")
@click.option("--tactic", help="MITRE tactic filter")
@click.option("--llm/--no-llm", default=True, help="Enable/disable LLM (default: enabled)")
@click.option(
    "--output-format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def run(  # noqa: C901
    agent_name: str,
    threat_intel: Optional[str],
    topic: Optional[str],
    technique: Optional[str],
    depth: str,
    no_web_search: bool,
    tactic: Optional[str],
    llm: bool,
    output_format: str,
) -> None:
    """Run an agent.

    LLM agents use Claude API via AWS Bedrock by default. Use --no-llm for fallback mode.

    \b
    Examples:
      # Hypothesis Generator
      athf agent run hypothesis-generator --threat-intel "APT29 targeting SaaS applications"
      athf agent run hypothesis-generator --threat-intel "Insider threat data exfiltration" --tactic collection

      # Hunt Researcher
      athf agent run hunt-researcher --topic "LSASS dumping"
      athf agent run hunt-researcher --topic "Pass-the-Hash" --technique T1003.002 --depth basic
      athf agent run hunt-researcher --topic "Credential Access" --no-web-search

      # Fallback mode (no LLM)
      athf agent run hypothesis-generator --threat-intel "..." --no-llm
    """
    if agent_name == "hypothesis-generator":
        if not threat_intel:
            console.print("[red]Error: --threat-intel required for hypothesis-generator[/red]")
            raise click.Abort()

        try:
            # Import LLM agents
            from athf.agents.llm import HypothesisGenerationInput, HypothesisGeneratorAgent

            hypothesis_agent = HypothesisGeneratorAgent(llm_enabled=llm)

            # Load context for hypothesis generation
            # Try to load past hunts and environment data if available
            past_hunts: List[dict[str, Any]] = []
            environment = {}

            # Try to load environment.md if it exists
            try:
                from pathlib import Path

                env_file = Path("environment.md")
                if env_file.exists():
                    # Parse basic environment info (data sources, platforms)
                    # TODO: Parse actual content from environment.md
                    environment = {
                        "data_sources": ["EDR telemetry", "SIEM logs", "Cloud logs"],
                        "platforms": ["Windows", "macOS", "Linux"],
                    }
            except Exception:
                # Use defaults if environment.md not found
                environment = {
                    "data_sources": ["EDR telemetry", "SIEM logs"],
                    "platforms": ["Windows", "macOS", "Linux"],
                }

            # Execute agent
            hypothesis_result = hypothesis_agent.execute(
                HypothesisGenerationInput(
                    threat_intel=threat_intel,
                    past_hunts=past_hunts,
                    environment=environment,
                )
            )

            if output_format == "json":
                console.print(json.dumps(hypothesis_result.metadata, indent=2))
            else:
                _display_hypothesis_generator_result(hypothesis_result)

        except ImportError as e:
            console.print(f"[red]Error loading agent: {e}[/red]")
            console.print("\n[dim]Make sure all dependencies are installed:[/dim]")
            console.print("  pip install boto3")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()

    elif agent_name == "hunt-researcher":
        if not topic:
            console.print("[red]Error: --topic required for hunt-researcher[/red]")
            raise click.Abort()

        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn

            from athf.agents.llm.hunt_researcher import HuntResearcherAgent, ResearchInput

            console.print("\n[bold cyan]Starting Research[/bold cyan]")
            console.print(f"[bold]Topic:[/bold] {topic}")
            console.print(f"[bold]Depth:[/bold] {depth} ({'~5 min' if depth == 'basic' else '~15-20 min'})")
            if technique:
                console.print(f"[bold]Technique:[/bold] {technique}")
            console.print()

            research_agent = HuntResearcherAgent(llm_enabled=llm)

            # Show progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Conducting research...", total=None)

                research_result = research_agent.execute(
                    ResearchInput(
                        topic=topic,
                        mitre_technique=technique,
                        depth=depth,
                        include_past_hunts=True,
                        include_telemetry_mapping=True,
                        web_search_enabled=not no_web_search,
                    )
                )

            if not research_result.is_success:
                console.print(f"[red]✗ Research failed: {research_result.error}[/red]")
                raise click.Abort()

            if output_format == "json":
                console.print(json.dumps(research_result.metadata, indent=2))
            else:
                _display_research_result(research_result)

        except ImportError as e:
            console.print(f"[red]Error loading agent: {e}[/red]")
            console.print("\n[dim]Make sure all dependencies are installed:[/dim]")
            console.print("  pip install boto3 tavily-python")
            raise click.Abort()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise click.Abort()

    else:
        console.print(f"[red]Error: Unknown agent: {agent_name}[/red]")
        console.print("\n[dim]Available agents:[/dim]")
        console.print("  • hypothesis-generator")
        console.print("  • hunt-researcher")
        raise click.Abort()


def _display_hypothesis_generator_result(result: Any) -> None:  # noqa: C901
    """Display hypothesis generator result."""
    if not result.is_success:
        console.print(f"[red]✗ Agent Error: {result.error}[/red]\n")
        return

    data = result.data

    console.print("[green]✓ Hypothesis generated successfully[/green]\n")

    console.print("[bold cyan]Hypothesis:[/bold cyan]")
    console.print(f"  {data.hypothesis}\n")

    console.print("[bold cyan]Justification:[/bold cyan]")
    console.print(f"  {data.justification}\n")

    if data.mitre_techniques:
        console.print("[bold cyan]MITRE ATT&CK Techniques:[/bold cyan]")
        for technique in data.mitre_techniques:
            console.print(f"  • {technique}")
        console.print()

    if data.data_sources:
        console.print("[bold cyan]Data Sources:[/bold cyan]")
        for source in data.data_sources:
            console.print(f"  • {source}")
        console.print()

    if data.expected_observables:
        console.print("[bold cyan]Expected Observables:[/bold cyan]")
        for observable in data.expected_observables:
            console.print(f"  • {observable}")
        console.print()

    if data.known_false_positives:
        console.print("[bold cyan]Known False Positives:[/bold cyan]")
        for fp in data.known_false_positives:
            console.print(f"  • {fp}")
        console.print()

    console.print(f"[bold cyan]Time Range:[/bold cyan] {data.time_range_suggestion}\n")

    if result.warnings:
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")
        console.print()

    if result.metadata:
        if "cost_usd" in result.metadata:
            console.print(f"[dim]Cost: ${result.metadata['cost_usd']:.4f}[/dim]")
        if "prompt_tokens" in result.metadata:
            console.print(
                f"[dim]Tokens: {result.metadata['prompt_tokens']} input + {result.metadata['completion_tokens']} output[/dim]"
            )
        console.print()


def _display_research_result(result: Any) -> None:
    """Display research result."""
    from rich.panel import Panel

    if not result.is_success:
        console.print(f"[red]✗ Agent Error: {result.error}[/red]\n")
        return

    output = result.data

    # Success panel
    console.print()
    console.print(
        Panel(
            f"[bold green]Research Complete: {output.research_id}[/bold green]\n\n"
            f"[bold]Topic:[/bold] {output.topic}\n"
            f"[bold]Duration:[/bold] {output.total_duration_ms / 1000:.1f} seconds\n"
            f"[bold]Cost:[/bold] ${output.total_cost_usd:.4f}\n"
            f"[bold]Web Searches:[/bold] {output.web_searches_performed}\n"
            f"[bold]LLM Calls:[/bold] {output.llm_calls}",
            title="Research Complete",
            border_style="green",
        )
    )

    # Summary of findings
    console.print("\n[bold cyan]Key Findings Summary[/bold cyan]")

    # System Research
    console.print(f"\n[bold]1. System Research:[/bold] {output.system_research.summary[:100]}...")

    # Adversary Tradecraft
    console.print(f"\n[bold]2. Adversary Tradecraft:[/bold] {output.adversary_tradecraft.summary[:100]}...")

    # Recommended Hypothesis
    if output.recommended_hypothesis:
        console.print("\n[bold green]Recommended Hypothesis:[/bold green]")
        console.print(f"  {output.recommended_hypothesis}")

    # Gaps
    if output.gaps_identified:
        console.print("\n[bold yellow]Gaps Identified:[/bold yellow]")
        for gap in output.gaps_identified[:3]:
            console.print(f"  - {gap}")

    # Next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Use standalone command for full research file:")
    console.print(f"     [cyan]athf research view {output.research_id}[/cyan]")
    console.print("  2. Generate hypothesis: [cyan]athf agent run hypothesis-generator[/cyan]")
    console.print(f"  3. Create hunt: [cyan]athf hunt new --research {output.research_id}[/cyan]")
    console.print()
