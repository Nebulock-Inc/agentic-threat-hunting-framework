# Hunt Format Guidelines

## Standard: LOCK Methodology with ABLE Scoping

All hunt files in this framework follow the **LOCK** (Learn-Observe-Check-Keep) methodology combined with **ABLE** scoping (Actor-Behavior-Location-Evidence). This unified format combines hypothesis planning and execution results in a single document.

## File Naming Convention

- **Format:** `H-####.md` (e.g., `H-0001.md`, `H-0002.md`)
- **Sequential numbering** starting from 0001
- **Single file** contains both the hunt methodology and execution results
- **No dated execution files** - update the same file as you iterate

## Template Structure

The HUNT_LOCK.md template contains these sections:

### Title & Metadata

```markdown
# H-XXXX: [Hunt Title]

**Hunt Metadata**
- Date: YYYY-MM-DD
- Hunter: [Your Name]
- Status: [Planning|In Progress|Completed]
- MITRE ATT&CK: [T####.### - Technique Name]
```

**Status Values:**

- **Planning** - Hunt is being designed
- **In Progress** - Hunt is actively being executed
- **Completed** - Hunt execution finished, results documented

---

## YAML Frontmatter (Optional at Level 0-1, Recommended at Level 2+)

### What is YAML Frontmatter?

YAML frontmatter is machine-readable metadata placed at the very top of hunt files. It enables:

- **AI-powered filtering** - Quickly find hunts by status, tactics, techniques, platform
- **Automated analysis** - Calculate hunt success rates, track findings, identify coverage gaps
- **Hunt relationships** - Link related hunts for context and knowledge building
- **Maturity progression** - Prepares your hunting program for Level 3+ automation

### When to Use YAML Frontmatter

| Maturity Level | Recommendation | Rationale |
|----------------|----------------|-----------|
| **Level 0-1** (Manual) | Optional | Focus on learning LOCK methodology first |
| **Level 2** (Searchable) | Recommended | AI can now filter and reference hunts programmatically |
| **Level 3+** (Generative/Agentic) | Required | Automation requires structured metadata |

### Dual-Format Approach

Hunt files use **both** YAML frontmatter and markdown metadata:

1. **YAML frontmatter** (lines 1-17) - Machine-readable, enables automation
2. **Markdown metadata** (below title) - Human-readable, provides visual context

**Why both?** YAML enables AI filtering while markdown provides at-a-glance context when reading hunts.

### Complete YAML Schema

```yaml
---
hunt_id: H-XXXX                    # Unique hunt identifier (required)
title: [Hunt Title]                # Full hunt title (required)
status: planning                   # Options: planning, in-progress, completed (required)
date: YYYY-MM-DD                   # Hunt creation or last update date (required)
hunter: [Your Name]                # Person or team conducting hunt (required)
platform: [Windows, macOS, Linux]  # Target platforms - array format (required)
tactics: [credential-access]       # MITRE ATT&CK tactics (required)
techniques: [T1003.001]            # MITRE ATT&CK technique IDs (required)
data_sources: [Splunk]             # SIEM/log platforms used (required)
related_hunts: []                  # Related hunt IDs (optional)
findings_count: 0                  # Total findings discovered (optional)
true_positives: 0                  # Confirmed malicious activity (optional)
false_positives: 0                 # Benign activity flagged (optional)
customer_deliverables: []          # For MSPs tracking deliverables (optional)
tags: [credential-theft]           # Freeform categorization tags (optional)
---
```

### Field Definitions

#### Required Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `hunt_id` | string | Unique identifier matching filename | `H-0042` |
| `title` | string | Full descriptive hunt title | `Kerberoasting Detection via Service Ticket Requests` |
| `status` | string | Hunt lifecycle stage | `planning`, `in-progress`, `completed` |
| `date` | string (YYYY-MM-DD) | Hunt creation or last updated date | `2025-11-30` |
| `hunter` | string | Person or team conducting hunt | `Security Team`, `John Doe` |
| `platform` | array | Operating systems or environments targeted | `[Windows, macOS, Linux]`, `[Cloud]`, `[Network]` |
| `tactics` | array | MITRE ATT&CK tactics (lowercase with hyphens) | `[credential-access, persistence]` |
| `techniques` | array | MITRE ATT&CK technique IDs | `[T1003.001, T1558.003]` |
| `data_sources` | array | SIEM, EDR, or log platforms used | `[Splunk, Sentinel, ClickHouse]` |

#### Optional Fields

| Field | Type | Purpose | Example | When to Use |
|-------|------|---------|---------|-------------|
| `related_hunts` | array | Hunt IDs that relate to this hunt | `[H-0015, H-0038]` | When building on past work or pivoting |
| `findings_count` | integer | Total findings (TP + FP + suspicious) | `15` | Post-execution or during KEEP phase |
| `true_positives` | integer | Confirmed malicious activity | `3` | Post-execution summary |
| `false_positives` | integer | Benign activity flagged | `12` | Post-execution summary |
| `customer_deliverables` | array | Client report references (for MSPs) | `[CUST-2025-Q1-001]` | Managed service providers |
| `tags` | array | Freeform categorization keywords | `[supply-chain, living-off-the-land]` | Additional context beyond ATT&CK |

### MITRE ATT&CK Tactic Reference

Use these **lowercase hyphenated** values for the `tactics` field:

- `initial-access`
- `execution`
- `persistence`
- `privilege-escalation`
- `defense-evasion`
- `credential-access`
- `discovery`
- `lateral-movement`
- `collection`
- `command-and-control`
- `exfiltration`
- `impact`

### Platform Values

Common values for the `platform` array:

- `Windows` - Windows endpoints/servers
- `macOS` - Apple macOS systems
- `Linux` - Linux distributions
- `Cloud` - Cloud services (AWS, Azure, GCP)
- `Network` - Network devices/traffic
- `Container` - Docker, Kubernetes
- `SaaS` - Software-as-a-Service applications

### Examples

#### Minimal YAML Frontmatter (Level 0-1)

```yaml
---
hunt_id: H-0001
title: macOS Data Collection via AppleScript
status: completed
date: 2025-11-19
hunter: Security Team
platform: [macOS]
tactics: [collection]
techniques: [T1005]
data_sources: [Splunk]
related_hunts: []
findings_count: 0
true_positives: 0
false_positives: 0
customer_deliverables: []
tags: [macos, applescript]
---
```

#### Comprehensive YAML Frontmatter (Level 2+)

```yaml
---
hunt_id: H-0042
title: Kerberoasting Detection via Service Ticket Requests
status: completed
date: 2025-11-30
hunter: Threat Hunting Team
platform: [Windows]
tactics: [credential-access]
techniques: [T1558.003]
data_sources: [Splunk, Windows Event Logs]
related_hunts: [H-0015, H-0038]
findings_count: 15
true_positives: 3
false_positives: 12
customer_deliverables: []
tags: [kerberos, active-directory, credential-theft, service-accounts]
---
```

#### Multi-Platform Hunt Example

```yaml
---
hunt_id: H-0078
title: JavaScript Malware Execution Detection
status: in-progress
date: 2025-12-01
hunter: Detection Engineering
platform: [Windows, macOS, Linux]  # Cross-platform TTP
tactics: [execution]
techniques: [T1059.007]
data_sources: [EDR, Sysmon]
related_hunts: [H-0004]
findings_count: 0
true_positives: 0
false_positives: 0
customer_deliverables: []
tags: [javascript, node-js, living-off-the-land, supply-chain]
---
```

### Adoption by Maturity Level

#### Level 0-1: Manual & Documented

**Goal:** Learn LOCK methodology, build hunting muscle memory

**YAML Frontmatter:** Optional - You can omit it entirely or include minimal fields

**Focus on:**

- Understanding hypothesis generation
- Writing clear queries
- Documenting lessons learned

**Example:** Use markdown metadata only, skip YAML frontmatter

#### Level 2: Searchable

**Goal:** Enable AI to search and reference past hunts

**YAML Frontmatter:** Recommended - Include all required fields + tags

**Focus on:**

- Consistent metadata across hunts
- Using AI to find related work
- Tracking ATT&CK coverage

**Example:** Add YAML with required fields, populate `tags` and `related_hunts`

#### Level 3+: Generative & Agentic

**Goal:** Automation, metrics, programmatic hunt generation

**YAML Frontmatter:** Required - All fields, especially findings metrics

**Focus on:**

- Hunt success rate analysis
- Automated coverage gap identification
- Programmatic hunt scheduling
- Knowledge graph construction

**Example:** Full YAML schema with all optional fields populated post-execution

### YAML Best Practices

**Consistency**

- Use lowercase hyphenated tactics (`credential-access`, not `Credential Access`)
- Use proper ATT&CK technique IDs (`T1003.001`, not `T1003`)
- Use kebab-case for multi-word tags (`living-off-the-land`, not `living_off_the_land`)

**When to Update**

- **During Planning:** Set `status: planning`, populate tactics/techniques/platform
- **During Execution:** Change `status: in-progress`
- **Post-Execution:** Update `status: completed`, add findings counts

**Related Hunts**

- Link to hunts you built upon (`related_hunts: [H-0022]`)
- Link to hunts that extend your findings (`related_hunts: [H-0045, H-0046]`)
- Don't overlink - only add hunts that directly inform or extend this work

**Tags**

- Supplement ATT&CK with context: `supply-chain`, `zero-day`, `apt29`
- Use lowercase hyphenated format: `credential-theft`, not `Credential Theft`
- 3-6 tags per hunt is ideal

---

### LEARN: Prepare the Hunt

Educational foundation and hunt planning.

**Hypothesis Statement:**
Clear statement of what you're hunting and why.

**ABLE Scoping Table:**

| Field | Your Input |
|-------|-----------|
| **Actor** *(Optional)* | Threat actor or "N/A" |
| **Behavior** | Actions, TTPs, methods, tools |
| **Location** | Endpoint, network, cloud environment |
| **Evidence** | **Source:** [Log source]<br>**Key Fields:** [field1, field2]<br>**Example:** [What malicious activity looks like] |

**Threat Intel & Research:**

- MITRE ATT&CK techniques
- CTI sources and references
- Historical context for your environment

**Related Tickets:**
Cross-references to SOC, IR, TI, or DE tickets

---

### OBSERVE: Expected Behaviors

Hypothesis of what you expect to find.

**What Normal Looks Like:**
Describe legitimate activity (false positive sources)

**What Suspicious Looks Like:**
Describe anomalous behaviors you're hunting

**Expected Observables:**

- Processes, network connections, files, registry keys, authentication events

---

### CHECK: Execute & Analyze

Investigation execution and results.

**Data Source Information:**

- Index/data source
- Time range analyzed
- Events processed
- Data quality notes

**Hunting Queries:**

```[language]
[Initial query]
```

**Query Notes:** Did it work? FPs? Gaps?

```[language]
[Refined query after iteration]
```

**Refinement Rationale:** What changed and why?

**Visualization & Analytics:**

- Time-series, heatmaps, anomaly detection used
- Patterns observed
- Screenshots referenced

**Query Performance:**

- What worked well
- What didn't work
- Iterations made

---

### KEEP: Findings & Response

Results, lessons, and follow-up actions.

**Executive Summary:**
3-5 sentences: What was found? Hypothesis proved/disproved?

**Findings Table:**

| Finding | Ticket | Description |
|---------|--------|-------------|
| [TP/FP/Suspicious] | [INC-####] | [Brief description] |

**True Positives:** Count and summary
**False Positives:** Count and patterns
**Suspicious Events:** Count requiring investigation

**Detection Logic:**

- Could this become automated detection?
- Thresholds and conditions for alerts
- Tuning considerations

**Lessons Learned:**

- What worked well
- What could be improved
- Telemetry gaps identified

**Follow-up Actions:**

- [ ] Checklist items for next steps
- [ ] Detection rule creation
- [ ] Hypothesis updates needed

**Follow-up Hunts:**

- H-XXXX: [New hunt ideas from findings]

---

**Hunt Completed:** [Date]

---

## Section Purpose Guide

### LEARN

**Purpose:** Build understanding and context before hunting.

- Explain the TTP being hunted
- Provide threat intel context
- Document why this hunt matters now
- Use ABLE framework to scope precisely

### OBSERVE

**Purpose:** Create clear, testable hypothesis.

- State what you expect to find
- Distinguish normal from suspicious
- List specific observables

### CHECK

**Purpose:** Execute investigation and document process.

- Embed queries directly in markdown
- Document what worked and what didn't
- Show query iterations and refinements
- Track performance and data quality

### KEEP

**Purpose:** Capture outcomes and enable improvement.

- Summarize findings (TP/FP/Suspicious)
- Extract lessons learned
- Identify detection opportunities
- Plan follow-up actions and hunts

## Hunt Workflow Best Practices

### Query Development

- **Embed queries in markdown** using code blocks with syntax highlighting
- **Comment your queries** to explain detection logic
- **Document iterations** - Show initial query and refinements
- **Explain why queries changed** based on findings

### ABLE Scoping

- **Actor is optional** - Focus on behavior unless actor context adds value
- **Evidence section is critical** - Include log sources, key fields, and examples
- **Be specific** - Vague scoping leads to vague results

### Single-File Workflow

- **Update the same file** as you iterate (no dated copies)
- **Status field tracks progress** (Planning → In Progress → Completed)
- **Keep query history** - Comment out old queries, don't delete them
- **Document why things changed** in lessons learned

### Status Management

- **Planning:** Hypothesis defined, queries being developed
- **In Progress:** Actively hunting, collecting data, refining queries
- **Completed:** Results documented, findings summarized, lessons captured

## Why LOCK + ABLE?

**LOCK methodology** ensures structured hunting:

- **Learn:** Educational foundation
- **Observe:** Clear hypothesis
- **Check:** Actionable detection
- **Keep:** Captured lessons

**ABLE scoping** provides precision:

- **Actor:** Who (optional context)
- **Behavior:** What (required - the actions)
- **Location:** Where (required - the environment)
- **Evidence:** How to find it (required - data sources and examples)

Together they create hunts that are educational, repeatable, and improve over time.

## Design Inspiration

This template combines best practices from multiple threat hunting frameworks:

- **LOCK methodology** (Learn-Observe-Check-Keep) for structured, educational hunting
- **ABLE scoping** (Actor-Behavior-Location-Evidence) for precise hunt definition
- **PEAK framework** (Prepare-Execute-Act with Knowledge) for single-file hypothesis+execution workflow

The result is a condensed, practical template that guides hunters from hypothesis through results while maintaining comprehensive documentation.

## Example Reference

See [H-0001.md](H-0001.md), [H-0002.md](H-0002.md), and [H-0003.md](H-0003.md) for complete hunt examples.
