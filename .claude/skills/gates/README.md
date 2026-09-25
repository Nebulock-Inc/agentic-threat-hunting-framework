# GATES Skill - Quick Start

## What It Does

The `/gates` skill validates hunt-derived detections using the GATES method:
- **G**eneralizable - Is this repeatable?
- **A**dditive - Does it fill a coverage gap?
- **T**unable - Can we distinguish attack from normal?
- **E**xposure-tested - Did we cover bypass scenarios?
- **S**ustainable - Can we maintain it?

## How to Use

### Basic Usage

Type this to your assistant — it is a skill invocation, not a shell command:

```text
/gates --hunt H-0064
```

## What It Produces

**Output:** exactly **one file per hunt**, holding every candidate detection that
hunt produced. The *hunt-level* verdict picks the format; see the hunt-level vs
candidate-level distinction in `AGENT_MEMORY_SCHEMA.md`.

### PROMOTE / CONDITIONAL → YAML
**File:** `hunt-promotion-analysis/H-XXXX_GATES.yaml`
**Naming:** one file per hunt, N candidates inside it, each keyed by `candidate_id`.
Never one file per detection — a consumer imports the hunt, not a directory listing,
and per-file splitting loses the cross-candidate context (`deployment_order`,
`aggregate_insights`) that makes the artifact self-contained.
- Deployment-ready detection templates
- Agent learning artifacts (patterns, learnings)
- Operational parameters (volume, FP rates)
- Prerequisites (for CONDITIONAL verdicts)

### HOLD / TIME_BOX / RECURRING_HUNT → Markdown
**File:** `hunt-promotion-analysis/H-XXXX_GATES.md`
- Analysis and rationale
- Activation triggers (for TIME_BOX)
- Strategy documentation (for RECURRING_HUNT)
- Preservation reasoning (for HOLD)

**Note:** "PROMOTE" in GATES context means deploying a detection rule to production. This is separate from the `athf hunt promote` CLI command, which moves hunt files between directories (test/ → production/).

**Schema:** `AGENT_MEMORY_SCHEMA.md` - Specification for machine-readable learning

**Compounding Intelligence:** Each validation creates structured artifacts that teach the system. Hunt 50 is smarter than Hunt 1 because it learned from 49 patterns: proactive deployment confidence, FP sources, telemetry gaps, volume thresholds.

## Scoring Logic

### BASE Criteria Scoring (0.0–5.0)

Each gate scores: PASS (1.0), PARTIAL (0.5), or FAIL (0.0). There is no UNKNOWN —
a gate you believe will pass but haven't evidenced is PARTIAL.

**Score bands** (contiguous, so every score has exactly one band):
- **4.0-5.0**: ✅ PROMOTE - Deploy to production
- **3.0-3.9**: ⚠️ CONDITIONAL - Complete prerequisites first
- **0.0-2.9**: ❌ HOLD - Significant rework needed

**A gate FAIL overrides the band.** A FAIL names a specific defect, and the fix for
that defect is a specific verdict — so A→DROP, G→TIME_BOX, E→HOLD, S→RECURRING_HUNT,
T→CONDITIONAL take precedence over whatever the score alone would say. Evaluate them
in that order and stop at the first match; the band applies only when no gate FAILed.
**`SKILL.md` Step 4 is the authoritative statement; this is a summary of it.**

### Rule Types

Typical, not prescriptive — score the evidence you have, don't score to the table.

- **BEHAVIORAL**: Process patterns, TTPs → typically 4.0-5.0
- **TOOL**: Named tool signatures → typically 4.0-5.0
- **IOC**: IPs, domains, hashes → typically 1.0-2.0, `G` FAIL → TIME_BOX
- **HYBRID**: Mixed behavioral + IOC → typically 2.0-3.0; split into two candidates
- **COMPOSITE**: Multiple signals combined → typically 3.0-4.0

## Integration with ADEF

```
LOCK (Hunt) → GATES (Validate) → ADEF (Engineer)
    ↓              ↓                   ↓
  KEEP      BASE validation         F - FIND
           (assert quality)     (detection artifacts)
```

The detection artifacts output feeds into ADEF's **F - FIND** phase for production engineering.

## Example Output

```
 GATES Validation Complete: H-0064

BASE Score: 5.0
Verdict: ✅ PROMOTE

File generated:
- hunt-promotion-analysis/H-0064_GATES.yaml

Next: Deploy to detection repository for EXPERIMENTAL soak period
```

## Testing the Skill

1. Complete a hunt with KEEP phase documented
2. Invoke: `/gates --hunt H-XXXX`
3. Review generated validation report
4. Use detection artifacts for ADEF workflow

## Next Step: Detection Engineering with ADEF

After GATES validation, proceed to detection engineering using ADEF (Agentic Detection Engineering Framework).

### Installation

```bash
pip install agentic-detection-engineering-framework
```

### Workflow

**Step 1 — in the ATHF workspace,** run GATES. Assistant input, not a shell command:

```text
/gates --hunt H-0064
```

→ writes `hunt-promotion-analysis/H-0064_GATES.yaml`

**Step 2 — import the document into ADEF.** One file in, N detections out:

```bash
adef hunt-promote --gates ~/athf-workspace/hunt-promotion-analysis/H-0064_GATES.yaml
# add --dry-run first to see what it would mint without writing anything
```

Deployable candidates (PROMOTE / CONDITIONAL / TIME_BOX) each get a `D-XXXX`, a
catalog record and a journal at the Find stage; archival ones (HOLD / DROP /
RECURRING_HUNT) are reported as skipped and consume no ID. Re-running after an edited
hunt updates the same records rather than duplicating them, which is why
`candidate_id` has to stay stable.

There is no directory to `cd` into: ADEF resolves its workspace from `ADEF_WORKSPACE`
(default `~/work/adef-workspace/`), so the command works from anywhere.

**Availability:** `--gates` is `adef hunt-promote`'s GATES-import mode. Run
`adef hunt-promote --help` to confirm your ADEF has it.

**The `H-XXXX_GATES.yaml` file is self-contained** - it includes all context needed for detection engineering (hunt metadata, BASE scores, detection logic, key learnings).

### Framework Relationship

```
ATHF Workspace                    ADEF Workspace
──────────────                    ──────────────
Hunt (LOCK)                       
   ↓
GATES Validate                    
   ↓
H-XXXX_GATES.yaml  ────────────→  FORGE (F-O-R-G-E)
                                     ↓
                                  Production Rule
```

### ADEF Repository

https://github.com/Nebulock-Inc/agentic-detection-engineering-framework
