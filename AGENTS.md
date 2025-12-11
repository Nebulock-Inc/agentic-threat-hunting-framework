# AGENTS.md - Context for AI Assistants

**Purpose:** This file tells AI assistants (GitHub Copilot, Claude Code, Cursor, etc.) what your threat hunting repository contains and how to use it.

**When to create this:** Level 2 (Searchable) - when you add AI integration to your hunting workflow.

**Who reads this:** AI tools that have access to your repository files.

---

## Repository Overview

This repository contains threat hunting hypotheses, execution notes, and lessons learned using the LOCK pattern (Learn → Observe → Check → Keep).

**AI assistants should:**

- **Read [knowledge/hunting-knowledge.md](knowledge/hunting-knowledge.md) before generating hypotheses** - This contains the "hunting brain" knowledge (hypothesis generation, behavioral models, pivot logic, analytical rigor, frameworks)
- Read past hunt notes before suggesting new hypotheses
- Reference lessons learned when generating queries
- Avoid suggesting hunts we've already completed
- Use [docs/environment.md](docs/environment.md) to inform hunt planning
- **Focus on behaviors and TTPs (top of Pyramid of Pain), not indicators** - Never build hunts around hashes or IPs alone

---

## Repository Structure

```
/
├── README.md              # Framework overview and landing page
├── AGENTS.md              # This file - AI assistant context
├── USING_ATHF.md          # Adoption and customization guide
├── SHOWCASE.md            # Example results and use cases
├── .athfconfig.yaml       # Workspace configuration (hunt prefix, SIEM settings)
│
├── hunts/                 # Hunt hypothesis cards (LOCK structure)
│   └── H-XXXX.md          # Single file per hunt (hypothesis, planning, outcomes)
│
├── queries/               # Query implementations for testing hypotheses
│   └── H-XXXX.spl         # Splunk/KQL queries with time bounds and result caps
│
├── runs/                  # Hunt execution results and findings
│   └── H-XXXX_YYYY-MM-DD.md  # Dated execution notes (LOCK structure)
│
├── templates/             # LOCK-structured templates for new hunts
│   └── HUNT_LOCK.md       # Unified template combining hypothesis + execution
│
├── prompts/               # AI prompt templates
│   ├── basic-prompts.md   # Level 0-1 copy-paste prompts
│   └── ai-workflow.md     # Level 2 AI-assisted workflows
│
├── knowledge/             # Domain expertise and hunting frameworks
│   └── hunting-knowledge.md  # Expert hunting knowledge base
│
├── integrations/          # MCP server catalog and quickstart guides
│   ├── MCP_CATALOG.md     # Available tool integrations
│   └── quickstart/        # Setup guides for specific tools
│
├── docs/                  # Detailed documentation
│   ├── environment.md     # Tech stack, tools, infrastructure inventory
│   ├── getting-started.md # Step-by-step adoption guide
│   ├── lock-pattern.md    # LOCK methodology details
│   ├── maturity-model.md  # Five levels explained
│   └── level4-agentic-workflows.md  # Level 4 autonomous agent examples
│
├── athf/                  # CLI source code (optional convenience tooling)
│   ├── commands/          # Hunt management commands
│   ├── core/              # Hunt parsing and validation
│   └── utils/             # Helper utilities
│
├── config/                # Configuration templates
├── scripts/               # Helper scripts
├── tests/                 # Test suite for CLI
└── assets/                # Images and diagrams
    ├── athf_logo.jpg
    ├── athf_lock.png
    └── athf_fivelevels.png
```

---

## Directory Structure & File Naming Conventions

The repository uses a **hunt-centric naming scheme** where all files related to a single hunt share the same hunt ID (H-####). This ensures traceability and makes it easy to find related artifacts.

### Folder Purposes & File Naming

| Folder | Purpose | File Naming | Example |
|--------|---------|-------------|---------|
| **hunts/** | Hunt hypothesis cards following LOCK pattern | `H-####.md` | `H-0042.md` |
| **queries/** | Query implementations (reusable, testable) | `H-####.spl` or `H-####.kql` | `H-0042.spl` |
| **runs/** | Execution results and findings from running a hunt | `H-####_YYYY-MM-DD.md` | `H-0042_2025-11-29.md` |
| **templates/** | LOCK-structured templates for new hunts | (referenced, not created per hunt) | `HUNT_LOCK.md` |

### Workflow: Hypothesis → Query → Results

The three-file workflow connects directly through hunt IDs:

```
H-0042.md (hypothesis, LOCK structure)
    ↓
H-0042.spl (query to test the hypothesis)
    ↓
H-0042_2025-11-29.md (results from running the query on Nov 29)
    ↓
H-0042_2025-12-06.md (results from re-running the same query on Dec 6)
```

**Key Points:**

- **hunts/** = The "what we're hunting for" (behavior, TTP, hypothesis)
- **queries/** = The "how we test it" (bounded, time-limited search logic)
- **runs/** = The "what we found" (execution results, decisions, lessons learned)
- **Dates in runs/** = Track hunt iteration over time (same hunt re-executed on different dates)

### Example: Complete Hunt Lifecycle

1. **Create hypothesis** → `hunts/H-0042.md` (LOCK-formatted hunt card)
2. **Draft query** → `queries/H-0042.spl` (Splunk query with time bounds and result caps)
3. **Execute hunt** → Run query, document findings → `runs/H-0042_2025-11-29.md` (LOCK-formatted results)
4. **Re-run hunt later** → Same query, new date → `runs/H-0042_2025-12-06.md` (new execution)
5. **Refine query** → Update `queries/H-0042.spl` based on lessons learned
6. **Re-run refined hunt** → `runs/H-0042_2025-12-13.md` (improved results)

### AI Guidance

When working with hunts:

- **Use hunt ID as primary reference** - "Let me look at H-0042" immediately tells you: hypothesis (hunts/), query (queries/), and all past executions (runs/)
- **Search by hunt ID first** - Check if hunt exists: `athf hunt search "H-0042"` (or `grep "H-0042" hunts/*.md` if CLI unavailable)
- **Link queries to hypotheses** - Every query should correspond to a hunt card (same H-#### ID)
- **Track execution history** - Multiple run files for same hunt ID shows iteration and learning over time

---

## Hunting Brain Knowledge Base

### knowledge/hunting-knowledge.md

**Purpose:** Embeds expert threat hunting knowledge into AI reasoning. This is Claude's "hunting brain" - the analytical frameworks, heuristics, and mental models that expert hunters internalize.

**When to consult:**

- **Before generating hypotheses** - Review Section 1 (Hypothesis Generation) and Section 5 (Pyramid of Pain)
- **During hunt execution** - Review Section 3 (Pivot Logic) for artifact chains
- **When analyzing findings** - Review Section 4 (Analytical Rigor) for confidence scoring and bias checks
- **When mapping TTPs** - Review Section 2 (Behavioral Models) for TTP → observable mappings

**Core Sections:**

1. **Hypothesis Generation Knowledge** - Pattern-based generation, quality criteria, good/bad examples, seed conversion
2. **Behavioral Models** - ATT&CK TTP → observable mappings, behavior-to-telemetry translation, blind spots, baselines
3. **Pivot Logic** - Artifact chains, pivot playbooks, when to pivot vs collapse decisions
4. **Analytical Rigor** - Confidence scoring rubric, evidence strength, cognitive bias checks, suspicious vs benign heuristics
5. **Framework Mental Models** - Pyramid of Pain, Diamond Model, Cyber Kill Chain, Hunt Maturity, Data Quality

**Key Principle:** All hunts must focus on **behaviors and TTPs (top half of Pyramid of Pain)**. Never build hunts solely around hashes, IPs, or domains - these are trivial for adversaries to change. Hunt for behaviors that are painful for adversaries to modify.

**AI Usage:**

- Apply frameworks, don't just mention them (e.g., use Pyramid of Pain to prioritize indicators, apply confidence rubric to score findings)
- Reference specific sections when explaining reasoning
- Demonstrate analytical rigor using the knowledge base principles

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
AI: *checks docs/environment.md* "I see you run Java applications with log aggregation
     in Splunk. Here's a hypothesis targeting your environment..."
```

**Note:** [docs/environment.md](docs/environment.md) may include CVE/patch status for context, but this framework focuses on **behavior-based hunting**, not vulnerability scanning.

---

## Data Sources & Environment Context

**Reference:** See [environment.md](docs/environment.md) for the comprehensive, authoritative inventory of your tech stack, tools, and infrastructure.

### Quick Reference for Hunt Planning

Before suggesting a hunt, I verify that the required data sources and telemetry are available in your environment. Use this table to see what I look for:

| Category | Hunt Requires | Why This Matters | Reference |
|----------|---------------|------------------|-----------|
| **SIEM/Logs** | Log aggregation platform with query language (SPL, KQL, etc.) | Can't hunt without searchable logs | See [docs/environment.md](docs/environment.md) "SIEM / Log Aggregation" |
| **Endpoint** | EDR with process, network, and/or file telemetry | Determines what adversary behaviors you can detect | See [docs/environment.md](docs/environment.md) "EDR / Endpoint Security" |
| **Network** | Flow data (NetFlow/IPFIX) or firewall/IDS logs | Needed for C2 communication, lateral movement, data exfiltration hunts | See [docs/environment.md](docs/environment.md) "Network Security" |
| **Cloud** | Cloud provider (AWS/Azure/GCP) with CloudTrail/activity logging | Scope of cloud hunting capability | See [docs/environment.md](docs/environment.md) "Cloud Security" |
| **Identity** | Active Directory or identity provider with auth logs | Needed for credential attack, lateral movement, persistence hunts | See [docs/environment.md](docs/environment.md) "Identity & Access" |

### How I Use This Information

**Before generating a hunt, I will:**

1. **Check [docs/environment.md](docs/environment.md)** for your actual tools, versions, and coverage
2. **Verify required data sources** exist (e.g., "Is SIEM available? What query language?")
3. **Confirm compatibility** (e.g., suggesting SPL queries only if you use Splunk)
4. **Note coverage gaps** (e.g., "You don't have EDR, so we can't hunt process execution patterns")
5. **Avoid suggesting hunts you can't run** (e.g., "Cloud hunting requires CloudTrail integration, which isn't documented")

**If I can't find data source information:**

- I will ask you directly: "Do you have [telemetry type]?" or "What's your query language?"
- I will reference the section in [docs/environment.md](docs/environment.md) that should contain the answer
- I will not make assumptions about your infrastructure

### Known Gaps & Blind Spots

See [environment.md "Known Gaps & Blind Spots"](docs/environment.md#known-gaps--blind-spots) for documented areas where visibility is limited. This informs hunt prioritization and helps avoid suggesting hunts for unmonitored systems.

---

## CLI Commands for AI Assistants

**Purpose:** ATHF includes optional CLI tools (`athf` command) that automate common hunt management tasks. When available, these commands are faster and more reliable than manual file operations.

### Quick Command Reference

| Command | Use When | Replaces Manual | Output Format |
|---------|----------|-----------------|---------------|
| `athf hunt new --technique T1003` | Creating new hunt | Manual file + YAML | Hunt file created |
| `athf hunt search "kerberoasting"` | Full-text search | grep across files | Text results |
| `athf hunt list --tactic credential-access` | Filter by metadata | grep + YAML parsing | Table/JSON/YAML |
| `athf hunt stats` | Calculate metrics | Manual TP/FP counting | Statistics summary |
| `athf hunt coverage` | ATT&CK gap analysis | Manual technique tracking | Coverage report |
| `athf hunt validate H-0001` | Check structure | Manual YAML check | Validation results |

### CLI Availability Check

AI assistants should verify CLI is installed before using:

```bash
athf --version
```

- **If succeeds** → Use CLI commands (faster, structured output)
- **If fails** → Use grep/manual fallback (shown in examples below)

### When to Use CLI vs Manual

**Use CLI when:**
- Creating hunts (handles ID generation, template, YAML frontmatter)
- Filtering by metadata (tactics, techniques, status, platform)
- Calculating statistics (automatic TP/FP/success rate calculation)
- Validating hunt structure (automatic checks)
- Need structured output (JSON/YAML for parsing)

**Use Manual/Grep when:**
- Reading hunt content (LOCK sections, lessons learned)
- Editing existing hunt files
- Custom filtering beyond CLI capabilities
- CLI not installed (Level 0-1 maturity)

**Full CLI documentation:** [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)

### AI-Friendly Hunt Creation (One-Liner Support)

**NEW:** `athf hunt new` now supports rich content flags for fully-populated hunt files without manual editing.

**Basic Usage:**
```bash
athf hunt new --title "Hunt Title" --technique T1003.001 --non-interactive
```

**AI-Friendly One-Liner (Full Hypothesis + ABLE Framework):**
```bash
athf hunt new \
  --title "macOS Unix Shell Abuse for Reconnaissance" \
  --technique "T1059.004" \
  --tactics "execution,defense-evasion" \
  --platforms "macos" \
  --data-sources "EDR process telemetry" \
  --hypothesis "Adversaries execute malicious commands via native macOS shells..." \
  --threat-context "macOS developer workstations are high-value targets..." \
  --actor "Generic adversary (malware droppers, supply chain attackers...)" \
  --behavior "Shell execution from unusual parents performing reconnaissance..." \
  --location "macOS endpoints (developer workstations)..." \
  --evidence "EDR process telemetry - Fields: process.name..." \
  --hunter "Your Name" \
  --non-interactive
```

**Benefits:**
✅ AI assistants can create fully-populated hunt files in one command
✅ No manual file editing required for basic hunts
✅ All LOCK template fields can be populated via CLI
✅ Backwards compatible (all flags are optional)

**Available Rich Content Flags:**
- `--hypothesis` - Full hypothesis statement
- `--threat-context` - Threat intel or context motivating the hunt
- `--actor` - Threat actor (for ABLE framework)
- `--behavior` - Behavior description (for ABLE framework)
- `--location` - Location/scope (for ABLE framework)
- `--evidence` - Evidence description (for ABLE framework)
- `--hunter` - Hunter name (default: "AI Assistant")

---

## Hunting Methodology

**Primary Framework:** [LOCK / PEAK / TaHiTI]

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

## Hunt Metadata & Machine-Readable Format

### YAML Frontmatter for AI

Starting at **Level 2 (Searchable)**, hunt files include **YAML frontmatter** - machine-readable metadata that enables AI assistants to:

- **Filter hunts programmatically** by status, tactics, techniques, platform
- **Discover related hunts** via `related_hunts` field
- **Calculate hunt metrics** (success rates, TP/FP ratios, findings counts)
- **Identify coverage gaps** (which ATT&CK techniques have we hunted?)
- **Track hunt evolution** (planning → in-progress → completed)

### How AI Should Use Hunt Metadata

**When user asks: "Find all completed hunts for credential access"**

AI should:

1. Read hunt files in `hunts/` folder
2. Parse YAML frontmatter from each file
3. Filter where:
   - `status: completed`
   - `tactics` array contains `credential-access`
4. Return matching hunt IDs and titles

**When user asks: "Have we hunted T1003 sub-techniques before?"**

AI should:

1. Parse YAML frontmatter from all hunts
2. Filter where `techniques` array matches `T1003.*` pattern
3. List matching hunts with their specific sub-techniques
4. Identify which T1003 sub-techniques have NOT been hunted

**When user asks: "Show me hunts with high false positive rates"**

AI should:

1. Parse YAML frontmatter from completed hunts
2. Calculate FP ratio: `false_positives / findings_count`
3. Sort hunts by FP ratio descending
4. Return top results with lessons learned from KEEP sections

### Metadata Schema Quick Reference

**Essential fields for AI filtering:**

```yaml
hunt_id: H-0042                    # Unique identifier
status: completed                  # planning | in-progress | completed
platform: [Windows, Linux]         # Target platforms (array)
tactics: [credential-access]       # MITRE tactics (array)
techniques: [T1003.001]            # MITRE techniques (array)
data_sources: [Splunk, EDR]        # Log platforms (array)
related_hunts: [H-0015]            # Related hunt IDs (array)
findings_count: 15                 # Total findings
true_positives: 3                  # Confirmed malicious
false_positives: 12                # Benign flagged
tags: [kerberos, credential-theft] # Freeform tags (array)
```

**Full schema documentation:** See [hunts/FORMAT_GUIDELINES.md](hunts/FORMAT_GUIDELINES.md#yaml-frontmatter-optional-at-level-0-1-recommended-at-level-2)

### AI Workflow Examples

#### Example 1: Finding Related Work

**CLI Approach (Recommended):**
```bash
athf hunt search "kerberoasting"
athf hunt list --tactic credential-access --technique T1558
```

**Manual Approach (Fallback if CLI unavailable):**
```bash
grep -r "kerberoasting" hunts/
grep "T1558" hunts/*.md
```

**AI Workflow:**
```
User: "Generate hypothesis for hunting Kerberoasting attacks"

AI Workflow:
1. Search for "Kerberoasting" using CLI or grep
2. Check `related_hunts` fields to find hunt chains
3. Read lessons learned from similar past hunts (H-0042)
4. Generate new hypothesis incorporating past findings
5. Suggest `related_hunts: [H-0042]` in new hunt metadata
```

#### Example 2: Coverage Gap Analysis

**CLI Approach (Recommended):**
```bash
athf hunt coverage
```

**Manual Approach (Fallback if CLI unavailable):**
```bash
# Parse YAML frontmatter from all hunts, count by tactic
grep -h "^tactics:" hunts/H-*.md | sort | uniq -c
```

**AI Workflow:**
```
User: "Which MITRE tactics do we need to hunt more?"

AI Workflow:
1. Get coverage data via CLI or manual YAML parsing
2. Count hunts per tactic:
   - credential-access: 8 hunts
   - persistence: 5 hunts
   - lateral-movement: 2 hunts  ← Low coverage
   - exfiltration: 1 hunt  ← Low coverage
3. Prioritize hunt suggestions for low-coverage tactics
4. Reference [docs/environment.md](docs/environment.md) to ensure we have telemetry
```

#### Example 3: Hunt Success Metrics

**CLI Approach (Recommended):**
```bash
athf hunt stats
```

**Manual Approach (Fallback if CLI unavailable):**
```bash
# Parse YAML from completed hunts, calculate TP/FP ratios
grep -A20 "^status: completed" hunts/H-*.md | grep -E "(true_positives|false_positives|findings_count)"
```

**AI Workflow:**
```
User: "What's our hunt success rate?"

AI Workflow:
1. Get statistics via CLI or manual parsing
2. Calculate metrics:
   - Total hunts: 15
   - Hunts with TPs: 8 (53% detection rate)
   - Average TP per hunt: 2.1
   - Average FP per hunt: 7.3
   - Most successful tactic: credential-access (75% TP rate)
3. Return summary with recommendations
```

#### Example 4: Platform-Specific Hunting

**CLI Approach (Recommended):**
```bash
athf hunt list --platform Linux --tactic persistence
```

**Manual Approach (Fallback if CLI unavailable):**
```bash
# Search for Linux + persistence in YAML frontmatter
grep -l "platform.*Linux" hunts/H-*.md | xargs grep -l "tactics.*persistence"
```

**AI Workflow:**
```
User: "Find all Linux persistence hunts"

AI Workflow:
1. Filter hunts via CLI or manual grep
2. Return matching hunts: H-0002, H-0018, H-0029
3. Show related techniques: T1053.003 (cron), T1543.002 (systemd)
4. Suggest coverage gaps: T1574 (hijack execution flow)
```

### Maturity-Based Metadata Usage

| Maturity Level | AI Capability | Metadata Requirements |
|----------------|---------------|----------------------|
| **Level 0-1** (Manual) | AI reads past hunts via grep | Metadata optional, focus on LOCK structure |
| **Level 2** (Searchable) | AI filters by tactics/techniques/status | YAML frontmatter recommended with core fields |
| **Level 3+** (Generative) | AI calculates metrics, identifies gaps | YAML required with findings counts populated |

### Important Notes for AI

**Backward Compatibility:**

- Hunts without YAML frontmatter are still valid
- For hunts without frontmatter, parse markdown metadata section
- Gracefully handle missing optional fields (use null/0 defaults)

**Parsing YAML:**

- YAML frontmatter starts with `---` on line 1
- YAML block ends with `---` (closing delimiter)
- Use standard YAML parsing libraries
- Handle arrays, integers, and strings correctly

**Field Conventions:**

- `tactics` uses lowercase hyphenated format: `credential-access`
- `platform` uses title case: `Windows`, `macOS`, `Linux`
- `tags` uses lowercase hyphenated format: `living-off-the-land`
- `techniques` uses standard ATT&CK IDs: `T1003.001`

**When Generating New Hunts:**

- Always include YAML frontmatter at Level 2+
- Populate `related_hunts` when building on past work
- Set `status: planning` for new hypotheses
- Leave findings fields at 0 until hunt execution

---

## Guardrails for AI Assistance

### Query Safety

- **Always include time bounds** (e.g., last 7 days, not "all time")
- **Limit result sets** (e.g., `| head 1000`, `TOP 100`)
- **Avoid expensive operations** without explicit approval (stats over 30+ days, full table scans)
- **Test on small windows first** before expanding timeframe

### Hypothesis Validation

- **Check if we've hunted this before** (grep hunts/ folder)
- **Verify data source availability** (reference [docs/environment.md](docs/environment.md))
- **Ensure hypothesis is testable** (can be validated with a query)
- **Consider false positive rate** (will this hunt generate noise?)

### Documentation

- **Use LOCK structure** for all hunt documentation
- **Capture negative results** (hunts that found nothing are still valuable)
- **Record lessons learned** (what worked, what didn't, what to try next time)
- **Link related hunts** (if this builds on past work, reference it)

### Memory and Context

- **Search before suggesting** - Check if we've hunted this TTP/behavior before
- **Reference [docs/environment.md](docs/environment.md)** - Ensure suggestions match our actual tech stack
- **Apply past lessons** - Use outcomes from similar hunts to improve new hypotheses

---

## Hypothesis Generation Workflow

**For complete workflows with examples, see [prompts/ai-workflow.md](prompts/ai-workflow.md)**

This section provides essential guidance for AI assistants generating threat hunting hypotheses. This is the most common Level 2 (Searchable) workflow.

### Essential Workflow Steps

**Core Process:**

1. **Consult Hunting Brain** - Read [knowledge/hunting-knowledge.md](knowledge/hunting-knowledge.md) Section 1 (Hypothesis Generation) and Section 5 (Pyramid of Pain)
2. **Search Memory First** - Check hunts/ for similar TTPs or past work
3. **Validate Environment** - Read [docs/environment.md](docs/environment.md) to confirm data sources exist
4. **Generate LOCK Hypothesis** - Create testable hypothesis following templates/HUNT_LOCK.md
5. **Apply Quality Criteria** - Use hunting-knowledge.md Section 1 quality checklist (Falsifiable, Scoped, Observable, Actionable, Contextual)
6. **Suggest Next Steps** - Offer to create hunt file or draft query

**Key Requirements:**

- **Focus on behaviors/TTPs (top of Pyramid of Pain)** - Never build hypothesis around hashes or IPs alone
- Match hypothesis format: "Adversaries use [behavior] to [goal] on [target]"
- Reference past hunts by ID (e.g., "Building on H-0022 lessons...")
- Specify data sources from [docs/environment.md](docs/environment.md) (e.g., "index=winlogs", "SecurityEvent table")
- Include bounded time range with justification
- Consider false positives from similar past hunts
- Apply hypothesis quality rubric from hunting-knowledge.md

**Output Must Follow:** [templates/HUNT_LOCK.md](templates/HUNT_LOCK.md) structure

**Complete workflow details, examples, and troubleshooting:** [prompts/ai-workflow.md](prompts/ai-workflow.md)

**Hunting Brain Reference:** [knowledge/hunting-knowledge.md](knowledge/hunting-knowledge.md) - Sections 1, 2, 5 are critical for hypothesis generation

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
- [Reference [docs/environment.md](docs/environment.md) "Known Gaps & Blind Spots" section]

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

**Current maturity level:** [0: Manual | 1: Documented | 2: Searchable | 3: Generative | 4: Agentic]

**Memory approach:**

- **Level 1-2:** Grep-based search across markdown files (no structured memory yet)
- **Level 3+:** [If applicable: SQLite/JSON index for faster search, agent-accessible structured memory]

**When AI needs to recall past hunts:**

- **CLI available:** Use `athf hunt search`, `athf hunt list --filter`, `athf hunt stats`
- **CLI unavailable:** Use grep/search across `hunts/` folder and [docs/environment.md](docs/environment.md)
- **Level 3+:** Query structured memory via CLI or custom scripts

**CLI benefits:** Structured output (JSON/YAML), built-in filtering, automatic YAML parsing

---

## Maintenance Notes

**Review this file when:**

- Adding new data sources (update "Data Sources" section)
- Changing AI tools (update "AI Workflow Examples")
- Reaching new maturity level (update "Memory Scaling")
- Discovering AI generates incorrect assumptions (add to "Guardrails")

**Last Updated:** [YYYY-MM-DD]
**Maintained By:** [Team/Individual]
