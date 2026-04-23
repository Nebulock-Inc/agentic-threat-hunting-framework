"""Eval runner for harness evaluation.

Runs eval datasets against agent outputs in two modes:
- offline: validates structural expectations from YAML (no LLM calls, CI-safe)
- live: calls the agent with real inputs, then validates the response
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from athf.harness.dataset import EvalCase, EvalDataset
from athf.harness.validators import (
    HypothesisValidator,
    ValidationResult,
    validate_hypothesis_against_expectations,
)

logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """Result for a single eval case."""

    case_id: str
    description: str
    passed: bool
    score: float
    structural_result: Optional[ValidationResult] = None
    expectation_result: Optional[ValidationResult] = None
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None


class HarnessEvaluator:
    """Runs eval datasets and produces scored results.

    Supports offline validation (structure-only, no LLM) and live evaluation
    (calls the real agent, then validates the response).
    """

    def run_offline(self, dataset: EvalDataset) -> List[CaseResult]:
        """Run offline structural validation for all cases.

        In offline mode we validate what we *can* without a live agent call:
        - Confirm eval cases are well-formed
        - Score expectation completeness (are the YAML expectations valid?)
        - Mark cases as structurally ready

        This mode is always CI-safe (no API keys required).

        Args:
            dataset: The eval dataset to validate.

        Returns:
            List of CaseResult, one per case.
        """
        results = []
        for case in dataset.cases:
            result = self._validate_case_structure(case)
            results.append(result)
        return results

    def run_live(self, dataset: EvalDataset, agent: Any) -> List[CaseResult]:
        """Run live evaluation by calling the agent with each case's input.

        Calls the agent, then runs both structural validation and expectation
        matching against the real output.

        Args:
            dataset: The eval dataset to run.
            agent: An Agent instance whose execute() will be called.

        Returns:
            List of CaseResult, one per case.
        """
        results = []
        for case in dataset.cases:
            result = self._evaluate_live_case(case, agent, dataset.agent)
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_case_structure(self, case: EvalCase) -> CaseResult:
        """Validate that an eval case has well-formed expectations."""
        violations: List[str] = []
        warnings: List[str] = []

        if not case.input:
            violations.append("case has no 'input' defined")
        if not case.expected:
            warnings.append("case has no 'expected' expectations — will always pass")

        passed = len(violations) == 0
        score = 1.0 if passed else 0.0

        return CaseResult(
            case_id=case.id,
            description=case.description,
            passed=passed,
            score=score,
            violations=violations,
            warnings=warnings,
        )

    def _evaluate_live_case(
        self, case: EvalCase, agent: Any, agent_type: str
    ) -> CaseResult:
        """Call agent and score its output against case expectations."""
        try:
            agent_result = self._call_agent(agent, case, agent_type)
        except Exception as exc:
            logger.debug("Agent call failed for case %s: %s", case.id, exc)
            return CaseResult(
                case_id=case.id,
                description=case.description,
                passed=False,
                score=0.0,
                error="Agent call failed: {}".format(exc),
            )

        if not agent_result.success or agent_result.data is None:
            return CaseResult(
                case_id=case.id,
                description=case.description,
                passed=False,
                score=0.0,
                error="Agent returned failure: {}".format(agent_result.error),
            )

        return self._score_output(case, agent_result.data, agent_type)

    def _call_agent(self, agent: Any, case: EvalCase, agent_type: str) -> Any:
        """Build agent input from eval case and call the agent.

        Supports hypothesis-generator and hunt-researcher agent types.
        """
        if agent_type in ("hypothesis-generator", "hypothesis_generator"):
            from athf.agents.llm.hypothesis_generator import HypothesisGenerationInput

            inp = HypothesisGenerationInput(
                threat_intel=case.input.get("threat_intel", ""),
                past_hunts=case.input.get("past_hunts", []),
                environment=case.input.get("environment", {}),
            )
            return agent.execute(inp)

        # Generic: pass the raw input dict and call execute()
        return agent.execute(case.input)

    def _score_output(
        self, case: EvalCase, output: Any, agent_type: str
    ) -> CaseResult:
        """Score agent output against case expectations.

        Combines structural validation with expectation matching.
        """
        structural_result: Optional[ValidationResult] = None
        expectation_result: Optional[ValidationResult] = None

        # Structural validation
        if agent_type in ("hypothesis-generator", "hypothesis_generator"):
            validator = HypothesisValidator()
            structural_result = validator.validate(output)

            # Expectation matching
            if case.expected:
                expectation_result = validate_hypothesis_against_expectations(
                    output, case.expected
                )

        # Combine scores
        scores = []
        if structural_result is not None:
            scores.append(structural_result.score)
        if expectation_result is not None:
            scores.append(expectation_result.score)

        avg_score = sum(scores) / len(scores) if scores else 1.0

        all_violations = []
        all_warnings = []
        if structural_result:
            all_violations.extend(structural_result.violations)
            all_warnings.extend(structural_result.warnings)
        if expectation_result:
            all_violations.extend(expectation_result.violations)
            all_warnings.extend(expectation_result.warnings)

        passed = len(all_violations) == 0

        return CaseResult(
            case_id=case.id,
            description=case.description,
            passed=passed,
            score=round(avg_score, 3),
            structural_result=structural_result,
            expectation_result=expectation_result,
            violations=all_violations,
            warnings=all_warnings,
        )

    def score_dict_output(
        self, case: EvalCase, output: Dict[str, Any], agent_type: str
    ) -> CaseResult:
        """Score a raw dict output (useful for testing without live agent calls).

        Args:
            case: The eval case.
            output: Raw dict representing agent output.
            agent_type: The agent type string.

        Returns:
            CaseResult with scores and violations.
        """
        return self._score_output(case, output, agent_type)
