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
| `PROMOTE` / `CONDITIONAL` | `H-XXXX_GATES.yaml` | Agent-queryable metadata + deployment templates |
| `HOLD` / `TIME_BOX` / `RECURRING_HUNT` / `DROP` | `H-XXXX_GATES.md` | Reasoning, strategy, activation triggers |
| Risk assessment (non-GATES) | `H-XXXX_ASSESSMENT.md` | Advisory and remediation guidance |
| Planning phase (not yet executed) | `H-XXXX_PLANNING_ASSESSMENT.md` | Pre-execution guidance |

Examples in this directory use an `_EXAMPLE` suffix to distinguish them from real
validation output.

## The examples

| File | Verdict | Deciding factor | What it demonstrates |
|------|---------|-----------------|----------------------|
| `outputs/H-0062_EXAMPLE.yaml` | `PROMOTE` | score band, no FAIL | Four candidates, two verdicts, `verdict_breakdown`, stable `candidate_id` slugs. **The reference for conformant YAML output.** |
| `outputs/H-0061_EXAMPLE.yaml` | `CONDITIONAL` | score 3.5 | Prerequisites as structured data; single-candidate hunt where `base_score_average` coincides with `base_score` |
| `outputs/H-0060_EXAMPLE.md` | `HOLD` | `S` FAIL at zero prevalence | The zero-prevalence rule: a quarterly re-run doesn't help when the hunt found nothing. Scores 3.0 — *outside* HOLD's band, by design |
| `outputs/H-0065_EXAMPLE.md` | `TIME_BOX` | `G` FAIL, behavior present | IOC watchlist with an expiry and refresh cycle. Pair it with H-0060: same rule, opposite side — prevalence is what separates `TIME_BOX` from `HOLD`. Scores 2.0 with three FAILs; `G` wins the precedence |
| `outputs/H-0064_EXAMPLE.md` | `RECURRING_HUNT` | `S` FAIL at high volume | Row 4's other branch: real signal, unsustainable as a standing rule |
| `outputs/H-0066_EXAMPLE.md` | — (non-GATES) | n/a | A hunt that correctly produces no detections. Also carries a hypothetical showing `S` (row 4) outranking `T` (row 5) |

`DROP` has no worked example yet. It comes from an `A` FAIL — coverage already exists —
and the verdict exists so a rejected idea is recorded rather than re-proposed next
quarter.

Three of the five verdicts above are decided by a gate FAIL rather than by the score
band, and two examples score outside the band their verdict implies. That is the FAIL
precedence in `SKILL.md` Step 4 working as intended, not an error in the examples.

## Values that are not in the enum

These appeared in earlier drafts and are wrong wherever they turn up:

- **`UNKNOWN`** as a criteria result — it has no point value, so scoring it silently
  drops the total. An unevidenced gate is `PARTIAL`.
- **`LIKELY_PASS`** — same problem: not in `PASS | PARTIAL | FAIL`, and unscoreable.
- **`PROMOTE_PENDING_VALIDATION`** — unnecessary. The ADVANCED criteria are PENDING for
  *every* candidate until it has soaked, so "pending validation" is the normal state of a
  `PROMOTE`, not a separate verdict.
- **`MERGE`, `EXPAND`, `MONITOR`, `NOT A DETECTION`, `EXPERIMENTAL`** in verdict
  position. The first four are remediation *actions* — put them in the narrative.
  `EXPERIMENTAL` is a deployment status, a different enum.

The canonical sets are in `AGENT_MEMORY_SCHEMA.md`.

## Planning-phase output

A hunt that hasn't run yet can't be scored. Write expectations as
`plausible | doubtful | blocked on —`, never as `PASS`/`PARTIAL`/`FAIL`: those are scoring
tokens, and using them invites someone to total the row into a verdict no evidence
supports. Note the likely *rule type* (behavioral, IOC, hybrid) — a hybrid usually splits
into two candidates with different verdicts — and re-run GATES properly after the KEEP
phase.
