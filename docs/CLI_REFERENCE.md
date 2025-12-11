# ATHF CLI Reference

Complete reference for all `athf` command-line interface commands.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [athf init](#athf-init)
- [athf hunt new](#athf-hunt-new)
- [athf hunt list](#athf-hunt-list)
- [athf hunt validate](#athf-hunt-validate)
- [athf hunt stats](#athf-hunt-stats)
- [athf hunt search](#athf-hunt-search)
- [athf hunt coverage](#athf-hunt-coverage)
- [Configuration](#configuration)
- [Exit Codes](#exit-codes)

---

## Installation

```bash
pip install athf-framework
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
version: 0.1.0
```

### Exit Codes

- `0`: Success
- `1`: Directory already initialized (`.athfconfig.yaml` exists)

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

Display MITRE ATT&CK coverage heatmap.

### Synopsis

```bash
athf hunt coverage [OPTIONS]
```

### Description

Analyze your hunt coverage across MITRE ATT&CK tactics and techniques. Shows which areas are well-covered and which have gaps.

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tactic` | String | - | Show coverage for specific tactic only |
| `--output` | Choice | table | Output format: `table`, `json`, `yaml` |
| `--matrix` | Choice | enterprise | ATT&CK matrix: `enterprise`, `mobile`, `ics` |

### Examples

**Overall coverage**:

```bash
athf hunt coverage
```

Output:
```
MITRE ATT&CK Coverage
─────────────────────────────────────────────────────────

Reconnaissance          ▓▓░░░░░░░░  2/10 techniques (20%)
Resource Development    ░░░░░░░░░░  0/7 techniques (0%)
Initial Access          ▓▓▓░░░░░░░  3/9 techniques (33%)
Execution              ▓▓▓▓░░░░░░  4/12 techniques (33%)
Persistence            ▓▓▓▓▓▓░░░░  6/19 techniques (32%)
Privilege Escalation   ▓▓▓▓▓▓▓░░░  7/13 techniques (54%)
Defense Evasion        ▓▓▓▓▓░░░░░  5/42 techniques (12%)
Credential Access      ▓▓▓▓▓▓▓▓░░  8/15 techniques (53%)
Discovery              ▓▓▓▓░░░░░░  4/30 techniques (13%)
Lateral Movement       ▓▓▓░░░░░░░  3/9 techniques (33%)
Collection             ▓▓▓▓▓░░░░░  5/17 techniques (29%)
Command and Control    ▓▓░░░░░░░░  2/16 techniques (13%)
Exfiltration           ▓░░░░░░░░░  1/9 techniques (11%)
Impact                 ▓░░░░░░░░░  1/13 techniques (8%)

Overall: 51/221 techniques (23%)
```

**Specific tactic**:

```bash
athf hunt coverage --tactic credential-access
```

Output:
```
Credential Access Coverage (8/15 techniques - 53%)
────────────────────────────────────────────────────

✓ T1003     OS Credential Dumping (3 hunts)
  ✓ T1003.001  LSASS Memory
  ✓ T1003.002  Security Account Manager
  ✓ T1003.003  NTDS

✗ T1040     Network Sniffing (0 hunts)

✓ T1110     Brute Force (1 hunt)
  ✗ T1110.001  Password Guessing
  ✓ T1110.003  Password Spraying

✓ T1558     Steal or Forge Kerberos Tickets (2 hunts)
  ✓ T1558.003  Kerberoasting
  ✗ T1558.004  AS-REP Roasting

...
```

**JSON output**:

```bash
athf hunt coverage --output json
```

Output:
```json
{
  "overall_coverage": 0.23,
  "tactics": {
    "credential-access": {
      "total_techniques": 15,
      "covered_techniques": 8,
      "coverage_percent": 53.3,
      "techniques": {
        "T1003": {
          "name": "OS Credential Dumping",
          "covered": true,
          "hunt_count": 3,
          "subtechniques": {
            "T1003.001": {"covered": true, "hunt_count": 1},
            "T1003.002": {"covered": true, "hunt_count": 1}
          }
        }
      }
    }
  }
}
```

### Exit Codes

- `0`: Success
- `1`: No hunts found

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
version: 0.1.0
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
      - run: pip install athf-framework
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
