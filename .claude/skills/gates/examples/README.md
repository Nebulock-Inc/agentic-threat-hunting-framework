# GATES Examples

An index of the worked outputs in `outputs/`. **The example content lives in those files
only** — this README deliberately does not reproduce it. Two copies of an example drift,
and that is exactly how several of these ended up stating scores their own criteria didn't
add up to.

## Which file a hunt produces

The **hunt-level** verdict picks the format — not the candidate verdicts inside it. A
`.yaml` from a PROMOTE hunt routinely contains TIME_BOX or HOLD candidates.

| Hunt verdict | File | Contains |
|--------------|------|----------|
| `PROMOTE` / `CONDITIONAL` / `TIME_BOX` | `H-XXXX_GATES.yaml` | Agent-queryable metadata + deployment templates |
| `HOLD` / `DROP` / `RECURRING_HUNT` | `H-XXXX_GATES.md` | Reasoning, strategy, activation triggers |
| Risk assessment (non-GATES) | `H-XXXX_ASSESSMENT.md` | Advisory and remediation guidance |
| Planning phase (not yet executed) | `H-XXXX_PLANNING_ASSESSMENT.md` | Pre-execution guidance |

Examples in this directory use an `_EXAMPLE` suffix to distinguish them from real
validation output. Their hunt IDs (`H-09XX`) are **fictional** — they intentionally do not
correspond to a hunt in anyone's hunt repository. Keep it that way when adding an example:
a real hunt ID published here discloses the authoring team's hunt numbering, and the
examples need a plausible ID, not a true one.

## The examples

| File | Verdict | Deciding factor | What it demonstrates |
|------|---------|-----------------|----------------------|
| `outputs/H-0903_EXAMPLE.yaml` | `PROMOTE` | score band, no FAIL | Four candidates, two verdicts, `verdict_breakdown`, stable `candidate_id` slugs. **The reference for conformant YAML output.** |
| `outputs/H-0902_EXAMPLE.yaml` | `CONDITIONAL` | score 3.5 | `deployment_prerequisites` — the field that makes a CONDITIONAL actionable — plus the hunt-level roll-up in its declared `{type, requirement, blocker, effort}` shape. Single-candidate hunt, so `base_score_average` coincides with `base_score` |
| `outputs/H-0901_EXAMPLE.yaml` | `PROMOTE` | score band, no FAIL | PROMOTE from the opposite direction to H-0903: nothing was measured rather than measured-clean. An unmeasured gate is `PARTIAL`, so the hunt still reaches 4.0 and deploys at `status: TEST` with the soak resolving the unknowns. Also shows an *omitted* `false_positives` — writing `0` would assert a measurement nobody took |
| `outputs/H-0906_EXAMPLE.yaml` | `TIME_BOX` | `G` FAIL, behavior present | The TIME_BOX `operational_parameters` (`activation_date` / `expiration_date` / `review_date` / `refresh_cycle_days`), `narrative_analysis`, and the only non-`sigma` engine in the set. Scores 2.0 with three FAILs; `G` wins the precedence |
| `outputs/H-0905_EXAMPLE.md` | `RECURRING_HUNT` | `S` FAIL at high volume | Real signal, unsustainable as a standing rule — the other branch of an `S` FAIL |
| `outputs/H-0907_EXAMPLE.md` | — (non-GATES) | n/a | A hunt that correctly produces no detections. Also carries a hypothetical showing `S` (row 4) outranking `T` (row 5) |

`HOLD` and `DROP` have no worked example yet.

- `HOLD` is reached three ways (`SKILL.md` Step 4): an `E` FAIL, which is an epistemic
  block — too few angles were tested to *judge* the candidate — and applies whether or
  not the behavior was observed; a score below 3.0 with no FAIL to decide it; and the
  zero-prevalence downgrade, where a verdict that would otherwise deploy is held because
  the behavior was never seen, so no amount of re-running helps. Only the third is about
  prevalence, and it is the one that gets mistaken for the definition. Do not confuse it
  with zero true positives either: H-0901 has zero TPs and is a PROMOTE, because the
  logic is sound and the absence is a measurement gap, not an absence of the behavior.
  `TIME_BOX` is the neighbouring case where the behavior *is* present but the logic
  expires (H-0906).
- `DROP` comes from an `A` FAIL — coverage already exists — and the verdict exists so a
  rejected idea is recorded rather than re-proposed next quarter.

Two of the four verdicts above are decided by a gate FAIL rather than by the score band,
and H-0906 scores outside the band its verdict implies. That is the FAIL precedence in
`SKILL.md` Step 4 working as intended, not an error in the examples.

`tests/test_gates_examples.py` enforces the rules this directory is supposed to
demonstrate: the extension matches the hunt-level verdict, every `base_score` is the
exact sum of its criteria, deployable candidates carry their required fields, and
prerequisites are written only where the schema declares them. Each of those checks
exists because a shipped example had already drifted.

## Values that are not in the enum

These appeared in earlier drafts and are wrong wherever they turn up:

- **`UNKNOWN`** as a criteria result — it has no point value, so scoring it silently
  drops the total. An unevidenced gate is `PARTIAL`.
- **`LIKELY_PASS`** — same problem: not in `PASS | PARTIAL | FAIL`, and unscoreable.
- **`PROMOTE_PENDING_VALIDATION`** — unnecessary. The ADVANCED criteria are PENDING for
  *every* candidate until it has soaked, so "pending validation" is the normal state of a
  `PROMOTE`, not a separate verdict.
- **`MERGE`, `EXPAND`, `MONITOR`, `NOT A DETECTION`, `TEST`** in verdict
  position. The first four are remediation *actions* — put them in the narrative.
  `TEST` is a deployment status, a different enum.

The canonical sets are in `AGENT_MEMORY_SCHEMA.md`.

## Planning-phase output

A hunt that hasn't run yet can't be scored. Write expectations as
`plausible | doubtful | blocked on —`, never as `PASS`/`PARTIAL`/`FAIL`: those are scoring
tokens, and using them invites someone to total the row into a verdict no evidence
supports. Note the likely *rule type* (behavioral, IOC, hybrid) — a hybrid usually splits
into two candidates with different verdicts — and re-run GATES properly after the KEEP
phase.
