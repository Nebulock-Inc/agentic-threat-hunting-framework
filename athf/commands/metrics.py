"""``athf metrics`` — show, summary, extract, and record hunting metrics.

Vault-agnostic CLI surface defined by ATHF core. Vault plugins extend this
group at import time via ``metrics.add_command(...)`` to add platform-specific
subcommands (e.g. cloud usage reporting, org-level rollups).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import click
from rich import box
from rich.console import Console
from rich.table import Table

from athf.core.metrics import (
    DEFAULT_AGGREGATES_PATH,
    EVENT_TYPES,
    Aggregator,
    EventStore,
    MetricEvent,
)

console = Console()


METRICS_EPILOG = """
\b
Examples:
  # Show metrics for a specific hunt
  athf metrics show --hunt H-0019

  # Show workspace-wide summary
  athf metrics summary

  # Refresh derived aggregates from events.jsonl + hunt files
  athf metrics extract

  # Record an event manually (or from a script)
  athf metrics record --type manual --hunt H-0019 --field note=ran-the-thing

\b
Storage:
  • metrics/events.jsonl   - append-only canonical event log
  • metrics/aggregates.json - derived view, regenerable via 'extract'
"""


@click.group(epilog=METRICS_EPILOG)
def metrics() -> None:
    """Track hunting metrics: cost, tokens, queries, events, outcomes.

    \b
    Auto-instrumented:
      • LLM agent calls (token + cost + duration)
      • Web search calls (latency + result count)
      • Similarity search calls (latency)

    \b
    Manual via 'record' or athf.metrics.record_*:
      • Hunt outcomes (TP / FP / inconclusive)
      • Custom events
    """


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


@metrics.command()
@click.option("--hunt", "hunt_id", required=True, help="Hunt ID (e.g., H-0019)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--workspace",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    help="Workspace root (default: cwd)",
)
def show(hunt_id: str, output_format: str, workspace: Path) -> None:
    """Show per-hunt metrics."""
    aggregator = Aggregator(workspace=workspace)
    payload = aggregator.load()
    if payload is None:
        # Auto-extract on first read so the command always works.
        payload = aggregator.extract()

    hunt = payload.get("hunts", {}).get(hunt_id)
    if not hunt:
        console.print(f"[yellow]No metrics found for hunt: {hunt_id}[/yellow]")
        console.print("[dim]Try: athf metrics extract[/dim]")
        raise click.ClickException(f"No metrics found for hunt: {hunt_id}")

    if output_format == "json":
        click.echo(json.dumps({"hunt_id": hunt_id, **hunt}, indent=2))
        return

    table = Table(title=f"Metrics — {hunt_id}", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    for label, key in (
        ("LLM calls", "llm_calls"),
        ("Input tokens", "input_tokens"),
        ("Output tokens", "output_tokens"),
        ("Cost (USD)", "cost_usd"),
        ("Queries", "queries"),
        ("Query duration (ms)", "query_duration_ms"),
        ("Rows returned", "rows_returned"),
        ("Web searches", "web_searches"),
        ("Similarity searches", "similarity_searches"),
        ("Events analyzed", "events_analyzed"),
        ("True positives", "true_positives"),
        ("False positives", "false_positives"),
    ):
        if key in hunt:
            value = hunt[key]
            if key == "cost_usd":
                table.add_row(label, f"${value:.4f}")
            else:
                table.add_row(label, f"{value:,}" if isinstance(value, (int, float)) else str(value))

    if "outcomes" in hunt and hunt["outcomes"]:
        outcomes = ", ".join(sorted(set(hunt["outcomes"])))
        table.add_row("Outcomes", outcomes)

    console.print(table)


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------


@metrics.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.option(
    "--workspace",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    help="Workspace root (default: cwd)",
)
def summary(output_format: str, workspace: Path) -> None:
    """Show workspace-wide totals + rollups."""
    aggregator = Aggregator(workspace=workspace)
    payload = aggregator.load()
    if payload is None:
        payload = aggregator.extract()

    if output_format == "json":
        click.echo(json.dumps(payload, indent=2))
        return

    totals = payload.get("totals", {})
    rollups = payload.get("rollups", {})

    console.print("\n[bold cyan]Hunting Metrics Summary[/bold cyan]")
    console.print(f"[dim]Generated: {payload.get('generated_at', 'unknown')}[/dim]\n")
    console.print(f"[bold]Hunts tracked:[/bold] {totals.get('hunts', 0)}\n")

    table = Table(title="Workspace Totals", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    for label, key, fmt in (
        ("LLM calls", "llm_calls", "{:,}"),
        ("Input tokens", "input_tokens", "{:,}"),
        ("Output tokens", "output_tokens", "{:,}"),
        ("Cost (USD)", "cost_usd", "${:.4f}"),
        ("Queries", "queries", "{:,}"),
        ("Web searches", "web_searches", "{:,}"),
        ("Similarity searches", "similarity_searches", "{:,}"),
        ("Events analyzed", "events_analyzed", "{:,}"),
        ("True positives", "true_positives", "{:,}"),
        ("False positives", "false_positives", "{:,}"),
    ):
        value = totals.get(key, 0)
        table.add_row(label, fmt.format(value))
    console.print(table)

    for title, key in (("By platform", "by_platform"), ("By tactic", "by_tactic")):
        bucket = rollups.get(key, {})
        if not bucket:
            continue
        rt = Table(title=title, box=box.ROUNDED)
        rt.add_column("Label", style="cyan")
        rt.add_column("Hunts", justify="right", style="green")
        for label, count in sorted(bucket.items(), key=lambda kv: (-kv[1], kv[0])):
            rt.add_row(label, str(count))
        console.print(rt)


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------


@metrics.command()
@click.option(
    "--workspace",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    help="Workspace root (default: cwd)",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Override output path (default: <workspace>/metrics/aggregates.json)",
)
def extract(workspace: Path, output: Optional[Path]) -> None:
    """Refresh metrics/aggregates.json from events.jsonl + hunt files."""
    aggregator = Aggregator(workspace=workspace, aggregates_path=output)
    payload = aggregator.extract()
    out_path = aggregator.aggregates_path
    hunt_count = len(payload.get("hunts", {}))
    console.print(f"[green]✓[/green] Wrote {out_path} ({hunt_count} hunts)")


# ---------------------------------------------------------------------------
# record
# ---------------------------------------------------------------------------


def _parse_field(raw: str) -> Tuple[str, Any]:
    if "=" not in raw:
        raise click.BadParameter(f"--field expects key=value, got {raw!r}")
    key, _, value = raw.partition("=")
    key = key.strip()
    value = value.strip()
    if not key:
        raise click.BadParameter(f"--field has empty key in {raw!r}")
    try:
        return key, int(value)
    except ValueError:
        pass
    try:
        return key, float(value)
    except ValueError:
        if value.lower() in ("true", "false"):
            return key, value.lower() == "true"
        return key, value


@metrics.command(name="record")
@click.option(
    "--type",
    "event_type",
    type=click.Choice(list(EVENT_TYPES)),
    default="manual",
    help=f"Event type (one of: {', '.join(EVENT_TYPES)})",
)
@click.option("--hunt", "hunt_id", default=None, help="Hunt ID (e.g., H-0019)")
@click.option("--session", "session_id", default=None, help="Session ID")
@click.option(
    "--field",
    "fields",
    multiple=True,
    help="Additional key=value field. Repeat to add several.",
)
@click.option(
    "--workspace",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
    help="Workspace root (default: cwd)",
)
def record_cmd(
    event_type: str,
    hunt_id: Optional[str],
    session_id: Optional[str],
    fields: Tuple[str, ...],
    workspace: Path,
) -> None:
    """Append a single metric event to metrics/events.jsonl."""
    parsed: Dict[str, Any] = dict(_parse_field(f) for f in fields)

    reserved = {
        "event_type": "--type",
        "event_id": "(generated automatically)",
        "hunt_id": "--hunt",
        "session_id": "--session",
        "timestamp": "(generated automatically)",
        "custom": "(custom fields are derived automatically from --field)",
    }
    known_kwargs: Dict[str, Any] = {}
    custom: Dict[str, Any] = {}
    for k, v in parsed.items():
        if k in reserved:
            raise click.BadParameter(
                f"--field {k!r} collides with a dedicated option; "
                f"use {reserved[k]} instead"
            )
        if k in MetricEvent.__dataclass_fields__:
            known_kwargs[k] = v
        else:
            custom[k] = v

    try:
        evt = MetricEvent(
            event_type=event_type,
            hunt_id=hunt_id,
            session_id=session_id,
            custom=custom,
            **known_kwargs,
        )
    except (TypeError, ValueError) as exc:
        raise click.BadParameter(f"could not build event: {exc}") from exc

    try:
        EventStore(workspace / "metrics" / "events.jsonl").append(evt)
    except OSError as exc:
        raise click.ClickException(f"failed to write event: {exc}") from exc

    console.print(f"[green]✓[/green] Recorded {event_type} event (id={evt.event_id})")
