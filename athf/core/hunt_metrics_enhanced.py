"""Enhanced hunt metrics with drill-downs, filters, and year-at-a-glance views."""

import csv
import io
from datetime import date
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich import box
from rich.table import Table

from athf.core.hunt_loader import HuntLoader
from athf.core.hunt_metrics import (
    HuntMetrics,
    _parse_date_field,
    calculate_metrics,
    parse_hunt_frontmatter,
)


def calculate_year_at_glance(hunt_dir: Path, year: int) -> List[HuntMetrics]:
    """Calculate metrics for all 4 quarters of a year.

    Creates a single HuntLoader and reuses it across all quarters for performance.
    """

    # Create loader once, reuse for all quarters
    loader = HuntLoader(hunt_dir)

    quarters = []
    quarter_dates = {
        1: (date(year, 1, 1), date(year, 3, 31)),
        2: (date(year, 4, 1), date(year, 6, 30)),
        3: (date(year, 7, 1), date(year, 9, 30)),
        4: (date(year, 10, 1), date(year, 12, 31)),
    }

    for q in range(1, 5):
        start_date, end_date = quarter_dates[q]
        metrics = calculate_metrics(hunt_dir, start_date, end_date, f"{year}-Q{q}", loader=loader)
        quarters.append(metrics)

    return quarters


def format_year_at_glance(quarters: List[HuntMetrics]) -> Table:
    """Format year-at-a-glance view (all 4 quarters) as Rich Table."""

    if not quarters:
        # Return empty table with message
        table = Table(title="No data available", box=box.SIMPLE)
        return table

    year = quarters[0].period_label.split('-')[0]

    # Create Rich table
    table = Table(
        title=f"📊 {year} YEAR-AT-A-GLANCE",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        title_style="bold white",
        show_lines=False,
    )

    # Add columns
    table.add_column("Metric", style="white", width=35)
    table.add_column("Q1", justify="center", width=10)
    table.add_column("Q2", justify="center", width=10)
    table.add_column("Q3", justify="center", width=10)
    table.add_column("Q4", justify="center", width=10)
    table.add_column("Trend", justify="center", width=8)

    # Metrics to show
    metrics_config = [
        ('Hunts Completed', 'completed_hunts', 'int'),
        ('Detections Created', 'detections_created', 'int'),
        ('Incidents Sourced', 'incidents_sourced', 'int'),
        ('Control Gaps', 'control_gaps', 'int'),
        ('Tactics Hunted (of 14)', 'tactics_count', 'int'),
        ('Data Available (%)', 'data_available_pct', 'pct'),
        ('Avg Duration (days)', 'avg_duration_days', 'float'),
    ]

    for label, attr, fmt in metrics_config:
        values = []
        for q in quarters:
            if attr == 'tactics_count':
                val = len(q.tactics_covered)
            else:
                val = getattr(q, attr)
            values.append(val)

        # Format values
        if fmt == 'int':
            formatted = [f"{v}" for v in values]
        elif fmt == 'float':
            formatted = [f"{v:.1f}" for v in values]
        elif fmt == 'pct':
            formatted = [f"{v:.0f}%" for v in values]
        else:
            formatted = [str(v) for v in values]

        # Trend signal with color - only compare quarters with data
        # Filter out zero values to avoid false trends mid-year
        non_zero_values = [v for v in values if v != 0]
        if len(non_zero_values) >= 2:
            if non_zero_values[-1] > non_zero_values[0]:
                trend = "[green]↑[/green]"
            elif non_zero_values[-1] < non_zero_values[0]:
                trend = "[red]↓[/red]"
            else:
                trend = "[yellow]→[/yellow]"
        else:
            # Not enough data for trend
            trend = "[dim]—[/dim]"

        table.add_row(
            label,
            formatted[0],
            formatted[1],
            formatted[2],
            formatted[3],
            trend
        )

    # Add caption with summary
    total_hunts = sum(q.total_hunts for q in quarters)
    completed_hunts = sum(q.completed_hunts for q in quarters)
    table.caption = f"[dim]Total hunts: {total_hunts} | Completed: {completed_hunts}[/dim]"

    return table


def _drill_down_generic(
    hunt_dir: Path,
    start_date: date,
    end_date: date,
    filter_fn: Callable[[Dict], bool],
    extract_fn: Callable[[Dict], Tuple],
    limit: int,
    loader: Optional[HuntLoader] = None
) -> List[Tuple]:
    """Generic drill-down implementation.

    Args:
        hunt_dir: Directory containing hunt files
        start_date: Start of date range
        end_date: End of date range
        filter_fn: Function to filter hunts (return True to include)
        extract_fn: Function to extract result tuple from hunt metadata
        limit: Maximum results to return
        loader: Optional HuntLoader for caching (scans directly if None)

    Returns:
        List of tuples from extract_fn
    """
    results: List[Tuple[Any, ...]] = []

    # Use loader if provided, otherwise scan directly
    if loader is not None:
        all_hunts = loader.load_all()
        for hunt_meta in all_hunts:
            hunt_date = _parse_date_field(hunt_meta.get('date'))

            if not hunt_date or not (start_date <= hunt_date <= end_date):
                continue

            if hunt_meta.get('status') != 'completed':
                continue

            # Apply custom filter
            if filter_fn(hunt_meta):
                results.append(extract_fn(hunt_meta))
    else:
        # Original behavior: direct filesystem scan
        for hunt_file in hunt_dir.rglob("H-*.md"):
            parsed_meta = parse_hunt_frontmatter(hunt_file)
            if not parsed_meta:
                continue

            hunt_date = _parse_date_field(parsed_meta.get('date'))

            if not hunt_date or not (start_date <= hunt_date <= end_date):
                continue

            if parsed_meta.get('status') != 'completed':
                continue

            # Apply custom filter
            if filter_fn(parsed_meta):
                results.append(extract_fn(parsed_meta))

    # Sort only if ALL results have numeric third element (not just first)
    if results and all(len(r) >= 3 and isinstance(r[2], (int, float)) for r in results):
        results.sort(key=lambda x: x[2], reverse=True)

    return results[:limit]


def drill_down_detections(hunt_dir: Path, start_date: date, end_date: date, limit: int = 20) -> List[Tuple[str, str, int]]:
    """Drill down: which hunts created detections?"""
    return _drill_down_generic(
        hunt_dir, start_date, end_date,
        filter_fn=lambda m: len(m.get('related_detections', [])) > 0,
        extract_fn=lambda m: (
            m.get('hunt_id', 'Unknown'),
            m.get('title', 'Unknown'),
            len(m.get('related_detections', []))
        ),
        limit=limit
    )


def drill_down_high_impact(hunt_dir: Path, start_date: date, end_date: date, threshold: int = 5, limit: int = 20) -> List[Tuple[str, str, int]]:
    """Drill down: hunts with high incident counts."""
    return _drill_down_generic(
        hunt_dir, start_date, end_date,
        filter_fn=lambda m: m.get('true_positives', 0) >= threshold,
        extract_fn=lambda m: (
            m.get('hunt_id', 'Unknown'),
            m.get('title', 'Unknown'),
            m.get('true_positives', 0)
        ),
        limit=limit
    )


def drill_down_control_gaps(hunt_dir: Path, start_date: date, end_date: date, limit: int = 20) -> List[Tuple[str, str, str]]:
    """Drill down: hunts that identified control gaps."""
    return _drill_down_generic(
        hunt_dir, start_date, end_date,
        filter_fn=lambda m: m.get('output_type') == 'control_gap',
        extract_fn=lambda m: (
            m.get('hunt_id', 'Unknown'),
            m.get('title', 'Unknown'),
            m.get('output_summary', 'N/A')
        ),
        limit=limit
    )


def format_drill_down(drill_type: str, results: List[Tuple], start_date: date, end_date: date) -> str:
    """Format drill-down results."""

    lines = [
        "",
        f"🔍 DRILL-DOWN: {drill_type.title()}",
        f"Period: {start_date} to {end_date}",
        "=" * 90,
        "",
    ]

    if not results:
        lines.append("No results found.")
        return "\n".join(lines)

    lines.append(f"Found {len(results)} hunts:")
    lines.append("")

    if drill_type == 'detections':
        lines.append(f"{'Hunt ID':<12} {'Detections':<12} {'Title':<60}")
        lines.append("-" * 90)
        for hunt_id, title, count in results:
            title_short = title[:57] + "..." if len(title) > 60 else title
            lines.append(f"{hunt_id:<12} {count:<12} {title_short:<60}")

    elif drill_type == 'high_impact':
        lines.append(f"{'Hunt ID':<12} {'Incidents':<12} {'Title':<60}")
        lines.append("-" * 90)
        for hunt_id, title, count in results:
            title_short = title[:57] + "..." if len(title) > 60 else title
            lines.append(f"{hunt_id:<12} {count:<12} {title_short:<60}")

    elif drill_type == 'control_gaps':
        lines.append(f"{'Hunt ID':<12} {'Title':<40} {'Gap Summary':<35}")
        lines.append("-" * 90)
        for hunt_id, title, summary in results:
            title_short = title[:37] + "..." if len(title) > 40 else title
            summary_short = summary[:32] + "..." if len(summary) > 35 else summary
            lines.append(f"{hunt_id:<12} {title_short:<40} {summary_short:<35}")

    lines.append("")
    return "\n".join(lines)


def format_as_csv(metrics: HuntMetrics) -> str:
    """Format metrics as CSV."""

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Period',
        'Total Hunts',
        'Completed Hunts',
        'Detections Created',
        'Incidents Sourced',
        'Control Gaps',
        'Tactics Covered',
        'Techniques Covered',
        'Data Available %',
        'Avg Duration Days',
        'Hunts Repeated',
        'Backlog Ratio',
        'Success Rate %',
    ])

    # Data
    writer.writerow([
        metrics.period_label,
        metrics.total_hunts,
        metrics.completed_hunts,
        metrics.detections_created,
        metrics.incidents_sourced,
        metrics.control_gaps,
        len(metrics.tactics_covered),
        len(metrics.techniques_covered),
        f"{metrics.data_available_pct:.1f}",
        f"{metrics.avg_duration_days:.1f}",
        metrics.hunts_repeated,
        f"{metrics.backlog_ratio:.2f}" if metrics.backlog_ratio is not None else "N/A",
        f"{metrics.success_rate_pct:.1f}",
    ])

    return output.getvalue()


def format_year_as_csv(quarters: List[HuntMetrics]) -> str:
    """Format year-at-a-glance as CSV."""

    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        'Quarter',
        'Total Hunts',
        'Completed Hunts',
        'Detections Created',
        'Incidents Sourced',
        'Control Gaps',
        'Tactics Covered',
        'Data Available %',
        'Avg Duration Days',
        'Hunts Repeated',
    ])

    # Data rows
    for q in quarters:
        writer.writerow([
            q.period_label,
            q.total_hunts,
            q.completed_hunts,
            q.detections_created,
            q.incidents_sourced,
            q.control_gaps,
            len(q.tactics_covered),
            f"{q.data_available_pct:.1f}",
            f"{q.avg_duration_days:.1f}",
            q.hunts_repeated,
        ])

    return output.getvalue()
