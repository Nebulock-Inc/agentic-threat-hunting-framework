"""Hunt file loader with caching for performance.

Caches parsed hunt metadata for 5 minutes to avoid repeated filesystem scans.
"""

import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from athf.core.hunt_metrics import parse_hunt_frontmatter


class HuntLoader:
    """Load and cache hunt file metadata."""

    def __init__(self, hunt_dir: Path, cache_ttl_seconds: int = 300):
        """Initialize loader.

        Args:
            hunt_dir: Directory containing hunt files
            cache_ttl_seconds: Cache time-to-live in seconds (default 5 minutes)
        """
        self.hunt_dir = hunt_dir
        self.cache_ttl = cache_ttl_seconds
        self._cache: Optional[List[Dict]] = None
        self._cache_time: Optional[float] = None
        self._lock = threading.RLock()

    def load_all(self, force_refresh: bool = False) -> List[Dict]:
        """Load all hunt files, using cache if available.

        Args:
            force_refresh: If True, bypass cache and reload from disk

        Returns:
            List of hunt metadata dictionaries (copy of cached data)
        """
        with self._lock:
            # Check if cache is valid
            if not force_refresh and self._is_cache_valid() and self._cache is not None:
                return self._cache.copy()

            # Scan filesystem
            hunts = []
            for hunt_file in self.hunt_dir.rglob("H-*.md"):
                meta = parse_hunt_frontmatter(hunt_file)
                if meta:
                    hunts.append(meta)

            # Update cache
            self._cache = hunts
            self._cache_time = time.time()

            return hunts.copy()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._cache is None or self._cache_time is None:
            return False

        age = time.time() - self._cache_time
        return age < self.cache_ttl

    def clear_cache(self) -> None:
        """Clear the cache to force next load from disk."""
        self._cache = None
        self._cache_time = None
