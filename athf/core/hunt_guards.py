"""Fool-proof guards for common user mistakes."""

from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def find_hunt_directory() -> Optional[Path]:
    """Find hunt directory, checking multiple locations.

    Returns:
        Path to hunt directory, or None if not found
    """
    import os

    candidates = []

    # Environment variable override (highest priority)
    if env_dir := os.getenv('ATHF_HUNT_DIR'):
        candidates.append(Path(env_dir))

    # Current directory (running from repo root)
    candidates.append(Path("hunts/production"))

    # Sibling repo (running from another repo in same parent)
    candidates.append(Path("../agentic-threat-hunting-framework/hunts/production"))

    # Installed package location (find where athf is installed)
    try:
        import athf
        package_dir = Path(athf.__file__).parent.parent
        candidates.append(package_dir / "hunts" / "production")
    except (ImportError, AttributeError):
        pass

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def parse_user_date(date_str: str) -> Optional[date]:
    """Parse user date string, trying multiple formats.

    Tries: ISO (2024-01-15), US (01/15/2024), EU (15/01/2024), compact (20240115)

    Args:
        date_str: Date string from user input

    Returns:
        Parsed date or None if invalid
    """
    formats = [
        "%Y-%m-%d",      # 2024-01-15 (ISO)
        "%m/%d/%Y",      # 01/15/2024 (US)
        "%d/%m/%Y",      # 15/01/2024 (EU)
        "%Y%m%d",        # 20240115 (compact)
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def validate_date_range(start: date, end: date) -> Tuple[bool, Optional[str]]:
    """Validate date range makes sense.

    Args:
        start: Start date
        end: End date

    Returns:
        (is_valid, error_message or warning)
    """
    if start > end:
        return False, f"Start date ({start}) is after end date ({end})"

    # Warn if range is very large
    delta = (end - start).days
    if delta > 730:  # > 2 years
        return True, f"Date range is {delta} days ({delta/365:.1f} years) - might be slow"

    return True, None


def check_period_compatibility(period: str, compare: str) -> Tuple[bool, Optional[str]]:
    """Check if periods are compatible for comparison.

    Args:
        period: Current period (e.g., "2024-Q4" or "2024")
        compare: Comparison period (e.g., "2024-Q3")

    Returns:
        (is_compatible, error_message)
    """
    curr_is_quarter = '-Q' in period
    comp_is_quarter = '-Q' in compare

    if curr_is_quarter != comp_is_quarter:
        return False, "Cannot compare quarter to full year. Compare like periods (Q to Q, or year to year)"

    return True, None


def suggest_date_range(hunts: List[Dict]) -> Optional[Tuple[str, date, date]]:
    """Suggest a date range based on available hunt data.

    Args:
        hunts: List of hunt metadata dictionaries

    Returns:
        Tuple of (suggested_period, earliest_date, latest_date) or None
    """
    from athf.core.hunt_metrics import _parse_date_field

    parsed_dates = [_parse_date_field(h.get('date')) for h in hunts]
    # Type narrow: filter out None values to get List[date]
    dates: List[date] = [d for d in parsed_dates if d is not None]

    if not dates:
        return None

    earliest: date = min(dates)
    latest: date = max(dates)

    # Suggest most recent quarter
    quarter = (latest.month - 1) // 3 + 1
    suggested_period = f"{latest.year}-Q{quarter}"

    return (suggested_period, earliest, latest)


def analyze_hunt_statuses(hunts: List[Dict]) -> Dict[str, int]:
    """Count hunts by status.

    Args:
        hunts: List of hunt metadata dictionaries

    Returns:
        Dictionary of {status: count}
    """
    statuses: Dict[str, int] = defaultdict(int)
    for h in hunts:
        status = h.get('status', 'unknown')
        statuses[status] += 1

    return dict(statuses)


def check_negative_durations(hunts: List[Dict]) -> List[Tuple[str, int]]:
    """Find hunts with negative durations (data errors).

    Args:
        hunts: List of completed hunt metadata

    Returns:
        List of (hunt_id, negative_days) tuples
    """
    from athf.core.hunt_metrics import _parse_date_field

    negative = []
    for h in hunts:
        if h.get('status') != 'completed':
            continue

        started = _parse_date_field(h.get('date'))
        finished = _parse_date_field(h.get('completed_date'))

        if started and finished:
            delta = (finished - started).days
            if delta < 0:
                negative.append((h.get('hunt_id', 'Unknown'), delta))

    return negative
