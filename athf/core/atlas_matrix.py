"""MITRE ATLAS reference data (adversarial threats to AI systems).

Sits beside :mod:`athf.core.attack_matrix` and never touches ATT&CK data.
ATLAS describes attacks *on* AI systems; hunts that merely *use* AI as an
analysis method should not be tagged with ATLAS IDs.

Data source: the v6 YAML published in ``mitre-atlas/atlas-data`` at
``dist/v6/ATLAS-YYYY.MM.yaml``. The legacy ``dist/ATLAS.yaml`` is deprecated
and frozen at 5.6.0, so this module refuses anything that is not format 6.x.
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

import yaml

logger = logging.getLogger(__name__)

ATLAS_TECHNIQUE_RE = re.compile(r"^AML\.T\d{4}(?:\.\d{3})?$")
ATLAS_TACTIC_RE = re.compile(r"^AML\.TA\d{4}$")
SUPPORTED_FORMAT_MAJOR = "6"


class AtlasTacticInfo(TypedDict):
    id: str
    name: str


class AtlasTechniqueInfo(TypedDict, total=False):
    id: str
    name: str
    description: str
    tactics: List[str]
    platforms: List[str]
    maturity: str
    is_subtechnique: bool
    parent_id: Optional[str]


class AtlasFormatError(ValueError):
    """Raised when ATLAS data is not in a supported shape."""


# Snapshot of ATLAS 2026.10 tactics. Used only when no data is cached, so
# tactic names still resolve; technique lookups need `athf atlas update`.
_FALLBACK_TACTICS: Dict[str, str] = {
    "AML.TA0000": "AI Model Access",
    "AML.TA0001": "AI Attack Adaptation",
    "AML.TA0002": "Reconnaissance",
    "AML.TA0003": "Resource Development",
    "AML.TA0004": "Initial Access",
    "AML.TA0005": "Execution",
    "AML.TA0006": "Persistence",
    "AML.TA0007": "Defense Evasion",
    "AML.TA0008": "Discovery",
    "AML.TA0009": "Collection",
    "AML.TA0010": "Exfiltration",
    "AML.TA0011": "Impact",
    "AML.TA0012": "Privilege Escalation",
    "AML.TA0013": "Credential Access",
    "AML.TA0014": "Command and Control",
    "AML.TA0015": "Lateral Movement",
}


def check_format_version(data: Any) -> None:
    """Raise :class:`AtlasFormatError` unless ``data`` is a v6 ATLAS document."""
    if not isinstance(data, dict):
        raise AtlasFormatError("ATLAS data is not a mapping")
    raw = data.get("format-version")
    major = str(raw).split(".", 1)[0] if raw else ""
    if major != SUPPORTED_FORMAT_MAJOR:
        raise AtlasFormatError(
            f"Unsupported ATLAS format-version {raw!r}; expected {SUPPORTED_FORMAT_MAJOR}.x. "
            "Run 'athf atlas update --force'."
        )
    if not isinstance(data.get("tactics"), dict) or not isinstance(data.get("techniques"), dict):
        raise AtlasFormatError("ATLAS data is missing the tactics/techniques maps")


class AtlasDataProvider(ABC):
    """Abstract source of ATLAS tactic and technique data."""

    @abstractmethod
    def get_tactics(self) -> Dict[str, AtlasTacticInfo]:
        """Return all known ATLAS tactics."""

    @abstractmethod
    def get_technique_by_id(self, technique_id: str) -> Optional[AtlasTechniqueInfo]:
        """Return technique metadata or None if not found."""

    @abstractmethod
    def get_techniques_for_tactic(self, tactic_id: str) -> List[AtlasTechniqueInfo]:
        """Return all techniques that achieve a given tactic."""

    @abstractmethod
    def get_sub_techniques(self, parent_id: str) -> List[AtlasTechniqueInfo]:
        """Return all sub-techniques under a parent technique."""

    @abstractmethod
    def get_version(self) -> str:
        """Return provider version and data source information."""

    @abstractmethod
    def is_live(self) -> bool:
        """True when backed by downloaded ATLAS data (technique lookups work)."""


class AtlasFallbackProvider(AtlasDataProvider):
    """Tactics only. Technique lookups return nothing."""

    def get_tactics(self) -> Dict[str, AtlasTacticInfo]:
        return {tid: AtlasTacticInfo(id=tid, name=name) for tid, name in _FALLBACK_TACTICS.items()}

    def get_technique_by_id(self, technique_id: str) -> Optional[AtlasTechniqueInfo]:
        return None

    def get_techniques_for_tactic(self, tactic_id: str) -> List[AtlasTechniqueInfo]:
        return []

    def get_sub_techniques(self, parent_id: str) -> List[AtlasTechniqueInfo]:
        return []

    def get_version(self) -> str:
        return "fallback (tactics only; run 'athf atlas update')"

    def is_live(self) -> bool:
        return False


class AtlasYamlProvider(AtlasDataProvider):
    """Provider backed by a cached ATLAS v6 YAML file. Loads lazily, once."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._tactics: Optional[Dict[str, AtlasTacticInfo]] = None
        self._techniques: Dict[str, AtlasTechniqueInfo] = {}
        self._version = ""

    def _ensure_loaded(self) -> None:
        if self._tactics is not None:
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        check_format_version(data)

        relationships = data.get("relationships") or {}
        if not isinstance(relationships, dict):
            relationships = {}
        tactics: Dict[str, AtlasTacticInfo] = {}
        for tid, raw in data["tactics"].items():
            if ATLAS_TACTIC_RE.match(str(tid)) and isinstance(raw, dict):
                tactics[tid] = AtlasTacticInfo(id=tid, name=str(raw.get("name", tid)))

        techniques: Dict[str, AtlasTechniqueInfo] = {}
        for tid, raw in data["techniques"].items():
            if not ATLAS_TECHNIQUE_RE.match(str(tid)) or not isinstance(raw, dict):
                continue
            rels = relationships.get(tid) or {}
            if not isinstance(rels, dict):
                rels = {}
            achieves_raw = rels.get("achieves") or []
            if not isinstance(achieves_raw, list):
                achieves_raw = []
            achieved = [
                str(r.get("target"))
                for r in achieves_raw
                if isinstance(r, dict) and ATLAS_TACTIC_RE.match(str(r.get("target", "")))
            ]
            is_sub = tid.count(".") == 2
            techniques[tid] = AtlasTechniqueInfo(
                id=tid,
                name=str(raw.get("name", "")),
                description=str(raw.get("description", "")),
                tactics=achieved,
                platforms=list(raw.get("platforms") or []),
                maturity=str(raw.get("maturity", "")),
                is_subtechnique=is_sub,
                # The ID grammar guarantees the parent; no need to trust `specializes`.
                parent_id=tid.rsplit(".", 1)[0] if is_sub else None,
            )

        collection = data.get("collection") or {}
        if not isinstance(collection, dict):
            collection = {}
        self._version = f"{collection.get('version', 'unknown')} (format {data['format-version']})"
        self._techniques = techniques
        self._tactics = tactics

    def get_tactics(self) -> Dict[str, AtlasTacticInfo]:
        self._ensure_loaded()
        assert self._tactics is not None
        return self._tactics

    def get_technique_by_id(self, technique_id: str) -> Optional[AtlasTechniqueInfo]:
        self._ensure_loaded()
        return self._techniques.get(technique_id)

    def get_techniques_for_tactic(self, tactic_id: str) -> List[AtlasTechniqueInfo]:
        self._ensure_loaded()
        return sorted(
            (t for t in self._techniques.values() if tactic_id in t.get("tactics", [])),
            key=lambda t: t["id"],
        )

    def get_sub_techniques(self, parent_id: str) -> List[AtlasTechniqueInfo]:
        self._ensure_loaded()
        return sorted(
            (t for t in self._techniques.values() if t.get("parent_id") == parent_id),
            key=lambda t: t["id"],
        )

    def get_version(self) -> str:
        self._ensure_loaded()
        return self._version

    def is_live(self) -> bool:
        return True


def get_atlas_cache_dir() -> Path:
    """Cache dir: $ATHF_ATLAS_CACHE, else {workspace}/.athf/atlas-data, else ~/.athf/atlas-data."""
    env_path = os.environ.get("ATHF_ATLAS_CACHE")
    if env_path:
        return Path(env_path)
    cwd = Path.cwd()
    if (cwd / ".athfconfig.yaml").exists():
        return cwd / ".athf" / "atlas-data"
    return Path.home() / ".athf" / "atlas-data"


def get_atlas_file_path() -> Path:
    return get_atlas_cache_dir() / "atlas.yaml"


_provider: Optional[AtlasDataProvider] = None


def get_atlas_provider() -> AtlasDataProvider:
    """Return the singleton provider, loading cached data eagerly.

    Eager load on purpose: a corrupt or legacy cache must degrade to the
    fallback *here*. If it raised later inside ``HuntParser.warnings()``, the
    best-effort wrapper ``hunt_file_warnings`` would swallow it and silently
    drop every other warning for that hunt too.
    """
    global _provider
    if _provider is not None:
        return _provider
    path = get_atlas_file_path()
    if path.exists():
        candidate = AtlasYamlProvider(path)
        try:
            candidate.get_tactics()
            _provider = candidate
        except Exception as exc:
            logger.warning("Ignoring unusable ATLAS cache at %s: %s", path, exc)
            _provider = AtlasFallbackProvider()
    else:
        _provider = AtlasFallbackProvider()
    return _provider


def reset_atlas_provider(provider: Optional[AtlasDataProvider] = None) -> None:
    """Replace the singleton (tests, or after `athf atlas update`). None re-resolves."""
    global _provider
    _provider = provider
