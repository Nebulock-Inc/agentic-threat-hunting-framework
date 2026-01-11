# The Five Levels of Agentic Hunting

ATHF defines a simple maturity model for evolving your hunting program. Each level builds on the previous one.

**Most teams will live at Levels 1–2. Everything beyond that is optional maturity.**

![The Five Levels of Agentic Hunting](../../../assets/athf_fivelevels.png)

## Overview

| Level | Capability | What You Get | Time to Implement |
|-------|-----------|--------------|-------------------|
| **0** | Ad-hoc | Hunts exist in Slack, tickets, or analyst notes | Current state |
| **1** | Documented | Persistent hunt records using LOCK | 1 day |
| **2** | Searchable | AI reads and recalls your hunts | 1 week |
| **3** | Generative | AI executes queries via MCP tools | 2-4 weeks |
| **4** | Agentic | Autonomous agents monitor and act | 1-3 months |

---

## How ATHF CLI Commands Support Each Level

**Important:** The CLI is optional. ATHF is markdown-first - you can achieve all maturity levels using just markdown files and your AI assistant. The CLI provides convenience commands for common workflows, but the framework structure works without it.

**If you choose to use the CLI**, it provides consistent commands across all maturity levels. What changes is **who uses them** and **how they're used**:

| Level | Who Uses CLI | How It's Used | Example |
|-------|--------------|---------------|---------|
| **1** | You (manually) | Create and validate hunts | `athf hunt new` creates structured hunt files<br>OR manually create markdown files |
| **2** | You + AI (interactive) | AI searches hunts, suggests refinements | AI uses `athf hunt search` to recall past work<br>OR AI searches markdown files directly |
| **3** | AI (on your behalf) | AI executes queries and documents results | AI uses MCP tools + `athf hunt new` to create hunts<br>OR AI writes markdown files directly |
| **4** | Autonomous agents | Agents coordinate through CLI | CTI agent uses `athf hunt new`, validator uses `athf hunt validate`<br>OR agents manipulate markdown files |

**Key insights:**
- The CLI doesn't change between levels - it becomes building blocks for increasingly sophisticated automation
- The framework structure (hunts/, LOCK pattern, AGENTS.md) is what enables AI assistance, not the CLI
- Choose CLI for convenience, skip it if you prefer direct markdown manipulation

---

## Level 1: Documented Hunts

**What you get:**

- **Persistent hunt records** that survive beyond Slack threads
- **Standardized structure** using the LOCK pattern
- **Knowledge transfer** for new team members
- **Searchable history** of what's been tested

You document hunts using LOCK in markdown.

### Example Hunt File

**File:** `hunts/H-0031.md`

```markdown
# H-0031: Detecting Remote Management Abuse via PowerShell and WMI (TA0002 / T1028 / T1047)

**Learn**
Incident response from a recent ransomware case showed adversaries using PowerShell remoting and WMI to move laterally between Windows hosts.
These techniques often bypass EDR detections that look only for credential theft or file-based artifacts.
Telemetry sources available: Sysmon (Event IDs 1, 3, 10), Windows Security Logs (Event ID 4624), and EDR process trees.

**Observe**
Adversaries may execute PowerShell commands remotely or invoke WMI for lateral movement using existing admin credentials.
Suspicious behavior includes PowerShell or wmiprvse.exe processes initiated by non-admin accounts or targeting multiple remote systems in a short time window.

**Check**
index=sysmon OR index=edr
(EventCode=1 OR EventCode=10)
| search (Image="*powershell.exe" OR Image="*wmiprvse.exe")
| stats count dc(DestinationHostname) as unique_targets by User, Computer, CommandLine
| where unique_targets > 3
| sort - unique_targets

**Keep**
Detected two accounts showing lateral movement patterns:
- `svc_backup` executed PowerShell sessions on five hosts in under ten minutes
- `itadmin-temp` invoked wmiprvse.exe from a workstation instead of a jump server

Confirmed `svc_backup` activity as legitimate backup automation.
Marked `itadmin-temp` as suspicious; account disabled pending review.

Next iteration: expand to include remote registry and PSExec telemetry for broader coverage.
```

### Benefits

When someone new joins the team, they can quickly see what was tested, what was learned, and what should be tried next. This alone prevents redundant hunts and lost context.

### Getting Started at Level 1

**Using the CLI (Recommended):**
```bash
# Initialize workspace
athf init

# Create your first hunt
athf hunt new --technique T1003.001 --title "LSASS Credential Dumping"

# Validate structure
athf hunt validate

# View your hunt catalog
athf hunt list
```

**Without the CLI (Pure Markdown):**
1. Copy a hunt template from [templates/](../templates/)
2. Fill out the LOCK sections
3. Save as `hunts/H-XXXX.md`
4. Commit to your repository

> **Note:** Both paths are equally valid. The CLI provides convenience, but the markdown-first approach gives you complete control. Many teams prefer pure markdown for simplicity and transparency. Choose what works best for your workflow.

**You can be operational at Level 1 within a day.**

---

## Level 2: Searchable Memory

**What you get:**

- **AI reads your repo** and understands your hunt history
- **AI recalls past hunts** when you ask questions
- **AI gives contextually correct suggestions** based on your environment
- **Instant context retrieval** - seconds instead of minutes

At Level 2, you add context files to your repository that provide AI assistants (Claude Code, GitHub Copilot, Cursor) with the knowledge they need to assist effectively.

### Required Context Files

#### [AGENTS.md](../../../AGENTS.md)

Provides environmental and structural context:

- Your repository structure (hunts/, templates/, queries/)
- Available data sources (SIEM indexes, EDR platforms, network logs)
- Workflow expectations and guardrails
- How AI should search past hunts before generating new ones

#### [knowledge/hunting-knowledge.md](../knowledge/hunting-knowledge.md)

Embeds threat hunting expertise:

- Pattern-based hypothesis generation frameworks (TTP-driven, Actor-driven, Behavior-driven, Telemetry Gap-driven)
- Quality criteria for evaluating hypotheses (falsifiable, scoped, observable, actionable, contextual)
- Observable-to-TTP mapping guidance
- Data quality considerations (completeness, timeliness, fidelity, accuracy, consistency)
- Best practices for working within the LOCK pattern

### What It Enables

Once these context files exist, you can open your repo in Claude Code or similar tools and ask:

> "What have we learned about T1028?"

The AI automatically searches your hunts directory, references past investigations, and suggests refined hypotheses based on lessons learned - applying expert threat hunting frameworks from the knowledge base. What used to take 20 minutes of grepping and copy-pasting now takes under five seconds.

**The combination of AGENTS.md (environmental context) and hunting-knowledge.md (domain expertise) transforms AI assistants from generic helpers into informed threat hunting partners.**

![Manual vs. AI-Assisted Content Creation](../../../assets/athf_manual_v_ai.png)

### Getting Started at Level 2

1. Review the included [AGENTS.md](../../../AGENTS.md) template
2. Customize it with your environment details
3. Review [knowledge/hunting-knowledge.md](../knowledge/hunting-knowledge.md) (already included)
4. Open your repo in Claude Code or similar AI assistant
5. Start asking questions about your hunts

**CLI Commands at Level 2:**
At this level, you still run commands manually, but AI helps you decide what to run:
```bash
# AI suggests: "Let me search for related hunts first"
athf hunt search "T1003"

# AI suggests: "Check your coverage gaps"
athf hunt coverage

# AI suggests: "Let's see your success rates"
athf hunt stats
```

The AI reads your hunt files and provides context-aware suggestions, but you execute the commands.

**You can be operational at Level 2 within a week.**

---

## Level 3: Generative Capabilities

**What you get:**

- **AI executes queries** directly in your SIEM
- **AI enriches findings** with threat intel lookups
- **AI creates tickets** in your case management system
- **AI updates hunt files** with results and commits changes

At this stage, you give your AI assistant **tools to interact with your security stack** via MCP (Model Context Protocol) servers. Instead of manually copying queries to Splunk or looking up IOCs in threat intel, Claude does it directly.

**Level 3 is about execution. The AI doesn't just suggest queries; it runs them with your tools.**

### Tool Integration

Connect MCP servers or APIs for the tools you already use in your security operations:

- **SIEM search** (Splunk, Elastic, Chronicle)
- **Endpoint data** (CrowdStrike, SentinelOne, Microsoft Defender)
- **Ticket creation** (Jira, ServiceNow, GitHub Issues)
- **Threat intel queries** (MISP, VirusTotal, AlienVault OTX)

**Level 3 is "Bring Your Own Tools"** - you connect MCP servers or APIs for whatever tools you already use.

### Capabilities

Your AI Assistant Can:

- **Run queries** - Execute hunt queries and retrieve results directly
- **Enrich findings** - Look up IOCs, correlate threat intelligence, check reputation
- **Update hunts** - Document findings and commit changes to hunt files
- **Trigger actions** - Create tickets, generate alerts, update case management

### Simple vs. Advanced Workflows

**Simple Example: Without MCP (Level 2)**

```
You: "Search for SSH brute force attempts"
Claude: "Here's a Splunk query: index=linux_secure action=failure | stats count by src_ip"
You: [Copies query to Splunk, runs it, pastes results back]
Claude: "I see 3 high-volume IPs..."
```

**With Splunk MCP (Level 3)**

```
You: "Search for SSH brute force attempts"
Claude: [Executes Splunk query via MCP]
"Found 3 source IPs with high failure rates:
- 203.0.113.45 (127 attempts)
- 198.51.100.22 (89 attempts)
- 192.0.2.15 (67 attempts)

Let me check CrowdStrike for detections..."
[Queries CrowdStrike MCP]
"203.0.113.45 connected to 3 hosts with Qakbot detections.
Should I create a Jira ticket for investigation?"
```

**The difference:** Claude executes queries, enriches data, and creates tickets - not just suggests them.

### CLI Integration at Level 3

At Level 3, AI uses CLI commands directly as part of workflows:

**Example: AI-Driven Hunt Creation**
```
You: "Search for SSH brute force and create a hunt"

AI: [Executes Splunk query via MCP]
    [Gets results: 3 high-volume IPs]
    [Uses: athf hunt new --technique T1110.001 --title "SSH Brute Force Detection"]
    [Documents findings in hunt file]
    [Uses: athf hunt validate to check structure]
    "Created H-0087.md documenting SSH brute force activity. Review?"
```

**The difference:** You direct the workflow, AI executes both MCP tools (Splunk) and CLI commands (athf).

### Getting Started at Level 3

1. Browse the catalog: See [integrations/MCP_CATALOG.md](../integrations/MCP_CATALOG.md)
2. Pick your first MCP: Start with Splunk or CrowdStrike
3. Follow quickstart guide: [integrations/quickstart/](../integrations/quickstart/)
4. Review example hunts: See [hunts/](../hunts/) directory

**Detailed workflows:** See [../integrations/README.md](../integrations/README.md) for comprehensive examples

### Success Criteria

- Claude **executes** hunt queries instead of just writing them
- IOCs are **enriched** automatically with threat intel
- Incident tickets are **created** with full context
- You focus on **analysis and decision-making**, not manual task execution

**Learn more:** [integrations/README.md](../integrations/README.md)

---

## Level 4: Agentic Workflows

**What you get:**

- **Agents monitor** CTI feeds without your intervention
- **Agents generate** draft hunts based on new threats
- **Agents coordinate** through shared LOCK memory
- **You validate and approve** rather than create from scratch

At this stage, you move from **reactive assistance** to **proactive automation**. Instead of asking your AI for help with each task, you deploy autonomous agents that monitor, reason, and act based on objectives you define.

The key difference from Level 3: **agents operate autonomously** rather than waiting for your prompts. They detect events, make decisions within guardrails, and coordinate with each other through shared memory (your LOCK-structured hunts).

### Multi-Agent Coordination

At Level 4, multiple specialized agents work together:

- **CTI Monitor Agent** - Watches threat feeds, identifies relevant TTPs
- **Hypothesis Generator Agent** - Creates draft hunt files in LOCK format
- **Validator Agent** - Checks queries against your data sources
- **Notifier Agent** - Alerts analysts when human review is needed

**Detailed workflows:** See [level4-agentic-workflows.md](level4-agentic-workflows.md) for comprehensive examples

### Example Scenario

1. **CTI Monitor Agent** runs every 6 hours, checking threat feeds
2. Detects new Qakbot campaign using T1059.003
3. Searches past hunts - finds we haven't covered this sub-technique
4. **Triggers Hypothesis Generator Agent**
5. Generator searches historical hunts for context
6. Creates draft hunt `H-0156.md` with LOCK structure
7. **Triggers Validator Agent**
8. Validator checks query against data sources from `AGENTS.md`
9. Flags for human review
10. **Triggers Notifier Agent**
11. Posts to Slack: "New hunt H-0156 ready for review"

**You wake up to:**
> "3 new draft hunts created overnight based on recent CTI. Ready for your review."

### CLI Commands in Autonomous Workflows

At Level 4, agents use CLI commands without your intervention:

**Autonomous Agent Workflow:**
```bash
# CTI Monitor Agent (runs every 6 hours)
athf hunt search "T1059.003"  # Check for existing hunts
# No matches found

# Hypothesis Generator Agent (triggered by CTI Monitor)
athf hunt new \
  --technique T1059.003 \
  --title "Qakbot JavaScript Dropper Detection" \
  --platform windows \
  --non-interactive

# Validator Agent (triggered by Generator)
athf hunt validate H-0156  # Ensure structure is correct
athf hunt coverage  # Update coverage metrics

# Notifier Agent (triggered by Validator)
# Posts to Slack: "H-0156 ready for review"
```

**The progression:**
- **Level 1:** You run `athf hunt new` manually
- **Level 2:** AI suggests when to run `athf hunt new`
- **Level 3:** AI runs `athf hunt new` when you ask
- **Level 4:** Agents run `athf hunt new` autonomously based on objectives

### The Maturity Progression

- **Level 2:** You ask AI questions, it responds
- **Level 3:** You direct AI to use tools
- **Level 4:** Agents work autonomously toward objectives, notify you when human judgment is needed

### Success Criteria

- Agents **monitor** CTI feeds without your intervention
- Agents **generate** draft hunts based on new threats
- Agents **coordinate** through shared memory (LOCK hunts)
- You focus on **validating** and **approving** rather than creating from scratch

### Implementation Options

Level 4 can be built using various agent frameworks:

- **LangGraph** - For building stateful, multi-agent workflows
- **CrewAI** - For role-based agent collaboration
- **AutoGen** - For conversational agent patterns
- **Custom orchestration** - Purpose-built for your environment

The key is that **all agents share the same memory layer** - your LOCK-structured hunts - ensuring consistency and enabling true coordination.

**Success can look like many things at Level 4.** You might have agents that autonomously execute queries using tools like the Splunk MCP server, or agents that orchestrate multi-step workflows across your security stack. At this stage, you're mature enough to make these architectural decisions based on your team's needs and risk tolerance.

---

## Choosing Your Level

**Most teams should start at Level 1 and move to Level 2.** Everything beyond that is optional maturity that depends on your team's needs, risk tolerance, and technical capability.

**Level 1:** Operational within a day
**Level 2:** Operational within a week
**Level 3:** 2-4 weeks depending on tool availability
**Level 4:** 1-3 months with custom agent development

The framework is designed to be flexible. Use what works for you, modify what doesn't, and skip what isn't relevant.
