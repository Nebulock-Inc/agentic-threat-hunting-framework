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
findings: []  # confirmed | suspected — each entry: subject, verdict, evidence, confirmation
ruled_out: []  # attempted_not_vulnerable | benign — each entry: subject, verdict, reason
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

### Lessons Learned

**What Worked Well:**
- [Successes]

**What Could Be Improved:**
- [Areas for improvement]

**Telemetry Gaps Identified:**
- [Missing data sources or visibility gaps]

### Follow-up Actions

- [ ] [Action item 1]
- [ ] [Action item 2]

### Follow-up Hunts

- [Related hunt ideas for future investigation]

---

**Hunt Completed:** YYYY-MM-DD
**Next Review:** [Date for recurring hunt if applicable]
