# Using ATHR in Your Organization

ATHR is a **framework for building agentic capability** in threat hunting. This guide helps you adopt it in your organization.

## Philosophy

ATHR teaches systems how to hunt with memory, learning, and autonomy. It's:

- **Framework, not platform** - Structure over software, adapt to your environment
- **Capability-focused** - Adds memory and agents to any hunting methodology (PEAK, SQRRL, custom)
- **Progression-minded** - Start simple (grep + ChatGPT), scale when complexity demands it

**ATHR is a mental model you can Git clone—then make agentic.**

## How to Adopt ATHR

### 1. Clone and Customize

```bash
git clone https://github.com/sydney-nebulock/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Make it yours
rm -rf .git  # Optional: start fresh
git init
```

### 2. Choose Your Integration Approach

**Option A: Standalone (ATHR only)**
Use ATHR's LOCK pattern as your hunting methodology. Simple, lightweight, agentic-first.

**Option B: Layered (ATHR + PEAK/SQRRL)**
Keep your existing hunting framework (PEAK, SQRRL, TaHiTI) and use ATHR to add memory and AI agents.

### 3. Adapt Templates to Your Environment

Edit `templates/` to match your:
- Data sources (Splunk indexes, KQL tables, Elastic indices)
- Organizational ATT&CK priorities
- Query style guides
- Approval workflows
- Existing framework (map PEAK phases to LOCK steps)

### 4. Start at Your Maturity Level

**Level 0-1 (Week 1):**
- Use AI prompts from `prompts/` with ChatGPT/Claude
- No infrastructure changes needed
- Focus: Learn AI-assisted hypothesis generation

**Level 2 (Month 1-2):**
- Save hunt notes in `hunts/` folder (or Jira, Confluence, etc.)
- Before each hunt: `grep -l "TTP" hunts/*.md` to check memory
- Share past hunts with AI for context

**Level 3+ (Month 3-6+):**
- Build simple agent scripts for repetitive tasks
- When grep is too slow (50+ hunts), add structured memory (JSON, SQLite)
- See `metrics/README.md` for memory scaling options

### 5. Build Your Hunt Library

The `hunts/` and `queries/` folders are **yours to fill**:
- Document your organization's threat landscape
- Capture your team's lessons learned
- Build institutional memory in LOCK format (AI-parseable)

### 6. Integrate with Your Tools

ATHR is designed to work with your existing stack:
- **SIEM**: Splunk, Sentinel, Elastic, Chronicle
- **Ticketing**: Jira, ServiceNow (hunt notes as tickets)
- **Detection-as-Code**: Sigma, YARA-L
- **Notebooks**: Jupyter, Observable
- **AI/Agents**: ChatGPT, Claude, LangChain, AutoGen
- **Orchestration**: SOAR, automation platforms

## Scaling ATHR in Your Organization

### Solo Hunter
- **Level 1-2**: Use AI prompts + grep-based memory
- Keep hunts in personal repo or folder
- Build memory with 10-20 hunt reports before adding agents

### Small Team (2-5 people)
- **Level 2-3**: Shared storage (git, SharePoint, Confluence, Jira)
- Grep works across any shared folder
- Collaborative memory via shared hunt notes
- One person can build simple agents for the team

### Security Team (5-20 people)
- **Level 3-4**: Structured memory (JSON, SQLite)
- Agent scripts for common tasks (hypothesis generation, documentation)
- Hunt scheduling and rotation
- Metrics dashboards from decision logs

### Enterprise SOC (20+ people)
- **Level 4-5**: Multi-agent orchestration
- Hunt library organized by threat actor/TTP
- Detection engineering pipeline integration
- Learning systems that adapt based on hunt outcomes

## Mapping ATHR to Your Existing Framework

### If You Use PEAK

Map ATHR's LOCK pattern to PEAK phases:

| PEAK Phase | LOCK Step | AI Integration |
|------------|-----------|----------------|
| **Prepare** | Learn + Observe | AI drafts hypothesis, recalls past hunts |
| **Execute** | Check | AI generates queries, automates execution |
| **Act with Knowledge** | Keep | AI documents lessons, updates detections |

Document your PEAK hunts in LOCK format for AI parsing.

### If You Use SQRRL

Map SQRRL to LOCK:

| SQRRL Phase | LOCK Step | AI Integration |
|-------------|-----------|----------------|
| **Hypothesis** | Learn + Observe | AI generates from context |
| **Investigation** | Check | AI builds queries, recalls similar hunts |
| **Pattern / Detection** | Keep | AI identifies trends, converts to rules |

### If You Use Custom Methodology

Map your process to LOCK's four steps:
1. **Context gathering** → Learn
2. **Hypothesis formation** → Observe
3. **Testing/validation** → Check
4. **Decision + lessons** → Keep

This makes your hunts AI-readable without changing your process.

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
If you use HEARTH format, add converters:
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

## Making ATHR "Yours"

### Rebrand for Your Organization
- Change logo in README
- Update terminology (if "LOCK Loop" doesn't fit your culture)
- Add your security principles

### Add Your Voice
- Replace examples with your real hunts (redacted)
- Document your team's unique lessons
- Share your threat hunting philosophy

### Extend with Tools
Build helpers that work for your environment:
- `new_hunt.sh` - Generate hunt from template
- `query_validator.py` - Check query safety
- `metrics_dashboard.py` - Visualize decision log

## Questions?

ATHR is designed to be self-contained and adaptable. If you have questions about how to adapt it:
1. Review the templates and example hunt (H-0001) for patterns
2. Check the prompts/ folder for AI-assisted workflows
3. Adapt freely - this framework is yours to modify

## Sharing Back (Optional)

While ATHR isn't a contribution repo, we'd love to hear how you're using it:
- Blog about your experience
- Share anonymized metrics
- Present at conferences
- Tag @your-handle or open a discussion

But your hunts, your data, and your lessons stay **yours**.

---

**Remember**: ATHR is a framework to internalize, not a platform to extend. Make it yours.
