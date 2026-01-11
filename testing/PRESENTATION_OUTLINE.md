# ATHF Presentation/Demo Outline

**Target Audience:** Security teams, threat hunters, SOC managers, security architects  
**Duration:** 45 minutes (including demo)  
**Format:** Live presentation with interactive demo

---

## 1. Opening & Problem Statement (4 minutes)

### The Memory Problem
- **Context:** Most threat hunting programs lose valuable context
- **Pain Points:**
  - Hunt notes scattered across Slack, tickets, personal notes
  - Queries written once, never reused or refined
  - Lessons learned exist only in analysts' heads
  - AI tools start from zero every time
  - Teams repeat work: "Have we hunted this before?"

### The Cost of Memory Loss
- **Time wasted:** Re-hunting the same TTPs
- **Knowledge gaps:** New team members can't access past work
- **Missed opportunities:** Can't build on previous findings
- **AI limitations:** Tools can't learn from your environment

**Transition:** "What if your hunts had memory? What if AI could recall every past investigation?"

---

## 2. Introducing ATHF (4 minutes)

### What is ATHF?
- **Agentic Threat Hunting Framework** - The memory and automation layer for threat hunting
- **Core value:** Structure, persistence, and context for your hunts
- **Philosophy:** Works with any methodology (PEAK, TaHiTI, custom) - not a replacement

### Key Features
- ✅ **Markdown-based** - Simple, version-controlled, human-readable
- ✅ **LOCK pattern** - Structured documentation (Learn → Observe → Check → Keep)
- ✅ **AI-ready** - Context files enable AI assistants to understand your environment
- ✅ **Tool-agnostic** - Works with Splunk, Elastic, Chronicle, any SIEM/EDR
- ✅ **Progressive maturity** - Start simple, scale as needed

### What ATHF Is NOT
- ❌ Not a SIEM or detection platform
- ❌ Not a replacement for your existing hunting methodology
- ❌ Not a commercial product - it's a framework to adopt and customize

**Visual:** Show repository structure (hunts/, templates/, knowledge/, integrations/)

---

## 3. The LOCK Pattern (6 minutes)

### The Four Phases

#### Learn: Gather Context
- Threat intelligence, alerts, anomalies
- Available data sources
- MITRE ATT&CK techniques

#### Observe: Form Hypothesis
- Specific adversary behavior
- Why it's suspicious
- What makes it detectable

#### Check: Test Hypothesis
- Bounded queries with time limits
- Document data sources
- Iterative refinement

#### Keep: Record Findings
- Results (true positives, false positives)
- Lessons learned
- Next steps

### Example Hunt Walkthrough
**Show:** H-0001 (macOS Information Stealer) or H-0002 (Linux Crontab Persistence)
- Walk through each LOCK section
- Show query evolution (iteration 1 → 2 → 3)
- Highlight lessons learned

**Key Message:** "Every hunt becomes part of your program's memory"

---

## 4. The Five Levels of Maturity (7 minutes)

### Overview
**Most teams will live at Levels 1-2. Everything beyond is optional maturity.**

| Level | Capability | Time to Implement | What You Get |
|-------|-----------|-------------------|--------------|
| **0** | Ad-hoc | Current state | Hunts in Slack/tickets |
| **1** | Documented | 1 day | Persistent hunt records |
| **2** | Searchable | 1 week | AI reads and recalls hunts |
| **3** | Generative | 2-4 weeks | AI executes queries via tools |
| **4** | Agentic | 1-3 months | Autonomous agents monitor and act |

### Level 1: Documented Hunts
- **What:** Document hunts using LOCK in markdown
- **Benefit:** Persistent, searchable history
- **Example:** Show `hunts/H-0001.md` structure

### Level 2: Searchable Memory
- **What:** Add AGENTS.md and knowledge files
- **Benefit:** AI can read your repo and recall past hunts
- **Example:** "What have we learned about T1003.001?" → AI searches hunts automatically

### Level 3: Generative Capabilities
- **What:** Connect MCP servers (Splunk, CrowdStrike, etc.)
- **Benefit:** AI executes queries directly, enriches findings
- **Example:** AI runs Splunk query, looks up IOCs, creates tickets

### Level 4: Agentic Workflows
- **What:** Autonomous agents monitor CTI, generate hunts
- **Benefit:** You validate and approve, agents do the work
- **Example:** CTI Monitor → Hypothesis Generator → Validator → Notifier

**Visual:** Show maturity progression diagram

---

## 5. 🎯 LIVE DEMO (15 minutes)

### Demo Setup
- **Environment:** Live repository (or prepared demo repo)
- **Tools:** Terminal, code editor, AI assistant (Claude Code/Cursor)
- **Scenario:** Create a new hunt from threat intelligence

### Demo Flow

#### Part 1: Level 1 - Creating a Hunt (2.5 minutes)
1. **Show CLI:** `athf hunt new --technique T1110.001 --title "SSH Brute Force"`
2. **Show generated file:** Walk through LOCK structure
3. **Fill in Learn section:** Add threat intel context
4. **Fill in Observe section:** Form hypothesis
5. **Fill in Check section:** Add query
6. **Fill in Keep section:** Document results

#### Part 2: Level 2 - AI Search & Recall (3.5 minutes)
1. **Ask AI:** "What hunts have we done for credential access?"
2. **Show AI searching:** `athf hunt search "credential"` or AI reading hunts/
3. **Ask AI:** "Generate a hypothesis for T1003.001 based on our past hunts"
4. **Show AI response:** References past hunts, applies lessons learned
5. **Show context loading:** `athf context --tactic credential-access`

#### Part 3: Level 3 - AI Query Execution (4 minutes)
1. **Ask AI:** "Search for SSH brute force attempts in the past hour"
2. **Show AI executing:** Via Splunk MCP (if available) or showing query
3. **Show results:** AI analyzes and presents findings
4. **Show enrichment:** AI looks up IOCs, correlates threat intel
5. **Show automation:** AI updates hunt file with results

#### Part 4: Level 4 - Autonomous Agents (2 minutes)
1. **Show agent workflow:** CTI Monitor → Hypothesis Generator
2. **Show generated hunt:** Agent-created `H-XXXX.md` draft
3. **Show validation:** Agent checks query against data sources
4. **Show notification:** Slack/email alert for human review

### Demo Takeaways
- ✅ **Level 1:** Simple documentation in minutes
- ✅ **Level 2:** AI instantly recalls past work
- ✅ **Level 3:** AI executes queries, saves time
- ✅ **Level 4:** Agents work autonomously

**Note:** Adjust demo based on available tools and time constraints

---

## 6. Real-World Results (3 minutes)

### Showcase Examples
**Reference:** SHOWCASE.md examples

#### Hunt #1: macOS Information Stealer
- **Result:** 1 true positive, 0 false positives
- **Time to detection:** 2 minutes
- **Impact:** Prevented exfiltration of 47 documents + credentials

#### Hunt #2: Linux Crontab Persistence
- **Result:** 1 true positive (cryptominer), 1 false positive
- **Time to detection:** 30 minutes
- **Impact:** Prevented $200/month in cloud compute costs

#### Hunt #3: AWS Lambda Persistence
- **Result:** 2 true positives, 0 false positives
- **Time to detection:** 3 minutes
- **Impact:** Prevented full AWS account compromise

### Key Metrics
- **Query refinement:** 3 iterations average (247 → 12 → 1 result)
- **False positive reduction:** 99%+ after refinement
- **Time saved:** 45+ minutes per hunt with AI assistance
- **Coverage improvement:** Identified gaps, filled them systematically

---

## 7. Getting Started (3 minutes)

### Quick Start Options

#### Option A: CLI-Enabled (Recommended)
```bash
pip install agentic-threat-hunting-framework
athf init
athf hunt new --technique T1003.001
```

#### Option B: Markdown-Only
```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cp templates/HUNT_LOCK.md hunts/H-0001.md
# Customize and document
```

### Implementation Path
1. **Week 1:** Document 5-10 hunts (Level 1)
2. **Week 2-4:** Add AGENTS.md, test AI integration (Level 2)
3. **Month 2-3:** Connect tools, enable query execution (Level 3)
4. **Month 3-6:** Deploy agents for automation (Level 4)

### Customization
- **Adapt templates** to your environment
- **Customize AGENTS.md** with your data sources
- **Fork and modify** - make it yours
- **Works with any methodology** - layer over PEAK, SQRRL, etc.

**Visual:** Show customization examples (environment.md, AGENTS.md)

---

## 8. Architecture & Integration (2 minutes)

### Repository Structure
```
athf/
├── hunts/          # Hunt documentation (H-XXXX.md)
├── templates/     # LOCK templates
├── knowledge/     # Domain expertise
├── integrations/  # MCP servers, tool integrations
├── queries/       # Query implementations
└── AGENTS.md      # AI context file
```

### Integration Options
- **MCP Servers:** Splunk, CrowdStrike, Jira, MISP
- **APIs:** Any tool with REST API
- **Custom:** Build your own integrations

### Tool Compatibility
- ✅ **SIEM:** Splunk, Elastic, Chronicle, Sentinel
- ✅ **EDR:** CrowdStrike, SentinelOne, Defender
- ✅ **Ticketing:** Jira, ServiceNow, GitHub Issues
- ✅ **Threat Intel:** MISP, VirusTotal, OTX

**Key Message:** "Bring your own tools - ATHF works with what you have"

---

## 9. Q&A & Next Steps (1 minute)

**Note:** With tight timing, consider taking questions throughout the presentation or extending if demo finishes early.

### Common Questions (Quick Reference)
- **Q:** Do I need to implement all levels?
  - **A:** No. Most teams live at Levels 1-2. Levels 3-4 are optional.

- **Q:** How long to get started?
  - **A:** Level 1 in a day, Level 2 in a week.

- **Q:** Can I use with PEAK/TaHiTI?
  - **A:** Yes! ATHF adds memory layer, doesn't replace methodology.

- **Q:** Do I need the CLI?
  - **A:** No. CLI is optional convenience. Markdown works without it.

- **Q:** Is this a commercial product?
  - **A:** No. Open-source framework - fork, customize, make it yours.

### Resources & Next Steps
- **GitHub:** https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
- **Quick Start:** `pip install agentic-threat-hunting-framework && athf init`
- **Documentation:** docs/getting-started.md
- **Examples:** hunts/ directory, SHOWCASE.md

**Action Items:**
1. Document one hunt in LOCK format (Level 1)
2. Add AGENTS.md for AI integration (Level 2)
3. Questions? GitHub Discussions or reach out directly

---

## Appendix: Backup Slides

### Advanced Topics (if time permits)
- Multi-agent coordination patterns
- Custom agent development
- Integration with detection-as-code pipelines
- Metrics and success measurement

### Troubleshooting
- Common setup issues
- CLI installation problems
- AI context file configuration
- MCP server setup

### Comparison with Other Frameworks
- ATHF vs. PEAK (methodology vs. memory layer)
- ATHF vs. HEARTH (format vs. framework)
- ATHF vs. commercial platforms (framework vs. product)

---

## Presentation Tips

### Visual Aids
- **Slide deck:** Use framework diagrams, maturity model, LOCK pattern
- **Live coding:** Terminal + code editor for demo
- **Screenshots:** Show example hunts, AI interactions
- **Diagrams:** Repository structure, agent workflows

### Demo Preparation
- **Pre-setup:** Have demo environment ready
- **Backup plan:** Recorded demo if live fails
- **Time management:** Keep demo focused, skip advanced features if needed
- **Interactive:** Encourage questions during demo
- **⚠️ 45-minute constraint:** Demo is priority - if running behind, shorten intro sections, not demo

### Engagement
- **Start with pain:** Memory loss resonates with all teams
- **Show, don't tell:** Demo is the most powerful part
- **Real examples:** Use actual hunts from showcase
- **Progressive disclosure:** Build from simple to complex

---

## Time Allocation Summary

| Section | Duration | Notes |
|---------|----------|-------|
| Opening & Problem | 4 min | Hook audience |
| Introducing ATHF | 4 min | Core concepts |
| LOCK Pattern | 6 min | Foundation |
| Maturity Model | 7 min | Progression |
| **🎯 LIVE DEMO** | **15 min** | **KEY SECTION** |
| Real-World Results | 3 min | Proof points |
| Getting Started | 3 min | Action items |
| Architecture | 2 min | Technical details |
| Q&A | 1 min | Quick wrap-up |
| **Total** | **45 min** | Tight timing - demo is priority |

---

**Remember:** The demo is the most impactful part. With 45 minutes total, prioritize the demo - if you're running behind schedule, shorten the intro sections rather than cutting demo time.

**Time Management Tips:**
- **Stick to timings:** Use a timer, especially for demo section
- **Skip if needed:** Architecture section can be shortened or skipped if behind
- **Q&A flexibility:** Can extend Q&A if demo finishes early, or cut short if needed
- **Demo priority:** 15 minutes for demo is non-negotiable - it's the proof point
