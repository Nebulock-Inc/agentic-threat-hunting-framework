"""Tests for the verdict ladder vocabulary."""

import pytest

from athf.core.verdicts import (
    CONFIRMED,
    LEGACY_VERDICTS,
    VERDICTS,
    VerdictError,
    counts_as_negative,
    counts_as_positive,
    normalize_verdict,
    requires_evidence,
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
