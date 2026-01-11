---
hunt_id: H-XXXX
title: [Hunt Title]
status: planning  # Options: planning, in-progress, completed
date: YYYY-MM-DD
hunter: [Your Name]
platform: [Windows, macOS, Linux, Cloud, Network]  # Array - can include multiple platforms
tactics: [initial-access, persistence, privilege-escalation, defense-evasion, credential-access, discovery, lateral-movement, collection, command-and-control, exfiltration, impact]
techniques: [T1003.001, T1059.001]  # MITRE ATT&CK technique IDs
data_sources: [Splunk, ClickHouse, Sentinel, etc.]  # SIEM/log platforms used
related_hunts: []  # Hunt IDs that relate to this hunt (e.g., [H-0001, H-0005])
findings_count: 0  # Total findings discovered (optional - can update post-execution)
true_positives: 0  # Count of confirmed malicious activity (optional)
false_positives: 0  # Count of benign activity flagged (optional)
customer_deliverables: []  # For managed service providers tracking client reports (optional)
tags: [supply-chain, credential-theft, living-off-the-land]  # Freeform tags for categorization
---

# H-XXXX: [Hunt Title]

> **Note:** YAML frontmatter above enables AI filtering and automation (Level 2+). It's optional at Level 0-1, recommended at Level 2+, required at Level 3+. The markdown metadata section below provides human-readable context.

**Hunt Metadata**

- **Date:** YYYY-MM-DD
- **Hunter:** [Your Name]
- **Status:** [Planning|In Progress|Completed]
- **MITRE ATT&CK:** [T####.### - Technique Name]

---

## LEARN: Prepare the Hunt

### Hypothesis Statement

[Clear statement of what you're hunting for and why. Example: "Detect credential dumping attempts via mimikatz on corporate Windows servers based on recent APT29 activity patterns."]

### ABLE Scoping

Define your hunt scope using the ABLE framework:

| **Field**   | **Your Input** |
|-------------|----------------|
| **Actor** *(Optional)* | [Threat actor or "N/A" - Focus on behavior first unless actor context adds value] |
| **Behavior** | [Describe the actions, TTPs, methods, or tools involved] |
| **Location** | [Where: endpoint, network segment, cloud environment, etc.] |
| **Evidence** | **Source:** [Log source]<br>**Key Fields:** [field1, field2, field3]<br>**Example:** [What malicious activity looks like]<br><br>**Source:** [Additional source]<br>**Key Fields:** [field1, field2, field3]<br>**Example:** [What malicious activity looks like] |

**ABLE Example:**

| **Field** | **Example** |
|-----------|-------------|
| **Actor** | `APT29 (Cozy Bear)` |
| **Behavior** | `Credential dumping via mimikatz.exe (T1003)` |
| **Location** | `Corporate Windows Servers` |
| **Evidence** | **Source:** Sysmon Event ID 1 (Process Creation)<br>**Key Fields:** process_name, command_line, parent_process, user, hash<br>**Example:** Execution of mimikatz.exe with "privilege::debug sekurlsa::logonpasswords"<br><br>**Source:** Windows Security Events 4624/4625<br>**Key Fields:** user, source_ip, event_id, timestamp<br>**Example:** Successful logon followed by high-privilege process launches |

### Threat Intel & Research

- **MITRE ATT&CK Techniques:**
  - `T#### - Tactic Name`
  - `T####.### - Technique Name`
- **CTI Sources & References:**
  - [Link to threat report, blog, or intel source]
  - [Additional reference]
- **Historical Context:**
  - Has this been observed before in your environment?
  - Are there existing detections or mitigations?
  - What makes this hunt relevant now?

### Related Tickets

| **Team** | **Ticket/Details** |
|----------|-------------------|
| **SOC/IR** | [Incident ticket or "N/A"] |
| **Threat Intel** | [TI ticket or "N/A"] |
| **Detection Engineering** | [Detection ticket or "N/A"] |
| **Other** | [Related context or "N/A"] |

---

## OBSERVE: Expected Behaviors

### What Normal Looks Like

[Describe legitimate activity that might trigger false positives]

- [Example: System administrators running privileged commands]
- [Example: Automated maintenance scripts]

### What Suspicious Looks Like

[Describe the anomalous behavior you're hunting for]

- [Example: Mimikatz execution outside maintenance windows]
- [Example: Credential access from non-admin users]

### Expected Observables

- **Processes:** [process_name, command_line patterns]
- **Network:** [connections, destinations, protocols]
- **Files:** [paths, names, hashes]
- **Registry:** [keys, values modified]
- **Authentication:** [logon types, privilege escalations]

---

## CHECK: Execute & Analyze

### Data Source Information

- **Index/Data Source:** [e.g., index=windows, Sysmon logs, CloudTrail]
- **Time Range:** [Start datetime] to [End datetime]
- **Events Analyzed:** [Number or "TBD"]
- **Data Quality:** [Good|Fair|Poor - note any telemetry gaps]

### Hunting Queries

#### Initial Query

```[language: spl, kql, sigma, etc.]
[Your initial hunt query]
```

**Query Notes:**

- Did this return expected results?
- False positives encountered?
- Gaps identified?

#### Refined Query

```[language]
[Refined query after initial analysis]
```

**Refinement Rationale:**

- What changed and why?
- What improvements did this bring?

### Visualization & Analytics

- [Describe any time-series, heatmaps, or anomaly detection used]
- [Note patterns observed in visualizations]
- [Add screenshots to support findings]

### Query Performance

- **What Worked Well:** [Effective detection logic, good data sources]
- **What Didn't Work:** [Query issues, detection gaps, data limitations]
- **Iterations Made:** [Summary of query refinements]

---

## KEEP: Findings & Response

### Executive Summary

[3-5 sentences summarizing the investigation. State whether hypothesis was proved/disproved and key findings.]

### Findings

| **Finding** | **Ticket** | **Description** |
|-------------|-----------|-----------------|
| [True Positive / False Positive / Suspicious] | [INC-####] | [Brief description of finding and impact] |
| [Finding type] | [Ticket] | [Description] |
| [Finding type] | [Ticket] | [Description] |

**True Positives:** [Count and summary]
**False Positives:** [Count and common patterns]
**Suspicious Events:** [Count requiring further investigation]

### Detection Logic

**Automation Opportunity:**

- Could this hunt become an automated detection?
- What thresholds or conditions would trigger alerts?
- Tuning considerations to reduce false positives?

**Proposed Detection:**

```[language]
[Draft detection rule if applicable]
```

### Lessons Learned

**What Worked Well:**

- [Successful query strategies]
- [Effective data sources]
- [Useful analysis techniques]

**What Could Be Improved:**

- [Query refinements needed]
- [Data gaps to address]
- [Tooling or process improvements]

**Telemetry Gaps Identified:**

- [Missing log sources]
- [Insufficient field visibility]
- [Collection improvements needed]

### Follow-up Actions

- [ ] [Escalate true positives to incident response]
- [ ] [Create detection rule from hunt logic]
- [ ] [Update hypothesis with learnings]
- [ ] [Address telemetry gaps with engineering team]
- [ ] [Schedule recurring hunt execution]
- [ ] [Document findings in knowledge base]
- [ ] [Share insights with SOC/IR/TI teams]

### Follow-up Hunts

[New hunt ideas spawned from this investigation]

- H-XXXX: [New hunt based on findings]
- H-XXXX: [Pivot hunt to explore related TTPs]

---

**Hunt Completed:** [Date]
**Next Review:** [Date for recurring hunt or "N/A"]
