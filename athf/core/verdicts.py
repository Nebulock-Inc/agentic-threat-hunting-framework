"""The verdict ladder: shared vocabulary for hunt outcomes.

Five verdicts replace the old ``TP`` / ``FP`` / ``inconclusive`` triple, each
carrying a gate that says what it takes to claim it:

- ``confirmed`` — telemetry evidence **plus** independent confirmation from
  outside the log corpus (controlled reproduction, host forensics, or
  configuration review).
- ``suspected`` — telemetry evidence only. The ceiling when you cannot
  independently confirm.
- ``attempted_not_vulnerable`` — attack behavior observed and the named
  control demonstrably held.
- ``benign`` — explained as legitimate activity.
- ``inconclusive`` — insufficient telemetry to decide.

Telemetry alone never reaches ``confirmed``. See
``athf/data/hunts/FORMAT_GUIDELINES.md`` for the field reference.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional, Tuple

CONFIRMED = "confirmed"
SUSPECTED = "suspected"
ATTEMPTED_NOT_VULNERABLE = "attempted_not_vulnerable"
BENIGN = "benign"
INCONCLUSIVE = "inconclusive"

VERDICTS = (
    CONFIRMED,
    SUSPECTED,
    ATTEMPTED_NOT_VULNERABLE,
    BENIGN,
    INCONCLUSIVE,
)

LEGACY_VERDICTS = ("tp", "fp")

_ALIASES = {"attempted-not-vulnerable": ATTEMPTED_NOT_VULNERABLE}

_POSITIVE = frozenset({CONFIRMED, "tp"})
_NEGATIVE = frozenset({BENIGN, "fp"})

# Which frontmatter list each verdict belongs in. ``findings`` is what you are
# reporting as malicious; ``ruled_out`` is what closed the question. Keeping them
# apart is what lets a report say "here is what we found, and here is what your
# controls stopped" instead of collapsing both into one number.
EXPECTED_LIST = {
    CONFIRMED: "findings",
    SUSPECTED: "findings",
    ATTEMPTED_NOT_VULNERABLE: "ruled_out",
    BENIGN: "ruled_out",
    INCONCLUSIVE: "ruled_out",
}

# Ways of writing "I did not actually do this" that a truthiness check would
# accept. An agent optimizing for the cheapest path past validation reaches for
# these long before it reaches for anything Python considers falsy.
_PLACEHOLDERS = frozenset(
    {
        "",
        "-",
        "--",
        "---",
        ".",
        "..",
        "...",
        "?",
        "??",
        "n/a",
        "n\\a",
        "na",
        "n.a.",
        "nil",
        "no",
        "none",
        "not applicable",
        "not available",
        "not confirmed",
        "not done",
        "null",
        "ok",
        "pending",
        "tbc",
        "tbd",
        "todo",
        "unconfirmed",
        "unknown",
        "yes",
    }
)

# Shortest string that can plausibly describe what was checked. Every legitimate
# example in the format guidelines is a full clause; this only has to be long
# enough that a token of assent cannot pass for an account.
_MIN_SUBSTANTIVE_LEN = 12

# Nouns that name the log corpus itself. Confirmation that cites one of these as
# its source is circular: the corpus is the thing being confirmed.
_CORPUS = (
    r"(?:telemetry|log(?:s|\s+data)?|quer(?:y|ies)|query\s+results?"
    r"|events?|evidence|data|above)"
)

# Ways of answering "how did you independently confirm this?" by pointing back at
# the input. An agent asked to confirm a finding reaches for the cheapest passing
# answer, and the cheapest is to cite the logs it just finished reading.
_SELF_REFERENCE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        # "see telemetry above", "see the evidence field", "see above"
        r"^(?:please\s+)?see\b",
        # Opening with a deferral is a pointer regardless of what it points at.
        r"^as\s+(?:shown|described|noted|stated|documented|detailed)\b",
        # "per the query results" — but not "per the host forensics report"
        r"^per\s+(?:the\s+)?" + _CORPUS + r"\b",
        # "same as evidence", "same as above"
        r"^same\s+as\b",
        # "confirmed by the telemetry" — the corpus cannot confirm itself
        r"\bconfirm(?:ed|s|ation)?\s+(?:by|from|in|via)\s+(?:the\s+)?" + _CORPUS + r"\b",
        # "the log data confirms it", "telemetry already confirmed this"
        r"\b" + _CORPUS + r"\s+(?:\w+\s+)?confirm(?:s|ed)?\b",
    )
)


class VerdictError(ValueError):
    """Raised when a verdict string is not part of the accepted vocabulary.

    Subclasses ``ValueError`` so callers that documented ``ValueError`` on
    their public API keep that contract.
    """


def _soften(raw: Any) -> str:
    """Lowercase / de-hyphenate without raising. Unknowns pass through."""
    if not isinstance(raw, str):
        return ""
    candidate = raw.strip().lower()
    return _ALIASES.get(candidate, candidate)


def normalize_verdict(raw: Any) -> str:
    """Return the canonical form of ``raw``, or raise :class:`VerdictError`.

    Accepts the five ladder verdicts (case-insensitive, and
    ``attempted-not-vulnerable`` for the hyphenated spelling) plus the legacy
    ``tp`` / ``fp`` values.

    Legacy ``tp`` / ``fp`` are returned lowercased but NOT remapped onto the
    ladder: those outcomes were recorded before the evidence gate existed, so
    promoting a legacy ``tp`` to ``confirmed`` would fabricate rigor nobody
    can vouch for.
    """
    if not isinstance(raw, str):
        raise VerdictError(
            "verdict must be a string; got {!r}".format(raw)
        )

    candidate = _soften(raw)
    if candidate in VERDICTS or candidate in LEGACY_VERDICTS:
        return candidate

    raise VerdictError(
        "verdict must be one of {}; got {!r}".format(
            ", ".join(VERDICTS + LEGACY_VERDICTS), raw
        )
    )


def requires_evidence(verdict: Any) -> bool:
    """Return ``True`` when the verdict is subject to the evidence gate."""
    return _soften(verdict) == CONFIRMED


def counts_as_positive(verdict: Any) -> bool:
    """Return ``True`` when the verdict participates in precision as a positive.

    ``suspected`` never passed the evidence gate, so it is deliberately
    excluded — counting it would import unverified findings into a quality
    number.
    """
    return _soften(verdict) in _POSITIVE


def counts_as_negative(verdict: Any) -> bool:
    """Return ``True`` when the verdict participates in precision as a negative.

    ``attempted_not_vulnerable`` is excluded: the behavior really was there,
    so the hunt was right. Scoring a working control as a false positive would
    punish hunters for reporting blocked attacks.
    """
    return _soften(verdict) in _NEGATIVE


def is_substantive(value: Any) -> bool:
    """Return ``True`` when ``value`` is prose that accounts for something.

    Guards the evidence gate and the control-naming rule. Non-strings are
    rejected outright: ``confirmation: true`` asserts that confirmation happened
    without saying what was done, which is exactly the claim the gate exists to
    refuse. Placeholders and single tokens of assent are rejected for the same
    reason — the gate asks what you checked, not whether you'd like to pass.
    """
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if candidate.lower().rstrip(".") in _PLACEHOLDERS:
        return False
    return len(candidate) >= _MIN_SUBSTANTIVE_LEN


def is_self_referential(value: Any) -> bool:
    """Return ``True`` when ``value`` cites the log corpus as its own confirmation.

    Applies to ``confirmation`` only. Mentioning telemetry is fine — "forensic
    image shows the crontab entry matching the process_activity log" is exactly
    the corroboration the ladder wants — so this anchors on the phrasings that
    *defer* to the corpus rather than scanning for telemetry words anywhere.
    """
    if not isinstance(value, str):
        return False
    candidate = " ".join(value.split())
    return any(pattern.search(candidate) for pattern in _SELF_REFERENCE_PATTERNS)


def tally_frontmatter_verdicts(
    frontmatter: Mapping[str, Any]
) -> Optional[Dict[str, int]]:
    """Tally verdicts across the ``findings`` / ``ruled_out`` frontmatter lists.

    Returns ``None`` when neither key holds a non-empty list, letting callers
    fall back to legacy counters. Malformed entries are skipped rather than
    raised: ``athf hunt validate`` is where a hunter is told their file is
    wrong, so reporting must survive anything already on disk.
    """
    found = False
    counts = {verdict: 0 for verdict in VERDICTS}

    for key in ("findings", "ruled_out"):
        value = frontmatter.get(key)
        if not isinstance(value, list):
            continue
        found = found or bool(value)
        for entry in value:
            if not isinstance(entry, Mapping):
                continue
            candidate = _soften(entry.get("verdict"))
            # A verdict is only counted from the list it belongs in. Otherwise a
            # `confirmed` entry parked in ``ruled_out`` would be credited as a
            # positive, which is the report separation collapsing quietly —
            # `athf hunt validate` rejects that shape, so drop it here.
            if EXPECTED_LIST.get(candidate) == key:
                counts[candidate] += 1

    return counts if found else None


def precision_pair(counts: Mapping[str, int]) -> Tuple[int, int]:
    """Return ``(positives, negatives)`` for a per-verdict count mapping."""
    positives = sum(n for v, n in counts.items() if counts_as_positive(v))
    negatives = sum(n for v, n in counts.items() if counts_as_negative(v))
    return positives, negatives


__all__ = [
    "VERDICTS",
    "LEGACY_VERDICTS",
    "CONFIRMED",
    "SUSPECTED",
    "ATTEMPTED_NOT_VULNERABLE",
    "BENIGN",
    "INCONCLUSIVE",
    "VerdictError",
    "normalize_verdict",
    "requires_evidence",
    "counts_as_positive",
    "counts_as_negative",
    "EXPECTED_LIST",
    "is_substantive",
    "is_self_referential",
    "tally_frontmatter_verdicts",
    "precision_pair",
]
