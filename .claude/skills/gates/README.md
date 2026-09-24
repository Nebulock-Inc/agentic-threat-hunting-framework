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
```bash
/gates --hunt H-0064
```

## What It Produces

**Output:** Single file per detection candidate, format varies by verdict type

### PROMOTE / CONDITIONAL → YAML
**File:** `hunt-promotion-analysis/H-XXXX_<detection-name>_GATES.yaml`
**Naming:** Multiple detections generate multiple files (e.g., H-0064_auth-anomaly_GATES.yaml, H-0064_mfa-bypass_GATES.yaml)
- Deployment-ready detection templates
- Agent learning artifacts (patterns, learnings)
- Operational parameters (volume, FP rates)
- Prerequisites (for CONDITIONAL verdicts)

### HOLD / TIME-BOX / RECURRING HUNT → Markdown
**File:** `hunt-promotion-analysis/H-XXXX_GATES.md`
- Analysis and rationale
- Activation triggers (for TIME-BOX)
- Strategy documentation (for RECURRING HUNT)
- Preservation reasoning (for HOLD)

**Note:** "PROMOTE" in GATES context means deploying a detection rule to production. This is separate from the `athf hunt promote` CLI command, which moves hunt files between directories (test/ → production/).

**Schema:** `AGENT_MEMORY_SCHEMA.md` - Specification for machine-readable learning

**Compounding Intelligence:** Each validation creates structured artifacts that teach the system. Hunt 50 is smarter than Hunt 1 because it learned from 49 patterns: proactive deployment confidence, FP sources, telemetry gaps, volume thresholds.

## Scoring Logic

### BASE Criteria Scoring (/5)

Each gate scores: PASS (1.0), PARTIAL (0.5), or FAIL (0.0).

**Verdict Ranges:**
- **4.0-5.0**: ✅ PROMOTE - Deploy to production
- **3.0-3.5**: ⚠️ CONDITIONAL - Complete prerequisites first
- **2.0-2.5**: ❌ HOLD or ⏱️ TIME-BOX (IOC-only)
- **0.0-1.5**: ❌ HOLD - Significant rework needed

### Rule Types
- **BEHAVIORAL**: Process patterns, TTPs → Expected 4-5/5
- **TOOL**: Tool signatures (Mimikatz) → Expected 4-5/5
- **IOC**: IPs, domains, hashes → Expected 1-2/5 (time-boxed)
- **HYBRID**: Mixed behavioral + IOC → Expected 2-3/5 (split recommended)
- **COMPOSITE**: Multiple signals combined → Expected 3-4/5

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

BASE Score: 5/5
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

```bash
# 1. In ATHF workspace: Run GATES validation
/gates --hunt H-0064
# → hunt-promotion-analysis/H-0064_GATES.yaml

# 2. Switch to ADEF workspace
cd ~/adef-workspace/

# 3. Run ADEF FORGE with path to GATES output
adef forge --input ~/athf-workspace/hunt-promotion-analysis/H-0064_GATES.yaml
```

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
