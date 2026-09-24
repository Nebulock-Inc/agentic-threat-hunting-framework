---
hunt_id: H-XXXX
title: [Hunt Title]
status: planning
date: YYYY-MM-DD
hunter: [Your Name]
platform: [Windows/Linux/macOS/Cloud]
tactics: [persistence, credential-access, etc.]
techniques: [T1003.001, T1005, etc.]
data_sources: [SIEM, EDR, etc.]
related_hunts: []
findings_count: 0
true_positives: 0
false_positives: 0
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

| **Finding** | **Ticket** | **Description** |
|-------------|-----------|-----------------|
| True Positive | [Ticket] | [Description] |
| False Positive | N/A | [Description] |

**True Positives:** [Count]
**False Positives:** [Count]

### Detection Logic

**Automation Opportunity:**

[Can this hunt become an automated detection rule?]

**Proposed Detection:**

```
[Detection rule if applicable]
```

**⚠️ Next Step: Validate with GATES**

If you documented detection logic above, run:
```bash
/gates --hunt H-XXXX
```

GATES validates detection quality using 5 criteria (Generalizable, Additive, Tunable, Exposure-tested, Sustainable) and provides verdict: PROMOTE, CONDITIONAL, HOLD, TIME-BOX, or RECURRING HUNT.

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

**Status:** [Not yet evaluated | PROMOTE | CONDITIONAL | HOLD | TIME-BOX | RECURRING HUNT]  
**BASE Score:** [X/5]

**How to run:** `/gates --hunt H-XXXX`

**Rationale:** 
- **G** (Generalizable): [PASS/PARTIAL/FAIL - Why?]
- **A** (Additive): [PASS/PARTIAL/FAIL - Why?]
- **T** (Tunable): [PASS/PARTIAL/FAIL - Why?]
- **E** (Exposure-tested): [PASS/PARTIAL/FAIL - Why?]
- **S** (Sustainable): [PASS/PARTIAL/FAIL - Why?]

**Verdict Meaning:**
- **PROMOTE** (4-5/5): Deploy immediately to production
- **CONDITIONAL** (3/5): Deploy after prerequisites (allowlists, tuning, etc.)
- **HOLD** (0-2/5): Preserve for future, not ready for deployment
- **TIME-BOX**: IOC-based detection with expiration date (e.g., 90 days)
- **RECURRING HUNT**: High volume, run quarterly instead of 24/7 alerting

**Next Steps:**
- [ ] [Action items based on verdict]
- [ ] **If PROMOTE**: Proceed to detection engineering with ADEF
  - Install ADEF: `pip install agentic-detection-engineering-framework`
  - Switch to ADEF workspace: `cd ~/adef-workspace/`
  - Run FORGE: `adef forge --input ~/athf-workspace/hunt-promotion-analysis/H-XXXX_GATES.yaml`
  - Repository: https://github.com/Nebulock-Inc/agentic-detection-engineering-framework
- [ ] **If CONDITIONAL**: Complete prerequisites first, then proceed to ADEF
- [ ] **If HOLD/TIME-BOX/RECURRING**: Document strategy (see GATES output for details)

### Follow-up Hunts

- [Related hunt ideas for future investigation]

---

**Hunt Completed:** YYYY-MM-DD
**Next Review:** [Date for recurring hunt if applicable]
