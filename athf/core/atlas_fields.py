"""Validation rules for the optional ATLAS front-matter fields.

``techniques`` stays ATT&CK-only; ATLAS IDs live in ``atlas_techniques`` and
``atlas_tactics``. Malformed IDs are errors. IDs that are well-formed but
absent from the cached data are warnings, because the cache may be stale.
"""

import re
from typing import Any, Dict, List, Optional

from athf.core.atlas_matrix import ATLAS_TACTIC_RE, ATLAS_TECHNIQUE_RE, AtlasDataProvider, get_atlas_provider

ATTACK_TECHNIQUE_RE = re.compile(r"^T\d{4}(?:\.\d{3})?\Z")

TECHNIQUES_KEY = "atlas_techniques"
TACTICS_KEY = "atlas_tactics"


def _list_field(frontmatter: Dict[str, Any], key: str, errors: List[str]) -> List[Any]:
    raw = frontmatter.get(key)
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.append(f"{key} must be a list; got {type(raw).__name__}")
        return []
    return raw


def _valid_strings(frontmatter: Dict[str, Any], key: str, pattern: "re.Pattern[str]") -> List[str]:
    raw = frontmatter.get(key)
    if not isinstance(raw, list):
        return []
    return [v for v in raw if isinstance(v, str) and pattern.match(v)]


def atlas_field_errors(frontmatter: Optional[Dict[str, Any]]) -> List[str]:
    """Structural errors in the ATLAS fields. Empty when absent or valid."""
    if not isinstance(frontmatter, dict):
        return []
    errors: List[str] = []

    for index, value in enumerate(_list_field(frontmatter, TECHNIQUES_KEY, errors)):
        where = f"{TECHNIQUES_KEY}[{index}]"
        if not isinstance(value, str):
            errors.append(f"{where} must be a string; got {type(value).__name__}")
        elif ATTACK_TECHNIQUE_RE.match(value):
            errors.append(f"{where} is an ATT&CK ID ({value}); move it to techniques")
        elif not ATLAS_TECHNIQUE_RE.match(value):
            errors.append(f"{where} has invalid ATLAS technique ID {value!r} (expected AML.T0000 or AML.T0000.000)")

    for index, value in enumerate(_list_field(frontmatter, TACTICS_KEY, errors)):
        where = f"{TACTICS_KEY}[{index}]"
        if not isinstance(value, str):
            errors.append(f"{where} must be a string; got {type(value).__name__}")
        elif not ATLAS_TACTIC_RE.match(value):
            errors.append(f"{where} has invalid ATLAS tactic ID {value!r} (expected AML.TA0000)")

    return errors


def _misplaced_atlas_ids(frontmatter: Dict[str, Any]) -> List[str]:
    """Check for ATLAS IDs incorrectly placed in the ATT&CK techniques field."""
    warnings: List[str] = []
    attack = frontmatter.get("techniques")
    if isinstance(attack, list):
        for value in attack:
            if isinstance(value, str) and value.startswith("AML."):
                warnings.append(
                    f"techniques contains ATLAS ID {value}; techniques is ATT&CK-only, move it to {TECHNIQUES_KEY}"
                )
    return warnings


def _unknown_id_warnings(provider: AtlasDataProvider, techniques: List[str], tactics: List[str]) -> List[str]:
    """Check if technique and tactic IDs exist in the provider's data."""
    warnings: List[str] = []
    version = provider.get_version()
    for tid in techniques:
        if provider.get_technique_by_id(tid) is None:
            warnings.append(
                f"Unknown ATLAS technique {tid} (not in ATLAS {version}); "
                "check the ID or run 'athf atlas update --force'"
            )
    known_tactics = provider.get_tactics()
    for tid in tactics:
        if tid not in known_tactics:
            warnings.append(
                f"Unknown ATLAS tactic {tid} (not in ATLAS {version}); "
                "check the ID or run 'athf atlas update --force'"
            )
    return warnings


def atlas_field_warnings(frontmatter: Optional[Dict[str, Any]]) -> List[str]:
    """Non-fatal advisories. Loads ATLAS data only if the hunt carries ATLAS IDs."""
    if not isinstance(frontmatter, dict):
        return []

    warnings = _misplaced_atlas_ids(frontmatter)

    techniques = _valid_strings(frontmatter, TECHNIQUES_KEY, ATLAS_TECHNIQUE_RE)
    tactics = _valid_strings(frontmatter, TACTICS_KEY, ATLAS_TACTIC_RE)
    if not techniques and not tactics:
        return warnings

    provider = get_atlas_provider()
    if not provider.is_live():
        return warnings  # Fallback knows no techniques; it cannot judge.

    warnings.extend(_unknown_id_warnings(provider, techniques, tactics))
    return warnings
