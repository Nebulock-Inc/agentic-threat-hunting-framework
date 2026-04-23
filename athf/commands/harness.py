"""Harness engineering commands — eval, validate, and inspect agent quality."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()

HARNESS_EPILOG = """
\b
Examples:
  # Run offline structural eval (no API keys needed, CI-safe)
  athf harness eval --agent hypothesis-generator

  # Run offline eval with JSON output
  athf harness eval --agent hypothesis-generator --format json

  # Run live eval (calls the real agent — requires API key)
  athf harness eval --agent hypothesis-generator --live

  # Use a custom dataset file
  athf harness eval --dataset path/to/my_evals.yaml

  # Validate a saved agent output file
  athf harness validate --agent hypothesis-generator --input output.json

  # List available bundled eval datasets
  athf harness list-datasets

\b
Offline vs Live mode:
  offline (default)  Validates eval case structure — no LLM calls, no API keys.
                     Safe for CI/CD. Checks that cases are well-formed.
  live (--live)      Calls the actual agent with each case's input, then scores
                     the real response. Requires a configured LLM provider.
"""


@click.group(epilog=HARNESS_EPILOG)
def harness() -> None:
    """Harness engineering — evaluate and validate agent quality.

    \b
    Implements the Agent = Model + Harness principle:
    * Sensors: computational validators that score agent outputs
    * Eval datasets: ground-truth cases for scoring agent quality
    * Reports: pass/fail tables with score breakdowns

    \b
    Key concepts (from harness engineering):
    • Guides (feedforward): AGENTS.md specs, constraints, exemplars
    • Sensors (feedback): validators, evals, LLM-as-judge

    \b
    Run 'athf harness eval --agent hypothesis-generator' to get started.
    """
    pass


@harness.command("eval")
@click.option(
    "--agent",
    "agent_name",
    default="hypothesis-generator",
    show_default=True,
    help="Agent to evaluate (hypothesis-generator, hunt-researcher)",
)
@click.option(
    "--dataset",
    "dataset_path",
    default=None,
    type=click.Path(exists=False),
    help="Path to YAML eval dataset (uses bundled dataset if not specified)",
)
@click.option(
    "--live",
    is_flag=True,
    default=False,
    help="Call the real agent (requires API key). Default: offline structural check.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
    help="Output format",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any case fails",
)
def eval_cmd(
    agent_name: str,
    dataset_path: Optional[str],
    live: bool,
    output_format: str,
    fail_fast: bool,
) -> None:
    """Run harness evaluation against an agent.

    In offline mode (default), validates eval case structure without LLM calls.
    In live mode (--live), calls the real agent and scores its responses.
    """
    from athf.harness.dataset import (
        get_bundled_dataset_for_agent,
        list_bundled_datasets,
        load_dataset,
    )
    from athf.harness.evaluator import HarnessEvaluator
    from athf.harness.metrics import build_report, render_report_json, render_report_table

    # Resolve dataset path
    if dataset_path:
        ds_path = Path(dataset_path)
    else:
        ds_path = get_bundled_dataset_for_agent(agent_name)
        if ds_path is None:
            available = [p.stem for p in list_bundled_datasets()]
            console.print(
                "[red]No bundled dataset found for agent '{}'.[/red]\n"
                "Available datasets: {}\n"
                "Specify a custom dataset with --dataset PATH".format(
                    agent_name, ", ".join(available) if available else "(none)"
                )
            )
            sys.exit(1)

    # Load dataset
    try:
        dataset = load_dataset(ds_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print("[red]Failed to load dataset: {}[/red]".format(exc))
        sys.exit(1)

    evaluator = HarnessEvaluator()

    if live:
        # Live mode: load agent and call it
        agent = _load_agent(agent_name)
        if agent is None:
            sys.exit(1)
        results = evaluator.run_live(dataset, agent)
    else:
        # Offline mode: structural validation only
        if output_format == "table":
            console.print(
                "[dim]Running offline structural eval "
                "(no LLM calls — use --live for real agent evaluation)[/dim]"
            )
        results = evaluator.run_offline(dataset)

    report = build_report(agent_name, dataset, results)

    if output_format == "json":
        click.echo(render_report_json(report))
    else:
        render_report_table(report, console)

    if fail_fast and report.failed > 0:
        sys.exit(1)


@harness.command("validate")
@click.option(
    "--agent",
    "agent_name",
    required=True,
    help="Agent type (hypothesis-generator, hunt-researcher)",
)
@click.option(
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to agent output JSON file to validate",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
)
def validate_cmd(agent_name: str, input_path: str, output_format: str) -> None:
    """Validate a saved agent output file.

    Reads a JSON file containing agent output and runs computational
    validators to check structural correctness.

    \b
    Example:
      # Save agent output to file, then validate it
      athf agent run hypothesis-generator --output output.json
      athf harness validate --agent hypothesis-generator --input output.json
    """
    from athf.harness.validators import HypothesisValidator, ResearchOutputValidator

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            output_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        console.print("[red]Failed to read input file: {}[/red]".format(exc))
        sys.exit(1)

    if agent_name in ("hypothesis-generator", "hypothesis_generator"):
        validator = HypothesisValidator()
        result = validator.validate(output_data)
    elif agent_name in ("hunt-researcher", "hunt_researcher"):
        validator_r = ResearchOutputValidator()
        result = validator_r.validate(output_data)
    else:
        console.print(
            "[red]Unknown agent '{}'. Supported: hypothesis-generator, hunt-researcher[/red]".format(
                agent_name
            )
        )
        sys.exit(1)

    if output_format == "json":
        click.echo(
            json.dumps(
                {
                    "passed": result.passed,
                    "score": result.score,
                    "violations": result.violations,
                    "warnings": result.warnings,
                },
                indent=2,
            )
        )
    else:
        status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
        score_color = "green" if result.score >= 0.8 else ("yellow" if result.score >= 0.5 else "red")

        console.print("\n[bold]Validation Result:[/bold]")
        console.print("  Agent:  {}".format(agent_name))
        console.print("  File:   {}".format(input_path))
        console.print("  Status: {}".format(status))
        console.print("  Score:  [{}]{:.2f}[/{}]".format(score_color, result.score, score_color))

        if result.violations:
            console.print("\n[bold red]Violations:[/bold red]")
            for v in result.violations:
                console.print("  [red]✗[/red] {}".format(v))

        if result.warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for w in result.warnings:
                console.print("  [yellow]⚠[/yellow] {}".format(w))

        if result.passed and not result.warnings:
            console.print("\n[green]✓ Output passes all validation checks.[/green]")

    if not result.passed:
        sys.exit(1)


@harness.command("list-datasets")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    show_default=True,
)
def list_datasets_cmd(output_format: str) -> None:
    """List available bundled eval datasets."""
    from athf.harness.dataset import list_bundled_datasets, load_dataset

    datasets = list_bundled_datasets()

    if output_format == "json":
        result = []
        for path in datasets:
            try:
                ds = load_dataset(path)
                result.append(
                    {
                        "file": path.name,
                        "agent": ds.agent,
                        "description": ds.description,
                        "cases": ds.case_count,
                        "version": ds.version,
                    }
                )
            except Exception as exc:
                result.append({"file": path.name, "error": str(exc)})
        click.echo(json.dumps(result, indent=2))
        return

    if not datasets:
        console.print("[yellow]No bundled eval datasets found.[/yellow]")
        return

    table = Table(title="Bundled Eval Datasets", show_header=True, header_style="bold cyan")
    table.add_column("File", style="dim")
    table.add_column("Agent")
    table.add_column("Description")
    table.add_column("Cases", justify="right")

    for path in datasets:
        try:
            ds = load_dataset(path)
            table.add_row(path.name, ds.agent, ds.description, str(ds.case_count))
        except Exception as exc:
            table.add_row(path.name, "[red]error[/red]", str(exc), "—")

    console.print(table)


# ------------------------------------------------------------------
# Agent loader helper
# ------------------------------------------------------------------

def _load_agent(agent_name: str) -> Optional[object]:
    """Load an agent instance by name for live evaluation.

    Returns None (after printing error) if the agent cannot be loaded.
    """
    try:
        if agent_name in ("hypothesis-generator", "hypothesis_generator"):
            from athf.agents.llm.hypothesis_generator import HypothesisGeneratorAgent

            return HypothesisGeneratorAgent()

        if agent_name in ("hunt-researcher", "hunt_researcher"):
            from athf.agents.llm.hunt_researcher import HuntResearcherAgent

            return HuntResearcherAgent()

        console.print(
            "[red]Unknown agent '{}'. "
            "Supported agents: hypothesis-generator, hunt-researcher[/red]".format(agent_name)
        )
        return None

    except Exception as exc:
        console.print("[red]Failed to load agent '{}': {}[/red]".format(agent_name, exc))
        return None
