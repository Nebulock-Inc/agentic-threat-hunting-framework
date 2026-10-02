---
hunt_id: H-XXXX
title: [Hunt Title]
status: planning
date: YYYY-MM-DD
hunter: [Your Name]
hunt_type: hypothesis  # one of: hypothesis | baseline | model-assisted
platform: [Windows/Linux/macOS/Cloud]
tactics: [persistence, credential-access, etc.]
techniques: [T1003.001, T1005, etc.]
data_sources: [SIEM, EDR, etc.]
related_hunts: []
findings_count: 0
findings: []  # confirmed | suspected — each entry: subject, verdict, evidence, confirmation
ruled_out: []  # attempted_not_vulnerable | benign | inconclusive — each entry: subject, verdict, reason (attempted_not_vulnerable also needs control)
# Legacy counters, kept for hunts predating the ladder. Leave commented out: an
# explicit value overrides the counts derived from findings/ruled_out above, so
# `true_positives: 0` would mask a real confirmed finding.
# true_positives: 0
# false_positives: 0
customer_deliverables: []
tags: []
---

# H-XXXX: [Hunt Title]

**Hunt Metadata**

- **Date:** YYYY-MM-DD
- **Hunter:** [Your Name]
- **Status:** Planning
- **MITRE ATT&CK:** [Primary Technique]

---

## LEARN: Prepare the Hunt

### Hypothesis Statement

[What behavior are you looking for? What will you observe if the hypothesis is true?]

### Threat Context

[What threat actor/malware/TTP motivates this hunt?]

### ABLE Scoping

| **Field**   | **Your Input** |
|-------------|----------------|
| **Actor** *(Optional)* | [Threat actor or malware family] |
| **Behavior** | [TTP or behavior pattern] |
| **Location** | [Systems, networks, or environments to hunt] |
| **Evidence** | [Data sources and key fields to examine] |

### Threat Intel & Research

- **MITRE ATT&CK Techniques:** [List relevant techniques]
- **CTI Sources & References:** [Links to reports, blogs, etc.]

### Related Tickets

| **Team** | **Ticket/Details** |
|----------|-------------------|
| **SOC/IR** | [Ticket numbers or N/A] |

---

## OBSERVE: Expected Behaviors

### What Normal Looks Like

[Describe legitimate activity that should not trigger alerts]

### What Suspicious Looks Like

[Describe adversary behavior patterns to hunt for]

### Expected Observables

- **Processes:** [Process names, command lines]
- **Network:** [Connections, protocols, domains]
- **Files:** [File paths, extensions, sizes]
- **Registry:** [Registry keys if applicable]
- **Authentication:** [Login patterns if applicable]

---

## CHECK: Execute & Analyze

### Data Source Information

- **Index/Data Source:** [SIEM index or data source]
- **Time Range:** [Date range for hunt]
- **Events Analyzed:** [Approximate count]
- **Data Quality:** [Assessment of data completeness]

### Hunting Queries

#### Initial Query

```
[Your initial query]
```

**Query Notes:**
- [What did this query return?]
- [What worked? What didn't?]

#### Refined Query

```
[Your refined query after iterations]
```

**Refinement Rationale:**
- [Why did you change the query?]
- [What improvements were made?]

### Visualization & Analytics

[Describe any visualizations, timelines, or statistical analysis]

### Query Performance

**What Worked Well:**
- [Effective filters or techniques]

**What Didn't Work:**
- [Challenges or limitations]

**Iterations Made:**
- [Document query evolution]

---

## KEEP: Findings & Response

### Executive Summary

[Concise summary of hunt results and key findings]

### Findings

Only `confirmed` and `suspected` belong here.

| **Verdict** | **Subject** | **Ticket** | **Evidence** | **Independent Confirmation** |
|-------------|-------------|-----------|--------------|------------------------------|
| `confirmed` | [Host/account] | [Ticket] | [Telemetry — source and fields] | [Reproduction, host forensics, or config review] |
| `suspected` | [Host/account] | [Ticket] | [Telemetry — source and fields] | None — telemetry only |

`confirmed` needs telemetry **plus** confirmation from outside the log corpus. Telemetry alone caps at `suspected`.

### Ruled Out

| **Verdict** | **Subject** | **What Closed It** |
|-------------|-------------|--------------------|
| `attempted_not_vulnerable` | [Host/account] | [Name the control that held and how you verified it] |
| `benign` | [Host/account] | [Legitimate activity that explains it] |
| `inconclusive` | [Host/account] | [Telemetry that was missing] |

`attempted_not_vulnerable` and `benign` always go here, never in Findings.

**Counts:** `confirmed` [N] · `suspected` [N] · `attempted_not_vulnerable` [N] · `benign` [N] · `inconclusive` [N]

### Detection Logic

**Automation Opportunity:**

[Can this hunt become an automated detection rule?]

**Proposed Detection:**

```
[Detection rule if applicable]
```

**⚠️ Next Step: Validate with GATES**

Ask your assistant to run GATES whether or not you filled in the detection logic above —
this is assistant input, not a shell command. An empty **Proposed Detection** is not a
reason to skip it: GATES derives candidates from your queries, their results and your
"What Suspicious Looks Like" bullets, so an exploration hunt is the case it helps most.

```text
/gates --hunt H-XXXX
```

GATES validates detection quality using 5 criteria (Generalizable, Additive, Tunable, Exposure-tested, Sustainable) and returns a verdict per candidate: PROMOTE, CONDITIONAL, TIME_BOX, RECURRING_HUNT, HOLD, or DROP.

### Lessons Learned

**What Worked Well:**
- [Successes]

**What Could Be Improved:**
- [Areas for improvement]

**Telemetry Gaps Identified:**
- [Missing data sources or visibility gaps]

### Follow-up Actions

- [ ] Run GATES validation: `/gates --hunt H-XXXX`
- [ ] Document GATES verdict in "GATES Verdict" section below
- [ ] [Action item 1]
- [ ] [Action item 2]

### GATES Verdict

**Status:** [Not yet evaluated | PROMOTE | CONDITIONAL | TIME_BOX | RECURRING_HUNT | HOLD | DROP]  
**BASE Score:** [X.X]  *(float 0.0–5.0, not "X/5")*

**How to run:** `/gates --hunt H-XXXX`

**Rationale:** 
- **G** (Generalizable): [PASS/PARTIAL/FAIL - Why?]
- **A** (Additive): [PASS/PARTIAL/FAIL - Why?]
- **T** (Tunable): [PASS/PARTIAL/FAIL - Why?]
- **E** (Exposure-tested): [PASS/PARTIAL/FAIL - Why?]
- **S** (Sustainable): [PASS/PARTIAL/FAIL - Why?]

**Verdict Meaning:**

Each gate scores PASS (1.0), PARTIAL (0.5) or FAIL (0.0), summed to 0.0–5.0. Bands:

- **PROMOTE** (4.0-5.0): Deploy immediately to production
- **CONDITIONAL** (3.0-3.9): Deploy after prerequisites (allowlists, tuning, etc.)
- **HOLD** (0.0-2.9): Preserve for future, not ready for deployment

A **gate FAIL overrides the band**, because a FAIL names a specific defect and the fix
for that defect is a specific verdict:

Evaluate in this order and stop at the first match — when two gates fail, the earlier
one has to be solved first:

1. **A** FAIL → **DROP**: already covered, so there's nothing to add
2. **G** FAIL → **TIME_BOX**: IOC-based, so give it an expiry (e.g. 90 days)
3. **E** FAIL → **HOLD**: expand coverage, then re-assess
4. **S** FAIL → **RECURRING_HUNT**: too high-volume for 24/7 alerting; run it quarterly
5. **T** FAIL → **CONDITIONAL**: needs a baseline/allowlist before it can ship

Rows 2 and 4 both mean *carry the rule anyway, on a cycle*. If the hunt found **zero
instances** of the behavior, neither is worth the maintenance — the verdict is **HOLD**.
This does not apply when no gate FAILed: 0 TPs over a clean baseline is a proactive
**PROMOTE**.

**Next Steps:**
- [ ] [Action items based on verdict]
- [ ] **If PROMOTE or CONDITIONAL**: Proceed to detection engineering with ADEF
  - Install ADEF: `pip install agentic-detection-engineering-framework`
  - Import: `adef hunt-promote --gates ~/athf-workspace/hunt-promotion-analysis/H-XXXX_GATES.yaml`
    (`--dry-run` to preview). No `cd` needed — ADEF resolves its workspace from
    `ADEF_WORKSPACE`. A CONDITIONAL candidate lands flagged
    `needs_review: gates_conditional`, so finish its prerequisites before deploying.
  - Repository: https://github.com/Nebulock-Inc/agentic-detection-engineering-framework
- [ ] **If HOLD/DROP/TIME_BOX/RECURRING_HUNT**: Document strategy (see GATES output for details)

### Follow-up Hunts

- [Related hunt ideas for future investigation]

---

**Hunt Completed:** YYYY-MM-DD
**Next Review:** [Date for recurring hunt if applicable]
