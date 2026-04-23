"""Eval dataset loader for harness evaluation.

Datasets are YAML files with ground-truth eval cases used to score
agent outputs without requiring live LLM calls.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class EvalCase:
    """A single evaluation case with input, expectations, and rubric weights."""

    id: str
    description: str
    input: Dict[str, Any]
    expected: Dict[str, Any] = field(default_factory=dict)
    rubric_weights: Dict[str, float] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class EvalDataset:
    """A collection of eval cases for a specific agent."""

    version: str
    agent: str
    description: str
    cases: List[EvalCase]

    @property
    def case_count(self) -> int:
        return len(self.cases)

    def get_case(self, case_id: str) -> Optional[EvalCase]:
        for case in self.cases:
            if case.id == case_id:
                return case
        return None


def load_dataset(path: Path) -> EvalDataset:
    """Load an eval dataset from a YAML file.

    Args:
        path: Path to the YAML dataset file.

    Returns:
        EvalDataset with parsed cases.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML is malformed or missing required fields.
    """
    if not path.exists():
        raise FileNotFoundError("Eval dataset not found: {}".format(path))

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError("Invalid eval dataset: expected a YAML mapping in {}".format(path))

    for required in ("version", "agent", "cases"):
        if required not in raw:
            raise ValueError("Eval dataset missing required field '{}' in {}".format(required, path))

    cases = []
    for i, case_raw in enumerate(raw["cases"]):
        if not isinstance(case_raw, dict):
            raise ValueError("Case {} in {} is not a mapping".format(i, path))
        if "id" not in case_raw:
            raise ValueError("Case {} in {} is missing 'id' field".format(i, path))

        cases.append(
            EvalCase(
                id=case_raw["id"],
                description=case_raw.get("description", ""),
                input=case_raw.get("input", {}),
                expected=case_raw.get("expected", {}),
                rubric_weights=case_raw.get("rubric_weights", {}),
                tags=case_raw.get("tags", []),
            )
        )

    return EvalDataset(
        version=str(raw["version"]),
        agent=raw["agent"],
        description=raw.get("description", ""),
        cases=cases,
    )


def list_bundled_datasets() -> List[Path]:
    """Return paths to all bundled eval datasets.

    Returns:
        List of Path objects pointing to bundled YAML dataset files.
    """
    data_dir = Path(__file__).parent.parent / "data" / "harness" / "evals"
    if not data_dir.exists():
        return []
    return sorted(data_dir.glob("*.yaml"))


def get_bundled_dataset_for_agent(agent_name: str) -> Optional[Path]:
    """Find the bundled dataset file for a named agent.

    Args:
        agent_name: Agent name (e.g., "hypothesis-generator").

    Returns:
        Path to the dataset file, or None if not found.
    """
    # Normalize: "hypothesis-generator" -> "hypothesis_gen"
    slug_map = {
        "hypothesis-generator": "hypothesis_gen",
        "hypothesis_generator": "hypothesis_gen",
        "hunt-researcher": "hunt_researcher",
        "hunt_researcher": "hunt_researcher",
    }
    slug = slug_map.get(agent_name, agent_name.replace("-", "_"))

    data_dir = Path(__file__).parent.parent / "data" / "harness" / "evals"
    candidate = data_dir / "{}.yaml".format(slug)
    if candidate.exists():
        return candidate
    return None
