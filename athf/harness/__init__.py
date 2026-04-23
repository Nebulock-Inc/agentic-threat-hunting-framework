"""Harness engineering module for ATHF agents.

Implements the Agent = Model + Harness pattern with:
- Guides (feedforward): structured prompts, constraints, exemplars
- Sensors (feedback): computational validators, eval runners, metrics
"""

from athf.harness.dataset import EvalCase, EvalDataset, load_dataset, list_bundled_datasets
from athf.harness.evaluator import CaseResult, HarnessEvaluator
from athf.harness.metrics import HarnessReport, build_report, render_report_table, render_report_json
from athf.harness.validators import (
    ValidationResult,
    HypothesisValidator,
    ResearchOutputValidator,
)

__all__ = [
    "EvalCase",
    "EvalDataset",
    "load_dataset",
    "list_bundled_datasets",
    "CaseResult",
    "HarnessEvaluator",
    "HarnessReport",
    "build_report",
    "render_report_table",
    "render_report_json",
    "ValidationResult",
    "HypothesisValidator",
    "ResearchOutputValidator",
]
