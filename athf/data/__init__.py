"""ATHF reference data and templates."""

from importlib.resources import files
from pathlib import Path


def get_data_path() -> Path:
    """Get the path to ATHF data directory.

    Returns:
        Path to the athf/data directory containing templates, knowledge,
        prompts, hunts, docs, and integrations.
    """
    return Path(str(files("athf.data")))
