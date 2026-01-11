"""ATHF reference data and templates."""

import sys
from pathlib import Path

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files  # type: ignore[import-not-found,no-redef]


def get_data_path() -> Path:
    """Get the path to ATHF data directory.

    Returns:
        Path to the athf/data directory containing templates, knowledge,
        prompts, hunts, docs, and integrations.
    """
    return Path(str(files("athf.data")))
