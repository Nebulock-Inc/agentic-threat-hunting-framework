"""Hunt metrics calculation for 'Measure the Hunt' framework.

Computes quarterly metrics from hunt frontmatter.
"""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import statistics
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import yaml
from rich.table import Table
from rich import box

if TYPE_CHECKING:
    from athf.core.hunt_loader import HuntLoader


def _parse_date_field(value: Any) -> Optional[date]:
    """Parse date field from hunt metadata.

    Handles both date objects and ISO date strings.
    """
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


@dataclass
class HuntMetrics:
    """Computed metrics for a period."""

    # Period
    period_label: str
    start_date: date
    end_date: date

    # Outputs (3 metrics)
    total_hunts: int
    completed_hunts: int
    detections_created: int  # Count of related_detections entries
    incidents_sourced: int   # Sum of true_positives
    control_gaps: int        # Count of output_type: control_gap

    # By type/criticality
    by_output_type: Dict[str, int]
    by_criticality: Dict[str, int]

    # Coverage (3 metrics)
    tactics_covered: List[str]
    techniques_covered: List[str]
    by_technology: Dict[str, int]  # Count by technology_domain
    data_available_pct: float      # % hunts with data_sources_available: true

    # Operations (3 metrics)
    avg_duration_days: float
    median_duration_days: float
    hunts_repeated: int            # Count of repeat_classification: unplanned
    backlog_ratio: Optional[float]  # Ratio as float (e.g., 2.5 for "2.5:1")
    backlogged_count: int          # Raw backlog count
    total_findings: int
    success_rate_pct: float  # Hunts with TP > 0


def parse_hunt_frontmatter(file_path: Path) -> Optional[Dict[str, Any]]:
    """Extract YAML frontmatter from hunt markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        result = yaml.safe_load(parts[1])
        return result if isinstance(result, dict) else None
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        # Log warning but return None to continue scanning
        return None


def calculate_metrics(
    hunt_dir: Path,
    start_date: date,
    end_date: date,
    period_label: str,
    loader: Optional["HuntLoader"] = None
) -> HuntMetrics:
    """Calculate metrics for hunts in date range.

    Args:
        hunt_dir: Directory containing hunt files
        start_date: Start of date range
        end_date: End of date range
        period_label: Label for this period
        loader: Optional HuntLoader for caching (creates new if None)
    """

    # Use loader if provided, otherwise scan directly
    hunts: List[Dict[str, Any]] = []
    if loader is not None:
        all_hunts = loader.load_all()
        # Filter by date range
        for hunt_meta in all_hunts:
            hunt_date = _parse_date_field(hunt_meta.get('date'))
            if hunt_date and start_date <= hunt_date <= end_date:
                hunts.append(hunt_meta)
    else:
        # Original behavior: direct filesystem scan
        for hunt_file in hunt_dir.rglob("H-*.md"):
            meta: Optional[Dict[str, Any]] = parse_hunt_frontmatter(hunt_file)
            if not meta:
                continue

            hunt_date = _parse_date_field(meta.get('date'))

            if hunt_date and start_date <= hunt_date <= end_date:
                hunts.append(meta)

    # Filter out hunts excluded from metrics
    hunts = [h for h in hunts if not h.get('exclude_from_metrics', False)]

    # Calculate metrics
    completed = [h for h in hunts if h.get('status') == 'completed']

    # Outputs
    detections = sum(
        len(h.get('related_detections') or [])
        for h in completed
    )

    incidents = sum(h.get('true_positives') or 0 for h in completed)

    control_gaps = sum(
        1 for h in completed
        if h.get('output_type') == 'control_gap'
    )

    # By type
    by_type: Dict[str, int] = {}
    for h in completed:
        otype = h.get('output_type', 'unknown')
        by_type[otype] = by_type.get(otype, 0) + 1

    # By criticality
    by_crit: Dict[str, int] = {}
    for h in completed:
        crit = h.get('output_criticality', 'unknown')
        by_crit[crit] = by_crit.get(crit, 0) + 1

    # Coverage
    all_tactics: set[str] = set()
    all_techniques: set[str] = set()
    for h in completed:
        all_tactics.update(h.get('tactics') or [])
        all_techniques.update(h.get('techniques') or [])

    # By technology
    by_tech: Dict[str, int] = {}
    for h in completed:
        tech = h.get('technology_domain', 'unknown')
        by_tech[tech] = by_tech.get(tech, 0) + 1

    # Data sources available (Coverage metric #5)
    # Accept bool True, non-empty string, or non-empty list
    hunts_with_data = sum(
        1 for h in completed
        if h.get('data_sources_available') in (True, 'true', 'True', 'yes', 'Yes')
        or (isinstance(h.get('data_sources_available'), (list, str))
            and len(h.get('data_sources_available') or '') > 0)
    )
    data_available_pct = (hunts_with_data / len(completed) * 100) if completed else 0

    # Duration (Operations metric #9)
    durations = []
    for h in completed:
        started = _parse_date_field(h.get('date'))
        finished = _parse_date_field(h.get('completed_date'))
        if started and finished:
            delta_days = (finished - started).days
            if delta_days > 0:  # Only count positive durations
                durations.append(delta_days)

    avg_duration = sum(durations) / len(durations) if durations else 0
    median_duration = statistics.median(durations) if durations else 0

    # Hunts repeated (Operations metric #7)
    # Count unplanned repeats only (planned repeats are intentional)
    hunts_repeated = sum(
        1 for h in completed
        if h.get('repeat_classification') == 'unplanned'
    )

    # Backlog ratio (Operations metric #8)
    # Backlog = hunts with status 'planning' that have a backlog_date
    backlogged = sum(
        1 for h in hunts
        if h.get('status') == 'planning' and h.get('backlog_date')
    )

    if len(completed) > 0:
        backlog_ratio = backlogged / len(completed)
    else:
        backlog_ratio = None

    # Success rate
    success = sum(1 for h in completed if (h.get('true_positives') or 0) > 0)
    success_rate = (success / len(completed) * 100) if completed else 0

    # Total findings
    total_findings = sum(h.get('findings_count') or 0 for h in completed)

    return HuntMetrics(
        period_label=period_label,
        start_date=start_date,
        end_date=end_date,
        total_hunts=len(hunts),
        completed_hunts=len(completed),
        detections_created=detections,
        incidents_sourced=incidents,
        control_gaps=control_gaps,
        by_output_type=by_type,
        by_criticality=by_crit,
        tactics_covered=sorted(all_tactics),
        techniques_covered=sorted(all_techniques),
        by_technology=by_tech,
        data_available_pct=data_available_pct,
        avg_duration_days=avg_duration,
        median_duration_days=median_duration,
        hunts_repeated=hunts_repeated,
        backlog_ratio=backlog_ratio,
        backlogged_count=backlogged,
        total_findings=total_findings,
        success_rate_pct=success_rate,
    )


def format_metrics(metrics: HuntMetrics) -> str:
    """Format metrics as text output."""

    lines = [
        f"\n📊 Hunt Metrics: {metrics.period_label}",
        "=" * 60,
        "",
        f"OUTPUTS ({metrics.completed_hunts} hunts completed)",
        f"  ✓ Detections created or tuned: {metrics.detections_created}",
        f"  ✓ Incidents sourced from hunts: {metrics.incidents_sourced}",
        f"  ✓ Control gaps identified: {metrics.control_gaps}",
    ]

    # Show output type breakdown
    if metrics.by_output_type:
        known_types = {k: v for k, v in metrics.by_output_type.items() if k != 'unknown'}
        unknown_count = metrics.by_output_type.get('unknown', 0)

        if known_types:
            type_str = ", ".join(f"{k}({v})" for k, v in known_types.items())
            lines.append(f"    By type: {type_str}")

        if unknown_count > 0:
            lines.append(f"    ⚠️  {unknown_count} hunts missing output_type")

    lines.extend([
        "",
        "COVERAGE",
        f"  ✓ ATT&CK tactics hunted: {len(metrics.tactics_covered)} of 14 ({len(metrics.tactics_covered) / 14 * 100:.0f}%)",
    ])

    # Show technologies hunted
    if metrics.by_technology:
        known_tech = {k: v for k, v in metrics.by_technology.items() if k != 'unknown'}
        if known_tech:
            tech_str = ", ".join(f"{k}({v})" for k, v in known_tech.items())
            lines.append(f"  ✓ Technologies hunted: {tech_str}")

        unknown_tech = metrics.by_technology.get('unknown', 0)
        if unknown_tech > 0:
            lines.append(f"    ⚠️  {unknown_tech} hunts missing technology_domain")

    lines.extend([
        f"  ✓ Techniques hunted: {len(metrics.techniques_covered)}",
        "",
        "OPERATIONS",
        f"  ✓ Average hunt duration: {metrics.avg_duration_days:.1f} days",
        f"  ✓ Total findings: {metrics.total_findings}",
        f"  ✓ Success rate: {metrics.success_rate_pct:.0f}% ({int(metrics.success_rate_pct * metrics.completed_hunts / 100)} hunts with TP)",
        ""
    ])

    return "\n".join(lines)


def format_quarterly_scorecard(current: HuntMetrics, previous: Optional[HuntMetrics] = None) -> Table:
    """Format as quarterly scorecard using Rich Table - matches slide deck format.

    Returns a Rich Table object for clean, professional display of the 9 starter metrics.
    """

    def trend_signal(curr_val: Any, prev_val: Any) -> str:
        """Calculate trend: up/flat/down."""
        if prev_val is None:
            return "--"
        if isinstance(curr_val, (int, float)) and isinstance(prev_val, (int, float)):
            if curr_val > prev_val:
                return "↑"
            elif curr_val < prev_val:
                return "↓"
            else:
                return "→"
        return "--"

    # Create table with clean styling
    table = Table(
        title=f"📊 QUARTERLY HUNT SCORECARD: {current.period_label}",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        title_style="bold white",
        show_lines=True,  # Show lines between rows for better readability
    )

    # Add columns
    table.add_column("Arena", style="dim", width=12)
    table.add_column("Metric", width=35)
    table.add_column("Last Q", justify="center", width=10)
    table.add_column("This Q", justify="center", width=10)
    table.add_column("Signal", justify="center", width=10)

    # OUTPUTS (3 metrics)
    last_q_det = str(previous.detections_created) if previous else "---"
    last_q_inc = str(previous.incidents_sourced) if previous else "---"
    last_q_gap = str(previous.control_gaps) if previous else "---"

    table.add_row(
        "[yellow]Outputs[/yellow]",
        "Detections created or tuned",
        last_q_det,
        str(current.detections_created),
        trend_signal(current.detections_created, previous.detections_created if previous else None)
    )
    table.add_row(
        "[yellow]Outputs[/yellow]",
        "Incidents sourced from hunts",
        last_q_inc,
        str(current.incidents_sourced),
        trend_signal(current.incidents_sourced, previous.incidents_sourced if previous else None)
    )
    table.add_row(
        "[yellow]Outputs[/yellow]",
        "Control gaps identified",
        last_q_gap,
        str(current.control_gaps),
        trend_signal(current.control_gaps, previous.control_gaps if previous else None)
    )

    # COVERAGE (3 metrics)
    curr_tactics = len(current.tactics_covered)
    prev_tactics = len(previous.tactics_covered) if previous else None

    curr_data_pct = f"{current.data_available_pct:.0f}%"
    prev_data_pct = f"{previous.data_available_pct:.0f}%" if previous else "---"

    # Technologies hunted
    curr_tech = [k for k in current.by_technology.keys() if k != 'unknown']
    prev_tech = [k for k in previous.by_technology.keys() if k != 'unknown'] if previous else []
    curr_tech_str = str(len(curr_tech))
    prev_tech_str = str(len(prev_tech)) if prev_tech else "---"

    table.add_row(
        "[cyan]Coverage[/cyan]",
        "ATT&CK tactics hunted (of 14)",
        str(prev_tactics) if prev_tactics is not None else "---",
        str(curr_tactics),
        trend_signal(curr_tactics, prev_tactics)
    )
    table.add_row(
        "[cyan]Coverage[/cyan]",
        "Hunts with data available (%)",
        prev_data_pct,
        curr_data_pct,
        trend_signal(current.data_available_pct, previous.data_available_pct if previous else None)
    )
    table.add_row(
        "[cyan]Coverage[/cyan]",
        "Technologies hunted",
        prev_tech_str,
        curr_tech_str,
        trend_signal(len(curr_tech), len(prev_tech))
    )

    # OPERATIONS (3 metrics)
    curr_duration = f"{current.avg_duration_days:.1f}"
    prev_duration = f"{previous.avg_duration_days:.1f}" if previous else "---"

    curr_ratio = f"{current.backlog_ratio:.1f}:1" if current.backlog_ratio is not None else "N/A"
    prev_ratio = f"{previous.backlog_ratio:.1f}:1" if previous and previous.backlog_ratio is not None else "N/A"

    table.add_row(
        "[magenta]Operations[/magenta]",
        "Hunts repeated more than twice",
        str(previous.hunts_repeated) if previous else "---",
        str(current.hunts_repeated),
        trend_signal(current.hunts_repeated, previous.hunts_repeated if previous else None)
    )
    table.add_row(
        "[magenta]Operations[/magenta]",
        "Backlog ratio (backlog : done)",
        prev_ratio,
        curr_ratio,
        "--"
    )
    table.add_row(
        "[magenta]Operations[/magenta]",
        "Average hunt duration (days)",
        prev_duration,
        curr_duration,
        trend_signal(current.avg_duration_days, previous.avg_duration_days if previous else None)
    )

    # Add caption/footer
    table.caption = "[dim]Legend: ↑ Up / → flat / ↓ Down\nLead with outputs for the boardroom. Keep operations for your own team.[/dim]"

    return table
