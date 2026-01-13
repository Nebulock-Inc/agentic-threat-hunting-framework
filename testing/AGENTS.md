# AGENTS.md - Context for AI Assistants

**Purpose:** This file provides AI assistants with context about your threat hunting repository and environment.

---

## Repository Overview

This repository contains threat hunting investigations using the LOCK pattern (Learn → Observe → Check → Keep).

**AI assistants should:**

- **Start with [athf/data/docs/getting-started.md](../athf/data/docs/getting-started.md)** - Entry point for framework adoption
- **Read [athf/data/knowledge/hunting-knowledge.md](../athf/data/knowledge/hunting-knowledge.md)** - Expert hunting frameworks and analytical methods
- **Browse past hunts** - Search hunt history before suggesting new hypotheses
- Reference lessons learned when generating queries
- Use [athf/data/docs/environment.md](../athf/data/docs/environment.md) to inform hunt planning
- **Focus on behaviors and TTPs (top of Pyramid of Pain), not indicators**

---

## 🎯 TOKEN OPTIMIZATION: Structured Output Rules

**CRITICAL**: Use structured output formats for query analysis to reduce token costs by 75%.

**Three Output Modes:**

1. **JSON Format** (Use 80% of time) - For security findings, event logs, structured data
   - Rules: JSON only, suspicion_score > 30 only, one-sentence reasons, no preambles
2. **Table Format** (Quick triage) - Columnar data for rapid scanning
3. **Narrative** (Sparingly) - Final hunt reports, deliverables, hypothesis generation

**Impact**: Verbose output ~2,000 tokens vs. Structured ~500 tokens = significant cost savings

---

## Repository Structure

```
/
├── README.md              # Framework overview
├── AGENTS.md              # 🤖 This file - AI context
├── USING_ATHF.md          # Adoption guide
├── SHOWCASE.md            # Example results
├── .athfconfig.yaml       # Workspace configuration
│
├── hunts/                 # Hunt investigations (H-XXXX.md)
│   └── README.md          # Hunt creation guide
│
├── investigations/        # Exploratory work (I-XXXX.md)
│   └── README.md          # Investigation workflow guide
│
├── queries/               # Query implementations
│   └── README.md          # Query library documentation
│
├── templates/             # Hunt templates
├── prompts/               # AI workflow templates
├── knowledge/             # Hunting expertise and frameworks
│   ├── hunting-knowledge.md      # Core hunting knowledge
│   ├── mitre-attack.md           # ATT&CK framework methodology
│   └── domains/                  # Domain-specific knowledge
│       ├── endpoint-security.md  # Process execution, LOTL, persistence
│       ├── iam-security.md       # Authentication, credential attacks
│       ├── insider-threat.md     # Data exfiltration, sabotage
│       └── cloud-security.md     # AWS/Azure/GCP threats
│
├── integrations/          # MCP servers and tool integrations
│   ├── MCP_CATALOG.md     # Available integrations
│   └── quickstart/        # Integration setup guides
│
├── docs/                  # Detailed documentation
│   ├── CLI_REFERENCE.md   # Complete CLI command reference
│   ├── environment.md     # Tech stack and data sources
│   └── getting-started.md # Adoption guide
│
├── athf/                  # CLI source code
│   ├── commands/          # Hunt/investigate management
│   ├── core/              # Parsers and validation
│   └── utils/             # Helper utilities
│
└── tests/                 # Test suite
```

---

## Hunting Knowledge Base

### athf/data/knowledge/hunting-knowledge.md

The file [athf/data/knowledge/hunting-knowledge.md](../athf/data/knowledge/hunting-knowledge.md) contains expert threat hunting knowledge that AI should apply when generating hypotheses:

**Core Sections:**
1. **Hypothesis Generation** - Pattern-based generation, quality criteria, examples
2. **Behavioral Models** - ATT&CK TTP → observable mappings, behavior-to-telemetry translation
3. **Pivot Logic** - Artifact chains, pivot playbooks, decision criteria
4. **Analytical Rigor** - Confidence scoring, evidence strength, bias checks
5. **Framework Mental Models** - Pyramid of Pain, Diamond Model, Hunt Maturity, Data Quality

**Key Principle:** All hunts must focus on **behaviors and TTPs (top half of Pyramid of Pain)**. Never build hunts solely around hashes, IPs, or domains.

**When to consult:**
- Before generating hypotheses (review Section 1 and Section 5)
- During hunt execution (review Section 3 for pivot logic)
- When analyzing findings (review Section 4 for confidence scoring)

---

## Data Sources

See [athf/data/docs/environment.md](../athf/data/docs/environment.md) for complete data source inventory including:
- SIEM/log aggregation platforms
- EDR/endpoint telemetry coverage
- Network visibility capabilities
- Cloud logging (AWS CloudTrail, Azure Activity Logs, GCP Audit Logs)
- Identity and authentication logs
- Known visibility gaps and blind spots

**AI Note:** Always verify data sources exist in [athf/data/docs/environment.md](../athf/data/docs/environment.md) before generating queries.

---

## Hunting Methodology

This repository follows the **LOCK pattern**:

1. **Learn** - Gather context (CTI, alert, anomaly, threat intel)
2. **Observe** - Form hypothesis about adversary behavior
3. **Check** - Test with bounded, safe query
4. **Keep** - Record decision and lessons learned

**AI assistants should:**
- Generate hypotheses in LOCK format (see [athf/data/templates/HUNT_LOCK.md](../athf/data/templates/HUNT_LOCK.md))
- Ensure queries are bounded by time, scope, and impact
- Document lessons learned after hunt execution
- Reference past hunts when suggesting new ones

---

## Investigation Workflow

**Purpose:** Investigations (I-XXXX) are for exploratory work, alert triage, and ad-hoc analysis that **does NOT contribute to hunt metrics**.

**Use investigations when:** Alert triage, exploring new data sources, testing queries, uncertain hypothesis, avoiding metrics pollution

**Use hunts when:** Testable hypothesis, repeatable detection logic, tracking metrics, deliverables, ATT&CK coverage

**Key Differences:**

| Aspect | Hunts (H-XXXX) | Investigations (I-XXXX) |
|--------|----------------|-------------------------|
| **Purpose** | Hypothesis-driven hunting | Exploratory analysis |
| **Metrics** | Tracked (TP/FP/costs) | **NOT tracked** |
| **Directory** | `hunts/` | `investigations/` |
| **Validation** | Strict (CI/CD enforced) | Lightweight |

**CLI Commands:**
- `athf investigate new` - Create investigation (interactive or --non-interactive)
- `athf investigate list [--type finding]` - List/filter investigations
- `athf investigate search "keyword"` - Full-text search
- `athf investigate validate I-XXXX` - Lightweight validation
- `athf investigate promote I-XXXX` - Promote to formal hunt

**Cross-Referencing:**
- Investigations → Hunts: Use `related_hunts: [H-0013]` field
- Hunts → Investigations: Use `spawned_from: I-0042` field

---

## Guardrails for AI Assistance

### Query Safety

- **Always include time bounds** (e.g., last 7 days, not "all time")
- **Limit result sets** (e.g., `| head 1000`, `TOP 100`, `LIMIT 1000`)
- **Avoid expensive operations** without explicit approval
- **Test on small windows first** before expanding timeframe

### Hypothesis Validation

- **Check if we've hunted this before** - Search past hunts by MITRE tactic or keyword
- **Verify data source availability** (reference [athf/data/docs/environment.md](../athf/data/docs/environment.md))
- **Ensure hypothesis is testable** (can be validated with a query)
- **Consider false positive rate** (will this hunt generate noise?)

### Documentation

- **Use LOCK structure** for all hunt documentation
- **Capture negative results** (hunts that found nothing are still valuable)
- **Record lessons learned** (what worked, what didn't, what to try next)
- **Link related hunts** (reference past work)

### Memory and Context

- **Search before suggesting** - Check if we've hunted this TTP/behavior before
- **Reference environment.md** - Ensure suggestions match our actual tech stack
- **Apply past lessons** - Use outcomes from similar hunts to improve new hypotheses

---

## Hypothesis Generation Workflow

**Core Process:**

1. **Consult Hunting Brain** - Read [athf/data/knowledge/hunting-knowledge.md](../athf/data/knowledge/hunting-knowledge.md) Section 1 (Hypothesis Generation) and Section 5 (Pyramid of Pain)
2. **Search Memory First** - **REQUIRED: Use `athf similar "your hypothesis keywords"` to check for duplicate hunts** (saves time, avoids redundant work)
3. **Validate Environment** - Read [athf/data/docs/environment.md](../athf/data/docs/environment.md) to confirm data sources exist
4. **Generate LOCK Hypothesis** - Create testable hypothesis following [athf/data/templates/HUNT_LOCK.md](../athf/data/templates/HUNT_LOCK.md)
5. **Apply Quality Criteria** - Use quality checklist (Falsifiable, Scoped, Observable, Actionable, Contextual)
6. **Suggest Next Steps** - Offer to create hunt file or draft query

**Key Requirements:**

- **Focus on behaviors/TTPs (top of Pyramid of Pain)** - Never build hypothesis around hashes or IPs alone
- Match hypothesis format: "Adversaries use [behavior] to [goal] on [target]"
- Reference past hunts by ID (e.g., "Building on H-0022 lessons...")
- Specify data sources from [athf/data/docs/environment.md](../athf/data/docs/environment.md)
- Include bounded time range with justification
- Consider false positives from similar past hunts
- Apply hypothesis quality rubric from hunting-knowledge.md

**Output Must Follow:** [athf/data/templates/HUNT_LOCK.md](../athf/data/templates/HUNT_LOCK.md) structure

**Complete workflow details:** [athf/data/prompts/ai-workflow.md](../athf/data/prompts/ai-workflow.md)

---

## Hunt Execution Workflow

ATHF provides the following hunt execution capabilities:

1. **Load Context** - `athf context --hunt H-XXXX --format json`
   - Loads environment.md, past hunts, domain knowledge
   - Saves ~75% token usage vs. multiple Read operations
   - Returns JSON/YAML/Markdown with structured context

2. **Find Similar Hunts** - `athf similar "hypothesis keywords"`
   - Semantic search to check for duplicate hunts
   - Finds related past work
   - Avoids redundant effort

**Recommended Workflow:**

1. Use `athf similar "hypothesis keywords"` to check for duplicate hunts
2. Use `athf context --hunt H-XXXX --format json` to load context
3. Write query with proper bounds (time limits, LIMIT clause, no SQL comments)
4. Execute query manually via your data source tool (SIEM, database client, etc.)
5. Document results in hunt file

**Benefits:**
- Context loading saves ~75% token usage
- Semantic search prevents duplicate work
- Manual execution provides full control
- Works with any data source (not limited to specific integrations)

---

## Priority TTPs

### High Priority (based on threat model)

- TA0006 - Credential Access
- TA0004 - Privilege Escalation
- TA0008 - Lateral Movement

**AI Note:** Prioritize hunt suggestions for high-priority TTPs with available telemetry.

---

## CLI Commands for AI Assistants

**Purpose:** ATHF includes CLI tools (`athf` command) that automate common hunt management tasks. When available, these commands are faster and more reliable than manual file operations.

### 🔧 SETUP: Virtual Environment Activation

**CRITICAL:** The `athf` command requires the virtual environment to be activated. Activate it once at the start of your session:

```bash
source .venv/bin/activate
```

**Verify activation:**
```bash
which athf
# Should output: /Users/sydney/work/hunt-vault/.venv/bin/athf

athf --version
# Should succeed with version number
```

**Why this matters:**
- System `athf` (if installed) may lack dependencies like `scikit-learn`
- Venv `athf` has all required dependencies (scikit-learn, anthropic, etc.)
- Activation ensures correct Python interpreter

**For AI Assistants:** Before running any `athf` commands, verify venv is activated with `which athf`. If it returns a system path, run `source .venv/bin/activate` first.

---

### ⚠️ CRITICAL: Two Mandatory Tools for AI Assistants

**These two commands are REQUIRED for all hunt workflows:**

1. **`athf similar "hypothesis keywords"`** - BEFORE creating hunt hypothesis
   - Prevents duplicate hunts
   - Finds related past work
   - Saves time and token costs
   - Example: `athf similar "password spraying"`

2. **`athf context --hunt H-XXXX`** - BEFORE executing hunt queries
   - Loads all context in one command (~5 Read operations → 1 command)
   - Saves ~75% token usage
   - Returns JSON/YAML/Markdown with environment.md + past hunts + domain knowledge
   - Example: `athf context --tactic credential-access --format json`

**Failure to use these tools will result in:**
- Duplicate hunts (wasted effort)
- Excessive token costs
- Slower hunt execution

---

### Quick Command Reference

| Command | Use When | Replaces Manual | Output Format |
|---------|----------|-----------------|---------------|
| `athf env setup` | Setup Python environment | Manual venv + pip install | Environment created |
| `athf hunt new` | Creating new hunt | Manual file + YAML | Hunt file created |
| `athf hunt search "kerberoasting"` | Full-text search | grep across files | Text results |
| `athf hunt list --tactic credential-access` | Filter by metadata | grep + YAML parsing | Table/JSON/YAML |
| `athf hunt stats` | Calculate metrics | Manual TP/FP counting | Statistics summary |
| `athf hunt coverage` | ATT&CK gap analysis | Manual technique tracking | Coverage report |
| `athf hunt validate H-0001` | Check structure | Manual YAML check | Validation results |
| `athf context --hunt H-0013` | AI context loading | ~5 Read operations | JSON/Markdown/YAML |
| `athf similar "password spraying"` | Find similar hunts | Manual hunt search | Table/JSON/YAML |
| `athf investigate new` | Create investigation | Manual file + YAML | Investigation file created |
| `athf investigate list` | List investigations | grep across files | Table/JSON/YAML |
| `athf investigate search "keyword"` | Search investigations | grep across files | Text results |
| `athf investigate validate I-0001` | Check investigation | Manual check | Validation results |
| `athf investigate promote I-0001` | Convert to hunt | Manual file creation | Hunt file created |

### CLI Availability Check

AI assistants should verify CLI is installed before using:

```bash
athf --version
```

- **If succeeds** → Use CLI commands (faster, structured output)
- **If fails** → Use grep/manual fallback

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
- CLI not installed

**Full CLI documentation:** [athf/data/docs/CLI_REFERENCE.md](../athf/data/docs/CLI_REFERENCE.md)

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
  --tactic "execution" \
  --platform "macOS" \
  --data-source "EDR process telemetry" \
  --hypothesis "Adversaries execute malicious commands via native macOS shells..." \
  --threat-context "macOS developer workstations are high-value targets..." \
  --actor "Generic adversary (malware droppers, supply chain attackers...)" \
  --behavior "Shell execution from unusual parents performing reconnaissance..." \
  --location "macOS endpoints (developer workstations)..." \
  --evidence "EDR process telemetry - Fields: process.name, parent.process.name..." \
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

### AI Context Export & Semantic Search

**Purpose:** Two commands designed specifically for AI assistants to reduce token usage and avoid duplicate hunts.

#### `athf context` - AI-Optimized Context Loading

**Why this helps AI:**
- **Reduces context-loading from ~5 tool calls to 1** - Single command replaces multiple Read operations
- **Saves ~2,000 tokens per hunt**
- **Pre-filtered, structured content** - Only relevant files included
- **Easier parsing** - JSON/YAML output formats

**Usage examples:**
```bash
# Export context for specific hunt
athf context --hunt H-0013 --format json

# Export context for all credential access hunts
athf context --tactic credential-access --format json

# Export context for macOS platform hunts
athf context --platform macos --format json

# Combine filters: persistence hunts on Linux platform
athf context --tactic persistence --platform linux --format json

# Export full repository context (use sparingly)
athf context --full --format json
```

**What's included:**
- `athf/data/docs/environment.md` - Tech stack, data sources
- Past hunts - Filtered by hunt ID, tactic, platform, or combinations
- Domain knowledge - Relevant domain files based on tactic

**When to use:**
- **Before generating hunt hypothesis** - Get environment, past hunts, domain knowledge
- **Before generating queries** - Get data sources, past query examples
- **When user asks about specific hunt** - Load hunt content + context
- **When exploring tactics** - Get all hunts for a specific tactic

#### `athf similar` - Semantic Hunt Search

**Why this helps AI:**
- **Find similar hunts even with different terminology** - Semantic search, not keyword matching
- **Avoid duplicate hunts** - Check if similar hunt already exists
- **Discover patterns** - Find related hunts across history
- **Better than grep** - Conceptual matching, not string matching

**Usage examples:**
```bash
# Find hunts similar to text query
athf similar "password spraying via RDP"

# Find hunts similar to specific hunt
athf similar --hunt H-0013

# Limit results to top 5
athf similar "kerberos" --limit 5

# Export as JSON for parsing
athf similar "credential theft" --format json

# Set minimum similarity threshold
athf similar "reconnaissance" --threshold 0.3
```

**Similarity scoring:**
- **≥0.50** = Very similar (likely duplicate or closely related)
- **0.30-0.49** = Similar (same domain or tactic)
- **0.15-0.29** = Somewhat similar (related concepts)
- **<0.15** = Low similarity (different topics)

**When to use:**
- **Before creating new hunt** - Check if similar hunt already exists
- **When user describes hunt** - Find existing hunts matching description
- **When exploring patterns** - Discover hunt clusters by topic
- **After hypothesis generation** - Verify not duplicating work

**Combined workflow (context + similar):**
```
User: "Help me hunt for Kerberoasting"
AI: 1. athf similar "kerberoasting" --format json
       → Check for similar hunts first
    2. If similar hunt exists (score > 0.3):
       - athf context --hunt H-XXXX --format json
       - Suggest continuing existing hunt
    3. If no similar hunt:
       - athf context --tactic credential-access --format json
       - Generate new hypothesis with context
       - Create new hunt
```

**Requirements:**
- `scikit-learn` must be installed for `athf similar`
- Install with: `pip install scikit-learn`

---

## Maintenance

**Review this file when:**
- Adding new data sources (update "Data Sources" section)
- Changing priority TTPs (update "Priority TTPs")
- Discovering AI generates incorrect assumptions (add to "Guardrails")
- Team practices change
- New integrations or hunt templates added (update "Repository Structure")

**Last Updated:** 2025-12-17
**Maintained By:** ATHF Framework Team
