"""Tests for the MetricEvent schema."""

from __future__ import annotations

import json

import pytest

from athf.core.metrics import EVENT_TYPES, MetricEvent


def test_minimal_event_round_trips() -> None:
    evt = MetricEvent(event_type="manual")
    raw = json.dumps(evt.to_dict())
    rebuilt = MetricEvent.from_dict(json.loads(raw))
    assert rebuilt.event_type == "manual"
    assert rebuilt.timestamp == evt.timestamp
    assert rebuilt.event_id == evt.event_id


def test_llm_call_round_trips() -> None:
    evt = MetricEvent(
        event_type="llm_call",
        hunt_id="H-0001",
        agent="hypothesis-generator",
        model="claude-sonnet-4",
        input_tokens=120,
        output_tokens=80,
        cost_usd=0.0015,
        duration_ms=420,
    )
    rebuilt = MetricEvent.from_dict(json.loads(json.dumps(evt.to_dict())))
    assert rebuilt.input_tokens == 120
    assert rebuilt.output_tokens == 80
    assert rebuilt.cost_usd == pytest.approx(0.0015)


def test_unknown_event_type_rejected() -> None:
    with pytest.raises(ValueError):
        MetricEvent(event_type="not_a_real_type")


def test_event_types_constant_is_complete() -> None:
    assert "llm_call" in EVENT_TYPES
    assert "query" in EVENT_TYPES
    assert "web_search" in EVENT_TYPES
    assert "similarity_search" in EVENT_TYPES
    assert "hunt_outcome" in EVENT_TYPES
    assert "manual" in EVENT_TYPES


def test_to_dict_drops_none_fields_but_keeps_required() -> None:
    evt = MetricEvent(event_type="manual", hunt_id="H-9")
    out = evt.to_dict()
    assert "event_type" in out
    assert "timestamp" in out
    assert "event_id" in out
    assert out["hunt_id"] == "H-9"
    assert "input_tokens" not in out  # was None


def test_unknown_keys_preserved_under_custom() -> None:
    evt = MetricEvent.from_dict({
        "event_type": "manual",
        "weird_field": "value",
    })
    assert evt.custom["weird_field"] == "value"


def test_custom_field_preserved() -> None:
    evt = MetricEvent(event_type="manual", custom={"trace_id": "abc"})
    rebuilt = MetricEvent.from_dict(json.loads(json.dumps(evt.to_dict())))
    assert rebuilt.custom == {"trace_id": "abc"}
