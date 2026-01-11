# ATHF CLI Reference

Complete reference for all `athf` command-line interface commands.

## Command Quick Reference

| Command | Category | Description |
|---------|----------|-------------|
| [`athf init`](#athf-init) | Setup | Initialize ATHF workspace directory structure |
| [`athf env setup`](#athf-env) | Environment | Setup Python virtual environment with dependencies |
| [`athf env info`](#athf-env) | Environment | Show virtual environment information |
| [`athf hunt new`](#athf-hunt-new) | Hunt Management | Create new hunt from template with auto-generated ID |
| [`athf hunt list`](#athf-hunt-list) | Hunt Management | List all hunts with optional filtering |
| [`athf hunt validate`](#athf-hunt-validate) | Hunt Management | Validate hunt file structure and metadata |
| [`athf hunt stats`](#athf-hunt-stats) | Hunt Management | Display hunt statistics and success metrics |
| [`athf hunt search`](#athf-hunt-search) | Hunt Management | Full-text search across all hunts |
| [`athf hunt coverage`](#athf-hunt-coverage) | Hunt Management | Display MITRE ATT&CK coverage heatmap |
| [`athf investigate new`](#athf-investigate-new) | Investigation Management | Create new investigation file for exploratory work |
| [`athf investigate list`](#athf-investigate-list) | Investigation Management | List all investigations with optional filtering |
| [`athf investigate search`](#athf-investigate-search) | Investigation Management | Full-text search across investigations |
| [`athf investigate validate`](#athf-investigate-validate) | Investigation Management | Validate investigation file structure |
| [`athf investigate promote`](#athf-investigate-promote) | Investigation Management | Promote investigation to formal hunt |
| [`athf context`](#athf-context) | AI Optimization | Export AI-optimized context bundle (saves ~75% tokens) |
| [`athf similar`](#athf-similar) | AI Optimization | Find similar hunts using semantic search |

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [athf init](#athf-init)
- [athf env](#athf-env)
- [athf context](#athf-context)
- [athf similar](#athf-similar)
- [athf hunt new](#athf-hunt-new)
- [athf hunt list](#athf-hunt-list)
- [athf hunt validate](#athf-hunt-validate)
- [athf hunt stats](#athf-hunt-stats)
- [athf hunt search](#athf-hunt-search)
- [athf hunt coverage](#athf-hunt-coverage)
- [athf investigate new](#athf-investigate-new)
- [athf investigate list](#athf-investigate-list)
- [athf investigate search](#athf-investigate-search)
- [athf investigate validate](#athf-investigate-validate)
- [athf investigate promote](#athf-investigate-promote)
- [Configuration](#configuration)
- [Exit Codes](#exit-codes)

---

## Installation

```bash
pip install agentic-threat-hunting-framework
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

---

## Global Options

These options work with any `athf` command:

```bash
athf --version          # Show version and exit
athf --help             # Show help message
athf <command> --help   # Show help for specific command
```

---

## athf init

Initialize ATHF directory structure in the current directory.

### Synopsis

```bash
athf init [OPTIONS]
```

### Description

Creates the standard ATHF directory structure with templates, configuration files, and documentation. This is typically the first command you run when setting up a new threat hunting workspace.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--non-interactive` | Flag | False | Skip interactive prompts and use defaults |
| `--siem` | Choice | splunk | SIEM platform: `splunk`, `sentinel`, `elastic` |
| `--edr` | Choice | crowdstrike | EDR platform: `crowdstrike`, `sentinelone`, `defender` |
| `--hunt-prefix` | String | H | Prefix for hunt IDs (e.g., H-0001) |
| `--retention-days` | Integer | 90 | Default data retention in days |

### Examples

**Interactive mode** (recommended for first-time setup):

```bash
athf init
```

You'll be prompted for:
```
SIEM platform [splunk/sentinel/elastic]: splunk
EDR platform [crowdstrike/sentinelone/defender]: crowdstrike
Hunt ID prefix [H]: HUNT
Default data retention (days) [90]: 180
```

**Non-interactive mode** (use defaults):

```bash
athf init --non-interactive
```

**Custom configuration**:

```bash
athf init \
  --siem sentinel \
  --edr defender \
  --hunt-prefix TH \
  --retention-days 180
```

### Directory Structure Created

```
.
├── .athfconfig.yaml           # Configuration file
├── AGENTS.md                  # AI assistant instructions
├── hunts/                     # Hunt documentation
├── queries/                   # Reusable query library
├── runs/                      # Hunt execution logs
└── templates/                 # Hunt templates
    └── HUNT_LOCK.md
```

### Configuration File

Creates `.athfconfig.yaml`:

```yaml
siem: splunk
edr: crowdstrike
hunt_prefix: H
retention_days: 90
initialized: 2025-12-02T14:30:00
version: 0.2.1
```

### Exit Codes

- `0`: Success
- `1`: Directory already initialized (`.athfconfig.yaml` exists)

---

## athf env

Manage Python virtual environment for ATHF development.

### Synopsis

```bash
athf env [COMMAND] [OPTIONS]
```

### Description

Provides commands for managing Python virtual environments, including setup, information display, and cleanup. Simplifies dependency management and ensures consistent development environments.

### Subcommands

| Command | Description |
|---------|-------------|
| `setup` | Setup virtual environment with dependencies |
| `info` | Show virtual environment information |
| `clean` | Remove virtual environment |
| `activate` | Show command to activate virtual environment |
| `deactivate` | Show command to deactivate virtual environment |

### athf env setup

Setup Python virtual environment with dependencies.

**Synopsis:**
```bash
athf env setup [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--python` | String | python3 | Python interpreter to use |
| `--dev` | Flag | False | Install development dependencies |
| `--clean` | Flag | False | Remove existing venv before setup |

**Examples:**

```bash
# Basic setup
athf env setup

# Setup with dev dependencies
athf env setup --dev

# Clean install
athf env setup --clean

# Use specific Python version
athf env setup --python python3.11 --dev
```

### athf env info

Show virtual environment information.

**Synopsis:**
```bash
athf env info
```

**Examples:**

```bash
athf env info
```

**Output:**
```
Virtual Environment Info:

  Location: /path/to/.venv
  Python: Python 3.11.5
  Packages: 42 installed
  athf: ✓ Installed (version 0.2.1)
  scikit-learn: ✓ Installed (required for athf similar)
```

### athf env clean

Remove virtual environment.

**Synopsis:**
```bash
athf env clean
```

**Examples:**

```bash
athf env clean
```

### athf env activate

Show command to activate virtual environment.

**Synopsis:**
```bash
athf env activate
```

**Examples:**

```bash
# Show activation command
athf env activate

# Copy and run the printed command
source .venv/bin/activate
```

**Note:** Cannot activate directly (subprocesses can't modify parent shell). Copy and run the printed command.

### athf env deactivate

Show command to deactivate virtual environment.

**Synopsis:**
```bash
athf env deactivate
```

**Examples:**

```bash
# Show deactivation command
athf env deactivate

# Copy and run the printed command
deactivate
```

### Exit Codes

- `0`: Success
- `1`: Environment operation failed

---

## athf context

Export AI-optimized context bundle to reduce token usage.

### Synopsis

```bash
athf context [OPTIONS]
```

### Description

Combines relevant files into a single structured output for AI assistants. Reduces context-loading from ~5 tool calls to 1, saving ~2,000 tokens per hunt (~75% reduction). Includes environment.md, hunts/INDEX.md, hunt files, and domain knowledge.

**Token Savings:**
- **Without context**: ~5 Read operations, ~3,000 tokens
- **With context**: 1 command, ~1,000 tokens
- **Savings**: ~2,000 tokens per hunt (~$0.03 per hunt)

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--hunt` | String | - | Hunt ID to export context for (e.g., H-0013) |
| `--tactic` | String | - | MITRE tactic to filter hunts (e.g., credential-access) |
| `--platform` | String | - | Platform to filter hunts (e.g., macos, windows, linux) |
| `--full` | Flag | False | Export full repository context (use sparingly) |
| `--format` | Choice | json | Output format: `json`, `markdown`, `yaml` |
| `--output` | Path | - | Output file path (default: stdout) |

**Note:** Must specify exactly one of: `--hunt`, `--tactic`, `--platform`, or `--full`.

### Examples

**Export context for specific hunt:**

```bash
athf context --hunt H-0013 --format json
```

**Export context for all credential access hunts:**

```bash
athf context --tactic credential-access --format json
```

**Export context for macOS platform hunts:**

```bash
athf context --platform macos --format json
```

**Export as markdown:**

```bash
athf context --hunt H-0013 --format markdown
```

**Save to file:**

```bash
athf context --hunt H-0013 --format json --output context.json
```

**Export full repository context** (large output):

```bash
athf context --full --format json
```

### Output Structure (JSON)

```json
{
  "metadata": {
    "generated_by": "athf context",
    "filters": {
      "hunt": "H-0013",
      "tactic": null,
      "platform": null,
      "full": false
    }
  },
  "environment": "# Tech stack, data sources...",
  "hunt_index": "# Hunt metadata index...",
  "hunts": [
    {
      "hunt_id": "H-0013",
      "content": "---\nhunt_id: H-0013\ntitle: ..."
    }
  ],
  "domain_knowledge": [
    {
      "file": "knowledge/hunting-knowledge.md",
      "content": "# Hunting knowledge..."
    }
  ]
}
```

### Use Cases

- **AI assistants**: Reduce context-loading from ~5 tool calls to 1
- **Token optimization**: Pre-filtered, structured content only
- **Hunt planning**: Get all relevant context in one shot
- **Query generation**: Include past hunt lessons and data sources

### Exit Codes

- `0`: Success
- `1`: Invalid filter options or missing files

---

## athf similar

Find hunts similar to a query or hunt ID using semantic search.

### Synopsis

```bash
athf similar [QUERY] [OPTIONS]
athf similar --hunt HUNT_ID [OPTIONS]
```

### Description

Uses semantic similarity (TF-IDF) to find related hunts even when terminology differs. Better than keyword search for discovering patterns and avoiding duplicate hunts. Requires `scikit-learn` to be installed.

**Why This Helps:**
- Semantic search (not just keyword matching)
- Find related hunts with different terminology
- Discover patterns across hunt history
- Identify similar hunts to avoid duplication

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `QUERY` | String (optional) | Search query text |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--hunt` | String | - | Hunt ID to find similar hunts for (e.g., H-0013) |
| `--limit` | Integer | 10 | Maximum number of results |
| `--format` | Choice | table | Output format: `table`, `json`, `yaml` |
| `--threshold` | Float | 0.1 | Minimum similarity score (0-1) |

**Note:** Must provide either `QUERY` or `--hunt` option.

### Examples

**Find hunts similar to text query:**

```bash
athf similar "password spraying via RDP"
```

**Find hunts similar to specific hunt:**

```bash
athf similar --hunt H-0013
```

**Limit results to top 5:**

```bash
athf similar "kerberos" --limit 5
```

**Export as JSON:**

```bash
athf similar "credential theft" --format json
```

**Set minimum similarity threshold:**

```bash
athf similar "reconnaissance" --threshold 0.3
```

### Output (Table Format)

```
Similar to: password spraying

Found 3 similar hunts

Score  Hunt ID    Title                Status       Tactics
─────────────────────────────────────────────────────────────
0.421  H-0014     Password Spraying    📋 planning  credential-access
0.318  H-0008     Brute Force Login    ✅ completed credential-access
0.251  H-0022     Account Takeover     🔄 in-progress initial-access

Similarity Score Legend:
  ≥0.50 = Very similar  |  0.30-0.49 = Similar  |  0.15-0.29 = Somewhat similar
```

### Output (JSON Format)

```json
[
  {
    "hunt_id": "H-0014",
    "similarity_score": 0.421,
    "title": "Password Spraying Detection",
    "status": "planning",
    "tactics": ["credential-access"],
    "techniques": ["T1110.003"],
    "platform": ["windows"]
  }
]
```

### Similarity Score Interpretation

| Score Range | Meaning | Recommendation |
|-------------|---------|----------------|
| ≥0.50 | Very similar | Likely duplicate or closely related |
| 0.30-0.49 | Similar | Same domain or tactic |
| 0.15-0.29 | Somewhat similar | Related concepts |
| <0.15 | Low similarity | Different topics |

### Installation

Requires `scikit-learn`:

```bash
pip install "agentic-threat-hunting-framework[similarity]"
```

Or install scikit-learn separately:

```bash
pip install scikit-learn
```

### Exit Codes

- `0`: Success
- `1`: Missing query/hunt option, scikit-learn not installed, or hunt not found

---

## athf hunt new

Create a new hunt from template with auto-generated ID.

### Synopsis

```bash
athf hunt new [OPTIONS]
```

### Description

Creates a new hunt file with proper YAML frontmatter and LOCK structure. Automatically assigns the next available hunt ID and generates a complete template.

### Options

**Basic Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--non-interactive` | Flag | False | Skip interactive prompts |
| `--technique` | String | Required* | MITRE ATT&CK technique (e.g., T1003.001) |
| `--title` | String | Required* | Hunt title |
| `--tactics` | String | - | Comma-separated tactics (e.g., credential-access,defense-evasion) |
| `--platforms` | String | - | Comma-separated platforms (e.g., windows,linux,macos) |
| `--data-sources` | String | - | Comma-separated data sources |
| `--hunter` | String | AI Assistant | Your name or handle |
| `--severity` | Choice | medium | Severity: `low`, `medium`, `high`, `critical` |

**Rich Content Options (for AI assistants & automation):**

| Option | Type | Description |
|--------|------|-------------|
| `--hypothesis` | String | Full hypothesis statement |
| `--threat-context` | String | Threat intel or context motivating the hunt |
| `--actor` | String | Threat actor description (for ABLE framework) |
| `--behavior` | String | Behavior description (for ABLE framework) |
| `--location` | String | Location/scope description (for ABLE framework) |
| `--evidence` | String | Evidence description (for ABLE framework) |

\* Required in non-interactive mode

### Examples

**Interactive mode** (recommended):

```bash
athf hunt new
```

Prompts:
```
MITRE ATT&CK Technique (e.g., T1003.001): T1558.003
Hunt Title: Kerberoasting Detection via Unusual TGS Requests
Primary Tactic [credential-access]: credential-access
Target Platforms (comma-separated) [windows]: windows
Data Sources (comma-separated) [windows-event-logs]: windows-event-logs,edr-telemetry
Your Name [Your Name]: Jane Doe
Severity [medium]: high
```

**Non-interactive mode**:

```bash
athf hunt new \
  --technique T1558.003 \
  --title "Kerberoasting Detection" \
  --tactics credential-access \
  --platforms windows \
  --data-sources "windows-event-logs,edr-telemetry" \
  --hunter "Jane Doe" \
  --severity high \
  --non-interactive
```

**Minimal example** (non-interactive):

```bash
athf hunt new \
  --technique T1003.001 \
  --title "LSASS Memory Dumping" \
  --non-interactive
```

**AI-friendly one-liner with rich content** (full hypothesis + ABLE framework):

```bash
athf hunt new \
  --title "macOS Unix Shell Abuse for Reconnaissance" \
  --technique "T1059.004" \
  --tactics "execution,defense-evasion" \
  --platforms "macos" \
  --data-sources "EDR process telemetry" \
  --hypothesis "Adversaries execute malicious commands via native macOS shells to perform reconnaissance and staging activities" \
  --threat-context "macOS developer workstations are high-value targets for supply chain attacks and credential theft" \
  --actor "Generic adversary (malware droppers, supply chain attackers, insider threats)" \
  --behavior "Shell execution from unusual parents performing reconnaissance or accessing sensitive files" \
  --location "macOS endpoints (developer workstations, CI/CD infrastructure)" \
  --evidence "EDR process telemetry - Fields: process.name, process.parent.name, process.command_line" \
  --hunter "Your Name" \
  --non-interactive
```

**Benefits of rich content flags:**
- ✅ AI assistants can create fully-populated hunt files in one command
- ✅ No manual file editing required for basic hunts
- ✅ All LOCK template fields can be populated via CLI
- ✅ Backwards compatible (all new flags are optional)

### Output

```
✓ Created new hunt: H-0023
  File: /path/to/hunts/H-0023.md
  Title: Kerberoasting Detection
  Technique: T1558.003

Next steps:
  1. Edit hunts/H-0023.md
  2. Fill in the LOCK sections
  3. Execute your hunt
  4. Document findings
```

### Generated File Structure

```yaml
---
hunt_id: H-0023
title: "Kerberoasting Detection"
status: in-progress
date: 2025-12-02
updated: 2025-12-02
hunter: "Jane Doe"
techniques:
  - T1558.003
tactics:
  - credential-access
platforms:
  - windows
data_sources:
  - windows-event-logs
  - edr-telemetry
severity: high
tags: []
true_positives: 0
false_positives: 0
---

## LEARN
...
```

### Exit Codes

- `0`: Success
- `1`: Missing required options (non-interactive mode)
- `2`: Invalid technique format

---

## athf hunt list

List all hunts with optional filtering.

### Synopsis

```bash
athf hunt list [OPTIONS]
```

### Description

Display all hunts in a formatted table. Supports filtering by status, tactic, technique, and platform. Output formats include table (default), JSON, and YAML.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--status` | Choice | - | Filter by status: `in-progress`, `completed`, `paused`, `archived` |
| `--tactic` | String | - | Filter by MITRE ATT&CK tactic |
| `--technique` | String | - | Filter by technique (e.g., T1003.001) |
| `--platform` | String | - | Filter by platform |
| `--output` | Choice | table | Output format: `table`, `json`, `yaml` |

### Examples

**List all hunts**:

```bash
athf hunt list
```

Output:
```
Hunt ID  Title                          Status      Technique   Findings
─────────────────────────────────────────────────────────────────────────
H-0001   macOS Information Stealer      completed   T1005       1 (1 TP)
H-0002   Kerberoasting Detection        in-progress T1558.003   -
H-0015   LSASS Memory Access            completed   T1003.001   3 (2 TP)
H-0023   Cloud Persistence via Lambda   paused      T1098       -
```

**Filter by status**:

```bash
athf hunt list --status completed
```

**Filter by tactic**:

```bash
athf hunt list --tactic credential-access
```

**Filter by technique**:

```bash
athf hunt list --technique T1003.001
```

**Multiple filters**:

```bash
athf hunt list --status completed --platform windows
```

**JSON output** (for scripts/automation):

```bash
athf hunt list --output json
```

Output:
```json
[
  {
    "hunt_id": "H-0001",
    "title": "macOS Information Stealer Detection",
    "status": "completed",
    "techniques": ["T1005"],
    "tactics": ["collection"],
    "platforms": ["macos"],
    "true_positives": 1,
    "false_positives": 0
  }
]
```

**YAML output**:

```bash
athf hunt list --output yaml
```

### Exit Codes

- `0`: Success
- `1`: No hunts directory found (run `athf init` first)

---

## athf hunt validate

Validate hunt file structure and metadata.

### Synopsis

```bash
athf hunt validate [HUNT_ID]
```

### Description

Validates hunt files against the ATHF format specification. Checks YAML frontmatter, required fields, LOCK sections, and ATT&CK technique format.

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `HUNT_ID` | String (optional) | Specific hunt to validate (e.g., H-0001). If omitted, validates all hunts. |

### Examples

**Validate specific hunt**:

```bash
athf hunt validate H-0001
```

Output (success):
```
✓ Hunt H-0001 is valid
  - YAML frontmatter: OK
  - Required fields: OK
  - ATT&CK technique: OK
  - LOCK sections: OK
```

Output (errors):
```
✗ Hunt H-0023 has validation errors:
  - Missing required field: hunter
  - Invalid technique format: T1003 (expected: T1003.001)
  - Missing LOCK section: CHECK
```

**Validate all hunts**:

```bash
athf hunt validate
```

Output:
```
Validating 4 hunts...

✓ H-0001: Valid
✗ H-0002: 1 error
  - Missing required field: hunter
✓ H-0015: Valid
✓ H-0023: Valid

Summary: 3 valid, 1 invalid
```

### Validation Rules

**Required frontmatter fields**:
- `hunt_id`
- `title`
- `status`
- `date`
- `hunter`
- `techniques`

**ATT&CK technique format**:
- Pattern: `T1234.001` (technique + subtechnique)
- Must start with `T`
- Must be in techniques list

**LOCK sections**:
- All four sections must be present: LEARN, OBSERVE, CHECK, KEEP
- Sections must be Markdown H2 headers: `## LEARN`

**Status values**:
- Must be one of: `in-progress`, `completed`, `paused`, `archived`

### Exit Codes

- `0`: All hunts valid
- `1`: Validation errors found

---

## athf hunt stats

Display hunt statistics and success metrics.

### Synopsis

```bash
athf hunt stats [OPTIONS]
```

### Description

Calculate and display statistics about your hunts, including success rates, true positive/false positive ratios, and hunt velocity.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--period` | Choice | all | Time period: `all`, `30d`, `90d`, `1y` |
| `--output` | Choice | table | Output format: `table`, `json`, `yaml` |

### Examples

**Overall statistics**:

```bash
athf hunt stats
```

Output:
```
Hunt Statistics
───────────────────────────────────────
Total Hunts:              23
Completed:                15 (65%)
In Progress:              5 (22%)
Paused:                   2 (9%)
Archived:                 1 (4%)

Success Metrics
───────────────────────────────────────
Hunts with Findings:      12 (80% of completed)
True Positives:           18
False Positives:          7
TP/FP Ratio:              2.6:1

Average per Hunt
───────────────────────────────────────
True Positives:           1.2
False Positives:          0.5
Time to Complete:         4.2 days

Coverage
───────────────────────────────────────
Unique Techniques:        15
Unique Tactics:           8
Platforms Covered:        4 (Windows, Linux, macOS, AWS)
```

**Last 30 days**:

```bash
athf hunt stats --period 30d
```

**JSON output**:

```bash
athf hunt stats --output json
```

Output:
```json
{
  "total_hunts": 23,
  "completed": 15,
  "in_progress": 5,
  "success_rate": 0.80,
  "true_positives": 18,
  "false_positives": 7,
  "tp_fp_ratio": 2.6,
  "unique_techniques": 15,
  "unique_tactics": 8
}
```

### Exit Codes

- `0`: Success
- `1`: No hunts found

---

## athf hunt search

Full-text search across all hunts.

### Synopsis

```bash
athf hunt search QUERY [OPTIONS]
```

### Description

Search hunt content (including frontmatter, LOCK sections, queries, and findings) for a specific term or phrase.

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `QUERY` | String | Search query (supports regex) |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--case-sensitive` | Flag | False | Enable case-sensitive search |
| `--regex` | Flag | False | Treat query as regex pattern |
| `--output` | Choice | table | Output format: `table`, `json`, `yaml` |

### Examples

**Simple search**:

```bash
athf hunt search kerberoasting
```

Output:
```
Found 3 matches:

H-0002: Kerberoasting Detection via Unusual TGS Requests
  Match in LEARN section:
    "...technique to detect kerberoasting attacks by identifying unusual..."

H-0008: Service Account Reconnaissance
  Match in OBSERVE section:
    "...similar patterns to kerberoasting but focuses on enumeration..."

H-0012: Golden Ticket Detection
  Match in title:
    "Kerberoasting and Golden Ticket Detection"
```

**Search for technique ID**:

```bash
athf hunt search "T1003.001"
```

**Regex search**:

```bash
athf hunt search "lsass|mimikatz|procdump" --regex
```

**Case-sensitive search**:

```bash
athf hunt search "LSASS" --case-sensitive
```

**JSON output**:

```bash
athf hunt search kerberoasting --output json
```

Output:
```json
[
  {
    "hunt_id": "H-0002",
    "title": "Kerberoasting Detection",
    "matches": [
      {
        "section": "LEARN",
        "line": 15,
        "context": "...technique to detect kerberoasting attacks..."
      }
    ]
  }
]
```

### Exit Codes

- `0`: Matches found
- `1`: No matches found

---

## athf hunt coverage

Show MITRE ATT&CK technique coverage across hunts with visual progress bars.

### Synopsis

```bash
athf hunt coverage [OPTIONS]
```

### Description

Displays a comprehensive visual coverage heatmap of all 14 MITRE ATT&CK tactics, showing which techniques you've hunted and which represent blind spots. Uses progress bars to visualize coverage percentage per tactic.

**Features:**
- Visual progress bars for all 14 ATT&CK tactics
- Coverage percentages (X/Y techniques covered)
- Overall coverage statistic across the entire matrix
- Detailed view showing technique-to-hunt mapping

**Use Cases:**
- Identify blind spots in your hunting program
- Prioritize future hunt topics
- Demonstrate coverage to stakeholders
- Align hunting with threat intelligence priorities
- Balance hunt portfolio across tactics

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--detailed` | Flag | False | Show detailed technique coverage with hunt references |

### Examples

**Show coverage heatmap:**

```bash
athf hunt coverage
```

**Output:**
```
MITRE ATT&CK Coverage
──────────────────────────────────────────────────────────────────────

Reconnaissance            ░░░░░░░░░░░░░░░░░░░░  0/10 techniques (0%)
Resource Development      ░░░░░░░░░░░░░░░░░░░░  0/7 techniques (0%)
Initial Access            ░░░░░░░░░░░░░░░░░░░░  0/9 techniques (0%)
Execution                 ░░░░░░░░░░░░░░░░░░░░  0/12 techniques (0%)
Persistence               ███████░░░░░░░░░░░░░  7/19 techniques (37%)
Privilege Escalation      ████░░░░░░░░░░░░░░░░  3/13 techniques (23%)
Defense Evasion           ░░░░░░░░░░░░░░░░░░░░  0/42 techniques (0%)
Credential Access         ░░░░░░░░░░░░░░░░░░░░  0/15 techniques (0%)
Discovery                 ░░░░░░░░░░░░░░░░░░░░  0/30 techniques (0%)
Lateral Movement          ░░░░░░░░░░░░░░░░░░░░  0/9 techniques (0%)
Collection                ███░░░░░░░░░░░░░░░░░  3/17 techniques (18%)
Command and Control       ░░░░░░░░░░░░░░░░░░░░  0/16 techniques (0%)
Exfiltration              ░░░░░░░░░░░░░░░░░░░░  0/9 techniques (0%)
Impact                    ░░░░░░░░░░░░░░░░░░░░  0/13 techniques (0%)

Overall: 10/221 techniques (5%)
```

**Show detailed technique breakdown:**

```bash
athf hunt coverage --detailed
```

**Detailed Output:**
```
🔍 Detailed Technique Coverage

Persistence (2 hunts, 7 unique techniques)
  • T1027 - H-0002
  • T1053.003 - H-0002
  • T1059.004 - H-0002
  • T1071.001 - H-0002
  • T1078.004 - H-0003
  • T1098 - H-0003
  • T1546.004 - H-0003

Collection (1 hunts, 3 unique techniques)
  • T1005 - H-0001
  • T1059.002 - H-0001
  • T1555.003 - H-0001
```

### Progress Bar Legend

- `█` = Covered technique
- `░` = Uncovered technique (blind spot)

### Exit Codes

- `0`: Success
- `1`: No hunts found

---

## athf investigate new

Create a new investigation file for exploratory work and ad-hoc analysis.

### Synopsis

```bash
athf investigate new [OPTIONS]
```

### Description

Creates investigation files for work that should NOT be tracked in hunt metrics. Investigations are perfect for alert triage, data source baselining, query sandboxing, and exploratory analysis. Investigations use a flexible LOCK structure and can be promoted to formal hunts if they prove valuable.

**When to use investigations:**
- Alert triage and finding investigation
- Baseline new data sources
- Explore query logic before formal hunt
- Ad-hoc analysis without metrics pollution
- Sandbox work for uncertain hypotheses

**Key differences from hunts:**
- NOT tracked in metrics (no TP/FP counts)
- Flexible LOCK structure (sections optional)
- Lightweight validation
- Can be promoted to formal hunts

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--title` | String | Required* | Investigation title |
| `--type` | Choice | exploratory | Type: `finding`, `baseline`, `exploratory`, `other` |
| `--tags` | String | - | Comma-separated tags (e.g., alert-triage,powershell) |
| `--data-source` | String | - | Data sources (can specify multiple with multiple flags) |
| `--related-hunt` | String | - | Related hunt IDs (can specify multiple with multiple flags) |
| `--investigator` | String | ATHF | Investigator name |
| `--non-interactive` | Flag | False | Skip interactive prompts |

\* Required in non-interactive mode

### Examples

**Interactive mode** (recommended):

```bash
athf investigate new
```

**Non-interactive with all options:**

```bash
athf investigate new \
  --title "Alert Triage - PowerShell Execution" \
  --type finding \
  --tags alert-triage,powershell,customer-x \
  --data-source "EDR Telemetry" \
  --data-source "ClickHouse" \
  --related-hunt H-0013 \
  --investigator "Jane Doe" \
  --non-interactive
```

**Create baseline investigation:**

```bash
athf investigate new \
  --title "Baseline AWS CloudTrail Events" \
  --type baseline \
  --tags baseline,cloudtrail,aws \
  --data-source "CloudTrail" \
  --non-interactive
```

**Create exploratory investigation:**

```bash
athf investigate new \
  --title "Credential Access Pattern Exploration" \
  --type exploratory \
  --tags sandbox,credential-access \
  --non-interactive
```

### Output

```
🔍 Creating new investigation

Investigation ID: I-0001

✅ Created I-0001: Alert Triage - PowerShell Execution

Next steps:
  1. Edit investigations/I-0001.md to document your investigation
  2. Use LOCK pattern sections (optional/flexible)
  3. View all investigations: athf investigate list
  4. Promote to hunt if valuable: athf investigate promote I-0001
```

### Generated File Structure

```yaml
---
investigation_id: I-0001
title: "Alert Triage - PowerShell Execution"
date: 2025-12-17
investigator: "Jane Doe"
type: finding
related_hunts:
  - H-0013
data_sources:
  - EDR Telemetry
  - ClickHouse
tags:
  - alert-triage
  - powershell
  - customer-x
---

# I-0001: Alert Triage - PowerShell Execution

...LOCK sections (optional)...
```

### Exit Codes

- `0`: Success
- `1`: Missing required options (non-interactive mode)

---

## athf investigate list

List all investigations with optional filtering.

### Synopsis

```bash
athf investigate list [OPTIONS]
```

### Description

Display all investigations in a formatted table. Supports filtering by type, tags, and multiple output formats.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--type` | Choice | - | Filter by type: `finding`, `baseline`, `exploratory`, `other` |
| `--tags` | String | - | Filter by tags (comma-separated) |
| `--output` | Choice | table | Output format: `table`, `json`, `yaml` |

### Examples

**List all investigations:**

```bash
athf investigate list
```

Output:
```
                    Investigations
╭──────┬─────────────────┬─────────────┬──────────────┬────────────╮
│ ID   │ Title           │ Type        │ Tags         │ Date       │
├──────┼─────────────────┼─────────────┼──────────────┼────────────┤
│ I-01 │ Alert Triage    │ finding     │ alert-triage │ 2025-12-17 │
│ I-02 │ CloudTrail      │ baseline    │ baseline,aws │ 2025-12-17 │
│      │ Baseline        │             │              │            │
│ I-03 │ Credential      │ exploratory │ sandbox      │ 2025-12-17 │
│      │ Patterns        │             │              │            │
╰──────┴─────────────────┴─────────────┴──────────────┴────────────╯

Total: 3 investigations
```

**Filter by type:**

```bash
athf investigate list --type finding
```

**Filter by tags:**

```bash
athf investigate list --tags alert-triage
```

**JSON output:**

```bash
athf investigate list --output json
```

Output:
```json
[
  {
    "file_path": "investigations/I-0001.md",
    "investigation_id": "I-0001",
    "frontmatter": {
      "investigation_id": "I-0001",
      "title": "Alert Triage - PowerShell Execution",
      "date": "2025-12-17",
      "type": "finding",
      "tags": ["alert-triage", "powershell"]
    }
  }
]
```

### Exit Codes

- `0`: Success
- `1`: No investigations directory found

---

## athf investigate search

Full-text search across all investigation files.

### Synopsis

```bash
athf investigate search QUERY
```

### Description

Performs full-text search across all investigation files, including frontmatter, LOCK sections, and findings.

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `QUERY` | String | Search query (case-insensitive) |

### Examples

**Search for PowerShell:**

```bash
athf investigate search "PowerShell"
```

Output:
```
Found 2 investigation(s) matching "PowerShell":

I-0001: Alert Triage - PowerShell Execution
  investigations/I-0001.md

I-0005: Process Execution Baseline
  investigations/I-0005.md
```

**Search for customer-specific findings:**

```bash
athf investigate search "customer-x"
```

**Search for baseline work:**

```bash
athf investigate search "baseline CloudTrail"
```

### Exit Codes

- `0`: Matches found
- `1`: No matches found

---

## athf investigate validate

Validate investigation file structure.

### Synopsis

```bash
athf investigate validate INVESTIGATION_ID
```

### Description

Validates investigation files against the ATHF format specification. Uses lightweight validation checking only minimal required fields. Does NOT validate LOCK sections (which are optional/flexible for investigations) or findings counts.

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `INVESTIGATION_ID` | String | Investigation to validate (e.g., I-0001) |

### Examples

**Validate specific investigation:**

```bash
athf investigate validate I-0001
```

Output (success):
```
✅ I-0001 is valid
```

Output (errors):
```
❌ I-0001 has validation errors:
  • Missing required frontmatter field: title
  • Invalid investigation_id format: I-001 (expected format: I-0001)
```

### Validation Rules

**Required frontmatter fields** (minimal):
- `investigation_id`
- `title`
- `date`

**Investigation ID format:**
- Pattern: `I-0001` (I- prefix + 4 digits)
- Must match filename

**Type values** (if present):
- Must be one of: `finding`, `baseline`, `exploratory`, `other`

**Note:** Unlike hunt validation, investigation validation is lightweight and does NOT check:
- LOCK section structure (sections are optional/flexible)
- Findings counts (investigations not tracked in metrics)
- Tactics/techniques (optional metadata)

### Exit Codes

- `0`: Investigation valid
- `1`: Validation errors found

---

## athf investigate promote

Promote investigation to formal hunt with hunt-required metadata.

### Synopsis

```bash
athf investigate promote INVESTIGATION_ID [OPTIONS]
```

### Description

Converts an investigation to a formal hunt, adding hunt-required metadata (tactics, techniques, platform) and enabling metrics tracking. The investigation file remains in the investigations directory, and both files cross-reference each other.

**What promotion does:**
1. Creates new hunt file (H-XXXX.md) in hunts/ directory
2. Copies investigation content to hunt file
3. Adds required hunt metadata (tactics, techniques, platform)
4. Adds hunt tracking fields (findings_count, true_positives, false_positives)
5. Creates bidirectional references:
   - Hunt includes `spawned_from: I-XXXX`
   - Investigation updated with promotion note

### Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `INVESTIGATION_ID` | String | Investigation to promote (e.g., I-0001) |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--technique` | String | Required* | MITRE ATT&CK technique (e.g., T1003.001) |
| `--tactic` | String | - | MITRE tactics (can specify multiple with multiple flags) |
| `--platform` | String | - | Target platforms (can specify multiple with multiple flags) |
| `--status` | Choice | in-progress | Hunt status: `planning`, `in-progress`, `completed`, `archived` |
| `--non-interactive` | Flag | False | Skip interactive prompts |

\* Required in non-interactive mode

### Examples

**Interactive promotion** (prompts for details):

```bash
athf investigate promote I-0042
```

**Non-interactive with all options:**

```bash
athf investigate promote I-0042 \
  --technique T1059.001 \
  --tactic execution \
  --tactic defense-evasion \
  --platform Windows \
  --status in-progress \
  --non-interactive
```

### Output

```
🔄 Promoting investigation to hunt

Investigation: I-0042 - PowerShell Execution Analysis

Hunt ID: H-0023

✅ Promoted I-0042 to H-0023
Updated investigations/I-0042.md with promotion note

Next steps:
  1. Edit hunts/H-0023.md to refine hunt hypothesis
  2. Add MITRE ATT&CK coverage if needed
  3. Validate hunt: athf hunt validate H-0023
  4. View hunt: athf hunt list --status in-progress
```

### After Promotion

- **Hunt file created:** hunts/H-0023.md (tracked in metrics)
- **Investigation updated:** investigations/I-0042.md (promotion note added)
- **Investigation remains:** Still NOT tracked in metrics
- **Cross-references:** Both files link to each other

### Exit Codes

- `0`: Success
- `1`: Investigation not found or parsing error
- `2`: Missing required options (non-interactive mode)

---

## Configuration

ATHF uses `.athfconfig.yaml` for configuration:

```yaml
# SIEM platform
siem: splunk  # Options: splunk, sentinel, elastic

# EDR platform
edr: crowdstrike  # Options: crowdstrike, sentinelone, defender

# Hunt ID prefix
hunt_prefix: H  # Generates: H-0001, H-0002, etc.

# Default data retention
retention_days: 90

# Metadata (auto-generated)
initialized: 2025-12-02T14:30:00
version: 0.2.1
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ATHF_CONFIG` | Path to config file | `.athfconfig.yaml` |
| `ATHF_HUNTS_DIR` | Path to hunts directory | `./hunts` |
| `ATHF_TEMPLATE_DIR` | Path to templates | `./templates` |

Example:

```bash
export ATHF_HUNTS_DIR="/opt/threat-hunting/hunts"
athf hunt list
```

---

## Exit Codes

All `athf` commands use standard exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error (file not found, validation failed, etc.) |
| `2` | Invalid arguments or options |
| `130` | Interrupted by user (Ctrl+C) |

Use in scripts:

```bash
if athf hunt validate H-0001; then
    echo "Hunt is valid"
else
    echo "Hunt has errors"
    exit 1
fi
```

---

## Tips and Tricks

### Use with Grep and Awk

```bash
# List only completed hunts
athf hunt list --output json | jq '.[] | select(.status=="completed")'

# Count hunts by tactic
athf hunt list --output json | jq -r '.[].tactics[]' | sort | uniq -c

# Find high-severity hunts
athf hunt list --output json | jq '.[] | select(.severity=="high")'
```

### Automation with Shell Scripts

```bash
#!/bin/bash
# Create weekly hunt report

WEEK=$(date +%Y-W%V)
REPORT="reports/hunt-report-$WEEK.md"

echo "# Weekly Hunt Report - $WEEK" > "$REPORT"
echo "" >> "$REPORT"

echo "## Statistics" >> "$REPORT"
athf hunt stats --period 7d >> "$REPORT"

echo "" >> "$REPORT"
echo "## Completed Hunts" >> "$REPORT"
athf hunt list --status completed --output json | \
  jq -r '.[] | "- \(.hunt_id): \(.title)"' >> "$REPORT"

echo "Report generated: $REPORT"
```

### CI/CD Integration

```yaml
# .github/workflows/validate-hunts.yml
name: Validate Hunts

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install agentic-threat-hunting-framework
      - run: athf hunt validate
```

### Batch Operations

```bash
# Create multiple hunts from a list
cat techniques.txt | while read tech title; do
  athf hunt new \
    --technique "$tech" \
    --title "$title" \
    --non-interactive
done

# Validate all hunts and save results
for hunt in hunts/H-*.md; do
  hunt_id=$(basename "$hunt" .md)
  athf hunt validate "$hunt_id" 2>&1 | tee "validation-$hunt_id.log"
done
```

---

## See Also

- [Getting Started Guide](getting-started.md)
- [Installation Guide](INSTALL.md)
- [Hunt Format Guidelines](../hunts/FORMAT_GUIDELINES.md)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)

---

## Need Help?

- **CLI help**: `athf --help` or `athf <command> --help`
- **GitHub Issues**: [Report bugs or request features](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)
- **Documentation**: [docs/getting-started.md](getting-started.md)
