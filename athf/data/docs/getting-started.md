# Getting Started with ATHF

This guide walks you through setting up the Agentic Threat Hunting Framework, from your first documented hunt to advanced AI-powered capabilities.

**This framework is meant to be flexible.** Adapt it to your environment, data sources, and team structure. Use what works for you, modify what doesn't, and skip what isn't relevant.

## Step 1: Choose Your Setup Path

ATHF offers two paths to get started:

### Option A: CLI-Enabled (Recommended)

Install the Python CLI for convenience commands:

```bash
# Clone and install
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
pip install -e .

# Verify installation
athf --version
```

**Benefits:** Interactive hunt creation, automated validation, built-in search and stats

### Option B: Markdown-Only

Use the framework structure without CLI tools:

```bash
# Clone only
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
```

**Benefits:** Maximum simplicity, full control, no dependencies

> **Note:** Both paths work equally well. The CLI is optional convenience - the framework structure (hunts/, LOCK pattern, AGENTS.md) is what enables AI assistance.

## Step 2: Explore the Structure

Take a few minutes to understand the repository layout:

```
agentic-threat-hunting-framework/
├── README.md              # Framework overview
├── AGENTS.md              # AI assistant context
├── config/                # Workspace configuration
│   └── .athfconfig.yaml   # Hunt prefix, SIEM/EDR settings
├── athf/                  # CLI source code (optional)
│   ├── commands/          # Hunt management commands
│   ├── core/              # Hunt parsing and validation
│   └── utils/             # Helper utilities
├── hunts/                 # Hunt hypothesis cards (H-XXXX.md)
├── queries/               # Query implementations (H-XXXX.spl/kql)
├── runs/                  # Hunt execution results (H-XXXX_YYYY-MM-DD.md)
├── templates/             # LOCK-structured hunt templates
├── knowledge/             # Threat hunting expertise
├── prompts/               # AI workflow templates
├── integrations/          # MCP server catalog and quickstart guides
├── docs/                  # Detailed documentation
└── assets/                # Images and diagrams
```

**Key files to review:**

- [templates/](../templates/) - Ready-to-use LOCK hunt templates
- [hunts/](../hunts/) - Example hunts showing the LOCK pattern
- [AGENTS.md](../../../AGENTS.md) - Template for AI context (customize later)

## Step 3: Document Your First Hunt (Level 1)

Start simple. Pick a recent hunt or create a new one and document it using the LOCK pattern.

### Create a Hunt File

**Using the CLI (Option A):**

```bash
# Interactive mode - CLI will prompt you for details
athf hunt new

# Or non-interactive with flags
athf hunt new \
  --technique T1110.001 \
  --title "SSH Brute Force Detection" \
  --platform linux \
  --tactic initial-access

# Validate the hunt structure
athf hunt validate

# View your hunt catalog
athf hunt list
```

**Manual Creation (Option B):**

1. Copy a template:

   ```bash
   cp templates/HUNT_LOCK.md hunts/H-0001.md
   ```

2. Fill out the LOCK sections:
   - **Learn:** What motivated this hunt?
   - **Observe:** What behavior are you looking for?
   - **Check:** What query did you run?
   - **Keep:** What did you find? What's next?

3. Save and commit:

   ```bash
   git add hunts/H-0001.md
   git commit -m "Add hunt H-0001: [Brief description]"
   ```

> **Tip:** The CLI (`athf hunt new`) creates the file with YAML frontmatter automatically. Manual creation gives you full control over the content.

### Example Structure

See [hunts/H-0001.md](../hunts/H-0001.md) for a complete example. Here's a simplified structure:

```markdown
# H-0001: SSH Brute Force Detection

**Learn**
Recent CTI indicates increased SSH brute force activity targeting cloud infrastructure.
Available data: Linux auth.log via Splunk (index=linux_secure)

**Observe**
Adversaries may attempt multiple SSH authentication failures from a single source IP.
Successful login after many failures is highly suspicious.

**Check**
index=linux_secure action=failure
| stats count by src_ip
| where count > 20

**Keep**
Found 3 IPs with >100 attempts.
- 203.0.113.45: 247 attempts, 0 successes
- 198.51.100.22: 189 attempts, 1 success (investigate)
- 192.0.2.15: 134 attempts, 0 successes

Next: Correlate with EDR to see if successful login led to further activity.
```

**Congratulations!** You're now at Level 1. You have persistent, searchable hunt records.

## Step 4: Add AI Context Files (Level 2)

To make your hunts AI-accessible, add context files that describe your environment and provide domain expertise.

### Customize AGENTS.md

1. Open [AGENTS.md](../../../AGENTS.md)
2. Update the following sections:
   - **Data Sources:** Replace placeholders with your actual SIEM indexes, EDR platforms, etc.
   - **Technology Stack:** List your security tools
   - **Known Visibility Gaps:** Document what you can't see

Example customization:

```markdown
## Data Sources

### SIEM / Log Aggregation
- **Platform:** Splunk Enterprise
- **Indexes:**
  - `index=winlogs` - Windows Event Logs
  - `index=linux_secure` - Linux auth.log
  - `index=edr` - CrowdStrike Falcon telemetry
- **Retention:** 90 days
- **Query Language:** SPL

### EDR / Endpoint Security
- **Platform:** CrowdStrike Falcon
- **Telemetry:** Process execution, network connections, file modifications
- **Query Access:** Splunk integration via index=edr
```

### Review hunting-knowledge.md

The repository includes [knowledge/hunting-knowledge.md](../knowledge/hunting-knowledge.md) with expert threat hunting frameworks. Review it to understand:

- How to generate quality hypotheses
- Observable-to-TTP mapping patterns
- Analytical rigor best practices

**No changes needed** - this file provides universal hunting expertise that AI assistants will apply to your environment.

### Test AI Integration

1. Open your repository in Claude Code, GitHub Copilot, or Cursor
2. Ask: "What hunts have we documented?"
3. Ask: "What data sources do we have for Windows endpoint hunting?"
4. Ask: "Generate a hypothesis for T1003.001 LSASS dumping"

If the AI can answer these questions using your repository context, you're successfully at Level 2!

**Time investment:** Approximately 1 week to customize AGENTS.md and test AI integration.

### Hunt Metadata Evolution (Level 2+)

At Level 2+, enhance your hunt files with **YAML frontmatter** - machine-readable metadata that enables AI to filter, analyze, and track hunts programmatically.

**What is YAML Frontmatter?**

YAML frontmatter is structured metadata placed at the top of hunt files, enabling:

- AI-powered filtering by status, tactics, techniques, platform
- Automated hunt success metrics calculation
- ATT&CK coverage gap analysis
- Hunt relationship tracking

**When to Adopt:**

| Maturity Level | YAML Recommendation |
|----------------|---------------------|
| Level 0-1 (Manual) | Optional - Focus on learning LOCK first |
| Level 2 (Searchable) | Recommended - Enables AI filtering |
| Level 3+ (Generative/Agentic) | Required - Automation needs structured data |

**How to Add YAML Frontmatter:**

1. Open an existing hunt file (e.g., `hunts/H-0001.md`)
2. Add YAML block at the very top:

```yaml
---
hunt_id: H-0001
title: Linux Crontab Persistence Detection
status: completed
date: 2025-11-19
hunter: Security Team
platform: [Linux]
tactics: [persistence]
techniques: [T1053.003]
data_sources: [Auditd, Syslog]
related_hunts: []
findings_count: 3
true_positives: 1
false_positives: 1
customer_deliverables: []
tags: [linux, cron, persistence]
---
```

1. Keep the existing markdown metadata section below the title for human readability

**Full documentation:** See [hunts/FORMAT_GUIDELINES.md](../hunts/FORMAT_GUIDELINES.md#yaml-frontmatter-optional-at-level-0-1-recommended-at-level-2)

**Why Both YAML and Markdown Metadata?**

- **YAML** - Enables AI filtering: "Find all completed credential-access hunts"
- **Markdown** - Provides at-a-glance context when reading hunts

**AI Benefits with YAML:**

Once you add frontmatter to your hunts, AI can:

- Filter: "Show me all Windows persistence hunts"
- Analyze: "What's our hunt success rate by tactic?"
- Discover: "Which T1003 sub-techniques have we hunted?"
- Track: "Find hunts related to H-0015"

## Step 5: Connect Tools (Level 3 - Optional)

Level 3 is about giving AI the ability to execute queries and interact with your security stack.

### Choose Your First Integration

Start with the tool you use most frequently:

- **Splunk:** [integrations/quickstart/splunk.md](../integrations/quickstart/splunk.md)
- **Other tools:** Browse [integrations/MCP_CATALOG.md](../integrations/MCP_CATALOG.md)

### Setup Process

1. **Find the MCP server** for your tool
2. **Follow the quickstart guide** for configuration
3. **Test with a simple query** (e.g., "Search for failed SSH logins in the past hour")
4. **Verify AI can execute** the query and return results

### Success Criteria

You're at Level 3 when:

- Claude can execute queries in your SIEM without copy-paste
- AI enriches findings with threat intel automatically
- Tickets are created with full context

**Time investment:** 2-4 weeks depending on tool availability and complexity.

**Detailed examples:** See [../integrations/README.md](../integrations/README.md)

## Step 6: Deploy Agents (Level 4 - Optional)

Level 4 is for teams ready to move from reactive assistance to proactive automation.

### Planning Your Agent Architecture

Before building agents, define:

1. **What should agents monitor?** (CTI feeds, internal alerts, anomaly detection)
2. **What should they generate?** (Draft hunts, enriched tickets, summary reports)
3. **Where do humans review?** (Approval gates, validation checkpoints)
4. **What are the guardrails?** (No auto-execution, human-in-the-loop, logging)

### Choose an Agent Framework

- **LangGraph** - Best for stateful, multi-step workflows
- **CrewAI** - Best for role-based agent teams
- **AutoGen** - Best for conversational patterns
- **Custom** - Build exactly what you need

### Start Small

Don't build a full agent pipeline on day one:

1. **First agent:** CTI monitor that flags new TTPs
2. **Second agent:** Hypothesis generator that creates draft hunts
3. **Third agent:** Notifier that alerts your team

**Time investment:** 1-3 months with custom development.

**Detailed examples:** See [level4-agentic-workflows.md](level4-agentic-workflows.md)

## CLI Quick Reference

If you installed the CLI (Option A), here are the most useful commands:

### Hunt Management

```bash
# Create hunts
athf hunt new                           # Interactive mode
athf hunt new --technique T1003.001 --title "LSASS Dumping"

# List and search
athf hunt list                          # All hunts
athf hunt list --status completed       # Filter by status
athf hunt list --platform windows       # Filter by platform
athf hunt search "kerberoasting"        # Full-text search

# Validation and stats
athf hunt validate                      # Validate all hunts
athf hunt validate H-0001               # Validate specific hunt
athf hunt stats                         # Show statistics
athf hunt coverage                      # MITRE ATT&CK coverage
```

### Workspace Initialization

```bash
athf init                               # Interactive setup
athf init --non-interactive             # Use defaults
```

**Full documentation:** [CLI Reference](CLI_REFERENCE.md)

## Next Steps

**At Level 1:**

- Document 5-10 hunts (use `athf hunt new` or manual markdown)
- Establish a hunt numbering convention (CLI handles this automatically)
- Train team on LOCK pattern
- Optional: Run `athf hunt validate` to ensure consistency

**At Level 2:**

- Customize AGENTS.md for your environment
- Use AI to search past hunts (or `athf hunt search` for CLI users)
- Generate hypotheses based on lessons learned
- Optional: Use `athf hunt stats` and `athf hunt coverage` to identify gaps

**At Level 3:**

- Connect your most-used tool (Splunk, CrowdStrike, etc.)
- Run a full hunt with AI executing queries (AI can use `athf hunt new` to document results)
- Measure time saved vs. manual execution

**At Level 4:**

- Deploy one monitoring agent (agents can use `athf hunt new --non-interactive` to create hunts autonomously)
- Review agent-generated drafts (use `athf hunt validate` for automated checks)
- Iterate on guardrails and approval gates

## Common Questions

**Q: Do I need to implement all levels?**
A: No. Most teams will live at Levels 1-2. Levels 3-4 are optional maturity.

**Q: How long does it take to get started?**
A: Level 1 can be operational in a day. Level 2 takes about a week. Levels 3-4 depend on your technical capability and available tools.

**Q: Can I customize the LOCK pattern?**
A: Yes! Adapt it to your methodology. The structure is a starting point, not a prescription.

**Q: What if we use a different hunting methodology (PEAK, TaHiTI)?**
A: ATHF works with any methodology. LOCK is the documentation layer, not a replacement for your existing process.

**Q: Do I need to use the CLI?**
A: No. The CLI is optional convenience tooling. You can achieve all maturity levels (1-4) using just markdown files. The framework structure (hunts/, LOCK pattern, AGENTS.md) is what enables AI assistance, not the CLI.

**Q: Can I use the CLI with my existing hunt files?**
A: Yes! The CLI commands (`athf hunt list`, `athf hunt search`, `athf hunt validate`) work with any markdown files in the hunts/ directory, whether created manually or via CLI.

## Need Help?

- Browse [docs/](.) for detailed guides
- Check [integrations/](../integrations/) for tool-specific setup
- Review [hunts/](../hunts/) for example hunts
- Open an issue on [GitHub](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues)

Happy thrunting!
