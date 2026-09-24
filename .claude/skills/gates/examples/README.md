# GATES Examples

This directory contains example GATES validation outputs showing different hunt types and verdicts.

## Output Types

The GATES method generates different output files based on the hunt verdict:

| Hunt Outcome | File Generated | Contains |
|--------------|----------------|----------|
| **PROMOTE / CONDITIONAL** | `H-XXXX_GATES.yaml` | Dual-purpose: agent learning + deployment templates |
| **HOLD / TIME-BOX / RECURRING HUNT** | `H-XXXX_GATES.md` | Analysis and reasoning (no deployment or time-boxed) |
| **Risk Assessment** | `H-XXXX_ASSESSMENT.md` | Advisory guidance (non-GATES) |
| **Planning Phase** | `H-XXXX_PLANNING_ASSESSMENT.md` | Pre-execution guidance |

**Filename Convention:**
- **Production outputs:** `H-XXXX_GATES.yaml` or `H-XXXX_GATES.md`
- **Example outputs:** `H-XXXX_EXAMPLE.yaml` or `H-XXXX_EXAMPLE.md` (this directory)
- Examples use `_EXAMPLE` suffix to distinguish from production validation files

---

## Example 1: PROMOTE Verdict (Deployable Detection)

**Hunt:** Supply chain compromise detection  
**Verdict:** PROMOTE (composite detection)  
**File:** See `H-0062_EXAMPLE.yaml` in outputs/ for real PROMOTE example

**Key sections in YAML:**

```yaml
hunt_metadata:
  hunt_id: H-0005
  techniques: [T1195.002]
  tactics: [execution, initial-access]

gates_validation:
  verdict: PROMOTE_PENDING_VALIDATION
  detections_promoted: 1  # Composite detection
  key_learnings:
    - "Composite detections achieve higher confidence with lower FP rate"
    - "Multi-step correlation reduces noise significantly"

narrative_analysis: |
  ## Detection 3: Supply Chain Composite
  
  **BASE Score: 4/5**
  
  **G - Generalizable: PASS**
  Multi-step behavioral pattern (install + shell + recon)
  
  **A - Additive: PASS**
  High-confidence T1195.002 detection
  
  **T - Tunable: LIKELY_PASS**
  Composite specificity reduces FPs
  
  **E - Exposure-tested: PARTIAL**
  Covers primary path, some gaps remain
  
  **S - Sustainable: LIKELY_PASS**
  Low expected volume

detections:
  - detection_id: 3
    name: "Supply Chain Compromise - Install + Shell + Recon"
    
    gates_assessment:
      verdict: PROMOTE_PENDING_VALIDATION
      base_score: 4
      
    deployment:
      engine: composite
      status: EXPERIMENTAL
      
      detection_logic:
        description: |
          Requires all 3 steps within 5 minutes:
          1. Package install
          2. node.exe → cmd.exe spawn
          3. Recon commands (whoami/net/ipconfig)
```

**Why YAML output:**
- Detection is deployable (PROMOTE verdict)
- Contains deployment templates ready for automation
- Agent-queryable metadata for learning patterns

---

## Example 2: HOLD Verdict (Analysis Only)

**Hunt:** Zero TPs observed, preserve for future  
**Verdict:** HOLD (no operational need)  
**File:** `H-0060_GATES.md`

**Markdown structure:**

```markdown
# GATES Validation: H-0060

**Verdict:** HOLD
**BASE Score:** 1.5/5

## Summary

Detection logic validated by emulation but 0 TPs in ~8B events.
No operational need. Preserve as quarterly threat-intel-driven hunt.

## Reasoning

**G - Generalizable: PASS**
Behavioral pattern (browser extension abuse), not IOC-based.

**A - Additive: PARTIAL**
Fills T1176.001 gap, but zero TPs = no operational need.

**T - Tunable: UNKNOWN**
No execution results to validate FP rate.

**E - Exposure-tested: PASS**
Multiple detection angles tested.

**S - Sustainable: FAIL**
Unknown volume, no TPs to justify investigation burden.

## Recommendations

Convert to quarterly recurring hunt. Activate if threat intel shows activity.

Preserved detection logic:
- Angle 1: Headless Chrome + extension flags
- Angle 2: Browser → interpreter chain
- Angle 5: C2 domains (IOC watchlist)

Fast-track deployment plan if activated:
- Day 0: Threat intel triggers
- Day 1-7: Deploy IOC watchlist
- Day 7-14: Deploy behavioral detection with allowlist
```

**Why Markdown output:**
- No detections being deployed (HOLD verdict)
- Lightweight narrative explanation
- Preservation of logic for future use

---

## Example 3: CONDITIONAL Verdict (Prerequisites Required)

**Hunt:** Kerberos RC4 cipher detection  
**Verdict:** CONDITIONAL (deploy after SPN allowlist built)  
**File:** `H-0061_EXAMPLE.yaml`

**Key sections in YAML:**

```yaml
gates_validation:
  verdict: CONDITIONAL
  base_score_average: 3.5

detections:
  - detection_id: 3
    name: "Kerberos Ticket with Deprecated Cipher"
    
    gates_assessment:
      verdict: CONDITIONAL
      base_score: 3.5
      criteria:
        tunable: PARTIAL  # Requires allowlist
        sustainable: PARTIAL  # Allowlist maintenance
    
    prerequisites:
      - title: "Build SPN Allowlist"
        description: "Identify all known RC4 SPNs before deploying"
        steps:
          - "Baseline: 30-day SPN inventory"
          - "Customer validation: Verify SPNs"
          - "Document: Why each SPN uses RC4"
      
      - title: "Quarterly Allowlist Review"
        description: "SPN allowlist maintenance schedule"
```

**Why CONDITIONAL verdict:**
- Detection logic is sound (T1558.003 coverage)
- 30/day volume manageable with tuning
- Requires SPN allowlist before deployment (Azure NetApp Files, Azure Files)
- Quarterly allowlist maintenance needed (infrastructure changes)

---

## Example 4: TIME-BOX Verdict (Campaign-Specific IOC)

**Hunt:** ClickFix C2 domain watchlist  
**Verdict:** TIME-BOX (90-day campaign tracking)  
**File:** `H-0065_EXAMPLE.md`

**Markdown structure:**

```markdown
# Example: TIME-BOX Verdict (Campaign-Specific IOC Detection)

**BASE Score:** 2/5

## BASE Criteria Scoring

**G - Generalizable: ❌ FAIL**
IOC-based detection (domain watchlist), not behavioral pattern.
Expires when campaign ends or adversary rotates infrastructure.

**S - Sustainable: ❌ FAIL**
High maintenance burden:
- IOCs expire in 30-90 days (domain rotation)
- Requires quarterly threat intel refresh

## Deployment Guidance

### Time-Boxed Deployment (90 Days)

**Activation Date:** 2026-09-20 (ClickFix campaign reported)
**Expiration Date:** 2026-12-20 (90 days)
**Review Date:** 2026-12-15 (assess campaign status)

**IOC Watchlist (Domains):**
- clickfix-cdn[.]com
- legitimate-update[.]net
- windows-patch[.]org

**Refresh Triggers:**
1. New ClickFix domains identified (threat intel update)
2. Campaign ends (all domains sinkholed/dead)
3. 90 days elapse (mandatory review)
```

**Why TIME-BOX verdict:**
- IOC-based = not generalizable (expires with campaign)
- Immediate value during campaign window
- 90-day lifespan (domain rotation expected)
- Complements behavioral detections (fast deployment)

---

## Example 5: RECURRING HUNT Verdict (High Volume)

**Hunt:** EC2 encryption disable detection  
**Verdict:** RECURRING HUNT (quarterly execution, not 24/7)  
**File:** `H-0064_EXAMPLE.md`

**Markdown structure:**

```markdown
# Example: RECURRING HUNT Verdict (High Volume, Quarterly Execution)

**BASE Score:** 2/5

## BASE Criteria Scoring

**T - Tunable: ❌ FAIL**
- Baseline: 2,537 events/day = 76,000/month
- Attack frequency: ~0-1/year
- Signal-to-noise: 0.0013% TP rate
- Investigation capacity: Cannot investigate 2,537/day

**S - Sustainable: ❌ FAIL**
- Alert volume: 2,537 alerts/day = unsustainable
- Allowlist maintenance: High (tenant churn)
- SOC impact: 140-210 alerts/week even with allowlists

## Recurring Hunt Strategy

### Execution Frequency: Quarterly

**Q1 Hunt (January):**
- Query: Last 90 days of encryption disable events
- Baseline: Expected TenantAdmin volume (~230K events)
- Hunt: Anomalous patterns (non-TenantAdmin, production accounts)
- Time investment: 4-8 hours (bounded, manageable)

## Quarterly Hunt Workflow

### Phase 1: Baseline Measurement (30 min)
### Phase 2: Principal Analysis (1 hour)
### Phase 3: Account Scope Analysis (1 hour)
### Phase 4: Temporal Analysis (1 hour)
### Phase 5: Correlation Hunt (2 hours)
```

**Why RECURRING HUNT verdict:**
- Volume unsustainable for 24/7 (2,537 events/day)
- Allowlist maintenance burden too high (tenant churn)
- Quarterly hunt catches 90% of attacks with 1% SOC effort
- Better than HOLD: detection has value, just not as standing alert

---

## Example 6: Risk Assessment (Non-GATES)

**Hunt:** Infrastructure security posture  
**Type:** Risk assessment (not behavioral detection)  
**File:** `H-0066_ASSESSMENT.md`

**Markdown structure:**

```markdown
# Security Assessment: H-0066

**Type:** Infrastructure risk assessment (not behavioral detection)

## Findings

- **Network Segmentation:** Multiple sites with varying posture (flat networks, camera co-mingling)
- **NDAA compliance:** Hikvision/Dahua presence with federal nexus
- **Positive Control:** Some sites properly segmented

## Deliverable

Per-client advisories + remediation guidance (not detection rules)

## GATES Applicability

Not applicable - configuration findings, not behavioral patterns.
Findings are:
- Configuration states (segmentation)
- Compliance issues (vendor presence)
- Exposure assessments (Shodan validation)

None are automatable as standing detections.

## Output

Client-specific security advisory:
- Sites with flat networks: Remediate segmentation, replace NDAA vendors
- Sites with proper segmentation: Maintain posture, annual validation
```

**Why Assessment output:**
- No behavioral detections (configuration issues)
- Advisory/remediation focus
- Non-GATES workflow

---

## Example 7: Planning Phase Assessment

**Hunt:** Hypothesis defined, not yet executed  
**Type:** Pre-execution guidance  
**File:** (Conceptual example - no file in outputs/)

**Markdown structure:**

```markdown
# H-0006 Planning Assessment

**Status:** Planning (not executed)

## GATES Applicability

NOT READY FOR GATES VALIDATION

Hunt is in planning phase. GATES requires completed CHECK/KEEP phases.

## Hypothesis Analysis

**Hypothesis:** Periodic beacon to CDN-lookalike domain

**Detection Pattern Potential:** HIGH

**Pre-Assessment (if hunt validates):**
- G: PARTIAL (behavioral + IOC hybrid)
- A: LIKELY PASS (T1071.001 C2 detection)
- T: UNKNOWN (depends on baseline)
- E: UNKNOWN (needs bypass testing)
- S: PARTIAL (domain rotation = IOC maintenance)

**Expected Verdict:** HYBRID
- Behavioral layer (periodicity) → CONDITIONAL
- IOC layer (domain) → TIME-BOX

## Recommendations for Execution

### Query Strategy
1. Domain-specific search
2. Periodicity analysis
3. Domain characteristics (WHOIS)
4. Baseline comparison

### Detection Opportunities
- Angle 1: Domain IOC → TIME-BOX
- Angle 2: Periodic beacon → CONDITIONAL
- Angle 3: Young domain + periodicity → BEHAVIORAL

## Next Steps

1. Execute hunt (run queries)
2. Complete KEEP phase (findings)
3. Re-run GATES for full validation
```

**Why Planning output:**
- Hunt not executed yet
- Provides execution guidance
- Pre-assessment of detection potential

---

## Summary

**GATES adapts output format to hunt state:**

- **Deployable detections (PROMOTE/CONDITIONAL)** → YAML (agent learning + deployment templates)
- **Analysis/guidance (HOLD/TIME-BOX/RECURRING)** → Markdown (reasoning, strategy, activation triggers)
- **Risk assessments** → Advisory (remediation, not detection)
- **Planning phase** → Guidance (execution recommendations)

**Key principle:** File extension indicates outcome
- `.yaml` = Deployable detection (PROMOTE or CONDITIONAL with prerequisites)
- `.md` = Analysis, guidance, or advisory (HOLD/TIME-BOX/RECURRING/Risk Assessment)

**Verdict Type Coverage:**
- ✅ **PROMOTE** (Example 1, H-0062) - 4-5/5, deploy immediately
- ✅ **CONDITIONAL** (Example 3, H-0061) - 3/5, deploy after prerequisites
- ✅ **HOLD** (Example 2, H-0060) - 0-2/5, preserve for future
- ✅ **TIME-BOX** (Example 4, H-0065) - IOC-based, 90-day campaign tracking
- ✅ **RECURRING HUNT** (Example 5, H-0064) - High volume, quarterly execution
- ✅ **Risk Assessment** (Example 6, H-0066) - Advisory, non-GATES workflow
- ✅ **Planning Phase** (Example 7) - Pre-execution guidance

---

## Full Example Files

See `outputs/` directory for **real validation outputs from tested hunts:**

### H-0062_EXAMPLE.yaml (✅ PROMOTE)
**Real hunt:** ClickFix clipboard abuse campaign  
**Shows:** 4 detections scored, zero baseline FPs, deployment priorities  
**Key pattern:** Remote msiexec = 5.0/5 score, deploy immediately  
**File size:** 3KB - complete AGENT_MEMORY_SCHEMA format

### H-0061_EXAMPLE.yaml (⚠️ CONDITIONAL)
**Real hunt:** Kerberos RC4 cipher detection  
**Shows:** 3.5/5 score, SPN allowlist required, quarterly maintenance  
**Key pattern:** Tuning required before deployment = CONDITIONAL  
**File size:** 5KB - prerequisites + deployment roadmap

### H-0060_EXAMPLE.md (❌ HOLD)
**Real hunt:** EDGECUTION browser extension technique  
**Shows:** 0 TPs in ~8B events, preserve detection logic, activation plan  
**Key pattern:** Zero prevalence = HOLD (not DROP), quarterly recurring hunt  
**File size:** 3KB - lightweight analysis

### H-0065_EXAMPLE.md (⏱️ TIME-BOX)
**Real hunt:** ClickFix C2 domain watchlist  
**Shows:** IOC-based detection, 90-day lifespan, campaign tracking strategy  
**Key pattern:** Campaign-specific = TIME-BOX (not PROMOTE), expires with campaign  
**File size:** 6KB - IOC refresh cycle, activation/deactivation triggers

### H-0064_EXAMPLE.md (🔄 RECURRING HUNT)
**Real hunt:** EC2 encryption disable detection  
**Shows:** 2,537 events/day, quarterly hunt workflow, 5-phase correlation analysis  
**Key pattern:** High volume = RECURRING HUNT (not standing detection), 90% coverage with 1% SOC effort  
**File size:** 8KB - quarterly execution strategy, volume analysis

### H-0066_EXAMPLE.md (📊 Risk Assessment)
**Real hunt:** IP camera infrastructure security assessment  
**Shows:** Configuration findings (not behavioral), client advisory output  
**Key pattern:** Network segmentation = advisory, not detection  
**File size:** 4KB - non-GATES workflow

**What these demonstrate:**
- Real BASE criteria scoring with evidence from actual hunts
- All 5 verdict types + risk assessment workflow
- Agent-queryable metadata (techniques, patterns, learnings)
- Deployment templates, prerequisites, and maintenance strategies
- Zero vs. non-zero TP scenarios
- Behavioral vs. configuration vs. IOC-based detections
- Volume-driven verdict selection (low → PROMOTE, medium → CONDITIONAL, high → RECURRING HUNT)
- Time-boxed vs. standing detection strategies
