"""Tests for investigation discovery, including nested directory layouts."""

from __future__ import annotations

from pathlib import Path

import pytest

from athf.core.investigation_parser import (
    find_investigation_file,
    get_all_investigations,
    get_next_investigation_id,
)


def _write_investigation(path: Path, investigation_id: str, title: str = "Test") -> Path:
    """Write a minimal valid investigation file at an arbitrary path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
investigation_id: {investigation_id}
title: {title}
date: 2026-08-03
type: finding
---

# {investigation_id}: {title}

Notes.
""",
        encoding="utf-8",
    )
    return path


class TestGetAllInvestigations:
    """Discovery of investigation files."""

    def test_returns_empty_for_missing_directory(self, tmp_path):
        assert get_all_investigations(tmp_path / "nope") == []

    def test_finds_flat_investigations(self, tmp_path):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "I-0002.md", "I-0002")

        found = get_all_investigations(tmp_path)

        assert [i["investigation_id"] for i in found] == ["I-0001", "I-0002"]

    def test_finds_nested_investigations(self, tmp_path):
        """Investigations organized into subdirectories must still be found.

        Hunts (hunts/production/2026/Q3/) and research already recurse; before
        this fix, investigations used a non-recursive glob and silently ignored
        anything below the top level.
        """
        _write_investigation(tmp_path / "2026" / "Q3" / "I-0001.md", "I-0001")

        found = get_all_investigations(tmp_path)

        assert [i["investigation_id"] for i in found] == ["I-0001"]

    def test_sorts_by_investigation_id_not_path(self, tmp_path):
        """Nesting must not reorder results.

        Sorting by path would put investigations/2026/Q3/I-0003.md before
        investigations/I-0001.md, because "2026" < "I-0001.md".
        """
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "2026" / "Q3" / "I-0003.md", "I-0003")
        _write_investigation(tmp_path / "archive" / "I-0002.md", "I-0002")

        found = get_all_investigations(tmp_path)

        assert [i["investigation_id"] for i in found] == ["I-0001", "I-0002", "I-0003"]

    def test_skips_unparseable_files_without_failing(self, tmp_path):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        (tmp_path / "I-0002.md").write_text("---\n: : bad yaml :\n---\n", encoding="utf-8")

        found = get_all_investigations(tmp_path)

        assert [i["investigation_id"] for i in found] == ["I-0001"]

    def test_ignores_non_investigation_markdown(self, tmp_path):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        (tmp_path / "README.md").write_text("# Investigations\n", encoding="utf-8")
        (tmp_path / "AGENTS.md").write_text("# Context\n", encoding="utf-8")

        found = get_all_investigations(tmp_path)

        assert [i["investigation_id"] for i in found] == ["I-0001"]


class TestGetNextInvestigationId:
    """ID allocation must account for every investigation on disk."""

    def test_first_id_when_empty(self, tmp_path):
        assert get_next_investigation_id(tmp_path) == "I-0001"

    def test_increments_past_flat_investigations(self, tmp_path):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "I-0002.md", "I-0002")

        assert get_next_investigation_id(tmp_path) == "I-0003"

    def test_increments_past_nested_investigations(self, tmp_path):
        """Regression: nested investigations were invisible, so IDs collided.

        With a non-recursive glob this returned I-0001, overwriting or
        duplicating the existing investigation.
        """
        _write_investigation(tmp_path / "2026" / "Q3" / "I-0001.md", "I-0001")

        assert get_next_investigation_id(tmp_path) == "I-0002"

    def test_uses_highest_id_across_mixed_layout(self, tmp_path):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "2026" / "Q3" / "I-0007.md", "I-0007")
        _write_investigation(tmp_path / "archive" / "old" / "I-0004.md", "I-0004")

        assert get_next_investigation_id(tmp_path) == "I-0008"

    @pytest.mark.parametrize("bad_id", ["I-XXXX", "INV-1", "H-0001"])
    def test_ignores_malformed_ids(self, tmp_path, bad_id):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "other.md", bad_id)

        assert get_next_investigation_id(tmp_path) == "I-0002"


class TestFindInvestigationFile:
    """ID -> path resolution used by `investigate validate` and `promote`."""

    def test_finds_flat_file(self, tmp_path):
        target = _write_investigation(tmp_path / "I-0001.md", "I-0001")

        assert find_investigation_file(tmp_path, "I-0001") == target

    def test_finds_nested_file(self, tmp_path):
        """Regression: validate/promote built investigations/I-XXXX.md directly
        and failed with "Investigation file not found" for nested files."""
        target = _write_investigation(tmp_path / "2026" / "Q3" / "I-0001.md", "I-0001")

        assert find_investigation_file(tmp_path, "I-0001") == target

    def test_prefers_flat_over_nested(self, tmp_path):
        flat = _write_investigation(tmp_path / "I-0001.md", "I-0001")
        _write_investigation(tmp_path / "archive" / "I-0001.md", "I-0001")

        assert find_investigation_file(tmp_path, "I-0001") == flat

    def test_returns_none_when_absent(self, tmp_path):
        assert find_investigation_file(tmp_path, "I-9999") is None

    def test_returns_none_for_missing_directory(self, tmp_path):
        assert find_investigation_file(tmp_path / "nope", "I-0001") is None

    @pytest.mark.parametrize("bad_id", ["../../etc/passwd", "I-1", "I-0001/../x", "", "i-0001"])
    def test_rejects_malformed_ids(self, tmp_path, bad_id):
        _write_investigation(tmp_path / "I-0001.md", "I-0001")

        assert find_investigation_file(tmp_path, bad_id) is None

    def test_rejects_symlink_escaping_the_root(self, tmp_path):
        outside = tmp_path / "outside"
        _write_investigation(outside / "I-0001.md", "I-0001")
        root = tmp_path / "investigations"
        root.mkdir()
        (root / "linked").symlink_to(outside, target_is_directory=True)

        assert find_investigation_file(root, "I-0001") is None
