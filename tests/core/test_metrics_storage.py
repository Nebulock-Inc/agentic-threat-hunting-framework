"""Tests for EventStore JSONL append safety."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from athf.core.metrics import EventStore, MetricEvent


def test_append_creates_file_and_appends_lines(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "metrics" / "events.jsonl")
    store.append(MetricEvent(event_type="manual", custom={"i": 1}))
    store.append(MetricEvent(event_type="manual", custom={"i": 2}))

    lines = (tmp_path / "metrics" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["custom"]["i"] == 1
    assert parsed[1]["custom"]["i"] == 2


def test_read_all_yields_events_in_order(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.jsonl")
    for i in range(5):
        store.append(MetricEvent(event_type="manual", custom={"i": i}))

    events = list(store.read_all())
    assert [e.custom["i"] for e in events] == [0, 1, 2, 3, 4]


def test_read_all_skips_malformed_lines(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        '{"event_type":"manual","custom":{}}\n'
        "this is not json\n"
        '{"event_type":"manual","custom":{"i":2}}\n',
        encoding="utf-8",
    )
    events = list(EventStore(path).read_all())
    assert len(events) == 2


def test_read_all_returns_empty_for_missing_file(tmp_path: Path) -> None:
    assert list(EventStore(tmp_path / "missing.jsonl").read_all()) == []


def test_concurrent_appends_produce_n_valid_lines(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.jsonl")

    def worker(i: int) -> None:
        store.append(MetricEvent(event_type="manual", custom={"i": i}))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    indices = sorted(json.loads(line)["custom"]["i"] for line in lines)
    assert indices == list(range(10))
