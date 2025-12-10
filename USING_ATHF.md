# Using ATHF in Your Organization

ATHF is a **framework for building agentic capability** in threat hunting. This guide helps you adopt it in your organization.

## Philosophy

ATHF teaches systems how to hunt with memory, learning, and augmentation. It's:

- **Framework, not platform** - Structure over software, adapt to your environment
- **Capability-focused** - Adds memory and agents to any hunting methodology ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), custom)
- **Progression-minded** - Start simple (grep + ChatGPT), scale when complexity demands it

**Give your threat hunting program memory and agency.**

## How to Adopt ATHF

### 1. Clone and Customize

**Option A: With CLI Tools (Recommended)**

```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Install CLI for convenience commands
pip install -e .

# Initialize your workspace
athf init

# Make it yours (optional: remove origin and start fresh)
git remote remove origin
```

**Option B: Markdown-Only**

```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Make it yours
rm -rf .git  # Optional: start fresh
git init
```

> **Note:** The CLI is optional convenience tooling. The framework structure (hunts/, LOCK pattern, AGENTS.md) is what enables AI assistance, not the CLI.

### 2. Choose Your Integration Approach

**Option A: Standalone (ATHF only)**
Use ATHF's LOCK pattern as your hunting methodology. Simple, lightweight, agentic-first.

**Option B: Layered (ATHF + PEAK/SQRRL)**
Keep your existing hunting framework ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), [TaHiTI](https://www.betaalvereniging.nl/en/safety/tahiti/)) and use ATHF to add memory and AI agents.

**Why ATHF helps:**
Without structured memory, hunt notes scatter across Slack, tickets, or live in hunters' heads. ATHF gives your program persistent memory and AI integration.

### 3. Adapt Templates to Your Environment

Edit `templates/` to match your:

- Data sources (Splunk indexes, KQL tables, Elastic indices)
- Organizational ATT&CK priorities
- Query style guides
- Approval workflows
- Existing framework (map PEAK phases to LOCK steps)

**Also customize environmental context files:**

**environment.md** - Document your actual tech stack:

- Replace example security tools with what you actually run (SIEM, EDR, firewalls)
- List real technology stack (languages, frameworks, databases, cloud platforms)
- Add links to internal documentation (wikis, architecture diagrams, CMDB)
- Document known gaps and blind spots in your security coverage
- Optionally include patch status and CVE context for awareness
- Update quarterly or when major infrastructure changes occur

**AGENTS.md** - Configure AI assistant context:

- Update "Data Sources" section with your actual SIEM/EDR/network tools
- Add organization-specific threat model and priorities
- Document any compliance requirements affecting hunt scope
- List high-priority ATT&CK TTPs for your environment
- Update when data sources change or AI tooling changes

**knowledge/hunting-knowledge.md** - Threat hunting domain expertise (included in repo):

- Pre-loaded with expert hunting frameworks and quality criteria
- Generally used as-is unless you want to customize for your organization
- Contains hypothesis generation patterns, behavioral models, pivot logic, analytical rigor frameworks
- Referenced by AI assistants to apply expert hunting methodology

### 4. Start at Your Maturity Level

**Level 0 → 1: Manual → Documented (Week 1)**

- Create repository (git, SharePoint, Confluence, Jira, local folder)
- Start documenting hunts in LOCK-structured markdown (use `athf hunt new` or manual markdown)
- Build searchable memory
- No infrastructure changes needed
- Optional: Use `athf hunt validate` to ensure consistency

**Level 1 → 2: Documented → Searchable (Week 2-4)**

- Add AGENTS.md file to repo (customize for your environment)
- Ensure knowledge/hunting-knowledge.md is present (included in repo by default)
- Choose AI tool (GitHub Copilot, Claude Code, Cursor, or org-approved)
- AI can now read your hunt history automatically and apply expert hunting frameworks
- Optional: Use `athf hunt search`, `athf hunt stats`, `athf hunt coverage` to explore your hunts
- No coding required

**Level 2+: Searchable → Generative/Agentic (Month 3-6+)**

- Build scripts for repetitive tasks (if needed)
- When grep is too slow (50+ hunts), add structured memory (JSON, SQLite)

### 5. Build Your Hunt Library

The `hunts/` and `queries/` folders are **yours to fill**:

- Document your organization's threat landscape
- Capture your team's lessons learned
- Build institutional memory in LOCK format (AI-parseable)

### 6. Integrate with Your Tools

ATHF is designed to work with your existing stack. The README provides:

- **The Five Levels of Agentic Hunting** - Detailed explanation of each maturity level with "What you get" summaries and examples
- **Level 3: Generative Capabilities** - "Bring Your Own Tools" approach with MCP servers or APIs for SIEM, EDR, ticketing, and threat intel
- **Level 3-4 Examples** - Visual diagrams and detailed workflows showing multi-MCP coordination and autonomous agent patterns

See [integrations/README.md](integrations/README.md) and [integrations/MCP_CATALOG.md](integrations/MCP_CATALOG.md) for tool-specific guidance.

## Maintaining Environmental Context

The [environment.md](docs/environment.md) file is a living document that informs hunt planning and enables AI-assisted hypothesis generation at all maturity levels.

### Who Maintains This File?

**Shared responsibility model:**

- **Infrastructure/DevOps:** Contributes to environment.md (tech stack changes, new services)
- **Security architects:** Updates environment.md (network architecture, security tools)
- **Threat hunters:** Updates based on hunt findings (discovered services, blind spots)

**For small teams:** One person maintains environment.md, updates as needed.

### Maintenance Cadence

**environment.md:**

- **Quarterly reviews** - Scheduled review of entire file for accuracy
- **Event-driven updates** - When major changes occur:
  - New security tools deployed (SIEM upgrade, new EDR)
  - Infrastructure migrations (cloud migration, datacenter moves)
  - Major application launches
  - Security architecture changes

**AGENTS.md:**

- **As needed** - When data sources change, AI tools change, or team practices evolve
- **Semi-annual reviews** - Ensure AI assistant context remains accurate

**knowledge/hunting-knowledge.md:**

- **Rarely updated** - Core hunting frameworks are stable
- **Update only if** - Your organization develops unique hunting methodologies or you want to add organization-specific guidance
- **Most teams use as-is** - Pre-loaded expert knowledge is generally applicable across environments

### Memory Scaling Guidance

As your hunt repository grows, your memory needs evolve:

**10-50 hunts (Level 1-2):**

- Grep across markdown files works fine (or use `athf hunt search` if CLI installed)
- No additional structure needed
- Search `hunts/` and `environment.md` with grep or CLI
- Example (grep): `grep -i "nginx" environment.md hunts/*.md`
- Example (CLI): `athf hunt search "nginx"`

**50-200 hunts (Level 2-3):**

- Grep still works but starts to slow down
- CLI commands (`athf hunt search`, `athf hunt list --filter`) handle this scale well
- Consider adding simple helpers if not using CLI:
  - Tag system in markdown (e.g., `#ransomware`, `#credential-access`)
  - Hunt index file (manually maintained list of hunts by TTP)
  - Simple scripts to search across files
- environment.md becomes increasingly valuable for validating hunt feasibility

**200+ hunts (Level 3-4):**

- Structured memory becomes valuable:
  - CLI provides built-in YAML frontmatter parsing for programmatic access
  - JSON index of hunts (auto-generated from markdown)
  - SQLite database for faster queries (if needed beyond CLI)
  - Full-text search (Elasticsearch, local search tools)
- Agents can query structured memory efficiently

**Key principle:** Don't build structure until grep becomes painful. Most teams operate at 10-50 hunts where grep (or the CLI) is sufficient.

### Integration with Asset Management

**Optional but powerful:** Link environment.md to existing asset management systems.

**Manual approach (Level 1-2):**

- Reference your CMDB/asset inventory in environment.md
- Add links to ServiceNow, Jira, internal wikis
- Manually update when infrastructure changes

**Integrated approach (Level 3+):**

- Script to pull tech stack from CMDB API
- Auto-update environment.md sections from authoritative sources
- Keep tech inventory synchronized with actual infrastructure

**Example automation:**

```python
# Level 3 - Automated environment.md updates
def update_tech_stack():
    # Pull from CMDB API
    servers = cmdb_api.get_servers()
    applications = cmdb_api.get_applications()

    # Parse existing environment.md
    env_doc = parse_environment_md()

    # Update "Technology Stack" section
    env_doc['servers'] = format_server_list(servers)
    env_doc['applications'] = format_app_list(applications)

    # Write back to environment.md
    write_environment_md(env_doc)

# Run weekly via cron
```

**Benefit:** Ensures environment.md stays accurate as infrastructure changes, enabling AI to suggest feasible hunts based on actual data sources.

## Scaling ATHF in Your Organization

### Solo Hunter

- **Level 1-2: Documented → Searchable**: Repo + AI tool (GitHub Copilot, Claude Code)
- Keep hunts in personal repo or folder
- Build memory with 10-20 reports before considering automation
- Maintain environment.md yourself (15-30 min/quarter, event-driven updates)

### Small Team (2-5 people)

- **Level 1-2: Documented → Searchable**: Shared repo + AI tools
- Git, SharePoint, Confluence, Jira, or Notion
- Collaborative memory via shared hunt notes
- Optional: One person builds simple scripts for repetitive tasks
- Shared responsibility: All team members update environment.md as they discover changes

### Security Team (5-20 people)

- **Level 2-3: Searchable → Generative**: AI tools + optional automation
- Scripts for repetitive workflows (if needed)
- Metrics dashboards
- Structured memory when grep becomes slow
- Formalize environment.md updates (DevOps contributes, hunters consume)

### Enterprise SOC (20+ people)

- **Level 3-4: Generative → Agentic**: Automation + multi-agent systems
- Hunt library organized by TTP
- Detection engineering pipeline integration
- Learning systems (rare)
- Automated environment.md updates from CMDB/asset management

## Mapping ATHF to Your Existing Framework

ATHF complements existing hunting frameworks ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), [TaHiTI](https://www.betaalvereniging.nl/en/safety/tahiti/)) by adding memory and AI augmentation. You can use ATHF standalone or layer it over your current methodology.

**Key insight:** Use your existing framework (PEAK, SQRRL, etc.) for your hunting process, LOCK for your documentation structure, and ATHF to add memory and AI capability at each phase.

The LOCK pattern maps naturally to most hunting methodologies - Learn (Prepare), Observe (Hypothesis), Check (Investigate), Keep (Document).

## Adapting the LOCK Loop

LOCK is flexible—add gates as needed:

### Add Approval Gates

```
Learn → Observe → [Manager Approval] → Check → Keep
```

### Add Peer Review

```
Learn → Observe → Check → [Peer Review] → Keep
```

### Add Detection Pipeline

```
Learn → Observe → Check → Keep → [AI Converts to Detection] → Deploy
```

### Integrate with Incident Response

```
Learn → Observe → Check → Keep → [If Accept: AI Creates IR Ticket]
```

## Customization Examples

### Add Organization-Specific Fields

**Hunt Card Template:**

```markdown
## Organization Context
**Business Unit**: [Sales / Engineering / Finance]
**Data Classification**: [Public / Internal / Confidential]
**Compliance Framework**: [NIST / PCI / SOC2]
```

### Add Your Threat Model

Document your organization's threat landscape:

- Priority threat actors for your industry
- Common initial access vectors
- Crown jewels and critical assets
- Known gaps in coverage

Consider creating a `threat_model.md` file in your repo to capture this context.

### Create Hunt Categories

Organize `hunts/` by your priorities:

```
hunts/
├── ransomware/
├── insider_threat/
├── supply_chain/
├── cloud_compromise/
└── data_exfiltration/
```

## Integration Patterns

### With HEARTH

If you use [HEARTH](https://github.com/THORCollective/HEARTH) format, add converters:

```bash
./tools/convert_to_hearth.py hunts/H-0001.md
```

### With Detection-as-Code

Export hunts that get "accepted":

```bash
./tools/export_to_sigma.py queries/H-0001.spl
```

### With SOAR

Trigger automated hunts from SOAR:

```python
# Pseudocode
soar_playbook.trigger("run_athr_hunt", hypothesis=generated_hypothesis)
```

## Making ATHF "Yours"

### Rebrand for Your Organization

- Change logo in README
- Update terminology (if "LOCK Loop" doesn't fit your culture)
- Add your security principles

### Add Your Voice

- Replace examples with your real hunts (redacted)
- Document your team's unique lessons
- Share your threat hunting philosophy

### Extend with Tools

**Built-in CLI (Included):**

ATHF includes a Python CLI for common workflows:
- `athf hunt new` - Create hunts from templates with YAML frontmatter
- `athf hunt list` - List and filter hunts
- `athf hunt search` - Full-text search across hunt files
- `athf hunt validate` - Validate hunt structure
- `athf hunt stats` - Success rates and metrics
- `athf hunt coverage` - MITRE ATT&CK coverage analysis

**Custom helpers for your environment:**

Build additional tools as needed:
- `query_validator.py` - Check query safety before execution
- `metrics_dashboard.py` - Visualize hunt metrics
- Custom integrations with your SOAR/ticketing systems

## Questions?

ATHF is designed to be self-contained and adaptable. If you have questions about how to adapt it:

1. Review the templates and example hunt (H-0001) for patterns
2. Check the prompts/ folder for AI-assisted workflows
3. See the README for workflow diagrams, progression guidance, and detailed integration patterns
4. Adapt freely - this framework is yours to modify

## Sharing Back (Optional)

While ATHF isn't a contribution repo, we'd love to hear how you're using it:

- Blog about your experience
- Share anonymized metrics
- Present at conferences
- Open a discussion at [github.com/Nebulock-Inc/agentic-threat-hunting-framework](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)

But your hunts, your data, and your lessons stay **yours**.

---

**Remember**: ATHF is a framework to internalize, not a platform to extend. Make it yours.
