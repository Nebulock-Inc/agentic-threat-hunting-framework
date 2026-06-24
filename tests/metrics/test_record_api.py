"""Tests for the public athf.metrics recording API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import athf.metrics as m
from athf.core.metrics import EventStore


def _read_events(workspace: Path) -> list[dict]:
    path = workspace / "metrics" / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_record_llm_call_writes_one_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    m.record_llm_call(
        model="claude-sonnet-4",
        input_tokens=100,
        output_tokens=50,
        duration_ms=300,
        agent="hypothesis-generator",
        hunt_id="H-0001",
    )
    events = _read_events(tmp_path)
    assert len(events) == 1
    evt = events[0]
    assert evt["event_type"] == "llm_call"
    assert evt["hunt_id"] == "H-0001"
    assert evt["agent"] == "hypothesis-generator"
    assert evt["input_tokens"] == 100
    assert evt["output_tokens"] == 50
    assert evt["cost_usd"] > 0  # priced via cost_tracker


def test_record_llm_call_uses_explicit_cost_when_passed(tmp_path: Path) -> None:
    m.record_llm_call(
        model="some-model",
        input_tokens=10,
        output_tokens=5,
        duration_ms=10,
        cost_usd=0.0,
        hunt_id="H-X",
        workspace=tmp_path,
    )
    events = _read_events(tmp_path)
    assert events[0]["cost_usd"] == 0.0


def test_record_query_hashes_sql(tmp_path: Path) -> None:
    m.record_query(
        duration_ms=20,
        rows=10,
        sql="SELECT * FROM events",
        hunt_id="H-2",
        workspace=tmp_path,
    )
    events = _read_events(tmp_path)
    assert events[0]["event_type"] == "query"
    assert events[0]["custom"]["sql_hash"]
    assert events[0]["rows_returned"] == 10


def test_record_web_search_no_cost_field(tmp_path: Path) -> None:
    m.record_web_search(query="lsass dumping", duration_ms=900, hunt_id="H-3", workspace=tmp_path)
    events = _read_events(tmp_path)
    assert events[0]["event_type"] == "web_search"
    assert "cost_usd" not in events[0]
    # Raw query text is hashed (not persisted verbatim) for privacy.
    import hashlib

    assert events[0]["custom"]["query_hash"] == hashlib.sha256(b"lsass dumping").hexdigest()[:16]
    assert "query" not in events[0]["custom"]


def test_record_similarity_search_latency_only(tmp_path: Path) -> None:
    m.record_similarity_search(duration_ms=12, query="kerb", hunt_id="H-4", workspace=tmp_path)
    events = _read_events(tmp_path)
    assert events[0]["event_type"] == "similarity_search"
    assert events[0]["duration_ms"] == 12
    assert "cost_usd" not in events[0]


def test_record_hunt_outcome_canonicalizes(tmp_path: Path) -> None:
    m.record_hunt_outcome(hunt_id="H-1", outcome="TP", workspace=tmp_path)
    events = _read_events(tmp_path)
    assert events[0]["outcome"] == "tp"


def test_record_hunt_outcome_rejects_unknown(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        m.record_hunt_outcome(hunt_id="H-1", outcome="maybe", workspace=tmp_path)


def test_generic_record_routes_unknown_fields_to_custom(tmp_path: Path) -> None:
    m.record(
        "manual",
        hunt_id="H-9",
        workspace=tmp_path,
        note="ran the thing",
        anomaly_score=7,
    )
    events = _read_events(tmp_path)
    assert events[0]["event_type"] == "manual"
    assert events[0]["custom"]["note"] == "ran the thing"
    assert events[0]["custom"]["anomaly_score"] == 7


def test_generic_record_rejects_unknown_event_type(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        m.record("not_a_type", workspace=tmp_path)


def test_public_api_surface() -> None:
    expected = {
        "record_llm_call",
        "record_query",
        "record_web_search",
        "record_similarity_search",
        "record_hunt_outcome",
        "record",
    }
    assert expected.issubset({n for n in dir(m) if not n.startswith("_")})


def test_record_llm_call_swallows_storage_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Metrics must NEVER raise to callers."""
    def _explode(self, evt) -> None:  # type: ignore[no-untyped-def]
        raise RuntimeError("disk full")

    monkeypatch.setattr(EventStore, "append", _explode)
    # Should not raise
    m.record_llm_call(
        model="claude-sonnet-4",
        input_tokens=1,
        output_tokens=1,
        duration_ms=1,
        hunt_id="H-1",
        workspace=tmp_path,
    )
