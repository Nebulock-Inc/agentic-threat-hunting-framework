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
from typing import Any, Dict, List, Mapping, Optional, Tuple

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

# Characters that carry no meaning but move a string's first word out of reach of
# an anchored pattern. A zero-width space in front of "see telemetry above" bought
# a pass; twelve of the measured misses were nothing but a lead-in like this.
_ZERO_WIDTH = re.compile(r"[​-‏⁠﻿]")
_LEAD_IN = re.compile(r"^(?:\d+[.)]\s*|[\W_])+")

# The closing half of a wrapper. `_same as above_` kept its underscore glued to
# `above`, and an underscore is a word character, so the word boundary the pattern
# needed was never there.
_TRAIL_OUT = re.compile(r"[\W_]+$")

# Nouns that name the log corpus itself. Confirmation that cites one of these as
# its source is circular: the corpus is the thing being confirmed.
#
# Deliberately not extended. Measurement says this class is open — 18 of 18
# corpus synonyms a hunter might reach for instead ("the dataset", "the rows",
# "the index") pass untouched, and each noun added invites another. Enumeration
# raises the cost of the cheapest circular phrasing; it cannot close the gap.
# What closes it is knowing who produced the confirmation, not reading it.
_CORPUS = (
    r"(?:telemetry|log(?:s|\s+data)?|quer(?:y|ies)|query\s+results?"
    r"|events?|evidence|data|above)"
)

# Verbs for the confirmation work itself. Used to require that a deferral is
# deferring *confirmation* rather than merely containing a word like "pending".
_CONFIRMATION_WORK = (
    r"(?:confirm\w*|validat\w*|verif\w*|corroborat\w*|forensic\w*|reproduc\w*"
    r"|acquisition|acquir\w*|detonat\w*|imag(?:e|ed|ing)|triage|review\w*"
    r"|interview\w*|range\s+test)"
)

# Ways of answering "how did you independently confirm this?" by pointing back at
# the input. An agent asked to confirm a finding reaches for the cheapest passing
# answer, and the cheapest is to cite the logs it just finished reading.
#
# Every pattern requires a corpus noun. An earlier version also matched citation
# grammar on its own (`^see`, `^as documented`), which turned out to be the single
# largest source of false blocks: it rejected "As documented in the range runbook,
# we replayed the technique" — a real detonation, refused for its opening clause.
_CORPUS_CITATION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        # "see telemetry above", "see the evidence above", "see above" — but not
        # "see the attached forensic report", which points outside the corpus.
        r"\b(?:please\s+)?see\s+(?:the\s+)?" + _CORPUS + r"\b",
        # "same as evidence", "same as above"
        r"\bsame\s+as\s+(?:the\s+)?" + _CORPUS + r"\b",
        # "per the query results" — but not "per the host forensics report"
        r"\bper\s+(?:the\s+)?" + _CORPUS + r"\b",
        # "confirmed by the telemetry", "validated in the events we already have"
        r"\b(?:confirm|validat|verif|corroborat)\w*\s+(?:by|from|in|via)\s+"
        r"(?:the\s+)?" + _CORPUS + r"\b",
        # "the log data confirms it", "our telemetry confirms this". The corpus
        # noun has to be bare or take a bare determiner — "the forensic image data
        # confirms the artifact on disk" is outside work and must pass.
        r"(?:^|\b(?:the|this|that|these|those|our|my|its)\s+)" + _CORPUS
        + r"\s+(?:\w+\s+)?confirm(?:s|ed)?\b",
        # "as shown in the telemetry above", "as documented in the events listed
        # above". Citation grammar is only circular when it cites the corpus, so
        # the corpus noun has to be inside the citation itself — "as documented in
        # the range runbook, we replayed the technique" points somewhere real.
        r"^as\s+(?:shown|described|noted|stated|documented|detailed)\s+"
        r"(?:\w+\s+){0,3}?" + _CORPUS + r"\b",
    )
)

# Ways of saying "I did not do the confirmation" in the field that asserts it was
# done. Unlike citing the corpus this is honest — the verdict is simply the wrong
# one — so it earns its own reason code and its own instruction.
#
# Each pattern is narrowed to the confirmation claim rather than matching its
# vocabulary anywhere in the sentence. Unnarrowed, these rejected "recovered the
# scheduled task XML under C:\Windows\System32\Tasks\Updater" on `scheduled`, "the
# deployment tool cannot produce this argument pattern" on `cannot`, and "the role
# could not have assumed the admin role" on both — ordinary hunting prose, and the
# fastest way to teach a hunter that the gate is noise worth routing around.
_DEFERRAL_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        # "pending host forensics", "confirmation deferred to IR", "still outstanding"
        r"\b(?:pend(?:ing|s)?|await(?:ing|s)?|outstanding|deferred?|queued)\b",
        # "Planned: detonate in the range next sprint" — a plan, stated as a result
        r"^(?:planned|scheduled|to\s?do|next\s+steps?)\b",
        # "will confirm later", "not yet independently verified"
        r"\b(?:not\s+yet|yet\s+to\s+be|will\s+(?:be\s+)?confirm"
        r"|to\s+be\s+(?:confirmed|validated|verified)|follow-?up\s+required"
        r"|requires?\s+further|needs?\s+independent)\b",
        # "no independent confirmation performed", "reproduction not attempted",
        # "no out-of-band confirmation obtained" — hyphenated qualifiers count as
        # one intervening word, so the filler class allows them.
        r"\b(?:no|none|not|never|nothing)\s+(?:[\w-]+\s+){0,3}?"
        r"(?:confirm\w*|valid\w*|verif\w*|forensic\w*|reproduc\w*|review\w*"
        r"|perform\w*|happen\w*|obtain\w*|done|attempted|possible|available|recovered)\b",
        # "so this remains unconfirmed" — the negation is inside the word
        r"\b(?:remains?|still|is|are|was|were)\s+un(?:confirmed|verified|validated"
        r"|corroborated|substantiated)\b",
        # "could not validate", "unable to acquire the host" — the analyst is the
        # one who could not, not some component of the attack being described.
        r"\b(?:could\s*n[o']?t|cannot|can'?t|unable\s+to|was\s+not\s+able\s+to"
        r"|fail(?:ed|s)?\s+to|unsuccessful\s+at)\s+(?:\w+\s+){0,3}?"
        + _CONFIRMATION_WORK + r"\b",
        # "confirmation attempt failed"
        r"\b" + _CONFIRMATION_WORK + r"\s+(?:\w+\s+){0,2}?(?:fail\w*|unsuccessful)\b",
        # "assumed confirmed", "presumed malicious" — but not "assumed the admin role"
        r"\b(?:assum|presum)\w+\s+(?:\w+\s+){0,2}?"
        r"(?:confirm\w*|valid\w*|verif\w*|malicious|benign|true|compromis\w*)\b",
        # Hedges. A confirmation field is where you say what you did; "probably"
        # and "self-evident" are how you say you did nothing.
        r"\b(?:likely|probably|believed|inferred|self-?evident|obvious"
        r"|trust\s+me|reasonably\s+certain|unverified)\b",
        # "out of scope", "accepted risk", "closed without confirmation"
        r"\b(?:out\s+of\s+scope|deprioriti\w+|declined|waived|skipped"
        r"|without\s+confirmation|accepted\s+risk|not\s+worth)\b",
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


def _normalize_prose(value: str) -> str:
    """Collapse whitespace and strip decorative lead-ins.

    Markdown bullets, quote markers, list numbers, wrapping quotes and zero-width
    characters all changed which pattern could reach a string's first word without
    changing what it says. Normalizing here means the patterns describe phrasings
    rather than formatting.
    """
    candidate = " ".join(_ZERO_WIDTH.sub("", value).split())
    return _TRAIL_OUT.sub("", _LEAD_IN.sub("", candidate))


def cites_the_corpus(value: Any) -> bool:
    """Return ``True`` when ``value`` offers the log corpus as its own confirmation.

    Applies to ``confirmation`` only. Mentioning telemetry is fine — "forensic
    image shows the crontab entry matching the process_activity log" is exactly
    the corroboration the ladder wants — so this matches the phrasings that
    *defer to* the corpus, not every occurrence of a telemetry word.

    A passing result means no circular phrasing was recognized. It is not evidence
    that confirmation happened: measured against 128 deliberately circular strings
    this misses 11%, and "cross-validated by running a second query against the
    same table" is invisible to any pattern set. Reading a confirmation cannot
    establish that the work behind it occurred.
    """
    if not isinstance(value, str):
        return False
    candidate = _normalize_prose(value)
    return any(pattern.search(candidate) for pattern in _CORPUS_CITATION_PATTERNS)


def defers_confirmation(value: Any) -> bool:
    """Return ``True`` when ``value`` says the confirmation has not happened yet.

    "Pending host forensics" in a ``confirmation`` field is not a circular
    argument — it is an accurate note attached to the wrong verdict. Separated
    from :func:`cites_the_corpus` so the hunter is told to downgrade to
    ``suspected`` rather than accused of reasoning in a circle.
    """
    if not isinstance(value, str):
        return False
    return any(pattern.search(_normalize_prose(value)) for pattern in _DEFERRAL_PATTERNS)


# Reason codes returned by :func:`gate_failures`. Callers render these however
# suits them — ``athf hunt validate`` as hunter-facing messages, aggregation as
# "do not count this entry".
NOT_A_MAPPING = "not_a_mapping"
MISSING_VERDICT = "missing_verdict"
INVALID_VERDICT = "invalid_verdict"
LEGACY_VERDICT = "legacy_verdict"
MISROUTED = "misrouted"
UNSUPPORTED_CONFIRMATION = "unsupported_confirmation"
CIRCULAR_CONFIRMATION = "circular_confirmation"
DEFERRED_CONFIRMATION = "deferred_confirmation"
UNNAMED_CONTROL = "unnamed_control"
MISSING_PROVENANCE = "missing_provenance"
UNKNOWN_PRODUCER = "unknown_producer"
METHOD_EXCEEDS_CAPABILITY = "method_exceeds_capability"
CORPUS_ONLY_METHOD = "corpus_only_method"
SELF_DECLARED_CAPABILITY = "self_declared_capability"
UNATTESTED = "unattested"

# Ways of filling ``attested_by`` without naming anyone answerable. The first is
# not hypothetical: ``athf hunt new`` defaults ``--hunter`` to "AI Assistant", so
# the placeholder ships with the tool. A role, a team, or the automation itself
# cannot vouch for out-of-corpus work — only a person can.
_UNATTRIBUTABLE = frozenset(
    {
        "agent",
        "ai",
        "ai assistant",
        "assistant",
        "athf",
        "automation",
        "bot",
        "claude",
        "llm",
        "pipeline",
        "robot",
        "script",
        "system",
        "team",
        "the team",
    }
)

# Shortest string that can name a person. "Jo" is two.
_MIN_NAME_LEN = 2


def is_attributable(value: Any) -> bool:
    """Return ``True`` when ``value`` names someone who could be asked about it.

    Deliberately permissive about *shape* — "J. Halloran" and an email address
    both name a person, and a name-shaped pattern would reject real people. It
    only refuses the placeholders and role words that name nobody.
    """
    if not isinstance(value, str):
        return False
    candidate = " ".join(value.split())
    if len(candidate) < _MIN_NAME_LEN:
        return False
    folded = candidate.lower().rstrip(".")
    return folded not in _UNATTRIBUTABLE and folded not in _PLACEHOLDERS


def _provenance_failures(confirmation: Any, registry: Any) -> List[Tuple[str, Any]]:
    """Return why ``confirmation`` does not establish out-of-corpus provenance.

    Net-new ``confirmed`` requires a confirmation mapping: ``method``,
    ``produced_by``, ``attested_by``, ``detail``. Prose alone carries no producer,
    so it cannot clear this gate however well it reads — that is the point. The
    measured ceiling on reading confirmations is why the producer, not the
    sentence, decides whether ``confirmed`` is reachable.
    """
    from athf.core.provenance import CORPUS_ONLY_CAPABILITIES, SELF_DECLARATION_KEYS

    failures: List[Tuple[str, Any]] = []

    # Capability declared inside the finding is the forgeable field this gate
    # replaces. Refused rather than ignored, so nobody believes it counted.
    self_declared = [k for k in SELF_DECLARATION_KEYS if k in confirmation]
    if self_declared:
        failures.append((SELF_DECLARED_CAPABILITY, self_declared))

    producer = confirmation.get("produced_by")
    method = confirmation.get("method")

    if not is_substantive(confirmation.get("detail")):
        failures.append((UNSUPPORTED_CONFIRMATION, ["confirmation.detail"]))
    else:
        detail = confirmation["detail"]
        if cites_the_corpus(detail):
            failures.append((CIRCULAR_CONFIRMATION, detail))
        elif defers_confirmation(detail):
            failures.append((DEFERRED_CONFIRMATION, detail))

    if not is_attributable(confirmation.get("attested_by")):
        failures.append((UNATTESTED, confirmation.get("attested_by")))

    if not isinstance(method, str) or not method.strip():
        failures.append((MISSING_PROVENANCE, "confirmation.method"))
        return failures

    normalized = method.strip().lower()

    # Querying is real work and still cannot confirm: the corpus cannot
    # corroborate itself. Checked before capability so that declaring a
    # corpus-only capability never unlocks ``confirmed``.
    if normalized in CORPUS_ONLY_CAPABILITIES:
        failures.append((CORPUS_ONLY_METHOD, method))
        return failures

    if registry is None or not registry.knows(producer):
        failures.append((UNKNOWN_PRODUCER, producer))
        return failures

    if normalized not in registry.capabilities_for(producer):
        failures.append((METHOD_EXCEEDS_CAPABILITY, (producer, method)))

    return failures


def _evidence_gate_failures(
    entry: Mapping[str, Any], registry: Any = None
) -> List[Tuple[str, Any]]:
    """Return why ``entry`` does not carry independent confirmation.

    The evidence gate: telemetry alone never reaches ``confirmed``. Confirmation
    from outside the log corpus is mandatory, and it has to say what was checked —
    ``n/a`` and ``ok`` are how you spell "I didn't confirm this" while still
    satisfying a truthiness check.

    Net-new ``confirmed`` carries a confirmation *mapping* and is judged on
    provenance. A string confirmation is the pre-provenance shape: it is held to
    the prose check it was written against, and cannot reach ``confirmed``,
    because no sentence identifies who produced it.
    """
    if not is_substantive(entry.get("evidence")):
        return [(UNSUPPORTED_CONFIRMATION, ["evidence"])]

    confirmation = entry.get("confirmation")

    if isinstance(confirmation, Mapping):
        return _provenance_failures(confirmation, registry)

    if not is_substantive(confirmation):
        return [(UNSUPPORTED_CONFIRMATION, ["confirmation"])]

    # Prose confirmation. Still checked for circularity and deferral so the
    # hunter gets the specific reason, then refused for lacking provenance.
    failures: List[Tuple[str, Any]] = []
    if cites_the_corpus(confirmation):
        failures.append((CIRCULAR_CONFIRMATION, confirmation))
    elif defers_confirmation(confirmation):
        failures.append((DEFERRED_CONFIRMATION, confirmation))
    failures.append((MISSING_PROVENANCE, confirmation))
    return failures


def gate_failures(key: str, entry: Any, registry: Any = None) -> List[Tuple[str, Any]]:
    """Return the reasons ``entry`` in list ``key`` does not earn its verdict.

    The single source of truth behind both enforcement surfaces. Validation
    renders these as messages; aggregation treats a non-empty result as "do not
    count". They used to decide this separately — the tally consulted routing
    alone — so a ``confirmed`` entry whose confirmation read ``ok`` was rejected
    by validate and credited by the dashboard in the same breath.

    Only the verdicts that carry gates today are checked: ``confirmed`` needs
    substantive evidence plus non-circular confirmation, and
    ``attempted_not_vulnerable`` needs a named control. ``benign`` and
    ``inconclusive`` pass on shape alone — a known asymmetry with its own fix,
    since widening it here would silently drop existing counts.

    Each item is ``(code, detail)``. ``detail`` carries whatever the renderer
    needs: the offending value, or the list of unusable fields.
    """
    if not isinstance(entry, Mapping):
        return [(NOT_A_MAPPING, type(entry).__name__)]

    if "verdict" not in entry:
        return [(MISSING_VERDICT, None)]

    try:
        verdict = normalize_verdict(entry["verdict"])
    except VerdictError as exc:
        return [(INVALID_VERDICT, exc)]

    if verdict in LEGACY_VERDICTS:
        return [(LEGACY_VERDICT, verdict)]

    failures: List[Tuple[str, Any]] = []

    expected = EXPECTED_LIST[verdict]
    if expected != key:
        failures.append((MISROUTED, (verdict, expected)))

    if requires_evidence(verdict):
        failures.extend(_evidence_gate_failures(entry, registry))

    if verdict == ATTEMPTED_NOT_VULNERABLE and not is_substantive(entry.get("control")):
        failures.append((UNNAMED_CONTROL, entry.get("control")))

    # Capability declared at the top level of the finding, rather than inside the
    # confirmation. Same forgery, one level up.
    if requires_evidence(verdict):
        from athf.core.provenance import SELF_DECLARATION_KEYS

        stray = [k for k in SELF_DECLARATION_KEYS if k in entry]
        if stray and not any(code == SELF_DECLARED_CAPABILITY for code, _ in failures):
            failures.append((SELF_DECLARED_CAPABILITY, stray))

    return failures


def entry_fails_gate(key: str, entry: Any, registry: Any = None) -> bool:
    """Return ``True`` when ``entry`` in list ``key`` does not earn its verdict."""
    return bool(gate_failures(key, entry, registry))


def tally_frontmatter_verdicts(
    frontmatter: Mapping[str, Any], registry: Any = None
) -> Optional[Dict[str, int]]:
    """Tally verdicts across the ``findings`` / ``ruled_out`` frontmatter lists.

    Returns ``None`` when neither key holds a non-empty list, letting callers
    fall back to legacy counters. Entries that fail the gate are counted as
    zero rather than raising: ``athf hunt validate`` is where a hunter is told
    their file is wrong, so reporting must survive anything already on disk.
    A present-but-rejected list still returns counts, because falling back to
    legacy counters would let an ungated ``confirmed`` reappear as a legacy
    true positive.
    """
    found = False
    counts = {verdict: 0 for verdict in VERDICTS}

    for key in ("findings", "ruled_out"):
        value = frontmatter.get(key)
        if not isinstance(value, list):
            continue
        found = found or bool(value)
        for entry in value:
            if entry_fails_gate(key, entry, registry):
                continue
            counts[_soften(entry.get("verdict"))] += 1

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
    "cites_the_corpus",
    "defers_confirmation",
    "gate_failures",
    "entry_fails_gate",
    "NOT_A_MAPPING",
    "MISSING_VERDICT",
    "INVALID_VERDICT",
    "LEGACY_VERDICT",
    "MISROUTED",
    "UNSUPPORTED_CONFIRMATION",
    "CIRCULAR_CONFIRMATION",
    "DEFERRED_CONFIRMATION",
    "UNNAMED_CONTROL",
    "MISSING_PROVENANCE",
    "UNKNOWN_PRODUCER",
    "METHOD_EXCEEDS_CAPABILITY",
    "CORPUS_ONLY_METHOD",
    "SELF_DECLARED_CAPABILITY",
    "UNATTESTED",
    "is_attributable",
    "tally_frontmatter_verdicts",
    "precision_pair",
]
