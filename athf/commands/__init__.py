"""ATHF CLI commands (base commands only)."""

from athf.commands.context import context
from athf.commands.env import env
from athf.commands.hunt import hunt
from athf.commands.init import init
from athf.commands.investigate import investigate
from athf.commands.research import research
from athf.commands.similar import similar

# Optional: Splunk integration (requires requests package)
try:
    from athf.commands.splunk import splunk
except ImportError:
    splunk = None  # type: ignore[assignment]

__all__ = [
    "init",
    "hunt",
    "investigate",
    "research",
    "context",
    "similar",
    "env",
    "splunk",
]
