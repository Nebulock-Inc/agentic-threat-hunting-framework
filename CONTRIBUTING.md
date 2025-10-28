# Using ATHR in Your Organization

ATHR is a **framework for building agentic capability** in threat hunting. This guide helps you adopt it in your organization.

## Philosophy

ATHR teaches systems how to hunt with memory, learning, and augmentation. It's:

- **Framework, not platform** - Structure over software, adapt to your environment
- **Capability-focused** - Adds memory and agents to any hunting methodology ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), custom)
- **Progression-minded** - Start simple (grep + ChatGPT), scale when complexity demands it

**Give your threat hunting program memory and agency.**

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
Keep your existing hunting framework ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), [TaHiTI](https://www.betaalvereniging.nl/en/safety/tahiti/)) and use ATHR to add memory and AI agents.

**Why ATHR helps:**
Without structured memory, hunt notes scatter across Slack, tickets, or live in hunters' heads. ATHR gives your program persistent memory and AI integration.

### 3. Adapt Templates to Your Environment

Edit `templates/` to match your:
- Data sources (Splunk indexes, KQL tables, Elastic indices)
- Organizational ATT&CK priorities
- Query style guides
- Approval workflows
- Existing framework (map PEAK phases to LOCK steps)

### 4. Start at Your Maturity Level

**Level 0 → 1: Ephemeral → Persistent (Week 1)**
- Create repository (git, SharePoint, Confluence, Jira, local folder)
- Start documenting hunts in LOCK-structured markdown
- Build searchable memory
- No infrastructure changes needed

**Level 1 → 2: Persistent → Augmented (Week 2-4)**
- Add AGENTS.md file to repo
- Choose AI tool (GitHub Copilot, Claude Code, Cursor, or org-approved)
- AI can now read your hunt history automatically
- No coding required

**Level 2+: Augmented → Autonomous/Coordinated (Month 3-6+)**
- Build scripts for repetitive tasks (if needed)
- When grep is too slow (50+ hunts), add structured memory (JSON, SQLite)
- See `metrics/README.md` for memory scaling options

### 5. Build Your Hunt Library

The `hunts/` and `queries/` folders are **yours to fill**:
- Document your organization's threat landscape
- Capture your team's lessons learned
- Build institutional memory in LOCK format (AI-parseable)

### 6. Integrate with Your Tools

ATHR is designed to work with your existing stack. See the README sections for detailed integration guidance:
- **"Integration Patterns"** - Storage options, AI tools by level, SIEM compatibility
- **"What You'll Need From Your Tech Stack"** - Requirements for each maturity level
- **"How ATHR Works With Your Framework"** - Mapping to PEAK, SQRRL, custom methodologies

## Scaling ATHR in Your Organization

### Solo Hunter
- **Level 1-2: Persistent → Augmented**: Repo + AI tool (GitHub Copilot, Claude Code)
- Keep hunts in personal repo or folder
- Build memory with 10-20 reports before considering automation

### Small Team (2-5 people)
- **Level 1-2: Persistent → Augmented**: Shared repo + AI tools
- Git, SharePoint, Confluence, Jira, or Notion
- Collaborative memory via shared hunt notes
- Optional: One person builds simple scripts for repetitive tasks

### Security Team (5-20 people)
- **Level 2-3: Augmented → Autonomous**: AI tools + optional automation
- Scripts for repetitive workflows (if needed)
- Metrics dashboards
- Structured memory when grep becomes slow

### Enterprise SOC (20+ people)
- **Level 3-4: Autonomous → Coordinated**: Automation + multi-agent systems
- Hunt library organized by TTP
- Detection engineering pipeline integration
- Learning systems (rare)

## Mapping ATHR to Your Existing Framework

ATHR complements existing hunting frameworks ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), [TaHiTI](https://www.betaalvereniging.nl/en/safety/tahiti/)) by adding memory and AI augmentation. You can use ATHR standalone or layer it over your current methodology.

**See the README section "How ATHR Works With PEAK"** for detailed mapping showing how PEAK phases map to LOCK steps.

The key insight: Use PEAK for your hunting process, LOCK for your documentation structure, ATHR to integrate AI at each phase.

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
3. See the README for workflow diagrams, progression guidance, and detailed integration patterns
4. Adapt freely - this framework is yours to modify

## Sharing Back (Optional)

While ATHR isn't a contribution repo, we'd love to hear how you're using it:
- Blog about your experience
- Share anonymized metrics
- Present at conferences
- Tag @sydney-nebulock or open a discussion

But your hunts, your data, and your lessons stay **yours**.

---

**Remember**: ATHR is a framework to internalize, not a platform to extend. Make it yours.
