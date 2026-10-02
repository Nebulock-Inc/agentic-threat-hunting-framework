"""Tests for verdict-ladder outcomes on the public recording API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import athf.metrics as m
from athf.core.verdicts import VerdictError


def _read_events(workspace: Path) -> list[dict]:
    path = workspace / "metrics" / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize(
    "outcome,expected",
    [
        ("confirmed", "confirmed"),
        ("CONFIRMED", "confirmed"),
        ("suspected", "suspected"),
        ("attempted_not_vulnerable", "attempted_not_vulnerable"),
        ("attempted-not-vulnerable", "attempted_not_vulnerable"),
        ("benign", "benign"),
        ("inconclusive", "inconclusive"),
    ],
)
def test_ladder_verdicts_accepted(tmp_path: Path, outcome: str, expected: str) -> None:
    m.record_hunt_outcome(hunt_id="H-1", outcome=outcome, workspace=tmp_path)
    assert _read_events(tmp_path)[0]["outcome"] == expected


@pytest.mark.parametrize("outcome", ["TP", "tp", "FP", "fp"])
def test_legacy_outcomes_still_accepted_verbatim(tmp_path: Path, outcome: str) -> None:
    m.record_hunt_outcome(hunt_id="H-1", outcome=outcome, workspace=tmp_path)
    assert _read_events(tmp_path)[0]["outcome"] == outcome.lower()


def test_unknown_outcome_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        m.record_hunt_outcome(hunt_id="H-1", outcome="confirmed_exploited", workspace=tmp_path)


def test_verdict_error_is_a_value_error(tmp_path: Path) -> None:
    with pytest.raises(VerdictError):
        m.record_hunt_outcome(hunt_id="H-1", outcome="maybe", workspace=tmp_path)
