"""Test that Tavily search calls emit a web_search event."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from athf.core.web_search import TavilySearchClient


class _FakeTavilyClient:
    def search(self, **_: Any) -> dict[str, Any]:
        return {
            "results": [
                {"title": "T1", "url": "https://example.com", "content": "snippet", "score": 0.9},
            ],
            "answer": "ans",
            "images": [],
        }


def test_tavily_search_records_web_search_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TavilySearchClient(api_key="test-key")
    monkeypatch.setattr(client, "_get_client", lambda: _FakeTavilyClient())

    response = client.search(query="lsass dumping")
    assert len(response.results) == 1

    events_file = tmp_path / "metrics" / "events.jsonl"
    assert events_file.exists()
    evt = json.loads(events_file.read_text(encoding="utf-8").splitlines()[0])
    assert evt["event_type"] == "web_search"
    # Query text is now hashed (not persisted verbatim) so the metrics log
    # never holds raw search prose. Verify the hash is present and stable.
    import hashlib

    expected_hash = hashlib.sha256(b"lsass dumping").hexdigest()[:16]
    assert evt["custom"]["query_hash"] == expected_hash
    assert evt["custom"]["result_count"] == 1
    assert evt["custom"]["search_depth"] == "basic"
    assert "duration_ms" in evt
    assert "cost_usd" not in evt
