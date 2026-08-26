"""Tests for the verdict ladder vocabulary."""

import pytest

from athf.core.verdicts import (
    CIRCULAR_CONFIRMATION,
    CONFIRMED,
    DEFERRED_CONFIRMATION,
    LEGACY_VERDICTS,
    VERDICTS,
    VerdictError,
    cites_the_corpus,
    counts_as_negative,
    counts_as_positive,
    defers_confirmation,
    entry_fails_gate,
    gate_failures,
    is_substantive,
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


class TestCitesTheCorpus:
    """Pointer phrasings that answer "how did you confirm?" with "look at the input".

    Measured against a 100/128 labeled corpus. Every string below is quoted from
    that measurement, so the numbers in the comments are reproducible rather than
    asserted.
    """

    @pytest.mark.parametrize(
        "value",
        [
            "see telemetry above",
            "See the evidence above.",
            "please see the query results above",
            "same as evidence",
            "same as above",
            "per the query results",
            "Per the telemetry, this is confirmed.",
            "confirmed by the telemetry",
            "Confirmation from the log data.",
            "validated in the events we already have",
        ],
    )
    def test_corpus_pointers_are_caught(self, value):
        assert cites_the_corpus(value) is True, f"{value!r} pointed at the corpus and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "- see telemetry above",
            "* see the evidence above",
            "**see above**",
            "**See telemetry above.**",
            "> see the query results above",
            '"see telemetry above"',
            "​see telemetry above",
            "1. See telemetry above",
            "[see above](#evidence)",
            "_same as above_",
            "(see telemetry above)",
            "Reviewed the host configuration. Actually just see telemetry above.",
        ],
    )
    def test_lead_in_evasions_are_normalized_away(self, value):
        """A bullet, a bold marker, or a zero-width space used to buy a pass.

        Twelve of the measured false negatives were this and nothing else — the
        pattern was anchored at the string start and a single leading character
        moved the pointer out of reach.
        """
        assert cites_the_corpus(value) is True, f"{value!r} evaded via its lead-in"

    @pytest.mark.parametrize(
        "value",
        [
            "As documented in the range runbook, we replayed the technique on a "
            "sacrificial host and observed the same registry writes.",
            "As described in incident report IR-2026-0431, the artifact was recovered "
            "from disk by the forensics team.",
            "As shown in the attached forensic timeline from the disk image, the file "
            "predates the first execution.",
            "As noted in the vendor's malware analysis report, the loader writes exactly "
            "this persistence key.",
            "As stated by the system administrator during the interview, no maintenance "
            "window covered this activity.",
            "See the attached forensic report IR-2026-0431 for the recovered crontab and "
            "disk timeline.",
            "See the attack range reproduction notes; the technique was detonated and the "
            "artifact captured on disk.",
            "The forensic image data confirms the artifact exists on disk independent of "
            "the EDR telemetry.",
        ],
    )
    def test_citing_outside_work_is_not_citing_the_corpus(self, value):
        """These are the eight measured false positives — real corroboration, blocked.

        Six came from one pattern that matched citation *grammar* (`^as shown`)
        with no corpus noun anywhere in it. A hunter who writes up their range
        detonation in a runbook and then cites the runbook has done the work; the
        gate was punishing them for the sentence they chose to open with.
        """
        assert cites_the_corpus(value) is False, f"{value!r} is real work and was blocked"

    @pytest.mark.parametrize(
        "value",
        [
            "As shown in the telemetry above.",
            "As described in the evidence above.",
            "As noted in the query output.",
            "As documented in the events listed above.",
            "As detailed in the logs.",
            "As stated in the evidence field.",
            "​As shown in the telemetry above.",
        ],
    )
    def test_citation_grammar_still_caught_when_it_names_the_corpus(self, value):
        """The distinction the deleted pattern could not make.

        `As documented in the range runbook` and `As documented in the events
        above` share an opening and mean opposite things. Requiring the corpus
        noun keeps the second blocked without punishing the first.
        """
        assert cites_the_corpus(value) is True, f"{value!r} cited the corpus and passed"

    def test_possessive_corpus_still_counts(self):
        """"Our telemetry confirms it" is the same claim as "the telemetry confirms it"."""
        assert cites_the_corpus("Our telemetry independently confirms the finding.") is True

    def test_naming_telemetry_alongside_outside_work_is_fine(self):
        """Inverse case: the corroboration the ladder actually wants says both."""
        assert (
            cites_the_corpus(
                "Forensic image of the host shows the crontab entry matching the "
                "process_activity telemetry."
            )
            is False
        )

    def test_non_string_is_not_a_citation(self):
        assert cites_the_corpus(None) is False
        assert cites_the_corpus(True) is False


class TestDefersConfirmation:
    """Saying you did not do the confirmation, in a field asserting you did.

    Distinct from citing the corpus: a deferral is honest about the gap. The
    verdict is still wrong — this is `suspected` — but the message a hunter
    should see is "downgrade it", not "you reasoned in a circle".
    """

    @pytest.mark.parametrize(
        "value",
        [
            "Pending host forensics.",
            "Pending forensic acquisition of the host.",
            "Awaiting the host image from the endpoint team.",
            "Independent confirmation is still outstanding.",
            "Confirmation deferred to the IR team.",
            "Planned: detonate in the attack range next sprint.",
        ],
    )
    def test_temporal_deferral_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} deferred and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "Will confirm once the host is available.",
            "To be confirmed after the range test.",
            "Not yet independently verified.",
            "Forensics requested but not yet returned.",
            "Requires further validation by the IR team.",
            "Interview with the admin has not happened yet.",
        ],
    )
    def test_future_tense_deferral_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} deferred and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "No independent confirmation performed.",
            "No independent confirmation was possible.",
            "No forensic artifacts were recovered.",
            "Range reproduction not attempted.",
            "We did not perform configuration review.",
            "Host is offline, so no forensics were performed.",
            "No out-of-band confirmation obtained.",
            "Interviewed the administrator. She was unavailable, so this remains unconfirmed.",
        ],
    )
    def test_negated_confirmation_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} negated itself and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "Could not validate.",
            "Could not validate outside the log corpus.",
            "Unable to confirm independently.",
            "Unable to acquire the host before it was reimaged.",
            "Confirmation attempt failed; the artifact had been deleted.",
        ],
    )
    def test_incapacity_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} admitted incapacity and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "Assumed confirmed based on prior similar hunts.",
            "Presumed malicious without further validation.",
            "Inferred from the surrounding activity.",
            "This is self-evident from the pattern.",
        ],
    )
    def test_hedging_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} hedged and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "Out of scope for this hunt.",
            "Deprioritized by the IR lead.",
            "Accepted risk, no further work planned.",
            "Closed without confirmation at the customer's request.",
        ],
    )
    def test_declining_the_work_is_caught(self, value):
        assert defers_confirmation(value) is True, f"{value!r} declined the work and passed"

    @pytest.mark.parametrize(
        "value",
        [
            "Host forensics on WKSTN-4471 recovered the scheduled task XML under "
            "C:\\Windows\\System32\\Tasks\\Updater, independently corroborating the "
            "query results.",
            "Validated in the attack range that the legitimate deployment tool cannot "
            "produce this argument pattern, which rules out the benign explanation.",
            "Confirmed with the on-call SRE that no maintenance was scheduled, ruling "
            "out the change-management explanation.",
            "Reviewed the IAM policy document and the role could not have assumed the "
            "admin role before the change.",
            "Detonated in the attack range; the sandbox report is attached.",
        ],
    )
    def test_deferral_words_inside_real_work_still_pass(self, value):
        """Inverse case, and the reason these patterns are narrowed.

        A Windows scheduled task, a tool that *cannot* produce an argument, a
        maintenance window that was not scheduled — the deferral vocabulary
        collides with ordinary hunting prose. The first three are the measured
        collateral damage from the unnarrowed patterns; blocking them would teach
        hunters that the gate is noise and to route around it.
        """
        assert defers_confirmation(value) is False, f"{value!r} is real work and was blocked"

    def test_non_string_is_not_a_deferral(self):
        assert defers_confirmation(None) is False


class TestTheResidualIsAcknowledged:
    """Circular confirmations that no pattern set will ever catch.

    These assert the gap on purpose. Every string below is a claim to have
    confirmed a finding using nothing but the corpus, phrased with no pointer and
    no admission. "Cross-validated by running a second query against the same
    table" is grammatically indistinguishable from real corroboration; the only
    thing that separates them is whether the analyst could have run anything but a
    query, which is a fact about the analyst, not about the sentence.

    Measured residual: 14 of 128, after false positives reached zero. The next
    increment of recall costs precision on real hunting prose, which is the trade
    that made the gate worth routing around in the first place. Closing this needs
    provenance — what the producer was capable of, and who attests to it — not a
    fifteenth pattern.
    """

    @pytest.mark.parametrize(
        "value",
        [
            "The finding is supported by the telemetry we already collected.",
            "I re-ran the query and got the same rows, which validates the finding.",
            "Cross-validated by running a second query against the same table.",
            "The volume of matching rows makes this conclusive.",
            "The detection fired, which confirms the behavior.",
            "Verified by reading the raw event JSON.",
        ],
    )
    def test_undetectable_circularity_passes_the_prose_check(self, value):
        assert cites_the_corpus(value) is False
        assert defers_confirmation(value) is False

    def test_a_passing_confirmation_is_not_a_confirmed_verdict(self):
        """What the gate actually promises.

        An empty failure list means no known bad phrasing was recognized. It does
        not mean the confirmation happened. Anything reading `gate_failures` as
        proof of rigor has the contract backwards.
        """
        assert (
            gate_failures(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "Cross-validated by running a second query "
                    "against the same table.",
                },
            )
            == []
        )


class TestSubstantiveIsUnchanged:
    """Inverse case: the floor and placeholder set were measured clean.

    Both block 0 of 100 legitimate confirmations, so this change must leave them
    exactly as they are. Pinned here because they are the cheapest thing to
    "improve" while reintroducing false positives.
    """

    @pytest.mark.parametrize("value", ["n/a", "ok", "tbd", "pending", "none", "?", "-", ""])
    def test_placeholders_still_rejected(self, value):
        assert is_substantive(value) is False

    @pytest.mark.parametrize(
        "value",
        [
            "Detonated in range.",
            "Crontab recovered.",
            "IR-2026-0431 attached.",
        ],
    )
    def test_short_but_real_confirmations_still_pass_the_floor(self, value):
        assert is_substantive(value) is True

    @pytest.mark.parametrize("value", [True, 1, None, {"method": "forensics"}, ["a"]])
    def test_non_strings_still_rejected(self, value):
        assert is_substantive(value) is False


class TestGateDistinguishesCircularFromDeferred:
    def test_corpus_citation_reports_circular(self):
        codes = [
            code
            for code, _ in gate_failures(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "confirmed by the telemetry above",
                },
            )
        ]
        assert CIRCULAR_CONFIRMATION in codes
        assert DEFERRED_CONFIRMATION not in codes

    def test_deferral_reports_deferred(self):
        """A different failure needs a different instruction.

        Telling a hunter who wrote "pending host forensics" that they reasoned in
        a circle is wrong and unhelpful — they know the gap; they need to be told
        the verdict is `suspected` until it closes.
        """
        codes = [
            code
            for code, _ in gate_failures(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "Pending host forensics on the endpoint.",
                },
            )
        ]
        assert DEFERRED_CONFIRMATION in codes
        assert CIRCULAR_CONFIRMATION not in codes

    def test_real_confirmation_reports_nothing(self):
        assert (
            gate_failures(
                "findings",
                {
                    "verdict": "confirmed",
                    "evidence": "process_activity rows show crontab spawned by curl",
                    "confirmation": "As documented in the range runbook, we replayed the "
                    "technique on a sacrificial host and observed the same registry writes.",
                },
            )
            == []
        )

    @pytest.mark.parametrize("verdict", ["suspected", "benign", "inconclusive"])
    def test_only_confirmed_is_checked_for_deferral(self, verdict):
        """Inverse case: `suspected` is where a deferral belongs.

        "Pending host forensics" is the correct thing to write on a suspected
        finding. Applying the deferral check to every verdict would punish
        hunters for documenting the gap honestly.
        """
        key = "findings" if verdict == "suspected" else "ruled_out"
        assert (
            entry_fails_gate(
                key,
                {
                    "verdict": verdict,
                    "evidence": "authentication burst from a single source",
                    "confirmation": "Pending host forensics.",
                },
            )
            is False
        )


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
