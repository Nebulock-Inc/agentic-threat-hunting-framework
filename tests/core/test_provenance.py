"""Provenance gate: who produced a confirmation, and could they have.

The prose check on ``confirmation`` was measured to a floor it cannot cross —
"cross-validated by running a second query against the same table" is
grammatically indistinguishable from real corroboration. This gate stops reading
the sentence and asks instead what the producer is capable of.

The invariant every test here defends: **capabilities never travel in the same
payload as the verdict.** An LLM agent emits finding fields; it cannot emit a new
class attribute or rewrite workspace config. So a producer that can only run
queries is capped at ``suspected`` by construction, not by grading its prose.

Each rule is tested with its inverse. The last round shipped a synonym
false-positive because the tests agreed with the implementation's assumptions
instead of probing them.
"""

from __future__ import annotations

import pytest

from athf.core.provenance import (
    CORPUS_ONLY_CAPABILITIES,
    ProducerRegistry,
)
from athf.core.verdicts import (
    CIRCULAR_CONFIRMATION,
    CORPUS_ONLY_METHOD,
    LEGACY_VERDICT,
    METHOD_EXCEEDS_CAPABILITY,
    MISSING_PROVENANCE,
    SELF_ATTESTED,
    SELF_DECLARED_CAPABILITY,
    UNATTESTED,
    UNKNOWN_PRODUCER,
    gate_failures,
    tally_frontmatter_verdicts,
)


def codes(failures):
    """Reason codes only — details are asserted explicitly where they matter."""
    return {code for code, _ in failures}


# A registry shaped the way workspace config would supply it. ``analyst`` can do
# outside-corpus work; ``query-bot`` is the deep_baseline_investigator case.
CONFIG = {
    "provenance": {
        "producers": {
            "analyst": {"capabilities": ["clickhouse_query", "host_forensics"]},
            "query-bot": {"capabilities": ["clickhouse_query"]},
            "mute": {"capabilities": []},
            "shapeless": {},
        }
    }
}


@pytest.fixture
def registry():
    return ProducerRegistry.from_config(CONFIG)


def confirmed(**overrides):
    """A ``confirmed`` finding that passes every gate predating provenance."""
    entry = {
        "subject": "web-prod-04 / svc_deploy",
        "verdict": "confirmed",
        "evidence": "process_activity shows curl piping to sh under the deploy user",
        "confirmation": {
            "method": "host_forensics",
            "produced_by": "analyst",
            "attested_by": "Sydney Marrone",
            "detail": "recovered the dropped binary at /usr/local/bin/.upd on disk",
        },
    }
    entry.update(overrides)
    return entry


def confirmation(**overrides):
    """Mutate only the confirmation mapping."""
    body = dict(confirmed()["confirmation"])
    body.update(overrides)
    return confirmed(confirmation=body)


class TestRestrictiveByDefault:
    """No declaration means ``confirmed`` is refused — including for the author."""

    def test_no_registry_refuses_confirmed(self):
        # The decision: absence is restrictive. A permissive fallback would mean
        # every producer that skips the declaration keeps writing confirmed.
        #
        # The reason code is UNKNOWN_PRODUCER rather than MISSING_PROVENANCE: the
        # finding did supply provenance, the workspace just never declared the
        # producer. Both refuse confirmed; this one points the hunter at config
        # instead of blaming their finding.
        assert UNKNOWN_PRODUCER in codes(gate_failures("findings", confirmed()))

    def test_no_registry_still_allows_suspected(self):
        # The inverse. The gate applies to confirmed only; capping suspected too
        # would leave a corpus-only agent with nothing honest to emit.
        entry = {
            "subject": "fin-laptop-11",
            "verdict": "suspected",
            "evidence": "impossible-travel sign-ins 40 minutes apart from two ASNs",
        }
        assert gate_failures("findings", entry) == []

    def test_prose_confirmation_no_longer_reaches_confirmed(self, registry):
        # A string confirmation carries no producer, so it cannot clear the gate
        # however well it reads. This is the measured-ceiling fix: perfect prose
        # is not evidence that the work happened.
        entry = confirmed(
            confirmation="forensic image shows the crontab entry matching process_activity"
        )
        assert MISSING_PROVENANCE in codes(gate_failures("findings", entry, registry=registry))

    def test_empty_capability_list_refuses_confirmed(self, registry):
        entry = confirmation(produced_by="mute", method="host_forensics")
        assert METHOD_EXCEEDS_CAPABILITY in codes(
            gate_failures("findings", entry, registry=registry)
        )

    def test_producer_without_capabilities_key_refuses_confirmed(self, registry):
        # Registered but silent about capability is not the same as capable.
        entry = confirmation(produced_by="shapeless")
        assert METHOD_EXCEEDS_CAPABILITY in codes(
            gate_failures("findings", entry, registry=registry)
        )


class TestCapabilityCeiling:
    """A producer cannot claim a method it never declared."""

    def test_method_outside_declared_capability_is_refused(self, registry):
        # The structural heart. query-bot declares clickhouse_query only, so
        # host_forensics is unreachable no matter what its detail prose says.
        entry = confirmation(produced_by="query-bot", method="host_forensics")
        assert METHOD_EXCEEDS_CAPABILITY in codes(
            gate_failures("findings", entry, registry=registry)
        )

    def test_declared_method_passes(self, registry):
        # The inverse. Without this the gate could pass by refusing everything.
        assert gate_failures("findings", confirmed(), registry=registry) == []

    def test_unregistered_producer_is_refused(self, registry):
        entry = confirmation(produced_by="ghost-agent")
        assert UNKNOWN_PRODUCER in codes(gate_failures("findings", entry, registry=registry))

    def test_missing_produced_by_is_refused(self, registry):
        entry = confirmed()
        del entry["confirmation"]["produced_by"]
        assert gate_failures("findings", entry, registry=registry) != []

    def test_capability_vocabulary_stays_open(self):
        # Orgs must be able to declare confirming work the framework never
        # enumerated. A closed enum would make the gate wrong for everyone else.
        reg = ProducerRegistry.from_config(
            {"provenance": {"producers": {"ir": {"capabilities": ["memory_forensics"]}}}}
        )
        entry = confirmation(produced_by="ir", method="memory_forensics")
        assert gate_failures("findings", entry, registry=reg) == []

    def test_querying_never_confirms_even_when_declared(self, registry):
        # analyst really can run ClickHouse queries, and that is still not
        # confirmation — the corpus cannot corroborate itself. Declaring a
        # corpus-only capability must not unlock confirmed.
        entry = confirmation(produced_by="analyst", method="clickhouse_query")
        assert CORPUS_ONLY_METHOD in codes(gate_failures("findings", entry, registry=registry))

    def test_every_corpus_only_capability_is_refused_as_a_method(self):
        reg = ProducerRegistry.from_config(
            {
                "provenance": {
                    "producers": {
                        "everything": {"capabilities": sorted(CORPUS_ONLY_CAPABILITIES)}
                    }
                }
            }
        )
        for method in sorted(CORPUS_ONLY_CAPABILITIES):
            entry = confirmation(produced_by="everything", method=method)
            assert CORPUS_ONLY_METHOD in codes(
                gate_failures("findings", entry, registry=reg)
            ), f"{method} must not confirm"


class TestSelfDeclarationIsIgnored:
    """Capabilities in the finding are the forgeable field this replaces."""

    def test_capabilities_in_the_entry_are_refused(self, registry):
        # One token to forge, same authoring pass as the verdict. If this ever
        # passes, the gate has become the field it was built to replace.
        entry = confirmed()
        entry["analyst_capabilities"] = ["host_forensics"]
        entry["confirmation"] = dict(entry["confirmation"], produced_by="query-bot")
        assert SELF_DECLARED_CAPABILITY in codes(
            gate_failures("findings", entry, registry=registry)
        )

    def test_capabilities_inside_confirmation_are_refused(self, registry):
        entry = confirmation(produced_by="query-bot", capabilities=["host_forensics"])
        assert SELF_DECLARED_CAPABILITY in codes(
            gate_failures("findings", entry, registry=registry)
        )

    def test_registry_is_not_mutated_by_a_finding(self, registry):
        entry = confirmation(produced_by="query-bot", capabilities=["host_forensics"])
        gate_failures("findings", entry, registry=registry)
        assert registry.capabilities_for("query-bot") == frozenset({"clickhouse_query"})


class TestAttestation:
    """A named human, not a role and not the agent."""

    def test_missing_attestation_is_refused(self, registry):
        entry = confirmed()
        del entry["confirmation"]["attested_by"]
        assert UNATTESTED in codes(gate_failures("findings", entry, registry=registry))

    @pytest.mark.parametrize(
        "value",
        [
            "AI Assistant",  # the athf hunt new default — a placeholder by shipping
            "agent",
            "automation",
            "n/a",
            "unknown",
            "the team",
            "",
            "   ",
            True,
            None,
        ],
    )
    def test_placeholder_attestation_is_refused(self, registry, value):
        entry = confirmation(attested_by=value)
        assert UNATTESTED in codes(gate_failures("findings", entry, registry=registry))

    def test_named_human_passes(self, registry):
        # The inverse, and a guard against a name-shaped regex rejecting people.
        for name in ("Sydney Marrone", "J. Halloran", "sydney@nebulock.ai"):
            entry = confirmation(attested_by=name)
            assert gate_failures("findings", entry, registry=registry) == [], name


class TestAttestationIsIndependentOfTheProducer:
    """A producer cannot vouch for itself.

    ``attested_by`` exists so a second party is answerable for work that happened
    outside the corpus. When the same name fills both fields, nobody independent
    vouched for anything — the finding asserts "I did it, and I confirm I did it",
    which is the self-declaration the whole design moves out of the payload.

    Unlike the role-word denylist this is a closed rule: the producer name is
    already in the finding, so the check is a comparison rather than an
    enumeration, and it cannot be evaded by picking different vocabulary.
    """

    def test_producer_cannot_attest_to_itself(self, registry):
        entry = confirmation(produced_by="analyst", attested_by="analyst")
        assert SELF_ATTESTED in codes(gate_failures("findings", entry, registry=registry))

    def test_self_attestation_survives_case_and_padding(self, registry):
        # The comparison has to normalize, or the rule is one shift key wide.
        for spelling in ("Analyst", "  analyst  ", "ANALYST"):
            entry = confirmation(produced_by="analyst", attested_by=spelling)
            assert SELF_ATTESTED in codes(
                gate_failures("findings", entry, registry=registry)
            ), spelling

    def test_another_registered_producer_cannot_attest(self, registry):
        # A registered producer is a tool or a team in config, not a person who
        # can be asked about it. Naming a *different* one is still not a human
        # attestation, so the gate refuses it for the same reason.
        entry = confirmation(produced_by="analyst", attested_by="query-bot")
        assert SELF_ATTESTED in codes(gate_failures("findings", entry, registry=registry))

    def test_a_human_attesting_to_a_producer_still_passes(self, registry):
        # The inverse, and the case the field is for: a person vouches for the
        # tool's output. This must stay clean or the gate is unusable.
        entry = confirmation(produced_by="analyst", attested_by="Sydney Marrone")
        assert gate_failures("findings", entry, registry=registry) == []

    def test_a_human_whose_name_is_not_in_config_passes(self, registry):
        # Guard against implementing this as "attested_by must be absent from the
        # registry" in a way that also rejects unregistered *tools*: the rule is
        # about the producer relationship, not about registry membership per se.
        entry = confirmation(produced_by="analyst", attested_by="J. Halloran")
        assert gate_failures("findings", entry, registry=registry) == []

    def test_self_attestation_is_refused_for_a_capable_producer(self, registry):
        # The break as found: every other gate satisfied, capability real, detail
        # substantive — and still refused, because the attestation is circular.
        entry = confirmed(
            confirmation={
                "method": "host_forensics",
                "produced_by": "analyst",
                "attested_by": "analyst",
                "detail": "host triage recovered the crontab entry for svc_deploy from disk",
            }
        )
        assert SELF_ATTESTED in codes(gate_failures("findings", entry, registry=registry))

    def test_self_attestation_is_not_counted_by_aggregation(self, registry):
        # Validation and aggregation have diverged twice on this design. The tally
        # must refuse what validate refuses, or the dashboard credits it anyway.
        frontmatter = {
            "findings": [
                confirmed(
                    confirmation={
                        "method": "host_forensics",
                        "produced_by": "analyst",
                        "attested_by": "analyst",
                        "detail": "recovered the launchd plist from the endpoint disk image",
                    }
                )
            ]
        }
        counts = tally_frontmatter_verdicts(frontmatter, registry)
        assert counts is not None
        assert counts["confirmed"] == 0

    def test_unattributable_placeholder_still_reports_unattested(self, registry):
        # Two different problems keep two different reason codes: naming nobody is
        # not the same as a producer naming itself, and the hunter needs the
        # instruction that matches their mistake.
        entry = confirmation(produced_by="analyst", attested_by="the team")
        assert UNATTESTED in codes(gate_failures("findings", entry, registry=registry))


class TestProseDetailStillGated:
    """Provenance adds a gate; it does not retire the circularity check."""

    def test_circular_detail_is_still_refused(self, registry):
        # A capable producer with a named attestor can still write a circular
        # account, and it must still fail. Provenance says the work was possible,
        # not that this sentence describes it.
        entry = confirmation(detail="see telemetry above")
        assert CIRCULAR_CONFIRMATION in codes(
            gate_failures("findings", entry, registry=registry)
        )

    def test_missing_detail_is_refused(self, registry):
        entry = confirmation(detail="n/a")
        assert gate_failures("findings", entry, registry=registry) != []

    def test_substantive_detail_passes(self, registry):
        entry = confirmation(
            detail="replayed the technique on a sacrificial host in the range"
        )
        assert gate_failures("findings", entry, registry=registry) == []


class TestBackwardsCompatibility:
    """Ships to PyPI. Existing files must not gain new meaning."""

    def test_legacy_verdicts_are_never_promoted(self, registry):
        for verdict in ("tp", "fp"):
            failures = codes(gate_failures("findings", {"verdict": verdict}, registry=registry))
            assert failures == {LEGACY_VERDICT}

    def test_ungated_verdicts_are_untouched_by_provenance(self, registry):
        entry = {
            "subject": "build-runner-02",
            "verdict": "attempted_not_vulnerable",
            "reason": "execution blocked before the payload ran",
            "control": "SELinux enforcing mode",
        }
        assert gate_failures("ruled_out", entry, registry=registry) == []

    def test_registry_from_config_without_provenance_section(self):
        # Every workspace on PyPI today. Must load, and must be restrictive.
        reg = ProducerRegistry.from_config({"siem": "Splunk"})
        assert reg.is_empty()
        assert UNKNOWN_PRODUCER in codes(
            gate_failures("findings", confirmed(), registry=reg)
        )


class TestConfigCannotBeShadowedFromInsideTheHuntTree:
    """A config an agent can write must not be the config that licenses it.

    ``load_registry`` walks up from a starting directory and takes the first
    config it finds. Handed a hunt file's own directory, that walk starts inside
    the tree the finding author writes to — so an agent with file-write access
    drops ``.athfconfig.yaml`` next to ``H-0042.md``, declares itself capable of
    ``host_forensics``, and ``athf hunt validate`` accepts the ``confirmed``.

    That collapses the whole design. The point of putting capabilities in config
    was that an agent emitting findings cannot reach the file that grants them;
    if the grant can sit in the same directory as the claim, it is a
    self-declaration wearing a different filename.

    Resolution has to be anchored above the hunt tree, and validation has to
    agree with aggregation — a shadow config also made the two disagree, with
    validate reporting the file clean while the tally credited nothing.
    """

    CONFIRMED_ENTRY = (
        "findings:\n"
        "  - subject: host dev-20\n"
        "    verdict: confirmed\n"
        "    evidence: process_activity rows show crontab spawned by curl\n"
        "    confirmation:\n"
        "      method: host_forensics\n"
        "      produced_by: baseline-agent\n"
        "      attested_by: Sydney Marrone\n"
        "      detail: recovered the dropped binary from the imaged disk\n"
    )

    LOCK = "\n## LEARN\nx\n\n## OBSERVE\nx\n\n## CHECK\nx\n\n## KEEP\nx\n"

    SHADOW = (
        "provenance:\n"
        "  producers:\n"
        "    baseline-agent:\n"
        "      capabilities: [clickhouse_query, host_forensics]\n"
    )

    def _workspace(self, tmp_path):
        """Root config declares nothing; a shadow config sits by the hunt file."""
        (tmp_path / ".athfconfig.yaml").write_text(
            "workspace_name: shadow-test\n", encoding="utf-8"
        )
        deep = tmp_path / "hunts" / "production" / "2026" / "Q2"
        deep.mkdir(parents=True)
        (deep / ".athfconfig.yaml").write_text(self.SHADOW, encoding="utf-8")
        hunt = deep / "H-0042.md"
        hunt.write_text(
            "---\nhunt_id: H-0042\ntitle: Shadowed\nstatus: completed\n"
            f"date: 2026-08-26\n{self.CONFIRMED_ENTRY}---\n{self.LOCK}",
            encoding="utf-8",
        )
        return hunt

    def test_shadow_config_does_not_license_confirmed(self, tmp_path):
        from athf.core.hunt_parser import HuntParser

        hunt = self._workspace(tmp_path)
        parser = HuntParser(hunt)
        parser.parse()
        _, errors = parser.validate()

        assert any("baseline-agent" in e for e in errors), (
            "a config inside the hunt tree must not declare a producer; "
            f"got errors={errors!r}"
        )

    def test_root_config_still_licenses_confirmed(self, tmp_path):
        """Inverse: anchoring must not break the legitimate case.

        The same finding, with the producer declared at the workspace root
        instead, has to keep validating — otherwise the fix just bans
        ``confirmed`` everywhere and the gate looks like it works.
        """
        from athf.core.hunt_parser import HuntParser

        hunt = self._workspace(tmp_path)
        (hunt.parent / ".athfconfig.yaml").unlink()
        (tmp_path / ".athfconfig.yaml").write_text(self.SHADOW, encoding="utf-8")

        parser = HuntParser(hunt)
        parser.parse()
        is_valid, errors = parser.validate()
        assert is_valid, errors

    def test_config_subdirectory_at_root_still_works(self, tmp_path):
        """``config/.athfconfig.yaml`` is the layout ``athf init`` creates."""
        from athf.core.hunt_parser import HuntParser

        hunt = self._workspace(tmp_path)
        (hunt.parent / ".athfconfig.yaml").unlink()
        (tmp_path / ".athfconfig.yaml").unlink()
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / ".athfconfig.yaml").write_text(
            self.SHADOW, encoding="utf-8"
        )

        parser = HuntParser(hunt)
        parser.parse()
        is_valid, errors = parser.validate()
        assert is_valid, errors

    def test_validation_and_aggregation_resolve_the_same_registry(self, tmp_path):
        """The two surfaces must not disagree about who is declared.

        A shadow config previously gave validation a producer that aggregation
        never saw, which is the divergence class that already shipped once.
        """
        from athf.core.hunt_manager import HuntManager
        from athf.core.hunt_parser import HuntParser

        hunt = self._workspace(tmp_path)
        manager = HuntManager(tmp_path / "hunts")

        parser = HuntParser(hunt)
        parser.parse()
        is_valid, _ = parser.validate()

        counted = sum(h.get("confirmed", 0) for h in manager.list_hunts())
        assert is_valid == bool(counted), (
            f"validate says valid={is_valid} but tally counted {counted}"
        )
