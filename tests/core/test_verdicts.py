"""Tests for the verdict ladder vocabulary."""

import pytest

from athf.core.verdicts import (
    CONFIRMED,
    LEGACY_VERDICTS,
    VERDICTS,
    VerdictError,
    counts_as_negative,
    counts_as_positive,
    entry_fails_gate,
    normalize_verdict,
    requires_evidence,
    tally_frontmatter_verdicts,
)


class TestVocabulary:
    def test_canonical_ladder(self):
        assert VERDICTS == (
            "confirmed",
            "suspected",
            "attempted_not_vulnerable",
            "benign",
            "inconclusive",
        )

    def test_legacy_verdicts_still_accepted(self):
        assert set(LEGACY_VERDICTS) == {"tp", "fp"}


class TestNormalize:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("confirmed", "confirmed"),
            ("CONFIRMED", "confirmed"),
            ("  Suspected  ", "suspected"),
            ("attempted_not_vulnerable", "attempted_not_vulnerable"),
            ("attempted-not-vulnerable", "attempted_not_vulnerable"),
            ("benign", "benign"),
            ("inconclusive", "inconclusive"),
        ],
    )
    def test_canonical_values(self, raw, expected):
        assert normalize_verdict(raw) == expected

    @pytest.mark.parametrize("raw", ["tp", "TP", "fp", "FP"])
    def test_legacy_values_preserved_verbatim(self, raw):
        """Legacy TP/FP normalize to lowercase but are NOT remapped onto the
        ladder — a legacy TP never passed the evidence gate, so silently
        promoting it to `confirmed` would fabricate rigor."""
        assert normalize_verdict(raw) == raw.lower()

    @pytest.mark.parametrize("raw", ["maybe", "", "   ", "confirmed_exploited", "true"])
    def test_unknown_rejected(self, raw):
        with pytest.raises(VerdictError):
            normalize_verdict(raw)

    def test_non_string_rejected(self):
        with pytest.raises(VerdictError):
            normalize_verdict(None)


class TestEvidenceGate:
    def test_confirmed_requires_evidence(self):
        assert requires_evidence(CONFIRMED) is True

    @pytest.mark.parametrize(
        "verdict",
        ["suspected", "attempted_not_vulnerable", "benign", "inconclusive", "tp", "fp"],
    )
    def test_other_tiers_do_not_require_evidence(self, verdict):
        assert requires_evidence(verdict) is False


class TestPrecisionBuckets:
    @pytest.mark.parametrize("verdict", ["confirmed", "tp"])
    def test_positive_bucket(self, verdict):
        assert counts_as_positive(verdict) is True
        assert counts_as_negative(verdict) is False

    @pytest.mark.parametrize("verdict", ["benign", "fp"])
    def test_negative_bucket(self, verdict):
        assert counts_as_negative(verdict) is True
        assert counts_as_positive(verdict) is False

    @pytest.mark.parametrize("verdict", ["suspected", "attempted_not_vulnerable", "inconclusive"])
    def test_ungraded_tiers_are_in_neither_bucket(self, verdict):
        """`suspected` is not yet a positive and `attempted_not_vulnerable` is
        not a false positive — keeping both out of the precision math is the
        whole point of the ladder."""
        assert counts_as_positive(verdict) is False
        assert counts_as_negative(verdict) is False


class TestEntryFailsGate:
    """The single gate predicate shared by validation and aggregation.

    `athf hunt validate` and the rollup previously answered "does this entry
    count?" with two different pieces of code, so the tally credited entries
    validate had just rejected. Both now consult this.
    """

    def test_confirmed_entry_with_real_confirmation_passes(self):
        assert (
            entry_fails_gate(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "host triage recovered the crontab entry from disk",
                },
            )
            is False
        )

    def test_confirmed_entry_missing_confirmation_fails(self):
        assert (
            entry_fails_gate(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                },
            )
            is True
        )

    @pytest.mark.parametrize("value", ["n/a", "ok", "tbd", "", "   ", True, 1, None])
    def test_confirmed_entry_with_placeholder_confirmation_fails(self, value):
        assert (
            entry_fails_gate(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": value,
                },
            )
            is True
        ), f"{value!r} slipped past the shared gate"

    def test_misrouted_entry_fails(self):
        """A confirmed entry parked in ruled_out must not be credited."""
        assert (
            entry_fails_gate(
                "ruled_out",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "host triage recovered the crontab entry from disk",
                },
            )
            is True
        )

    def test_attempted_not_vulnerable_without_control_fails(self):
        assert (
            entry_fails_gate("ruled_out", {"verdict": "attempted_not_vulnerable"}) is True
        )

    def test_attempted_not_vulnerable_with_control_passes(self):
        assert (
            entry_fails_gate(
                "ruled_out",
                {"verdict": "attempted_not_vulnerable", "control": "SELinux enforcing, verified"},
            )
            is False
        )

    @pytest.mark.parametrize("verdict", ["suspected", "benign", "inconclusive"])
    def test_ungated_verdicts_pass_on_shape_alone(self, verdict):
        """Inverse case: this fix must not quietly start gating other verdicts.

        `benign` and `inconclusive` need their own referent rules, but that is a
        separate change with its own migration cost. Sneaking it in here would
        silently drop counts on the 127 existing ruled_out entries.
        """
        key = "findings" if verdict == "suspected" else "ruled_out"
        assert entry_fails_gate(key, {"verdict": verdict}) is False

    def test_unknown_verdict_fails(self):
        assert entry_fails_gate("findings", {"verdict": "totally-pwned"}) is True

    def test_legacy_verdict_inside_ladder_list_fails(self):
        assert entry_fails_gate("findings", {"verdict": "tp"}) is True

    def test_missing_verdict_fails(self):
        assert entry_fails_gate("findings", {"subject": "host-a"}) is True

    def test_non_mapping_fails(self):
        assert entry_fails_gate("findings", "a string") is True


class TestTallyRespectsTheGate:
    def test_ungated_confirmed_entry_is_not_credited(self):
        """The bug this fixes: validate rejected, the tally credited anyway."""
        counts = tally_frontmatter_verdicts(
            {
                "findings": [
                    {
                        "subject": "host-a",
                        "verdict": "confirmed",
                        "evidence": "process_activity rows show crontab spawned by curl",
                        "confirmation": "ok",
                    }
                ]
            }
        )
        assert counts["confirmed"] == 0

    def test_gated_and_ungated_entries_are_counted_separately(self):
        counts = tally_frontmatter_verdicts(
            {
                "findings": [
                    {
                        "subject": "host-a",
                        "verdict": "confirmed",
                        "evidence": "process_activity rows show crontab spawned by curl",
                        "confirmation": "host triage recovered the crontab entry from disk",
                    },
                    {
                        "subject": "host-b",
                        "verdict": "confirmed",
                        "evidence": "process_activity rows show crontab spawned by curl",
                        "confirmation": "n/a",
                    },
                ]
            }
        )
        assert counts["confirmed"] == 1

    def test_suspected_still_counted_without_confirmation(self):
        """Inverse case: suspected is the honest ceiling, never gated."""
        counts = tally_frontmatter_verdicts(
            {"findings": [{"subject": "host-a", "verdict": "suspected", "evidence": "burst"}]}
        )
        assert counts["suspected"] == 1

    def test_benign_still_counted(self):
        """Inverse case: `benign` gating is a separate change, not this one."""
        counts = tally_frontmatter_verdicts(
            {"ruled_out": [{"subject": "svc_backup", "verdict": "benign"}]}
        )
        assert counts["benign"] == 1

    def test_list_present_but_fully_ungated_does_not_fall_back_to_legacy(self):
        """A rejected entry must not make the hunt look ladder-free.

        Returning None here would hand the hunt back to the legacy counters and
        let an ungated `confirmed` reappear as a legacy true positive.
        """
        counts = tally_frontmatter_verdicts(
            {"findings": [{"subject": "host-a", "verdict": "confirmed", "confirmation": "ok"}]}
        )
        assert counts is not None
        assert counts["confirmed"] == 0

    def test_no_ladder_keys_still_returns_none(self):
        """Inverse case: legacy hunts must keep falling back to their counters."""
        assert tally_frontmatter_verdicts({"true_positives": 3}) is None
