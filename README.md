<div align="center">
  <img src="athr_logo.png" alt="Agentic Threat Hunting Framework Logo" width="400"/>
</div>

# Agentic Threat Hunting Framework (ATHR)

**Give your threat hunting program memory and agency.**

ATHR is a framework for building threat hunting systems that remember past investigations, learn from outcomes, and decide autonomously. It provides structure for progressing from manual hunting to AI-coordinated operations.

**Use it standalone, or layer it over PEAK, SQRRL, or your existing methodology.**

## The LOCK Pattern

Every threat hunting methodology follows the same core pattern—ATHR calls it **LOCK**:

```
🔒 Learn → Observe → Check → Keep
```

**L — Learn**: Gather context (CTI, alert, anomaly)
**O — Observe**: Form hypothesis about adversary behavior
**C — Check**: Test with bounded query
**K — Keep**: Record decision and lessons learned

LOCK isn't a new methodology—it's the **abstraction that makes threat hunting teachable to AI**.

- **PEAK** (Prepare → Execute → Act) follows LOCK
- **SQRRL** (Hypothesis → Investigation → Patterns) follows LOCK
- **Your custom process** probably follows LOCK

By standardizing hunt notes around LOCK, AI can understand your hunts regardless of which framework you use.

## Why ATHR?

**The Problem:**
Existing threat hunting frameworks (PEAK, SQRRL, TaHiTI) teach you *how to hunt*, but not *how to make hunting systems remember, learn, and act autonomously*.

Without structure for memory and agents:
- Hunters repeat investigations (no memory of past hunts)
- AI assistance is ad-hoc (copy/paste to ChatGPT with no context)
- Lessons learned stay in people's heads (knowledge loss when hunters leave)
- Scaling requires more hunters (no path to automation)

**ATHR's Solution:**
A framework specifically for building **agentic capability** in threat hunting:

1. **Memory by Design** - Architecture for recall (grep → structured → weighted)
2. **AI Integration Patterns** - From prompts to agents to learning systems
3. **Maturity Progression** - Pragmatic path from manual to autonomous
4. **Universal Structure** - LOCK pattern works across methodologies

**What Makes ATHR Different:**

| What You Need | Use This Framework |
|---------------|-------------------|
| How to structure hunts for teams | **PEAK** (Prepare → Execute → Act) |
| How to validate threat hypotheses | **SQRRL** (Hypothesis → Investigation → Detection) |
| How to coordinate hunt teams | **TaHiTI** (Team hunting methodology) |
| **How to add memory, AI, and agents** | **ATHR** (Manual → Autonomous) |

**ATHR is the only framework focused on making threat hunting agentic.**

## What ATHR Is

ATHR is a **framework for agentic threat hunting** - building systems that can remember, learn, and act with increasing autonomy.

**Core Components:**

1. **LOCK Pattern** - Universal structure for documenting hunts in AI-readable format
2. **Memory Architecture** - From simple grep to weighted learning systems
3. **Maturity Model** - 5 levels from manual to adaptive autonomous operations
4. **Templates & Patterns** - Practical implementations you can copy

**Scope:**
- **PEAK/SQRRL/TaHiTI**: Frameworks for *how humans hunt* (process, phases, methodology)
- **ATHR**: Framework for *how systems become agentic* (memory, learning, autonomy)

**Relationship:**
- **Standalone**: Use ATHR's LOCK pattern and maturity model to build agentic capability from scratch
- **Layered**: Apply ATHR's memory and agent patterns to your existing PEAK/SQRRL workflow

**Technical Scope:**
- **Works on**: Markdown files (git, SharePoint, Confluence, Jira, folders)
- **Works with**: ChatGPT, Claude, Copilot, custom agents, LangChain, AutoGen
- **Integrates with**: Any SIEM (Splunk, Sentinel, Elastic, Chronicle)

## The 5 Levels of Agentic Hunting

| Level | Name | What Changes | Memory | Tools |
|-------|------|--------------|--------|-------|
| **0. Manual** | Human-Only | You write everything yourself | None | Pen & paper, docs |
| **1. Assisted** | AI Drafts | AI helps write hypotheses/queries | None | ChatGPT prompts |
| **2. Informed** | AI + Memory | AI recalls past hunts before drafting | Hunt reports (grep) | ChatGPT + grep |
| **3. Automated** | Single Agent | One agent automates a repetitive task | Hunt reports | Python agent scripts |
| **4. Coordinated** | Multi-Agent | Multiple agents handle different tasks | Structured (JSON/DB) | Agent orchestration |
| **5. Adaptive** | Learning System | System learns what works, adapts priorities | Weighted outcomes | ML + agents |

**Start at Level 0. Most teams operate at Level 2-3. Progress only when complexity demands it.**

## Quick Start

### 1. Install the Templates

```bash
git clone https://github.com/sydney-nebulock/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
```

Or download and copy to any storage (SharePoint, Confluence, Jira, folders).

### 2. See the Example

Check `hunts/` for a complete hunt showing AI-assisted workflow:
- **H-0001.md** - Hypothesis template with AI guidance
- **H-0001_2025-10-22.md** - First execution
- **H-0001_2025-10-29.md** - Refined execution using memory

### 3. Start at Your Level

**Level 0-1: Use AI prompts**
- Copy prompts from `prompts/` folder
- Use with ChatGPT/Claude to draft hypotheses and queries
- Still validate and run everything manually

**Level 2: Add memory**
- Save hunt notes in `hunts/` folder
- Before each hunt: `grep -l "T1110" hunts/*.md` to check past hunts
- Share past hunt context with your AI assistant

**Level 3: Automate one task**
- Build a script that checks memory before generating hypothesis
- Or auto-fills execution reports from query results
- Or suggests similar past hunts

**Level 4-5: Agent orchestration**
- See `docs/` for architecture patterns (coming soon)

## What You Get

### Templates (`templates/`)
AI-ready templates for hunt hypotheses, execution reports, and queries. Designed to be:
- **Parseable by AI** - Structured markdown AI can read and write
- **Framework-agnostic** - Works with PEAK, SQRRL, or custom processes
- **Memory-first** - Captures lessons for future recall

### AI Prompts (`prompts/`)
- **hypothesis-generator.md** - Generate testable hypotheses from context
- **query-builder.md** - Draft safe, bounded queries
- **summarizer.md** - Document results and lessons learned

Copy these prompts into ChatGPT, Claude, or your AI tool.

### Example Hunt (`hunts/H-0001`)
Real-world example showing:
- How to structure hunt notes for AI parsing
- How to build memory through dated executions
- How lessons learned improve future hunts

### Memory System Guide (`metrics/`)
- Level 1-2: Grep-based memory (no additional tools)
- Level 3+: When to add structured memory (JSON, SQLite)
- Scaling guidance for 10, 50, 500+ hunts

## How ATHR Works With Your Framework

### Using PEAK + ATHR

PEAK's **Prepare → Execute → Act with Knowledge** maps naturally to LOCK:

| PEAK Phase | LOCK Step | AI Integration |
|------------|-----------|----------------|
| **Prepare** | Learn + Observe | AI drafts hypotheses (L1), recalls past hunts (L2) |
| **Execute** | Check | AI generates queries (L1), automates execution (L3) |
| **Act with Knowledge** | Keep | AI documents lessons, updates detections (L3-4) |

**LOCK is how AI understands your PEAK workflow.**

ATHR templates structure your Prepare/Execute/Act phases in LOCK format so agents can parse them.

### Using SQRRL + ATHR

SQRRL's **Hypothesis → Investigation → Pattern → Detection** also follows LOCK:

| SQRRL Phase | LOCK Step | AI Integration |
|-------------|-----------|----------------|
| **Hypothesis** | Learn + Observe | AI generates from context |
| **Investigation** | Check | AI builds queries, recalls similar hunts |
| **Pattern** | Keep (analysis) | AI identifies trends across hunts |
| **Detection** | Keep (action) | AI converts findings to rules |

**LOCK is the universal pattern.** SQRRL and PEAK both follow it—they just emphasize different aspects.

### Using Custom Methodology + ATHR

If you have your own process, map it to LOCK:

1. **What's your context input?** → Learn
2. **What's your testable statement?** → Observe
3. **How do you validate it?** → Check
4. **What do you capture?** → Keep

Structure your hunt notes in LOCK format, and AI can understand your methodology without custom training.

## Progression Guide

### Level 0 → 1: Add AI Assistance (Week 1)

**What to do:**
1. Copy `prompts/hypothesis-generator.md`
2. Fill in your context (CTI, alert, anomaly)
3. Paste into ChatGPT or Claude
4. Review and validate the output
5. Run your hunt as normal

**Signal you're ready for Level 2:** You have 10-20 completed hunt reports.

### Level 1 → 2: Add Memory (Week 4-8)

**What to do:**
1. Store hunt notes in `hunts/` folder (or Jira, Confluence, etc.)
2. Before each hunt, grep for similar hunts:
   ```bash
   grep -l "T1110.001" hunts/*.md  # Find by TTP
   grep -i "brute force" hunts/*.md  # Find by behavior
   ```
3. Include relevant past hunts in your AI prompt
4. AI now has memory context when drafting

**Signal you're ready for Level 3:** One task feels tedious (documentation, memory search, etc.)

### Level 2 → 3: Automate One Task (Month 3-6)

**What to do:**
1. Identify one repetitive task (e.g., "check memory before generating hypothesis")
2. Build a simple agent script:
   ```python
   # Example: Memory-aware hypothesis generator
   past_hunts = grep_hunts(ttp="T1110.001")
   context = f"Past hunts: {past_hunts}\nNew context: {user_input}"
   hypothesis = ai.generate(prompt=context)
   ```
3. Run the agent instead of manual AI prompting

**Signal you're ready for Level 4:** Grep is too slow (50+ hunts) or you need multiple hunts in parallel.

### Level 3 → 4: Multi-Agent Coordination (Month 6-12)

**What to do:**
1. Create structured memory (JSON index, SQLite, or markdown index)
2. Build specialized agents:
   - **Research agent**: Pulls threat intel and past hunts
   - **Query agent**: Generates queries from hypotheses
   - **Documentation agent**: Writes execution reports
3. Agents share access to central memory

**Signal you're ready for Level 5:** You want the system to learn what works.

### Level 4 → 5: Adaptive Learning (Year 1+)

**What to do:**
1. Implement weighted memory (successful hunts get higher priority)
2. Track metrics: hypothesis acceptance rate, time-to-detect, coverage
3. System suggests hypotheses based on past success patterns
4. Agents learn from outcomes to improve recommendations

**You might not need this level.** Level 2-3 is sufficient for most teams.

## What You'll Need From Your Tech Stack

ATHR is designed to work with what you already have. Here's what's required at each maturity level:

### Level 0-1: Manual + AI-Assisted
**Minimum requirements:**
- **Storage**: Any folder (local, SharePoint, Confluence, Jira, git)
- **SIEM Access**: Read-only query access to your SIEM (Splunk, Sentinel, Elastic, Chronicle)
- **AI Tool**: ChatGPT, Claude, or any LLM with copy/paste access
- **Skills**: Ability to write/edit markdown files

**That's it.** No APIs, no infrastructure, no code.

### Level 2: Informed (Memory)
**Additional requirements:**
- **Grep/Search**: Command line or file search tool (built into every OS)
- **Storage Pattern**: Consistent file naming (e.g., `H-0001_2025-01-15.md`)

**Still no coding required.** Just disciplined file organization.

### Level 3: Automated (Single Agent)
**Additional requirements:**
- **Programming**: Basic Python or scripting skills
- **AI API**: OpenAI API, Anthropic API, or Azure OpenAI endpoint
- **Environment**: Python 3.8+ with pip/conda
- **Budget**: ~$5-50/month for API calls (depending on usage)

**Infrastructure:**
- Everything runs on your laptop or a single VM
- No databases, no orchestration platforms needed yet

### Level 4: Coordinated (Multi-Agent)
**Additional requirements:**
- **Structured Memory**: SQLite (file-based) or PostgreSQL (if team needs shared access)
- **Agent Framework**: LangChain, AutoGen, or custom orchestration
- **Infrastructure**: Dedicated VM or container (2-4 CPU, 8GB RAM)
- **Budget**: ~$50-200/month for API calls

**Optional but helpful:**
- CI/CD pipeline (GitHub Actions, GitLab CI) for agent deployments
- Monitoring (logs, metrics) for agent performance
- Queue system (Redis, RabbitMQ) if running many parallel hunts

### Level 5: Adaptive (Learning)
**Additional requirements:**
- **Data Pipeline**: ETL for hunt metrics and outcomes
- **ML Infrastructure**: Vector database (Chroma, Pinecone) or embeddings store
- **Analytics**: Ability to track success rates, time-to-detect, coverage metrics
- **Budget**: ~$200-1000/month depending on scale

**This is rare.** Most teams stop at Level 3-4.

## Integration Patterns

### Storage Options
| Storage | Best For | Grep Support | Team Collaboration |
|---------|----------|--------------|-------------------|
| **Git** | Teams, version control | ✅ Native | ✅ Pull requests |
| **Local Folders** | Solo hunters | ✅ Native | ❌ No |
| **SharePoint/Confluence** | Enterprise compliance | ⚠️ Via export | ✅ Comments |
| **Jira/ServiceNow** | Integration with tickets | ⚠️ Via export | ✅ Workflows |
| **Notion/Obsidian** | Knowledge management | ✅ Search API | ✅ Sharing |

**Recommendation:** Start with git (free, grep-friendly, team-ready). Export to other tools as needed.

### AI Tools by Level
| Level | Tool | Cost | Skills Required |
|-------|------|------|-----------------|
| **1-2** | ChatGPT/Claude | $0-20/mo | Copy/paste |
| **1-2** | GitHub Copilot | $10/mo | Code editor |
| **3** | OpenAI/Anthropic API | $5-50/mo | Basic Python |
| **4** | LangChain/AutoGen | $50-200/mo | Python + orchestration |
| **5** | Custom ML pipeline | $200+/mo | ML engineering |

### SIEM Integration
ATHR works with any SIEM that supports query languages:

| SIEM | Query Language | Agent Integration |
|------|----------------|-------------------|
| **Splunk** | SPL | ✅ SDK available |
| **Microsoft Sentinel** | KQL | ✅ Azure SDK |
| **Elastic** | EQL/Lucene | ✅ Python client |
| **Chronicle** | YARA-L | ✅ API available |
| **Custom** | SQL/custom | ⚠️ Build adapter |

Templates are query-language agnostic. Agents can be trained on your SIEM's specific syntax.

## Philosophy

ATHR is a **framework for building agentic capability**, not a replacement for hunting methodologies.

**ATHR's thesis:**
Threat hunting becomes more effective when systems can:
1. **Remember** - Recall past hunts to avoid duplication and apply lessons
2. **Learn** - Identify patterns in what works and what doesn't
3. **Decide** - Act autonomously on validated patterns with appropriate constraints

**How ATHR achieves this:**
- **LOCK Pattern** - Standardizes hunt documentation for AI parsing
- **Memory Design** - Scalable architecture from grep to weighted systems
- **Maturity Levels** - Pragmatic progression path (don't over-engineer early)
- **Agent Patterns** - Practical examples for single-agent → multi-agent → learning systems

**Use ATHR when:**
- You want AI to assist or automate hunting tasks
- You need memory across hunts (avoid duplicates, apply lessons)
- You're building toward agent-driven hunting operations
- You want to make your hunting program learnable by machines

## Three Rules for Agentic Hunting

1. **Validate AI output** - Never run AI-generated queries without review
2. **Build memory first** - Agents without memory repeat mistakes
3. **Progress gradually** - Level 2 is better than Level 0, even if you never reach Level 5

## Examples

### Level 1: AI-Assisted Hypothesis

```
User → AI Prompt:
"I received a CTI report about APT29 using base64-encoded PowerShell.
Generate a threat hunting hypothesis following the template."

AI → Response:
"Adversaries use base64-encoded PowerShell commands to establish
persistence on Windows servers via scheduled tasks or WMI."

User → Validates and runs hunt
```

### Level 2: AI with Memory

```
User → Grep:
grep -l "T1059.001" hunts/*.md

Results: H-0015_2024-12-03.md, H-0023_2025-01-10.md

User → AI Prompt:
"Past hunts found this TTP mostly in scheduled tasks. Generate a
hypothesis for PowerShell persistence, excluding scheduled tasks."

AI → Response (informed by past hunts):
"Adversaries use base64-encoded PowerShell via WMI event consumers..."
```

### Level 3: Single Agent Automation

```python
# Memory-aware hypothesis generator agent
def generate_hypothesis(ttp, new_context):
    # Agent automatically checks memory
    past_hunts = search_hunts(ttp=ttp)

    # Agent drafts hypothesis with memory context
    prompt = f"""
    Past hunts for {ttp}:
    {past_hunts}

    New context: {new_context}

    Generate a hypothesis that doesn't duplicate past hunts.
    """

    return ai.generate(prompt)
```

### Level 4: Multi-Agent Workflow

```python
# Orchestrated agent workflow
research_agent.gather_intel(ttp="T1110.001")
memory_agent.find_similar_hunts(ttp="T1110.001")
hypothesis_agent.generate(context=research + memory)
query_agent.build_query(hypothesis)
# Human reviews and executes
docs_agent.document_results(findings)
```

## Why LOCK Matters for AI

Every hunting framework follows the same core logic:
1. Gather context
2. Form hypothesis
3. Test it
4. Learn from results

But each framework uses different terminology:
- PEAK: Prepare → Execute → Act
- SQRRL: Hypothesis → Investigation → Pattern
- TaHiTI: Plan → Hunt → Report

**This inconsistency makes it hard to train AI.**

LOCK solves this by providing a universal structure. When you document hunts in LOCK format:
- AI can parse hunt notes from any framework
- Memory recall works across methodologies
- Agents don't need framework-specific training

**LOCK is the API between human hunting frameworks and AI agents.**

## Relationship to Existing Frameworks

| Framework | Focus | Answers | Complements ATHR? |
|-----------|-------|---------|-------------------|
| **PEAK** | Hunting process (Prepare → Execute → Act) | "How should teams hunt systematically?" | ✅ Yes - ATHR adds memory + agents |
| **SQRRL** | Hypothesis-driven operations | "How do we validate threat hypotheses?" | ✅ Yes - ATHR structures for AI parsing |
| **TaHiTI** | Team coordination & collaboration | "How do hunt teams work together?" | ✅ Yes - ATHR adds agent automation |
| **ATHR** | Agentic capability (Manual → Autonomous) | "How do we make hunting remember and learn?" | Standalone or layered |

**ATHR is a parallel framework with a different concern:**
- **PEAK/SQRRL/TaHiTI**: *Process frameworks* (how humans hunt)
- **ATHR**: *Capability framework* (how systems become agentic)

**Used together:** PEAK for your hunting process + ATHR for memory/automation
**Used standalone:** ATHR's LOCK pattern is sufficient for simple operations

## FAQ

**Q: Do I need to use your templates?**
No. Use your own templates with ATHR prompts and memory patterns.

**Q: Does ATHR require agents/automation?**
No. Level 1-2 (AI-assisted + memory) work with just ChatGPT and grep. No coding required.

**Q: Can I use ATHR without PEAK/SQRRL?**
Yes. ATHR works with any hunting process. The maturity model is methodology-agnostic.

**Q: Is this just "use ChatGPT for threat hunting"?**
No. ATHR provides:
- Structured templates AI can parse consistently
- Memory system so AI doesn't repeat hunts
- Progression from assistance to autonomy
- Patterns for multi-agent coordination

**Q: Where's the agent code?**
Level 1-2 need no code (just prompts + grep). Level 3+ examples coming in `docs/` and `examples/`.

## Questions?

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for adoption strategies
- Review [prompts/README.md](prompts/README.md) for AI workflow guidance
- Review the templates and example hunt (H-0001)
- Open a discussion to share your agentic hunting setup

## License

MIT License - Use freely, adapt completely, keep your data private.

---

**ATHR: The memory and automation layer for threat hunting.**

Works with your methodology. Grows with your maturity. Stays out of your way.
