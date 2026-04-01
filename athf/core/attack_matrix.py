"""MITRE ATT&CK Matrix reference data with optional STIX integration.

This module provides ATT&CK tactic and technique data through a provider
abstraction. When mitreattack-python is installed, it uses live STIX data
(835+ techniques with full metadata). Otherwise, it falls back to a
hardcoded dictionary of 14 tactics with approximate counts.

Backward compatible: ATTACK_TACTICS, TOTAL_TECHNIQUES, and all existing
functions continue to work identically via module-level __getattr__.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

class TacticInfo(TypedDict):
    """Type definition for tactic information."""

    name: str
    technique_count: int
    order: int


class TechniqueInfo(TypedDict, total=False):
    """Type definition for technique metadata from STIX data."""

    id: str
    name: str
    description: str
    platforms: List[str]
    data_sources: List[str]
    tactic_shortnames: List[str]
    is_subtechnique: bool
    parent_id: Optional[str]
    url: str


# ---------------------------------------------------------------------------
# Fallback data (MITRE ATT&CK Enterprise Matrix v14, January 2024)
# ---------------------------------------------------------------------------

_FALLBACK_TACTICS: Dict[str, TacticInfo] = {
    "reconnaissance": {
        "name": "Reconnaissance",
        "technique_count": 10,
        "order": 1,
    },
    "resource-development": {
        "name": "Resource Development",
        "technique_count": 7,
        "order": 2,
    },
    "initial-access": {
        "name": "Initial Access",
        "technique_count": 9,
        "order": 3,
    },
    "execution": {
        "name": "Execution",
        "technique_count": 12,
        "order": 4,
    },
    "persistence": {
        "name": "Persistence",
        "technique_count": 19,
        "order": 5,
    },
    "privilege-escalation": {
        "name": "Privilege Escalation",
        "technique_count": 13,
        "order": 6,
    },
    "defense-evasion": {
        "name": "Defense Evasion",
        "technique_count": 42,
        "order": 7,
    },
    "credential-access": {
        "name": "Credential Access",
        "technique_count": 15,
        "order": 8,
    },
    "discovery": {
        "name": "Discovery",
        "technique_count": 30,
        "order": 9,
    },
    "lateral-movement": {
        "name": "Lateral Movement",
        "technique_count": 9,
        "order": 10,
    },
    "collection": {
        "name": "Collection",
        "technique_count": 17,
        "order": 11,
    },
    "command-and-control": {
        "name": "Command and Control",
        "technique_count": 16,
        "order": 12,
    },
    "exfiltration": {
        "name": "Exfiltration",
        "technique_count": 9,
        "order": 13,
    },
    "impact": {
        "name": "Impact",
        "technique_count": 13,
        "order": 14,
    },
}


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

class AttackDataProvider(ABC):
    """Abstract base class for ATT&CK data providers."""

    @abstractmethod
    def get_tactics(self) -> Dict[str, TacticInfo]:
        """Return all tactics as {shortname: TacticInfo}."""

    @abstractmethod
    def get_total_techniques(self) -> int:
        """Return the total number of techniques across all tactics."""

    @abstractmethod
    def get_sorted_tactic_keys(self) -> List[str]:
        """Return tactic keys sorted by ATT&CK matrix order."""

    @abstractmethod
    def get_technique_by_id(self, technique_id: str) -> Optional[TechniqueInfo]:
        """Look up a technique by its ATT&CK ID (e.g., 'T1003.001')."""

    @abstractmethod
    def get_techniques_for_tactic(self, tactic_key: str) -> List[TechniqueInfo]:
        """Return all techniques mapped to a given tactic."""

    @abstractmethod
    def get_sub_techniques(self, parent_id: str) -> List[TechniqueInfo]:
        """Return sub-techniques for a parent technique ID (e.g., 'T1003')."""

    @abstractmethod
    def get_version(self) -> str:
        """Return the ATT&CK version string."""

    @abstractmethod
    def is_stix(self) -> bool:
        """Return True if backed by live STIX data."""


# ---------------------------------------------------------------------------
# Fallback provider (hardcoded data)
# ---------------------------------------------------------------------------

class FallbackProvider(AttackDataProvider):
    """Provider backed by the hardcoded v14 tactic dictionary."""

    def get_tactics(self) -> Dict[str, TacticInfo]:
        return _FALLBACK_TACTICS

    def get_total_techniques(self) -> int:
        return sum(t["technique_count"] for t in _FALLBACK_TACTICS.values())

    def get_sorted_tactic_keys(self) -> List[str]:
        return sorted(_FALLBACK_TACTICS.keys(), key=lambda k: _FALLBACK_TACTICS[k]["order"])

    def get_technique_by_id(self, technique_id: str) -> Optional[TechniqueInfo]:
        return None

    def get_techniques_for_tactic(self, tactic_key: str) -> List[TechniqueInfo]:
        return []

    def get_sub_techniques(self, parent_id: str) -> List[TechniqueInfo]:
        return []

    def get_version(self) -> str:
        return "v14 (hardcoded fallback)"

    def is_stix(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# STIX provider (mitreattack-python)
# ---------------------------------------------------------------------------

def _get_stix_cache_dir() -> Path:
    """Return the STIX data cache directory.

    Checks (in order):
    1. ATHF_STIX_CACHE env var
    2. {workspace}/.athf/stix-data/ if .athfconfig.yaml exists
    3. ~/.athf/stix-data/ (global default)
    """
    env_path = os.environ.get("ATHF_STIX_CACHE")
    if env_path:
        return Path(env_path)

    # Check for workspace-local cache
    cwd = Path.cwd()
    if (cwd / ".athfconfig.yaml").exists():
        return cwd / ".athf" / "stix-data"

    # Global default
    return Path.home() / ".athf" / "stix-data"


def _get_stix_file_path() -> Path:
    """Return the expected path for the STIX JSON file."""
    return _get_stix_cache_dir() / "enterprise-attack.json"


class StixProvider(AttackDataProvider):
    """Provider backed by STIX data via mitreattack-python.

    Lazily loads data on first access and caches results in memory.
    """

    def __init__(self, stix_path: Optional[Path] = None):
        self._stix_path = stix_path or _get_stix_file_path()
        self._attack_data: Any = None  # MitreAttackData instance
        self._tactics_cache: Optional[Dict[str, TacticInfo]] = None
        self._technique_cache: Optional[Dict[str, TechniqueInfo]] = None
        self._tactic_techniques_cache: Dict[str, List[TechniqueInfo]] = {}

    def _ensure_loaded(self) -> None:
        """Lazily load STIX data on first access."""
        if self._attack_data is not None:
            return

        from mitreattack.stix20 import MitreAttackData

        if not self._stix_path.exists():
            raise FileNotFoundError(
                f"STIX data not found at {self._stix_path}. "
                "Run 'athf attack update' to download it."
            )

        logger.debug("Loading STIX data from %s", self._stix_path)
        self._attack_data = MitreAttackData(str(self._stix_path))

    def _build_tactics(self) -> Dict[str, TacticInfo]:
        """Build tactic dictionary from STIX data."""
        self._ensure_loaded()

        tactics: Dict[str, TacticInfo] = {}
        stix_tactics = self._attack_data.get_tactics(remove_revoked_deprecated=True)

        # Sort by kill chain order (x_mitre_shortname field maps to order)
        tactic_order = [
            "reconnaissance", "resource-development", "initial-access",
            "execution", "persistence", "privilege-escalation",
            "defense-evasion", "credential-access", "discovery",
            "lateral-movement", "collection", "command-and-control",
            "exfiltration", "impact",
        ]
        order_map = {k: i + 1 for i, k in enumerate(tactic_order)}

        for stix_tactic in stix_tactics:
            shortname = stix_tactic.get("x_mitre_shortname", "")
            if not shortname:
                continue

            # Count techniques for this tactic
            techniques = self._attack_data.get_techniques_by_tactic(
                stix_tactic["id"], "enterprise-attack", remove_revoked_deprecated=True
            )

            tactics[shortname] = TacticInfo(
                name=stix_tactic["name"],
                technique_count=len(techniques),
                order=order_map.get(shortname, 99),
            )

        return tactics

    def _build_technique_index(self) -> Dict[str, TechniqueInfo]:
        """Build technique lookup index from STIX data."""
        self._ensure_loaded()

        index: Dict[str, TechniqueInfo] = {}
        techniques = self._attack_data.get_techniques(remove_revoked_deprecated=True)

        for tech in techniques:
            ext_refs = tech.get("external_references", [])
            attack_id = ""
            url = ""
            for ref in ext_refs:
                if ref.get("source_name") == "mitre-attack":
                    attack_id = ref.get("external_id", "")
                    url = ref.get("url", "")
                    break

            if not attack_id:
                continue

            is_sub = tech.get("x_mitre_is_subtechnique", False)
            parent_id = None
            if is_sub and "." in attack_id:
                parent_id = attack_id.split(".")[0]

            # Extract tactic shortnames from kill chain phases
            tactic_shortnames: List[str] = []
            for phase in tech.get("kill_chain_phases", []):
                if phase.get("kill_chain_name") == "mitre-attack":
                    tactic_shortnames.append(phase["phase_name"])

            # Extract data sources
            data_sources: List[str] = tech.get("x_mitre_data_sources", [])

            index[attack_id] = TechniqueInfo(
                id=attack_id,
                name=tech.get("name", ""),
                description=tech.get("description", "")[:500],
                platforms=tech.get("x_mitre_platforms", []),
                data_sources=data_sources if data_sources else [],
                tactic_shortnames=tactic_shortnames,
                is_subtechnique=is_sub,
                parent_id=parent_id,
                url=url,
            )

        return index

    def get_tactics(self) -> Dict[str, TacticInfo]:
        if self._tactics_cache is None:
            self._tactics_cache = self._build_tactics()
        return self._tactics_cache

    def get_total_techniques(self) -> int:
        return sum(t["technique_count"] for t in self.get_tactics().values())

    def get_sorted_tactic_keys(self) -> List[str]:
        tactics = self.get_tactics()
        return sorted(tactics.keys(), key=lambda k: tactics[k]["order"])

    def get_technique_by_id(self, technique_id: str) -> Optional[TechniqueInfo]:
        if self._technique_cache is None:
            self._technique_cache = self._build_technique_index()
        return self._technique_cache.get(technique_id.upper())

    def get_techniques_for_tactic(self, tactic_key: str) -> List[TechniqueInfo]:
        if tactic_key in self._tactic_techniques_cache:
            return self._tactic_techniques_cache[tactic_key]

        if self._technique_cache is None:
            self._technique_cache = self._build_technique_index()

        result = [
            t for t in self._technique_cache.values()
            if tactic_key in t.get("tactic_shortnames", [])
        ]
        result.sort(key=lambda t: t.get("id", ""))
        self._tactic_techniques_cache[tactic_key] = result
        return result

    def get_sub_techniques(self, parent_id: str) -> List[TechniqueInfo]:
        if self._technique_cache is None:
            self._technique_cache = self._build_technique_index()

        parent = parent_id.upper()
        return sorted(
            [t for t in self._technique_cache.values() if t.get("parent_id") == parent],
            key=lambda t: t.get("id", ""),
        )

    def get_version(self) -> str:
        self._ensure_loaded()
        # Try to extract version from STIX bundle
        try:
            with open(str(self._stix_path), "r") as f:
                bundle = json.load(f)
            for obj in bundle.get("objects", []):
                if obj.get("type") == "x-mitre-collection":
                    version = obj.get("x_mitre_version", "")
                    if version:
                        return f"v{version} (STIX)"
        except Exception:
            pass

        # Fallback: use file modification time
        mtime = self._stix_path.stat().st_mtime
        age_days = int((time.time() - mtime) / 86400)
        return f"STIX (downloaded {age_days}d ago)"

    def is_stix(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Provider singleton
# ---------------------------------------------------------------------------

_provider: Optional[AttackDataProvider] = None


def _get_provider() -> AttackDataProvider:
    """Get or create the singleton ATT&CK data provider.

    Auto-selects StixProvider if mitreattack-python is installed AND
    cached STIX data exists, otherwise falls back to FallbackProvider.
    """
    global _provider
    if _provider is not None:
        return _provider

    try:
        import mitreattack.stix20  # noqa: F401
        stix_path = _get_stix_file_path()
        if stix_path.exists():
            _provider = StixProvider(stix_path)
            logger.debug("Using STIX provider: %s", stix_path)
        else:
            logger.debug(
                "mitreattack-python installed but no STIX data at %s. "
                "Run 'athf attack update' to download. Using fallback.",
                stix_path,
            )
            _provider = FallbackProvider()
    except ImportError:
        logger.debug("mitreattack-python not installed. Using fallback provider.")
        _provider = FallbackProvider()

    return _provider


def reset_provider(provider: Optional[AttackDataProvider] = None) -> None:
    """Reset the provider singleton (for testing or after update).

    Args:
        provider: Optional specific provider to use. If None, auto-selects.
    """
    global _provider
    _provider = provider


# ---------------------------------------------------------------------------
# Original public API (backward compatible)
# ---------------------------------------------------------------------------

def get_tactic_display_name(tactic_key: str) -> str:
    """Get the display name for a tactic key.

    Args:
        tactic_key: Tactic key (e.g., "credential-access")

    Returns:
        Display name (e.g., "Credential Access")
    """
    tactics = _get_provider().get_tactics()
    if tactic_key in tactics:
        return tactics[tactic_key]["name"]
    return tactic_key.replace("-", " ").title()


def get_tactic_technique_count(tactic_key: str) -> int:
    """Get the total technique count for a tactic.

    Args:
        tactic_key: Tactic key (e.g., "credential-access")

    Returns:
        Total technique count for the tactic
    """
    tactics = _get_provider().get_tactics()
    if tactic_key in tactics:
        return tactics[tactic_key]["technique_count"]
    return 0


def get_sorted_tactics() -> List[str]:
    """Get all tactic keys sorted by ATT&CK matrix order.

    Returns:
        List of tactic keys in matrix order
    """
    return _get_provider().get_sorted_tactic_keys()


# ---------------------------------------------------------------------------
# New public API
# ---------------------------------------------------------------------------

def get_technique(technique_id: str) -> Optional[TechniqueInfo]:
    """Look up a technique by ATT&CK ID.

    Args:
        technique_id: ATT&CK technique ID (e.g., "T1003.001")

    Returns:
        TechniqueInfo dict or None if not found / using fallback provider.
    """
    return _get_provider().get_technique_by_id(technique_id)


def get_techniques_for_tactic(tactic_key: str) -> List[TechniqueInfo]:
    """Get all techniques mapped to a tactic.

    Args:
        tactic_key: Tactic shortname (e.g., "credential-access")

    Returns:
        List of TechniqueInfo dicts. Empty if using fallback provider.
    """
    return _get_provider().get_techniques_for_tactic(tactic_key)


def get_sub_techniques(parent_id: str) -> List[TechniqueInfo]:
    """Get sub-techniques for a parent technique.

    Args:
        parent_id: Parent technique ID (e.g., "T1003")

    Returns:
        List of TechniqueInfo dicts. Empty if using fallback provider.
    """
    return _get_provider().get_sub_techniques(parent_id)


def get_attack_version() -> str:
    """Get the ATT&CK data version string."""
    return _get_provider().get_version()


def is_using_stix() -> bool:
    """Check if using live STIX data."""
    return _get_provider().is_stix()


# ---------------------------------------------------------------------------
# Module-level __getattr__ (PEP 562) for backward compatibility
# ---------------------------------------------------------------------------

def __getattr__(name: str) -> Any:
    """Support 'from athf.core.attack_matrix import ATTACK_TACTICS'."""
    if name == "ATTACK_TACTICS":
        return _get_provider().get_tactics()
    if name == "TOTAL_TECHNIQUES":
        return _get_provider().get_total_techniques()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
