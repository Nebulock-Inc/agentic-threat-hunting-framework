"""Tests for LLMAgent auto-instrumentation via athf.metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from athf.agents.base import LLMAgent


class _StubResponse:
    def __init__(self) -> None:
        self.text = "stub"
        self.model = "claude-sonnet-4"
        self.input_tokens = 10
        self.output_tokens = 20
        self.cost_usd = 0.001
        self.duration_ms = 50


class _StubProvider:
    def complete(self, **_: Any) -> _StubResponse:
        return _StubResponse()


class _StubAgent(LLMAgent[Any, Any]):
    def execute(self, input_data: Any) -> Any:  # pragma: no cover - unused
        return None


def test_llm_agent_emits_metric_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    agent = _StubAgent(provider=_StubProvider())
    agent._call_llm("hello")  # type: ignore[attr-defined]

    events_file = tmp_path / "metrics" / "events.jsonl"
    assert events_file.exists(), "metrics/events.jsonl should be created on first record"
    lines = events_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    evt = json.loads(lines[0])
    assert evt["event_type"] == "llm_call"
    assert evt["model"] == "claude-sonnet-4"
    assert evt["input_tokens"] == 10
    assert evt["output_tokens"] == 20
    assert evt["agent"] == "_StubAgent"
    assert evt["duration_ms"] == 50
    assert evt["cost_usd"] == pytest.approx(0.001)
