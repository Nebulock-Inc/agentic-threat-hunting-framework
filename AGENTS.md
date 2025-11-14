# AGENTS.md - Context for AI Assistants

**Purpose:** This file tells AI assistants (GitHub Copilot, Claude Code, Cursor, etc.) what your threat hunting repository contains and how to use it.

**When to create this:** Level 2 (Searchable) - when you add AI integration to your hunting workflow.

**Who reads this:** AI tools that have access to your repository files.

---

## Repository Overview

This repository contains threat hunting hypotheses, execution notes, and lessons learned using the LOCK pattern (Learn → Observe → Check → Keep).

**AI assistants should:**

- Read past hunt notes before suggesting new hypotheses
- Reference lessons learned when generating queries
- Avoid suggesting hunts we've already completed
- Use environment.md to inform hunt planning

---

## Repository Structure

```
/
├── hunts/              # Hunt files following LOCK pattern
│   └── H-XXXX.md       # Single file per hunt (Planning → In Progress → Completed)
├── templates/          # LOCK-structured templates for new hunts
│   └── HUNT_LOCK.md    # Unified template combining hypothesis + execution
├── prompts/            # AI prompt templates
│   ├── basic-prompts.md  # Level 0-1 copy-paste prompts
│   └── ai-workflow.md    # Level 2 AI-assisted workflows
├── queries/            # Reusable query patterns (optional)
└── environment.md      # Tech stack, tools, infrastructure inventory
```

---

## Environmental Context Files

### environment.md

**Contains:**

- Security tools (SIEM, EDR, firewalls, monitoring platforms)
- Technology stack (languages, frameworks, databases, cloud services)
- Network architecture and infrastructure
- Internal documentation links (wikis, architecture diagrams, asset inventory)

**How AI should use this:**

- Reference when generating hypotheses to ensure hunt is relevant to our tech stack
- Check data sources available before suggesting queries
- Understand what technologies are deployed (including patch levels/CVE context)
- Understand what visibility/telemetry we have for proposed hunts

**Example:**

```
User: "Generate hypothesis for hunting Log4j exploitation"
AI: *checks environment.md* "I see you run Java applications with log aggregation
     in Splunk. Here's a hypothesis targeting your environment..."
```

**Note:** environment.md may include CVE/patch status for context, but this framework focuses on **behavior-based hunting**, not vulnerability scanning.

---

## Data Sources

**Update this section with your actual data sources:**

### SIEM / Log Aggregation

- **Platform:** [e.g., Splunk Enterprise, Elastic Security, Microsoft Sentinel]
- **Indexes/Tables:** [e.g., `index=winlogs`, `SecurityEvent`, `logs-*`]
- **Retention:** [e.g., 90 days hot, 1 year cold]
- **Query Language:** [SPL, KQL, Lucene, etc.]

### EDR / Endpoint Security

- **Platform:** [e.g., CrowdStrike Falcon, Microsoft Defender, SentinelOne]
- **Telemetry:** [Process execution, network connections, file events]
- **Query Access:** [API, console, integrated with SIEM]

### Network Security

- **Flow Data:** [NetFlow, IPFIX, Zeek logs]
- **Packet Capture:** [Available? Retention period?]
- **Firewall Logs:** [Vendor, where logs are stored]
- **IDS/IPS:** [Snort, Suricata, alerts in SIEM]

### Cloud Security

- **Providers:** [AWS, Azure, GCP]
- **Logging:** [CloudTrail, Azure Monitor, Cloud Logging]
- **Where Stored:** [Centralized in SIEM? Separate platform?]

### Identity & Access

- **Identity Provider:** [Active Directory, Okta, Azure AD]
- **Authentication Logs:** [Where are auth events logged?]
- **MFA Events:** [Available? Where?]

**AI Note:** Always verify data sources exist before generating queries. Reference environment.md for detailed coverage.

---

## Hunting Methodology

**Primary Framework:** [PEAK / TaHiTI]

This repository follows the **LOCK pattern**:

1. **Learn** - Gather context (CTI, alert, anomaly, threat intel)
2. **Observe** - Form hypothesis about adversary behavior
3. **Check** - Test with bounded, safe query
4. **Keep** - Record decision and lessons learned

**AI assistants should:**

- Generate hypotheses in LOCK format (see templates/)
- Ensure queries are bounded by time, scope, and impact
- Document lessons learned after hunt execution
- Reference past hunts when suggesting new ones

---

## Guardrails for AI Assistance

### Query Safety

- **Always include time bounds** (e.g., last 7 days, not "all time")
- **Limit result sets** (e.g., `| head 1000`, `TOP 100`)
- **Avoid expensive operations** without explicit approval (stats over 30+ days, full table scans)
- **Test on small windows first** before expanding timeframe

### Hypothesis Validation

- **Check if we've hunted this before** (grep hunts/ folder)
- **Verify data source availability** (reference environment.md)
- **Ensure hypothesis is testable** (can be validated with a query)
- **Consider false positive rate** (will this hunt generate noise?)

### Documentation

- **Use LOCK structure** for all hunt documentation
- **Capture negative results** (hunts that found nothing are still valuable)
- **Record lessons learned** (what worked, what didn't, what to try next time)
- **Link related hunts** (if this builds on past work, reference it)

### Memory and Context

- **Search before suggesting** - Check if we've hunted this TTP/behavior before
- **Reference environment.md** - Ensure suggestions match our actual tech stack
- **Apply past lessons** - Use outcomes from similar hunts to improve new hypotheses

---

## AI Workflow Examples

### Level 2 (Searchable) - AI with Memory

**User asks:** "Generate hypothesis for hunting Kerberoasting attacks"

**AI should:**

1. Search `hunts/` for past Kerberoasting hunts
2. Check `environment.md` for Active Directory presence and logging capabilities
3. Read any lessons learned from similar hunts (T1558.003, credential access TTPs)
4. Generate LOCK-formatted hypothesis referencing available data sources
5. Suggest query targeting confirmed data sources (e.g., Windows Security Event Logs in Splunk)

### Level 3+ (Autonomous) - Scripted Workflows

When building automation scripts, AI should:

- Reference this AGENTS.md file to understand repo structure
- Use environment.md as the tech stack source of truth
- Follow LOCK structure when auto-generating hunt files
- Include human-in-the-loop validation for high-risk operations

---

## Hypothesis Generation Workflow

**For complete workflows with examples, see [prompts/ai-workflow.md](prompts/ai-workflow.md)**

This section provides essential guidance for AI assistants generating threat hunting hypotheses. This is the most common Level 2 (Searchable) workflow.

### Essential Workflow Steps

**Core Process:**

1. **Search Memory First** - Check hunts/ for similar TTPs or past work
2. **Validate Environment** - Read environment.md to confirm data sources exist
3. **Generate LOCK Hypothesis** - Create testable hypothesis following templates/HUNT_LOCK.md
4. **Suggest Next Steps** - Offer to create hunt file or draft query

**Key Requirements:**

- Match hypothesis format: "Adversaries use [behavior] to [goal] on [target]"
- Reference past hunts by ID (e.g., "Building on H-0022 lessons...")
- Specify data sources from environment.md (e.g., "index=winlogs", "SecurityEvent table")
- Include bounded time range with justification
- Consider false positives from similar past hunts

**Output Must Follow:** [templates/HUNT_LOCK.md](templates/HUNT_LOCK.md) structure

**Complete workflow details, examples, and troubleshooting:** [prompts/ai-workflow.md](prompts/ai-workflow.md)

---

## ATT&CK Coverage

**Optional - Document your priority TTPs:**

### High Priority TTPs (based on threat model)

- T1003 - Credential Dumping
- T1059 - Command and Scripting Interpreter
- T1110 - Brute Force
- T1078 - Valid Accounts
- [Add your priority TTPs]

### Known Coverage Gaps

- [TTPs you can't currently hunt due to telemetry gaps]
- [Reference environment.md "Known Gaps & Blind Spots" section]

**AI Note:** Prioritize hunt suggestions for high-priority TTPs with available telemetry.

---

## Organization-Specific Context

**Optional - Add details unique to your environment:**

### Threat Model

- [Industry-specific threats you care about]
- [Known adversary groups targeting your sector]
- [Past incidents that inform current focus]

### Business Context

- [Critical applications/services that need extra scrutiny]
- [Compliance requirements affecting hunt scope]
- [Operational constraints (maintenance windows, access restrictions)]

### Team Practices

- [Hunt cadence - daily, weekly, monthly?]
- [Who reviews/approves hunts before execution?]
- [Where do hunt results get reported?]

---

## Memory Scaling

**Current maturity level:** [0: Manual | 1: Documented | 2: Searchable | 3: Generative | 4: Autonomous]

**Memory approach:**

- **Level 1-2:** Grep-based search across markdown files (no structured memory yet)
- **Level 3+:** [If applicable: SQLite/JSON index for faster search, agent-accessible structured memory]

**When AI needs to recall past hunts:**

- Use grep/search across `hunts/` folder (hunt notes)
- Use grep/search across `environment.md` (tech stack and context)
- At Level 3+: Query structured memory if available

---

## Maintenance Notes

**Review this file when:**

- Adding new data sources (update "Data Sources" section)
- Changing AI tools (update "AI Workflow Examples")
- Reaching new maturity level (update "Memory Scaling")
- Discovering AI generates incorrect assumptions (add to "Guardrails")

**Last Updated:** [YYYY-MM-DD]
**Maintained By:** [Team/Individual]
