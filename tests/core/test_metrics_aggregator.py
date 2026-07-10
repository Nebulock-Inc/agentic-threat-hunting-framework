"""Tests for Aggregator: events.jsonl + hunt files → aggregates.json."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from athf.core.metrics import Aggregator, EventStore, MetricEvent


def _write_hunt(workspace: Path, hunt_id: str, frontmatter: str, body: str = "") -> None:
    hunts = workspace / "hunts"
    hunts.mkdir(parents=True, exist_ok=True)
    (hunts / f"{hunt_id}.md").write_text(
        f"---\n{frontmatter}\n---\n\n{body}\n",
        encoding="utf-8",
    )


def test_extract_with_only_events(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "metrics" / "events.jsonl")
    store.append(MetricEvent(
        event_type="llm_call",
        hunt_id="H-0001",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.01,
    ))
    store.append(MetricEvent(
        event_type="query",
        hunt_id="H-0001",
        duration_ms=250,
        rows_returned=5,
    ))

    agg = Aggregator(workspace=tmp_path).extract()

    h = agg["hunts"]["H-0001"]
    assert h["llm_calls"] == 1
    assert h["queries"] == 1
    assert h["input_tokens"] == 100
    assert h["output_tokens"] == 50
    assert h["query_duration_ms"] == 250
    assert h["cost_usd"] == pytest.approx(0.01)
    assert agg["totals"]["hunts"] == 1


def test_extract_with_only_hunt_files(tmp_path: Path) -> None:
    _write_hunt(
        tmp_path,
        "H-0042",
        "hunt_id: H-0042\n"
        "title: Test Hunt\n"
        "status: completed\n"
        "platform: macOS\n"
        "total_queries: 4\n"
        "events_analyzed: 1500\n"
        "true_positives: 1\n"
        "false_positives: 3",
    )

    agg = Aggregator(workspace=tmp_path).extract()
    h = agg["hunts"]["H-0042"]
    assert h["total_queries"] == 4
    assert h["events_analyzed"] == 1500
    assert h["true_positives"] == 1
    assert h["false_positives"] == 3
    assert h["precision"] == pytest.approx(0.25, rel=1e-3)


def test_extract_combines_events_and_files(tmp_path: Path) -> None:
    _write_hunt(
        tmp_path,
        "H-0001",
        "hunt_id: H-0001\ntitle: Combo\nplatform: Linux\ntrue_positives: 2\nfalse_positives: 0",
    )
    store = EventStore(tmp_path / "metrics" / "events.jsonl")
    store.append(MetricEvent(event_type="llm_call", hunt_id="H-0001", cost_usd=0.05))

    agg = Aggregator(workspace=tmp_path).extract()
    h = agg["hunts"]["H-0001"]
    assert h["llm_calls"] == 1
    assert h["true_positives"] == 2
    assert h["title"] == "Combo"


def test_extract_writes_aggregates_json(tmp_path: Path) -> None:
    Aggregator(workspace=tmp_path).extract()
    out = tmp_path / "metrics" / "aggregates.json"
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "schema_version" in payload
    assert "totals" in payload
    assert "hunts" in payload


def test_load_returns_none_if_no_aggregates(tmp_path: Path) -> None:
    assert Aggregator(workspace=tmp_path).load() is None


def test_load_returns_dict_after_extract(tmp_path: Path) -> None:
    agg = Aggregator(workspace=tmp_path)
    agg.extract()
    payload = agg.load()
    assert payload is not None
    assert payload["schema_version"]


def test_extract_skips_template_files(tmp_path: Path) -> None:
    hunts = tmp_path / "hunts"
    hunts.mkdir()
    (hunts / "H-TEMPLATE.md").write_text(
        "---\nhunt_id: H-TEMPLATE\n---\n",
        encoding="utf-8",
    )
    (hunts / "H-0099.md").write_text(
        "---\nhunt_id: H-0099\ntitle: Real\n---\n",
        encoding="utf-8",
    )

    agg = Aggregator(workspace=tmp_path).extract()
    assert "H-0099" in agg["hunts"]
    assert "H-TEMPLATE" not in agg["hunts"]


def test_extract_from_hunt_file_body_fallback() -> None:
    content = (
        "---\nhunt_id: H-0007\ntitle: Body fallback\n---\n\n"
        "**Total Queries Executed:** 12\n"
        "**Total Query Execution Time:** 4.5s\n"
        "**Events Analyzed:** ~2.5M\n"
        "**True Positives:** 3\n"
        "**False Positives:** 1\n"
    )
    out = Aggregator.extract_from_hunt_file(content)
    assert out["total_queries"] == 12
    assert out["execution_time_seconds"] == pytest.approx(4.5)
    assert out["events_analyzed"] == 2_500_000
    assert out["true_positives"] == 3
    assert out["false_positives"] == 1
    assert out["precision"] == 0.75


def test_rollups_by_platform(tmp_path: Path) -> None:
    _write_hunt(tmp_path, "H-0001", "hunt_id: H-0001\nplatform: Linux")
    _write_hunt(tmp_path, "H-0002", "hunt_id: H-0002\nplatform: Linux")
    _write_hunt(tmp_path, "H-0003", "hunt_id: H-0003\nplatform: macOS")

    agg = Aggregator(workspace=tmp_path).extract()
    rollups = agg["rollups"]["by_platform"]
    assert rollups.get("Linux") == 2
    assert rollups.get("macOS") == 1


def test_org_scoped_extract_excludes_other_tenants_hunt_files(tmp_path: Path) -> None:
    """Tenant-scoped extract must not backfill hunt files for hunts that had
    no org-matching events, or another tenant's hunt metadata leaks in."""
    store = EventStore(tmp_path / "metrics" / "events.jsonl")
    store.append(MetricEvent(
        event_type="query",
        hunt_id="H-ORG-A",
        organization_id="org-a",
        duration_ms=100,
    ))
    store.append(MetricEvent(
        event_type="query",
        hunt_id="H-ORG-B",
        organization_id="org-b",
        duration_ms=200,
    ))
    # Hunt files exist for BOTH hunts (shared workspace); files carry no org id.
    _write_hunt(tmp_path, "H-ORG-A", "hunt_id: H-ORG-A\ntotal_queries: 4")
    _write_hunt(tmp_path, "H-ORG-B", "hunt_id: H-ORG-B\ntotal_queries: 9")

    agg = Aggregator(workspace=tmp_path).extract(organization_id="org-a")

    assert "H-ORG-A" in agg["hunts"]
    # org-b's hunt (and its frontmatter metrics) must NOT appear in org-a's aggregate.
    assert "H-ORG-B" not in agg["hunts"]
    assert agg["totals"]["hunts"] == 1


def test_single_tenant_extract_still_merges_all_hunt_files(tmp_path: Path) -> None:
    """Without organization_id, hunt-file backfill is unchanged (merges all)."""
    _write_hunt(tmp_path, "H-0001", "hunt_id: H-0001\ntotal_queries: 4")
    _write_hunt(tmp_path, "H-0002", "hunt_id: H-0002\ntotal_queries: 9")

    agg = Aggregator(workspace=tmp_path).extract()

    assert "H-0001" in agg["hunts"]
    assert "H-0002" in agg["hunts"]
