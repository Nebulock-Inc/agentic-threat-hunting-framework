"""Tests for verdict-ladder rollup in HuntManager listing and stats."""

from __future__ import annotations

from pathlib import Path

import pytest

from athf.core.hunt_manager import HuntManager

LADDER = (
    "confirmed",
    "suspected",
    "attempted_not_vulnerable",
    "benign",
    "inconclusive",
)

LADDER_FRONTMATTER = (
    "findings:\n"
    "  - subject: web-prod-04\n"
    "    verdict: confirmed\n"
    "    evidence: OCSF process_activity\n"
    "    confirmation: host triage recovered the crontab\n"
    "  - subject: fin-laptop-11\n"
    "    verdict: suspected\n"
    "    evidence: authentication burst\n"
    "ruled_out:\n"
    "  - subject: build-runner-02\n"
    "    verdict: attempted_not_vulnerable\n"
    "    control: SELinux enforcing\n"
    "  - subject: svc_backup\n"
    "    verdict: benign\n"
    "    reason: nightly Veeam agent"
)


def _write(hunts: Path, hunt_id: str, extra: str = "") -> None:
    hunts.mkdir(parents=True, exist_ok=True)
    body = (
        f"hunt_id: {hunt_id}\ntitle: {hunt_id}\nstatus: completed\ndate: 2026-08-25"
        + (f"\n{extra}" if extra else "")
    )
    (hunts / f"{hunt_id}.md").write_text(f"---\n{body}\n---\n\n# {hunt_id}\n", encoding="utf-8")


class TestListHunts:
    def test_ladder_counts_surface_per_hunt(self, tmp_path: Path) -> None:
        _write(tmp_path / "hunts", "H-0001", LADDER_FRONTMATTER)

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["confirmed"] == 1
        assert hunt["suspected"] == 1
        assert hunt["attempted_not_vulnerable"] == 1
        assert hunt["benign"] == 1
        assert hunt["inconclusive"] == 0

    def test_ladder_drives_legacy_counters(self, tmp_path: Path) -> None:
        """A ladder hunt needs no hand-maintained true/false positive counts."""
        _write(tmp_path / "hunts", "H-0001", LADDER_FRONTMATTER)

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["true_positives"] == 1
        assert hunt["false_positives"] == 1

    def test_legacy_hunt_keeps_its_own_counters(self, tmp_path: Path) -> None:
        _write(tmp_path / "hunts", "H-0002", "true_positives: 2\nfalse_positives: 5")

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["true_positives"] == 2
        assert hunt["false_positives"] == 5
        assert all(hunt[tier] == 0 for tier in LADDER)

    def test_explicit_legacy_counters_win_over_ladder(self, tmp_path: Path) -> None:
        """Never silently overwrite a number a hunter typed by hand."""
        _write(
            tmp_path / "hunts",
            "H-0003",
            LADDER_FRONTMATTER + "\ntrue_positives: 9\nfalse_positives: 9",
        )

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["true_positives"] == 9
        assert hunt["confirmed"] == 1

    def test_generated_template_does_not_shadow_the_ladder(self, tmp_path: Path) -> None:
        """A freshly generated hunt must not ship legacy zeros that mask verdicts.

        `athf hunt new` frontmatter is the input here, so if the template emits
        `true_positives: 0` every new ladder hunt silently reports no positives.
        """
        from athf.core.template_engine import HUNT_TEMPLATE

        assert "true_positives: 0" not in HUNT_TEMPLATE
        assert "findings: []" in HUNT_TEMPLATE
        assert "ruled_out: []" in HUNT_TEMPLATE

    def test_hunt_without_any_counts_reports_zeros(self, tmp_path: Path) -> None:
        _write(tmp_path / "hunts", "H-0004")

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["true_positives"] == 0
        assert all(hunt[tier] == 0 for tier in LADDER)

    def test_malformed_ladder_does_not_drop_the_hunt(self, tmp_path: Path) -> None:
        """list_hunts swallows parse errors, so junk must not hide a hunt."""
        _write(tmp_path / "hunts", "H-0005", "findings: not-a-list\nruled_out:\n  - a string")

        hunts = HuntManager(tmp_path / "hunts").list_hunts()
        assert len(hunts) == 1
        assert all(hunts[0][tier] == 0 for tier in LADDER)

    def test_rollup_does_not_credit_what_validate_rejects(self, tmp_path: Path) -> None:
        """The rollup and `athf hunt validate` must agree on what counts.

        Previously validate reported two errors on this file while list_hunts
        reported confirmed=2 / true_positives=2 — the dashboard credited
        findings the gate had already refused.
        """
        from athf.core.hunt_parser import HuntParser

        ungated = (
            "findings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: process_activity rows show crontab spawned by curl\n"
            "    confirmation: ok\n"
            "  - subject: host-b\n"
            "    verdict: confirmed\n"
            "    evidence: process_activity rows show crontab spawned by curl\n"
            "    confirmation: tbd\n"
        )
        _write(tmp_path / "hunts", "H-0006", ungated)
        hunt_file = tmp_path / "hunts" / "H-0006.md"

        parser = HuntParser(hunt_file)
        parser.parse()
        ok, _ = parser.validate()
        assert not ok, "fixture must be a file validate rejects"

        hunt = HuntManager(tmp_path / "hunts").list_hunts()[0]
        assert hunt["confirmed"] == 0
        assert hunt["true_positives"] == 0


class TestCalculateStats:
    def test_tiers_roll_up_across_hunts(self, tmp_path: Path) -> None:
        hunts = tmp_path / "hunts"
        _write(hunts, "H-0001", LADDER_FRONTMATTER)
        _write(
            hunts,
            "H-0002",
            "ruled_out:\n"
            "  - subject: host-x\n"
            "    verdict: inconclusive\n",
        )

        stats = HuntManager(hunts).calculate_stats()
        assert stats["confirmed"] == 1
        assert stats["suspected"] == 1
        assert stats["attempted_not_vulnerable"] == 1
        assert stats["benign"] == 1
        assert stats["inconclusive"] == 1

    def test_precision_excludes_ungraded_tiers(self, tmp_path: Path) -> None:
        """suspected and attempted_not_vulnerable must not move the ratio."""
        hunts = tmp_path / "hunts"
        _write(hunts, "H-0001", LADDER_FRONTMATTER)

        stats = HuntManager(hunts).calculate_stats()
        assert stats["true_positives"] == 1
        assert stats["false_positives"] == 1
        assert stats["tp_fp_ratio"] == pytest.approx(1.0)

    def test_empty_workspace_still_reports_every_tier(self, tmp_path: Path) -> None:
        stats = HuntManager(tmp_path / "hunts").calculate_stats()
        assert all(stats[tier] == 0 for tier in LADDER)

    def test_success_rate_counts_confirmed_hunts(self, tmp_path: Path) -> None:
        hunts = tmp_path / "hunts"
        _write(hunts, "H-0001", LADDER_FRONTMATTER)
        _write(hunts, "H-0002")

        stats = HuntManager(hunts).calculate_stats()
        assert stats["completed_hunts"] == 2
        assert stats["success_rate"] == pytest.approx(50.0)

    def test_non_numeric_legacy_counter_does_not_crash(self, tmp_path: Path) -> None:
        """`athf hunt stats` runs right after validate in CI, over old files.

        A hand-typed `true_positives: "three"` is malformed, but aggregation
        reports over whatever is already on disk — only validate is allowed to
        object, so this must degrade rather than raise.
        """
        hunts = tmp_path / "hunts"
        _write(hunts, "H-0001", 'true_positives: "three"\nfalse_positives: 1')
        _write(hunts, "H-0002", "true_positives: 2\nfalse_positives: 1")

        stats = HuntManager(hunts).calculate_stats()
        assert stats["true_positives"] == 2
        assert stats["false_positives"] == 2

    def test_null_legacy_counter_does_not_crash(self, tmp_path: Path) -> None:
        _write(tmp_path / "hunts", "H-0003", "true_positives:\nfalse_positives:")

        stats = HuntManager(tmp_path / "hunts").calculate_stats()
        assert stats["true_positives"] == 0
        assert stats["false_positives"] == 0

    def test_numeric_string_legacy_counter_is_honored(self, tmp_path: Path) -> None:
        """Inverse case: coercion must not discard a recoverable number.

        YAML quoting is a common hand-editing artifact, so `"3"` is a real count
        typed by a hunter, not junk to zero out.
        """
        _write(tmp_path / "hunts", "H-0004", 'true_positives: "3"')

        stats = HuntManager(tmp_path / "hunts").calculate_stats()
        assert stats["true_positives"] == 3
