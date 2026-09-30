"""Conformance tests for the shipped GATES examples.

The examples are reference material an authoring agent copies from, so a defect in
one propagates into every document written afterwards. Three of these checks exist
because an example actually drifted from the contract:

* `H-0065_EXAMPLE` was markdown while its hunt-level verdict was TIME_BOX — a
  deployable verdict, which the routing rule sends to `.yaml`. A consumer following
  the contract looked for a `.yaml` and found nothing.
* `H-0062_EXAMPLE`, labelled "the reference for conformant YAML output", recorded a
  CONDITIONAL candidate's prerequisites under `gates_assessment.conditional_requirements`
  — a field the schema never declared. Downstream read the declared path, found
  nothing, and surfaced a blocked detection with no way to unblock it.
* Several examples once stated a `base_score` their own criteria didn't sum to.

`AGENT_MEMORY_SCHEMA.md` is the contract; these assertions are that document's
closed sets and required-field rules, applied to what the repo actually ships.
"""

import pathlib
import re

import pytest
import yaml

EXAMPLES = pathlib.Path(__file__).resolve().parent.parent / ".claude/skills/gates/examples/outputs"

# Canonical enums — AGENT_MEMORY_SCHEMA.md "Canonical enums".
DEPLOYABLE = {"PROMOTE", "CONDITIONAL", "TIME_BOX"}
ARCHIVAL = {"HOLD", "DROP", "RECURRING_HUNT"}
VERDICTS = DEPLOYABLE | ARCHIVAL
CRITERIA_POINTS = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}
GATES = ("generalizable", "additive", "tunable", "exposure_tested", "sustainable")
ENGINES = {"sigma", "sql", "sch_sql", "composite"}
STATUSES = {"TEST", "PRODUCTION", "DISABLED"}

# Field names that have held prerequisites in some draft but are not the declared
# one. The declared home is `deployment.operational_parameters.deployment_prerequisites`.
UNDECLARED_PREREQ_KEYS = ("conditional_requirements", "prerequisites", "deployment_prerequisites")


def _yaml_examples():
    paths = sorted(EXAMPLES.glob("*_EXAMPLE.yaml"))
    assert paths, f"no YAML examples found under {EXAMPLES}"
    return paths


def _stated_verdicts(text):
    """Yield the verdict each ``Verdict:`` line in a markdown narrative states.

    The verdict is the first enum token after the colon, so the emphasis and status
    emoji the examples wrap it in (``**Verdict:** ❌ RECURRING_HUNT``) don't hide it —
    matching a literal ``**Verdict:** PROMOTE`` missed exactly that spelling. Only the
    first token counts: a line reading "RECURRING_HUNT (not PROMOTE — G FAILed)"
    states one verdict and mentions another.
    """
    for line in text.splitlines():
        if "verdict:" not in line.lower():
            continue
        tail = line.split(":", 1)[1]
        stated = next((t for t in re.findall(r"[A-Z][A-Z_]{2,}", tail) if t in VERDICTS), None)
        if stated:
            yield stated


def _candidates(doc):
    """Yield ``(candidate_id, candidate)`` for every candidate in a document."""
    for cand in doc.get("detections") or []:
        yield cand.get("candidate_id"), cand


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_example_parses_and_declares_a_hunt_level_verdict(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert doc["hunt_metadata"]["hunt_id"].startswith("H-")
    assert doc["gates_validation"]["verdict"] in VERDICTS


def test_extension_matches_the_hunt_level_verdict():
    """Deployable → `.yaml`, archival → `.md`. The *hunt-level* verdict decides."""
    for path in _yaml_examples():
        verdict = yaml.safe_load(path.read_text(encoding="utf-8"))["gates_validation"]["verdict"]
        assert verdict in DEPLOYABLE, (
            f"{path.name} is YAML but its hunt-level verdict is {verdict}, which is "
            f"archival — an archival hunt emits `.md`."
        )

    # The converse: a `.md` example must not be a deployable hunt. Markdown examples
    # have no parseable verdict, so read the line that states it.
    for path in sorted(EXAMPLES.glob("*_EXAMPLE.md")):
        for stated in _stated_verdicts(path.read_text(encoding="utf-8")):
            assert stated not in DEPLOYABLE, (
                f"{path.name} is markdown but states verdict {stated}, which is "
                f"deployable — a deployable hunt emits `.yaml`."
            )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_candidate_ids_are_stable_slugs_and_unique(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    seen = set()
    for cid, _cand in _candidates(doc):
        assert isinstance(cid, str) and cid, f"{path.name}: a candidate has no candidate_id"
        assert cid == cid.lower() and " " not in cid and "_" not in cid, (
            f"{path.name}: candidate_id {cid!r} is not kebab-case"
        )
        assert not cid.isdigit(), f"{path.name}: candidate_id {cid!r} is an ordinal, not a slug"
        assert cid not in seen, f"{path.name}: duplicate candidate_id {cid!r}"
        seen.add(cid)


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_base_score_is_the_sum_of_its_criteria(path):
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for cid, cand in _candidates(doc):
        assessment = cand["gates_assessment"]
        criteria = assessment["criteria"]
        assert set(criteria) == set(GATES), f"{path.name}:{cid} does not score all five gates"
        expected = sum(CRITERIA_POINTS[criteria[g]] for g in GATES)
        assert assessment["base_score"] == expected, (
            f"{path.name}:{cid} states base_score {assessment['base_score']} but its "
            f"criteria sum to {expected}"
        )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_deployable_candidates_carry_the_required_fields(path):
    """AGENT_MEMORY_SCHEMA.md "Required fields"."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for cid, cand in _candidates(doc):
        verdict = cand["gates_assessment"]["verdict"]
        assert verdict in VERDICTS, f"{path.name}:{cid} has verdict {verdict}, not in the enum"
        if verdict not in DEPLOYABLE:
            assert "deployment" not in cand, (
                f"{path.name}:{cid} is {verdict} but carries a deployment block — omit it"
            )
            continue
        assert cand.get("name"), f"{path.name}:{cid} has no name"
        deployment = cand["deployment"]
        assert deployment.get("engine") in ENGINES, (
            f"{path.name}:{cid} engine {deployment.get('engine')!r} is not in {sorted(ENGINES)}"
        )
        assert deployment["detection_logic"].get("query", "").strip(), (
            f"{path.name}:{cid} is {verdict} but has no detection_logic.query"
        )
        if "status" in deployment:
            assert deployment["status"] in STATUSES, (
                f"{path.name}:{cid} status {deployment['status']!r} is not in {sorted(STATUSES)}"
            )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_conditional_candidates_state_their_prerequisites(path):
    """CONDITIONAL means "deploy once these are met"; without them it is unactionable."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for cid, cand in _candidates(doc):
        if cand["gates_assessment"]["verdict"] != "CONDITIONAL":
            continue
        prereqs = cand["deployment"]["operational_parameters"].get("deployment_prerequisites")
        assert prereqs, (
            f"{path.name}:{cid} is CONDITIONAL with no "
            f"deployment.operational_parameters.deployment_prerequisites"
        )
        assert all(isinstance(p, str) and p.strip() for p in prereqs), (
            f"{path.name}:{cid} deployment_prerequisites must be a list of strings"
        )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_time_box_candidates_record_their_expiry(path):
    """A TIME_BOX with no expiry is a PROMOTE that nobody dares delete."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for cid, cand in _candidates(doc):
        if cand["gates_assessment"]["verdict"] != "TIME_BOX":
            continue
        params = cand["deployment"]["operational_parameters"]
        for field in ("activation_date", "expiration_date", "review_date", "refresh_cycle_days"):
            assert params.get(field), f"{path.name}:{cid} is TIME_BOX with no {field}"


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_prerequisites_are_only_written_where_the_schema_declares_them(path):
    """One name for one concept.

    Four spellings of "prerequisites" have appeared across drafts of these files.
    Each new one is invisible to a consumer reading the contract, so the CONDITIONAL
    verdict arrives with nothing attached — which is how the field was lost.
    """
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    for cid, cand in _candidates(doc):
        for key in UNDECLARED_PREREQ_KEYS:
            assert key not in cand, (
                f"{path.name}:{cid} has a top-level {key!r}. Prerequisites belong at "
                f"deployment.operational_parameters.deployment_prerequisites"
            )
            assert key not in cand["gates_assessment"], (
                f"{path.name}:{cid} has gates_assessment.{key}. Prerequisites belong at "
                f"deployment.operational_parameters.deployment_prerequisites"
            )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_deployable_hunts_declare_their_platforms_and_data_sources(path):
    """Both are REQUIRED-when-deployable, and both must be lists.

    A consumer cannot deploy a detection without knowing which platform it targets
    and which feed it queries — and `data_sources` is what tells it that a dozen
    detections all ride one source that can go dark together. Written as a bare
    string instead of a list, a consumer iterating the value gets one entry per
    character, which is worse than omitting it.
    """
    meta = yaml.safe_load(path.read_text(encoding="utf-8"))["hunt_metadata"]
    for field, value in (
        ("platforms", meta.get("platforms")),
        ("techniques", meta.get("techniques")),
        ("data_sources", (meta.get("hunt_outcomes") or {}).get("data_sources")),
    ):
        assert value, f"{path.name} is a deployable hunt with no {field}"
        assert isinstance(value, list), (
            f"{path.name}: {field} is {type(value).__name__}, not a list — a consumer "
            f"iterating a bare string gets one entry per character"
        )
        assert all(isinstance(v, str) and v.strip() for v in value), (
            f"{path.name}: {field} must be non-empty strings"
        )


@pytest.mark.parametrize("path", _yaml_examples(), ids=lambda p: p.name)
def test_multi_feed_hunts_name_the_feed_per_candidate(path):
    """A consumer needing one feed takes the first hunt-level entry.

    That is right when every candidate reads the same thing and wrong the moment
    they don't — a registry detection filed under process creation is reported as
    going dark when the wrong feed breaks.

    Only the ambiguous shape is checked: several feeds AND several deployable
    candidates. A single candidate that genuinely correlates two feeds is not
    ambiguous, so the hunt-level list stands on its own.
    """
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    sources = (doc["hunt_metadata"].get("hunt_outcomes") or {}).get("data_sources") or []
    deployable = [
        (cid, cand)
        for cid, cand in _candidates(doc)
        if cand["gates_assessment"]["verdict"] in DEPLOYABLE
    ]
    if len(sources) < 2 or len(deployable) < 2:
        return
    for cid, cand in deployable:
        own = cand["deployment"].get("data_source")
        assert isinstance(own, str) and own.strip(), (
            f"{path.name}:{cid} — the hunt declares {len(sources)} data sources, so each "
            f"deployable candidate needs its own `deployment.data_source` (a single value)"
        )


def test_hunt_level_prerequisites_use_the_declared_shape():
    """`gates_validation.prerequisites` is `{type, requirement, blocker, effort}`."""
    for path in _yaml_examples():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for entry in doc["gates_validation"].get("prerequisites") or []:
            assert isinstance(entry, dict), (
                f"{path.name}: hunt-level prerequisites entry {entry!r} is a bare string; "
                f"the declared shape is a mapping, so a consumer can sort by `blocker`"
            )
            assert {"type", "requirement", "blocker"} <= set(entry), (
                f"{path.name}: hunt-level prerequisite {entry!r} is missing declared keys"
            )
