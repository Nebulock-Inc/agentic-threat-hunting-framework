# Using ATHF in Your Organization

ATHF is a **framework for building agentic capability** in threat hunting. This guide helps you adopt it.

## Philosophy

ATHF teaches systems how to hunt with memory, learning, and augmentation.

- **Framework, not platform** - Structure over software, adapt to your environment
- **Capability-focused** - Adds memory and agents to any hunting methodology ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), custom)
- **Progression-minded** - Start simple, scale when complexity demands it

## How to Adopt ATHF

### 1. Clone and Customize

```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Option A: With CLI (Recommended)
pip install -e .
athf init

# Option B: Markdown-Only
# Just start documenting hunts in hunts/ folder
```

> The CLI is optional convenience tooling. The framework structure (hunts/, LOCK pattern, AGENTS.md) enables AI assistance.

### 2. Choose Your Integration Approach

**Standalone:** Use ATHF's LOCK pattern as your hunting methodology (simple, agentic-first).

**Layered:** Keep your existing framework ([PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html), [SQRRL](https://www.threathunting.net/files/The%20Threat%20Hunting%20Reference%20Model%20Part%202_%20The%20Hunting%20Loop%20_%20Sqrrl.pdf), [TaHiTI](https://www.betaalvereniging.nl/en/safety/tahiti/)) and use ATHF to add memory and AI capability.

### 3. Customize Environmental Context

**environment.md** - Your actual tech stack:
- Security tools (SIEM, EDR, firewalls)
- Technology stack (languages, frameworks, cloud platforms)
- Known gaps and blind spots
- Update quarterly or when major changes occur

**AGENTS.md** - AI assistant context:
- Data sources and tools
- Organization threat model and priorities
- Compliance requirements
- High-priority ATT&CK TTPs

**knowledge/hunting-knowledge.md** - Expert hunting frameworks (included):
- Pre-loaded hunting methodology and analytical rigor
- Use as-is or customize for your organization

### 4. Start at Your Maturity Level

See the [README](README.md) for detailed maturity model explanation.

**Level 1: Documented (Week 1)**
- Create repository, start documenting hunts in LOCK format
- Use `athf hunt new` or manual markdown

**Level 2: Searchable (Week 2-4)**
- Add AGENTS.md and hunting-knowledge.md
- Choose AI tool (GitHub Copilot, Claude Code, Cursor)
- AI reads your hunt history automatically

**Level 3+: Generative/Agentic (Month 3-6+)**
- Build scripts for repetitive tasks (if needed)
- Add structured memory when grep becomes slow (50+ hunts)

## Maintaining Environmental Context

### Ownership & Cadence

**Who maintains:**
- **Infrastructure/DevOps:** Tech stack changes, new services
- **Security architects:** Network architecture, security tools
- **Threat hunters:** Hunt findings, discovered services, blind spots

**When to update:**
- **Quarterly:** Scheduled review of environment.md
- **Event-driven:** New security tools, infrastructure migrations, major application launches
- **AGENTS.md:** As needed when data sources or AI tools change
- **hunting-knowledge.md:** Rarely (core hunting frameworks are stable)

### Memory Scaling

| Hunt Volume | Approach | Tools |
|-------------|----------|-------|
| **10-50 hunts** | Grep or CLI search | `grep -i "keyword" hunts/*.md` or `athf hunt search` |
| **50-200 hunts** | CLI + simple helpers | Tags in markdown, hunt index, `athf hunt list --filter` |
| **200+ hunts** | Structured memory | JSON index, SQLite, full-text search |

**Key principle:** Don't build structure until grep becomes painful.

### Asset Management Integration (Optional)

**Manual (Level 1-2):** Reference CMDB/asset inventory in environment.md, add links to ServiceNow/Jira/wikis.

**Automated (Level 3+):** Script to pull tech stack from CMDB API, auto-update environment.md sections.

## Scaling by Team Size

| Team Size | Level | Focus |
|-----------|-------|-------|
| **Solo Hunter** | 1-2 | Personal repo + AI tool, maintain environment.md yourself (15-30 min/quarter) |
| **Small Team (2-5)** | 1-2 | Shared repo + AI tools, collaborative memory, shared environment.md responsibility |
| **Security Team (5-20)** | 2-3 | Optional automation scripts, metrics dashboards, formalized environment.md updates |
| **Enterprise SOC (20+)** | 3-4 | Hunt library by TTP, detection engineering pipeline, automated environment.md from CMDB |

## Customizing the LOCK Loop

LOCK is flexible—add gates as needed:

```
# Add approval gates
Learn → Observe → [Manager Approval] → Check → Keep

# Add peer review
Learn → Observe → Check → [Peer Review] → Keep

# Add detection pipeline
Learn → Observe → Check → Keep → [AI Converts to Detection] → Deploy
```

## Customization Examples

### Add Organization-Specific Fields

```markdown
## Organization Context
**Business Unit**: [Sales / Engineering / Finance]
**Data Classification**: [Public / Internal / Confidential]
**Compliance Framework**: [NIST / PCI / SOC2]
```

### Add Your Threat Model

Create `threat_model.md` to document:
- Priority threat actors for your industry
- Common initial access vectors
- Crown jewels and critical assets
- Known coverage gaps

### Organize Hunts by Priority

```
hunts/
├── ransomware/
├── insider_threat/
├── supply_chain/
└── cloud_compromise/
```

## Integration Patterns

### With HEARTH
```bash
./tools/convert_to_hearth.py hunts/H-0001.md
```

### With Detection-as-Code
```bash
./tools/export_to_sigma.py queries/H-0001.spl
```

### With SOAR
Trigger automated hunts from playbooks using generated hypotheses.

## Making ATHF "Yours"

### Rebrand
- Change logo, update terminology, add your security principles

### Add Your Voice
- Replace examples with your real hunts (redacted)
- Document your team's unique lessons
- Share your threat hunting philosophy

### Extend with Tools

**Built-in CLI:** See [README](README.md#-cli-commands) for complete command reference including:
- Hunt management (`athf hunt new/list/search/validate/stats/coverage`)
- Research agent (`athf research new`) - Deep pre-hunt research with 5-skill methodology
- Hypothesis generator (`athf agent run hypothesis-generator`) - AI-generated hunt hypotheses

**Custom helpers:** Build additional tools as needed (query validators, metrics dashboards, SOAR integrations).

## Questions?

1. Review templates and example hunt (H-0001) for patterns
2. Check prompts/ folder for AI-assisted workflows
3. See [README](README.md) for workflow diagrams and integration patterns
4. Adapt freely - this framework is yours to modify

## Sharing Back (Optional)

We'd love to hear how you're using ATHF:
- Blog about your experience
- Share anonymized metrics
- Present at conferences
- Open a discussion at [github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)

Your hunts, data, and lessons stay **yours**.

---

**Remember**: ATHF is a framework to internalize, not a platform to extend. Make it yours.
