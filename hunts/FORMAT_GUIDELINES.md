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
**Next Review:** [Date for recurring hunt or "N/A"]

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

## Best Practices

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

See [H-0001.md](H-0001.md) and [H-0002.md](H-0002.md) for complete hunt examples.
