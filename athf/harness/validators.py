"""Computational sensors for agent output validation.

These are deterministic, zero-LLM-cost validators (the cheap feedback layer).
They run fast and are safe for CI without any API keys.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Result from a computational validator."""

    passed: bool
    score: float  # 0.0–1.0
    violations: List[str] = field(default_factory=list)  # blocking failures
    warnings: List[str] = field(default_factory=list)  # non-blocking issues


# Regex patterns used across validators
_TECHNIQUE_RE = re.compile(r"^T\d{4}(\.\d{3})?$")
_HYPOTHESIS_PATTERN_RE = re.compile(r"adversar", re.IGNORECASE)
_RESEARCH_ID_RE = re.compile(r"^R-\d{4}$")


def _score_from_checks(passed_checks: int, total_checks: int) -> float:
    if total_checks == 0:
        return 1.0
    return round(passed_checks / total_checks, 3)


def _to_dict(output: Any) -> Dict[str, Any]:
    """Convert a dataclass, object, or dict to a plain dict.

    Handles both instance attributes and class-level attributes so tests can
    pass simple objects with class-level fields.
    """
    if isinstance(output, dict):
        return output
    # Collect class-level attributes first (skipping dunder/private)
    data: Dict[str, Any] = {}
    for key in vars(type(output)):
        if not key.startswith("_") and not callable(getattr(type(output), key)):
            data[key] = getattr(output, key)
    # Override with instance-level attributes (more specific)
    data.update(vars(output))
    return data


class HypothesisValidator:
    """Validates HypothesisGenerationOutput for structural correctness.

    Checks ATT&CK technique format, hypothesis pattern, required fields,
    and observable/data source completeness.
    """

    def validate(self, output: Any) -> ValidationResult:
        """Validate a HypothesisGenerationOutput (or plain dict).

        Args:
            output: HypothesisGenerationOutput dataclass or equivalent dict.

        Returns:
            ValidationResult with score, violations, and warnings.
        """
        data = _to_dict(output)

        violations: List[str] = []
        warnings: List[str] = []
        checks_passed = 0
        total_checks = 0

        # 1. Hypothesis string is present and non-empty
        total_checks += 1
        hypothesis = data.get("hypothesis", "")
        if not hypothesis or not hypothesis.strip():
            violations.append("hypothesis: field is empty or missing")
        else:
            checks_passed += 1

        # 2. Hypothesis matches adversary pattern
        total_checks += 1
        if hypothesis and _HYPOTHESIS_PATTERN_RE.search(hypothesis):
            checks_passed += 1
        else:
            warnings.append(
                "hypothesis: does not mention adversary behavior "
                '(expected pattern like "Adversaries use X to Y on Z")'
            )

        # 3. MITRE techniques present and correctly formatted
        total_checks += 1
        techniques: List[str] = data.get("mitre_techniques", [])
        if not techniques:
            warnings.append("mitre_techniques: no techniques specified")
            # Not a hard violation — some hypotheses may predate technique IDs
            checks_passed += 1
        else:
            invalid = [t for t in techniques if not _TECHNIQUE_RE.match(t)]
            if invalid:
                violations.append(
                    "mitre_techniques: invalid format(s): {} "
                    "(expected T1234 or T1234.001)".format(", ".join(invalid))
                )
            else:
                checks_passed += 1

        # 4. Data sources non-empty
        total_checks += 1
        data_sources: List[str] = data.get("data_sources", [])
        if not data_sources:
            violations.append("data_sources: at least one data source required")
        else:
            checks_passed += 1

        # 5. Expected observables count ≥ 1
        total_checks += 1
        observables: List[str] = data.get("expected_observables", [])
        if len(observables) < 1:
            violations.append("expected_observables: at least one observable required")
        else:
            checks_passed += 1

        # 6. Time range suggestion present
        total_checks += 1
        time_range: str = data.get("time_range_suggestion", "")
        if not time_range or not time_range.strip():
            warnings.append("time_range_suggestion: field is empty or missing")
            checks_passed += 1  # warning only
        else:
            checks_passed += 1

        # 7. Justification present
        total_checks += 1
        justification: str = data.get("justification", "")
        if not justification or not justification.strip():
            warnings.append("justification: field is empty or missing")
            checks_passed += 1  # warning only
        else:
            checks_passed += 1

        score = _score_from_checks(checks_passed, total_checks)
        passed = len(violations) == 0

        return ValidationResult(
            passed=passed,
            score=score,
            violations=violations,
            warnings=warnings,
        )


class ResearchOutputValidator:
    """Validates ResearchOutput for completeness of the 5-skill methodology."""

    REQUIRED_SKILLS = [
        "system_research",
        "adversary_tradecraft",
        "telemetry_mapping",
        "related_work",
        "synthesis",
    ]

    def validate(self, output: Any) -> ValidationResult:
        """Validate a ResearchOutput (or plain dict).

        Args:
            output: ResearchOutput dataclass or equivalent dict.

        Returns:
            ValidationResult with score, violations, and warnings.
        """
        data = _to_dict(output)

        violations: List[str] = []
        warnings: List[str] = []
        checks_passed = 0
        total_checks = 0

        # 1. Research ID format
        total_checks += 1
        research_id: str = data.get("research_id", "")
        if not research_id or not _RESEARCH_ID_RE.match(research_id):
            violations.append(
                "research_id: invalid or missing (expected R-XXXX format, got '{}')".format(research_id)
            )
        else:
            checks_passed += 1

        # 2. Topic non-empty
        total_checks += 1
        topic: str = data.get("topic", "")
        if not topic or not topic.strip():
            violations.append("topic: field is empty or missing")
        else:
            checks_passed += 1

        # 3. All 5 skills are present with non-empty summaries
        for skill_name in self.REQUIRED_SKILLS:
            total_checks += 1
            skill = data.get(skill_name)
            if skill is None:
                violations.append("{}: skill output is missing".format(skill_name))
                continue

            # Get summary from dataclass or dict
            if hasattr(skill, "summary"):
                summary = skill.summary
                key_findings = getattr(skill, "key_findings", [])
            elif isinstance(skill, dict):
                summary = skill.get("summary", "")
                key_findings = skill.get("key_findings", [])
            else:
                summary = ""
                key_findings = []

            if not summary or not summary.strip():
                violations.append("{}: summary is empty".format(skill_name))
            else:
                checks_passed += 1
                if not key_findings:
                    warnings.append("{}: no key_findings listed".format(skill_name))

        # 4. recommended_hypothesis present
        total_checks += 1
        rec_hypothesis: Optional[str] = data.get("recommended_hypothesis")
        if not rec_hypothesis or not str(rec_hypothesis).strip():
            warnings.append("recommended_hypothesis: not present (consider adding synthesis recommendation)")
            checks_passed += 1  # warning only
        else:
            checks_passed += 1

        # 5. data_source_availability non-empty
        total_checks += 1
        ds_avail: Dict[str, bool] = data.get("data_source_availability", {})
        if not ds_avail:
            warnings.append("data_source_availability: empty — telemetry coverage unknown")
            checks_passed += 1  # warning only
        else:
            checks_passed += 1

        score = _score_from_checks(checks_passed, total_checks)
        passed = len(violations) == 0

        return ValidationResult(
            passed=passed,
            score=score,
            violations=violations,
            warnings=warnings,
        )


def validate_hypothesis_against_expectations(
    output: Any,
    expected: Dict[str, Any],
) -> ValidationResult:
    """Check agent output against eval case expectations.

    Used by HarnessEvaluator to score a specific eval case.

    Args:
        output: HypothesisGenerationOutput or dict.
        expected: Expected values from the eval case YAML.

    Returns:
        ValidationResult scoring how well output meets expectations.
    """
    data = _to_dict(output)

    violations: List[str] = []
    warnings: List[str] = []
    checks_passed = 0
    total_checks = 0

    # mitre_techniques_contain — all listed techniques must appear
    expected_techniques = expected.get("mitre_techniques_contain", [])
    if expected_techniques:
        total_checks += 1
        actual_techniques = data.get("mitre_techniques", [])
        missing = [t for t in expected_techniques if t not in actual_techniques]
        if missing:
            violations.append(
                "mitre_techniques: missing expected technique(s): {}".format(", ".join(missing))
            )
        else:
            checks_passed += 1

    # data_sources_any_of — at least one listed source must appear
    expected_sources = expected.get("data_sources_any_of", [])
    if expected_sources:
        total_checks += 1
        actual_sources = [s.lower() for s in data.get("data_sources", [])]
        found = any(
            any(exp.lower() in actual for actual in actual_sources)
            for exp in expected_sources
        )
        if not found:
            violations.append(
                "data_sources: none of {} found in output".format(expected_sources)
            )
        else:
            checks_passed += 1

    # observables_min_count
    min_obs = expected.get("observables_min_count")
    if min_obs is not None:
        total_checks += 1
        actual_count = len(data.get("expected_observables", []))
        if actual_count < min_obs:
            violations.append(
                "expected_observables: count {} < minimum {}".format(actual_count, min_obs)
            )
        else:
            checks_passed += 1

    # hypothesis_pattern_match
    if expected.get("hypothesis_pattern_match"):
        total_checks += 1
        hypothesis = data.get("hypothesis", "")
        if _HYPOTHESIS_PATTERN_RE.search(hypothesis):
            checks_passed += 1
        else:
            violations.append(
                "hypothesis: does not match expected adversary pattern"
            )

    score = _score_from_checks(checks_passed, total_checks) if total_checks > 0 else 1.0
    passed = len(violations) == 0

    return ValidationResult(
        passed=passed,
        score=score,
        violations=violations,
        warnings=warnings,
    )
