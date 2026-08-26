"""Tests for verdict-ladder parsing and the evidence gate in HuntParser."""

from __future__ import annotations

from pathlib import Path

import pytest

from athf.core.hunt_parser import HuntParser

LOCK_BODY = """
# H-0100: Ladder hunt

## LEARN: Prepare the Hunt

Hypothesis.

## OBSERVE: Expected Behaviors

Baseline.

## CHECK: Execute & Analyze

Query.

## KEEP: Findings & Response

Summary.
"""


# Workspace config, written next to the hunt file so the parser loads it the way
# it would in a real workspace. Capabilities live here and never in the hunt file:
# an agent authoring a finding can emit `confirmation`, but it cannot grant itself
# the reach that makes `confirmed` available.
WORKSPACE_CONFIG = """provenance:
  producers:
    analyst:
      capabilities:
        - clickhouse_query
        - host_forensics
        - range_reproduction
        - configuration_review
"""


def _hunt(tmp_path: Path, frontmatter: str) -> HuntParser:
    (tmp_path / ".athfconfig.yaml").write_text(WORKSPACE_CONFIG, encoding="utf-8")
    path = tmp_path / "H-0100.md"
    path.write_text(f"---\n{frontmatter}\n---\n{LOCK_BODY}", encoding="utf-8")
    parser = HuntParser(path)
    parser.parse()
    return parser


BASE = "hunt_id: H-0100\ntitle: Ladder hunt\nstatus: completed\ndate: 2026-08-25"


def _confirmation(detail: str, method: str = "host_forensics", indent: str = "    ") -> str:
    """Render a confirmation mapping as hunt frontmatter YAML.

    ``produced_by`` has to name a producer the config above declared, and the
    method has to be one that producer can reach — that pairing is what the gate
    checks instead of grading ``detail``.
    """
    return (
        f"{indent}confirmation:\n"
        f"{indent}  method: {method}\n"
        f"{indent}  produced_by: analyst\n"
        f"{indent}  attested_by: Sydney Marrone\n"
        f"{indent}  detail: {detail}\n"
    )


def _errors(tmp_path: Path, frontmatter: str) -> list[str]:
    return _hunt(tmp_path, frontmatter).validate()[1]


class TestBackwardsCompatibility:
    def test_hunt_without_ladder_keys_validates_clean(self, tmp_path: Path) -> None:
        ok, errors = _hunt(tmp_path, BASE).validate()
        assert ok, errors

    def test_legacy_counters_validate_clean(self, tmp_path: Path) -> None:
        ok, errors = _hunt(
            tmp_path, BASE + "\ntrue_positives: 1\nfalse_positives: 0"
        ).validate()
        assert ok, errors

    def test_empty_ladder_lists_validate_clean(self, tmp_path: Path) -> None:
        ok, errors = _hunt(tmp_path, BASE + "\nfindings: []\nruled_out: []").validate()
        assert ok, errors


class TestParseExposesLadder:
    def test_findings_and_ruled_out_surface_in_parse(self, tmp_path: Path) -> None:
        parser = _hunt(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: web-prod-04\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity\n"
            "    confirmation: host triage recovered the crontab\n"
            "ruled_out:\n"
            "  - subject: svc_backup\n"
            "    verdict: benign\n"
            "    reason: nightly Veeam agent",
        )
        parsed = parser.parse()
        assert len(parsed["findings"]) == 1
        assert parsed["findings"][0]["verdict"] == "confirmed"
        assert len(parsed["ruled_out"]) == 1

    def test_absent_keys_parse_as_empty_lists(self, tmp_path: Path) -> None:
        parsed = _hunt(tmp_path, BASE).parse()
        assert parsed["findings"] == []
        assert parsed["ruled_out"] == []


class TestEvidenceGate:
    def test_confirmed_without_evidence_or_confirmation_is_rejected(
        self, tmp_path: Path
    ) -> None:
        errors = _errors(
            tmp_path,
            BASE + "\nfindings:\n  - subject: host-a\n    verdict: confirmed",
        )
        assert any("confirmed" in e and "host-a" in e for e in errors)

    def test_confirmed_with_evidence_but_no_confirmation_is_rejected(
        self, tmp_path: Path
    ) -> None:
        """Telemetry alone never reaches confirmed — that is the whole gate."""
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain",
        )
        assert any("confirmed" in e and "host-a" in e for e in errors)

    def test_confirmed_with_both_passes(self, tmp_path: Path) -> None:
        ok, errors = _hunt(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            + _confirmation("recovered the dropper binary from disk"),
        ).validate()
        assert ok, errors

    def test_empty_confirmation_string_does_not_satisfy_the_gate(
        self, tmp_path: Path
    ) -> None:
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: telemetry\n"
            '    confirmation: "   "',
        )
        assert any("host-a" in e for e in errors)

    @pytest.mark.parametrize(
        "value",
        [
            "n/a",
            "N/A",
            "n\\a",
            "na",
            "none",
            "None",
            "null",
            "tbd",
            "TODO",
            "pending",
            "unknown",
            "-",
            "--",
            ".",
            "?",
            "no",
        ],
    )
    def test_placeholder_confirmations_do_not_satisfy_the_gate(
        self, tmp_path: Path, value: str
    ) -> None:
        """'n/a' is how an agent spells 'I did not confirm this'.

        A truthiness check would accept every one of these, which inverts the
        gate: the two commonest natural spellings of "not confirmed" would pass
        while only Python-falsy values failed.
        """
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            f'    confirmation: "{value}"',
        )
        assert any("host-a" in e for e in errors), f"{value!r} slipped through the gate"

    @pytest.mark.parametrize("value", ["true", "1", "[an item]", "{key: value}"])
    def test_non_string_confirmation_does_not_satisfy_the_gate(
        self, tmp_path: Path, value: str
    ) -> None:
        """Confirmation has to be a human-readable account of what was checked."""
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            f"    confirmation: {value}",
        )
        assert any("host-a" in e for e in errors), f"{value} slipped through the gate"

    @pytest.mark.parametrize(
        "value",
        [
            "see telemetry above",
            "See the evidence field",
            "as shown in the logs",
            "per the query results",
            "confirmed by the telemetry",
            "the log data confirms it",
            "see above",
            "same as evidence",
        ],
    )
    def test_pointing_back_at_telemetry_does_not_satisfy_the_gate(
        self, tmp_path: Path, value: str
    ) -> None:
        """Restating the input is the exact shortcut this gate exists to refuse.

        An agent asked to confirm a finding will reach for the cheapest passing
        answer, and the cheapest is to cite the logs it just read. Independent
        confirmation has to come from outside the log corpus.
        """
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            f'    confirmation: "{value}"',
        )
        assert any("host-a" in e for e in errors), f"{value!r} slipped through the gate"

    @pytest.mark.parametrize(
        "method,value",
        [
            ("host_forensics", "host triage recovered the dropper binary from disk"),
            ("range_reproduction", "reproduced the spawn chain in the attack range"),
            (
                "configuration_review",
                "config review confirmed the cron entry was writable",
            ),
            (
                "host_forensics",
                "forensic image shows the crontab entry matching the process_activity log",
            ),
        ],
    )
    def test_genuine_independent_confirmation_passes(
        self, tmp_path: Path, method: str, value: str
    ) -> None:
        """The gate must not block real work, including mentioning telemetry.

        Each detail is paired with the method that actually produced it, declared
        by a producer the workspace config says can reach it. Real work has to keep
        passing — a gate that refuses everything is not a gate.
        """
        ok, errors = _hunt(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            + _confirmation(value, method=method),
        ).validate()
        assert ok, errors

    def test_terse_confirmation_does_not_satisfy_the_gate(self, tmp_path: Path) -> None:
        """'ok' is not an account of independent confirmation."""
        errors = _errors(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-a\n"
            "    verdict: confirmed\n"
            "    evidence: OCSF process_activity showed the spawn chain\n"
            "    confirmation: ok",
        )
        assert any("host-a" in e for e in errors)

    def test_suspected_needs_no_confirmation(self, tmp_path: Path) -> None:
        ok, errors = _hunt(
            tmp_path,
            BASE
            + "\nfindings:\n"
            "  - subject: host-b\n"
            "    verdict: suspected\n"
            "    evidence: 14 failed then 1 successful auth from a new ASN",
        ).validate()
        assert ok, errors


class TestControlNaming:
    def test_attempted_not_vulnerable_without_control_is_rejected(
        self, tmp_path: Path
    ) -> None:
        errors = _errors(
            tmp_path,
            BASE
            + "\nruled_out:\n  - subject: build-runner-02\n    verdict: attempted_not_vulnerable",
        )
        assert any("build-runner-02" in e for e in errors)

    def test_attempted_not_vulnerable_with_control_passes(self, tmp_path: Path) -> None:
        ok, errors = _hunt(
            tmp_path,
            BASE
            + "\nruled_out:\n"
            "  - subject: build-runner-02\n"
            "    verdict: attempted_not_vulnerable\n"
            "    control: SELinux enforcing\n"
            "    reason: ptrace attach denied in audit log",
        ).validate()
        assert ok, errors

    def test_reason_alone_does_not_satisfy_control_naming(self, tmp_path: Path) -> None:
        """`reason` is the generic field every ruled_out entry carries.

        Accepting it would leave "name the control" unenforced for essentially
        every entry, since benign rows use `reason` too.
        """
        errors = _errors(
            tmp_path,
            BASE
            + "\nruled_out:\n"
            "  - subject: build-runner-02\n"
            "    verdict: attempted_not_vulnerable\n"
            "    reason: SELinux enforcing denied the ptrace attach",
        )
        assert any("build-runner-02" in e for e in errors)

    @pytest.mark.parametrize("value", ["n/a", "none", "tbd", "-", "ok"])
    def test_placeholder_control_is_rejected(self, tmp_path: Path, value: str) -> None:
        errors = _errors(
            tmp_path,
            BASE
            + "\nruled_out:\n"
            "  - subject: build-runner-02\n"
            "    verdict: attempted_not_vulnerable\n"
            f'    control: "{value}"',
        )
        assert any("build-runner-02" in e for e in errors), f"{value!r} slipped through"


class TestRoutingRule:
    @pytest.mark.parametrize(
        "verdict", ["attempted_not_vulnerable", "benign", "inconclusive"]
    )
    def test_closed_verdicts_may_not_appear_in_findings(
        self, tmp_path: Path, verdict: str
    ) -> None:
        errors = _errors(
            tmp_path,
            BASE
            + f"\nfindings:\n  - subject: host-c\n    verdict: {verdict}\n    reason: a control held",
        )
        assert any("ruled_out" in e for e in errors)

    @pytest.mark.parametrize("verdict", ["confirmed", "suspected"])
    def test_open_verdicts_may_not_appear_in_ruled_out(
        self, tmp_path: Path, verdict: str
    ) -> None:
        """Routing has to be enforced both ways.

        A `confirmed` entry hiding in ruled_out still counts toward precision,
        which defeats the report separation the split exists for.
        """
        errors = _errors(
            tmp_path,
            BASE
            + f"\nruled_out:\n"
            f"  - subject: host-z\n"
            f"    verdict: {verdict}\n"
            f"    evidence: telemetry\n"
            f"    confirmation: host forensics recovered the dropper binary",
        )
        assert any("findings" in e and "host-z" in e for e in errors)

    @pytest.mark.parametrize("verdict", ["confirmed", "suspected"])
    def test_open_verdicts_belong_in_findings(self, tmp_path: Path, verdict: str) -> None:
        errors = _errors(
            tmp_path,
            BASE
            + f"\nfindings:\n"
            f"  - subject: host-d\n"
            f"    verdict: {verdict}\n"
            f"    evidence: telemetry\n"
            f"    confirmation: host forensics",
        )
        assert not any("ruled_out" in e for e in errors)


class TestMalformedInput:
    def test_invalid_verdict_names_the_offender(self, tmp_path: Path) -> None:
        errors = _errors(
            tmp_path, BASE + "\nfindings:\n  - subject: host-e\n    verdict: totally-pwned"
        )
        assert any("totally-pwned" in e for e in errors)

    def test_hyphenated_verdict_is_accepted(self, tmp_path: Path) -> None:
        ok, errors = _hunt(
            tmp_path,
            BASE
            + "\nruled_out:\n"
            "  - subject: host-f\n"
            "    verdict: attempted-not-vulnerable\n"
            "    control: WAF rule 942100",
        ).validate()
        assert ok, errors

    @pytest.mark.parametrize("verdict", ["tp", "fp"])
    def test_legacy_verdicts_are_rejected_inside_ladder_lists(
        self, tmp_path: Path, verdict: str
    ) -> None:
        """Legacy values live in the legacy scalar keys, not in ladder entries.

        Accepting them here validates clean but tallies zero everywhere, which
        is a silent-undercount path rather than a compatibility win.
        """
        errors = _errors(
            tmp_path,
            BASE + f"\nfindings:\n  - subject: host-h\n    verdict: {verdict}",
        )
        assert any("host-h" in e for e in errors)

    def test_missing_verdict_key_is_an_error_not_a_crash(self, tmp_path: Path) -> None:
        errors = _errors(tmp_path, BASE + "\nfindings:\n  - subject: host-g")
        assert any("verdict" in e for e in errors)

    def test_non_list_findings_is_an_error_not_a_crash(self, tmp_path: Path) -> None:
        errors = _errors(tmp_path, BASE + "\nfindings: not-a-list")
        assert any("findings" in e for e in errors)

    def test_non_mapping_entry_is_an_error_not_a_crash(self, tmp_path: Path) -> None:
        errors = _errors(tmp_path, BASE + "\nruled_out:\n  - just a string")
        assert any("ruled_out" in e for e in errors)

    def test_null_ladder_key_does_not_crash(self, tmp_path: Path) -> None:
        ok, _ = _hunt(tmp_path, BASE + "\nfindings:\nruled_out:").validate()
        assert ok
