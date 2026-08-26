"""Tests for verdict-ladder aggregation in the metrics core."""

from __future__ import annotations

from pathlib import Path

import pytest

from athf.core.metrics import Aggregator, EventStore, MetricEvent
from athf.core.provenance import ProducerRegistry

LADDER = (
    "confirmed",
    "suspected",
    "attempted_not_vulnerable",
    "benign",
    "inconclusive",
)

# Producer capabilities as workspace config supplies them. Aggregation consults
# the same registry as `athf hunt validate`, so a hunt whose producer the config
# never declared tallies zero here — the reason these fixtures write the config
# rather than putting capabilities in the hunt file.
PRODUCER_CONFIG = {
    "provenance": {"producers": {"analyst": {"capabilities": ["host_forensics"]}}}
}

WORKSPACE_CONFIG = """provenance:
  producers:
    analyst:
      capabilities:
        - host_forensics
"""

# The confirmation mapping in frontmatter YAML, indented for a `findings` entry.
CONFIRMATION = (
    "    confirmation:\n"
    "      method: host_forensics\n"
    "      produced_by: analyst\n"
    "      attested_by: Sydney Marrone\n"
    "      detail: host triage recovered the crontab entry from disk\n"
)


def _write_hunt(workspace: Path, hunt_id: str, frontmatter: str, body: str = "") -> None:
    hunts = workspace / "hunts"
    hunts.mkdir(parents=True, exist_ok=True)
    (workspace / ".athfconfig.yaml").write_text(WORKSPACE_CONFIG, encoding="utf-8")
    (hunts / f"{hunt_id}.md").write_text(
        f"---\n{frontmatter}\n---\n\n{body}\n",
        encoding="utf-8",
    )


class TestEventAccumulation:
    @pytest.mark.parametrize("verdict", LADDER)
    def test_each_tier_gets_its_own_counter(self, tmp_path: Path, verdict: str) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome=verdict))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h[verdict] == 1
        for other in LADDER:
            if other != verdict:
                assert h[other] == 0

    def test_confirmed_also_counts_as_a_legacy_true_positive(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="confirmed"))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["true_positives"] == 1
        assert h["false_positives"] == 0

    def test_benign_also_counts_as_a_legacy_false_positive(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="benign"))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["false_positives"] == 1
        assert h["true_positives"] == 0

    @pytest.mark.parametrize("verdict", ["suspected", "attempted_not_vulnerable", "inconclusive"])
    def test_ungraded_tiers_do_not_dilute_precision(self, tmp_path: Path, verdict: str) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="confirmed"))
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome=verdict))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["true_positives"] == 1
        assert h["false_positives"] == 0
        assert h[verdict] == 1

    def test_legacy_tp_still_accumulates_and_is_not_promoted(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="tp"))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["true_positives"] == 1
        assert h["confirmed"] == 0

    def test_hyphenated_outcome_normalizes(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(
            MetricEvent(
                event_type="hunt_outcome",
                hunt_id="H-1",
                outcome="attempted-not-vulnerable",
            )
        )

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["attempted_not_vulnerable"] == 1

    def test_unknown_outcome_is_ignored_not_fatal(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="maybe"))

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-1"]
        assert h["outcomes"] == ["maybe"]
        assert all(h[tier] == 0 for tier in LADDER)


class TestWorkspaceRollup:
    def test_tiers_roll_up_into_totals(self, tmp_path: Path) -> None:
        store = EventStore(tmp_path / "metrics" / "events.jsonl")
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-1", outcome="confirmed"))
        store.append(
            MetricEvent(
                event_type="hunt_outcome",
                hunt_id="H-2",
                outcome="attempted_not_vulnerable",
            )
        )
        store.append(MetricEvent(event_type="hunt_outcome", hunt_id="H-2", outcome="benign"))

        totals = Aggregator(workspace=tmp_path).extract()["totals"]
        assert totals["confirmed"] == 1
        assert totals["attempted_not_vulnerable"] == 1
        assert totals["benign"] == 1
        assert totals["suspected"] == 0
        assert totals["true_positives"] == 1
        assert totals["false_positives"] == 1


class TestFrontmatterVerdicts:
    def test_findings_and_ruled_out_increment_tiers(self, tmp_path: Path) -> None:
        _write_hunt(
            tmp_path,
            "H-0042",
            "hunt_id: H-0042\n"
            "title: Ladder hunt\n"
            "findings:\n"
            "  - subject: web-prod-04\n"
            "    verdict: confirmed\n"
            "    evidence: process_activity\n"
            + CONFIRMATION
            + "  - subject: fin-laptop-11\n"
            "    verdict: suspected\n"
            "    evidence: authentication burst\n"
            "ruled_out:\n"
            "  - subject: build-runner-02\n"
            "    verdict: attempted_not_vulnerable\n"
            "    control: SELinux enforcing\n"
            "    reason: ptrace attach denied\n"
            "  - subject: svc_backup\n"
            "    verdict: benign\n"
            "    reason: nightly Veeam agent",
        )

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-0042"]
        assert h["confirmed"] == 1
        assert h["suspected"] == 1
        assert h["attempted_not_vulnerable"] == 1
        assert h["benign"] == 1
        assert h["inconclusive"] == 0
        assert h["precision"] == pytest.approx(0.5)

    def test_legacy_only_hunt_contributes_legacy_counters_only(self, tmp_path: Path) -> None:
        _write_hunt(
            tmp_path,
            "H-0043",
            "hunt_id: H-0043\ntitle: Legacy\ntrue_positives: 1\nfalse_positives: 3",
        )

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-0043"]
        assert h["true_positives"] == 1
        assert h["false_positives"] == 3
        assert h["precision"] == pytest.approx(0.25)
        assert all(h[tier] == 0 for tier in LADDER)

    def test_misrouted_confirmed_does_not_inflate_precision(self, tmp_path: Path) -> None:
        """A confirmed entry in ruled_out must not be counted as a positive.

        `athf hunt validate` rejects this shape, but aggregation runs over
        whatever is on disk, so it must not credit a misrouted verdict.
        """
        _write_hunt(
            tmp_path,
            "H-0045",
            "hunt_id: H-0045\n"
            "title: Misrouted\n"
            "ruled_out:\n"
            "  - subject: host-z\n"
            "    verdict: confirmed\n"
            "    evidence: telemetry\n"
            "    confirmation: host forensics",
        )

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-0045"]
        assert h["true_positives"] == 0

    def test_malformed_findings_do_not_raise(self, tmp_path: Path) -> None:
        _write_hunt(
            tmp_path,
            "H-0044",
            "hunt_id: H-0044\ntitle: Junk\nfindings: not-a-list\nruled_out:\n  - just a string",
        )

        h = Aggregator(workspace=tmp_path).extract()["hunts"]["H-0044"]
        assert all(h[tier] == 0 for tier in LADDER)


class TestBodyCounts:
    def test_legacy_body_format(self) -> None:
        content = (
            "---\nhunt_id: H-0007\ntitle: Old format\n---\n\n"
            "**True Positives:** 3\n"
            "**False Positives:** 1\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out["true_positives"] == 3
        assert out["false_positives"] == 1
        assert out["precision"] == pytest.approx(0.75)

    def test_new_per_verdict_body_format(self) -> None:
        """Body counts parse — except ``confirmed``, which is gate-only.

        This test previously asserted ``confirmed == 3`` from the body. That was
        the bypass: an agent with query-only access could skip the `findings`
        list entirely and have the aggregate credit a number nobody gated, while
        `athf hunt validate` reported the file clean. See
        TestBodyCountsCannotBypassTheGate.
        """
        content = (
            "---\nhunt_id: H-0008\ntitle: New format\n---\n\n"
            "**Counts:** `confirmed` 3 · `suspected` 2 · "
            "`attempted_not_vulnerable` 4 · `benign` 1 · `inconclusive` 5\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out["confirmed"] == 0
        assert out["suspected"] == 2
        assert out["attempted_not_vulnerable"] == 4
        assert out["benign"] == 1
        assert out["inconclusive"] == 5

    def test_body_with_neither_format(self) -> None:
        content = (
            "---\nhunt_id: H-0009\ntitle: Nothing\n---\n\n"
            "### Findings\n\nNo counts recorded here.\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert "true_positives" not in out
        assert "false_positives" not in out
        assert "precision" not in out
        for tier in LADDER:
            assert tier not in out

    def test_unfilled_template_placeholders_are_not_counted(self) -> None:
        content = (
            "---\nhunt_id: H-0010\ntitle: Template\n---\n\n"
            "**Counts:** `confirmed` [N] · `suspected` [N] · "
            "`attempted_not_vulnerable` [N] · `benign` [N] · `inconclusive` [N]\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        for tier in LADDER:
            assert tier not in out

    def test_frontmatter_wins_over_body_counts(self) -> None:
        content = (
            "---\nhunt_id: H-0011\ntitle: Both\n"
            "findings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: process_activity rows show crontab spawned by curl\n"
            + CONFIRMATION
            + "---\n\n"
            "**Counts:** `confirmed` 9 · `suspected` 0 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        # Called directly rather than through a workspace, so the registry is
        # passed in — the entry has to clear the gate for the frontmatter count to
        # be the one that wins.
        out = Aggregator.extract_from_hunt_file(
            content, ProducerRegistry.from_config(PRODUCER_CONFIG)
        )
        assert out["confirmed"] == 1

    def test_absurd_body_count_is_not_credited(self) -> None:
        """An over-wide number is a paste artifact, not a finding count."""
        content = (
            "---\nhunt_id: H-0013\ntitle: Huge\n---\n\n"
            "**Counts:** `confirmed` 99999999999999999999999 · `suspected` 0 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out.get("confirmed", 0) == 0

    def test_realistic_body_count_still_parses(self) -> None:
        """Inverse case: the digit cap must not clip a real count."""
        content = (
            "---\nhunt_id: H-0014\ntitle: Normal\n---\n\n"
            "**Counts:** `confirmed` 3 · `suspected` 127 · "
            "`attempted_not_vulnerable` 0 · `benign` 4096 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out["suspected"] == 127
        assert out["benign"] == 4096


class TestBodyCountsCannotBypassTheGate:
    """A prose line in the body is not a route around provenance.

    The body counter reads a number a hunter typed in the KEEP section. Every
    other verdict is a summary of work; ``confirmed`` is a claim that work
    happened outside the log corpus, and there is no producer attached to a
    markdown sentence to check that against. An agent that can only run queries
    writes no ``findings`` list at all, types ```confirmed`` 3`` in the body, and
    the aggregate credits it while ``athf hunt validate`` reports the file clean
    — the exact validate/aggregate divergence 18272e8 closed for frontmatter.
    """

    def test_body_confirmed_is_never_credited(self) -> None:
        content = (
            "---\nhunt_id: H-0015\ntitle: Body-only confirmed\n---\n\n"
            "## KEEP\n\n**Counts:** `confirmed` 3 · `suspected` 0 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out.get("confirmed", 0) == 0
        assert out.get("true_positives", 0) == 0

    def test_body_confirmed_ignored_even_with_a_full_registry(self) -> None:
        """A declared producer does not rescue it — nothing names a producer."""
        content = (
            "---\nhunt_id: H-0016\ntitle: Body-only confirmed\n---\n\n"
            "**Counts:** `confirmed` 5 · `suspected` 0 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(
            content, ProducerRegistry.from_config(PRODUCER_CONFIG)
        )
        assert out.get("confirmed", 0) == 0

    def test_other_verdicts_in_the_body_still_count(self) -> None:
        """Inverse: only ``confirmed`` is gated, so the format stays usable.

        Dropping the whole body format would punish hunters recording honest
        negative results, which is the output this ladder exists to make
        first-class.
        """
        content = (
            "---\nhunt_id: H-0017\ntitle: Body counts\n---\n\n"
            "**Counts:** `confirmed` 0 · `suspected` 7 · "
            "`attempted_not_vulnerable` 2 · `benign` 4 · `inconclusive` 1\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out["suspected"] == 7
        assert out["attempted_not_vulnerable"] == 2
        assert out["benign"] == 4
        assert out["inconclusive"] == 1

    def test_body_confirmed_alone_does_not_fabricate_a_tally(self) -> None:
        """A body whose only verdict line is ``confirmed`` yields no counts.

        Otherwise suppressing the number would still leave a zeroed ladder
        asserting the hunt was tallied, and ``precision`` computed off it.
        """
        content = (
            "---\nhunt_id: H-0018\ntitle: Only confirmed\n---\n\n"
            "**Counts:** `confirmed` 4\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        for tier in LADDER:
            assert tier not in out
        assert "precision" not in out

    def test_gated_body_count_does_not_become_a_legacy_positive(self) -> None:
        """The refused number must not reappear through the legacy key.

        Same reasoning as tally_frontmatter_verdicts: falling back to a legacy
        counter is how an ungated ``confirmed`` gets laundered into a true
        positive.
        """
        content = (
            "---\nhunt_id: H-0019\ntitle: Laundering attempt\n---\n\n"
            "**Counts:** `confirmed` 6 · `suspected` 1 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out.get("true_positives", 0) == 0

    def test_body_counts_do_not_resurrect_an_ungated_entry(self) -> None:
        """A rejected entry must not fall through to the body-count scraper.

        Frontmatter presence is what suppresses the body counts, so a `confirmed`
        entry that fails the gate has to report zero rather than handing the file
        to a markdown line claiming nine.
        """
        content = (
            "---\nhunt_id: H-0012\ntitle: Ungated\n"
            "findings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: process_activity rows show crontab spawned by curl\n"
            "    confirmation: ok\n"
            "---\n\n"
            "**Counts:** `confirmed` 9 · `suspected` 0 · "
            "`attempted_not_vulnerable` 0 · `benign` 0 · `inconclusive` 0\n"
        )
        out = Aggregator.extract_from_hunt_file(content)
        assert out["confirmed"] == 0
        assert out["true_positives"] == 0
