# AI Prompt Library

This folder contains prompts to help you accelerate threat hunting at different maturity levels.

---

## What's Here

### basic-prompts.md

**Level:** 0-1 (Manual/Documented)
**Use for:** Copy-paste prompts for ChatGPT, Claude, or other AI assistants

Contains three prompt templates:

1. **Generate Hypothesis** - From CTI, alerts, or anomalies
2. **Build Query** - Safe, bounded queries for Splunk, KQL, or Elastic
3. **Document Results** - Capture findings in LOCK format

**When to use:** You're working outside an AI-enabled IDE and need quick assistance with hypothesis generation, query building, or documentation.

---

### ai-workflow.md

**Level:** 2 (Searchable) - AI with Memory
**Use for:** AI tools that can read your repository (Claude Code, GitHub Copilot, Cursor)

Contains:

- System prompt for AI tools
- 4 core workflows (threat intel, anomaly investigation, proactive hunting, documentation)
- Complete example conversation showing AI reasoning
- Tool-specific tips and troubleshooting
- Quality checklists

**When to use:** You have AI tools with file access to your hunt repository and want them to search past hunts, validate against environment.md, and generate context-aware hypotheses.

---

## How to Choose

**Use basic-prompts.md if:**

- You're just getting started with AI-assisted hunting
- You don't have AI tool subscriptions yet
- You want simple copy-paste templates
- You're working in a web interface (ChatGPT, Claude.ai)

**Use ai-workflow.md if:**

- You have Claude Code, GitHub Copilot, or Cursor
- Your hunt repository has AGENTS.md, knowledge/hunting-knowledge.md, and documented past hunts
- You want AI to search memory, apply expert hunting frameworks, and apply lessons learned
- You're ready for more advanced workflows

---

## Quick Start

### Level 0-1: Basic Prompts

1. Open [basic-prompts.md](basic-prompts.md)
2. Copy the prompt template you need
3. Fill in your context (hypothesis, data sources, results)
4. Paste into ChatGPT, Claude, or your AI assistant
5. Review and refine the output

**Example:**

```
# You have threat intel about PowerShell abuse
→ Use "Generate Hypothesis" prompt from basic-prompts.md
→ Paste CTI report into context section
→ AI generates testable hypotheses
```

### Level 2: AI Workflows

1. Open your hunt repository in Claude Code, Copilot, or Cursor
2. Provide the system prompt from [ai-workflow.md](ai-workflow.md)
3. Ask AI to search past hunts before generating new ones
4. Follow the workflow guides for common scenarios

**Example:**

```
You: "Check if we've hunted T1003.001 before. Use the system prompt from prompts/ai-workflow.md"
AI: [Searches hunts/, reads environment.md, generates context-aware hypothesis]
```

---

## Safety Reminders

### AI Assistance ≠ Autopilot

- **Always review** AI-generated hypotheses for feasibility
- **Always test** AI-generated queries on small timeframes first
- **Always validate** that queries are safe and bounded
- **Use your judgment** - You know your environment better than AI

### Before Running Any AI-Generated Query

1. Check for time bounds (`earliest=-Xd`)
2. Check for result limits (`| head N` or `| take N`)
3. Test on 1-hour window before expanding to days
4. Verify it won't impact SIEM performance

---

## Platform-Specific Tips

**Splunk Users:**

- Mention "Splunk SPL" in your prompts
- Specify data models when available
- AI knows common Splunk patterns (tstats, eval, stats)

**KQL Users (Sentinel/Defender):**

- Mention "KQL for Sentinel" or "KQL for Defender"
- Specify table names (SecurityEvent, DeviceProcessEvents, etc.)
- AI understands Sentinel-specific syntax

**Elastic Users:**

- Mention "Elastic EQL" or "Lucene query"
- Specify index patterns
- Note which Elastic stack version you're using

---

## Next Steps

### After Using Basic Prompts

1. Document your hunts using [templates/HUNT_LOCK.md](../templates/HUNT_LOCK.md)
2. Create AGENTS.md in your repository (see main README)
3. Ensure knowledge/hunting-knowledge.md is present (included in repo by default)
4. Progress to Level 2 with ai-workflow.md

### After Level 2 Workflows

1. See real examples in [hunts/H-0001.md](../hunts/H-0001.md) and [hunts/H-0002.md](../hunts/H-0002.md)
2. Review format guidelines in [hunts/FORMAT_GUIDELINES.md](../hunts/FORMAT_GUIDELINES.md)
3. Consider Level 3 (MCP integrations) in [integrations/](../integrations/)

---

## Customizing for Your Environment

Feel free to modify these prompts:

- Add your organization's specific data sources
- Include your ATT&CK coverage gaps
- Reference your baseline automation
- Add your threat model priorities

---

## Contributing

Have a better prompt? Found a useful workflow?

- Submit a PR with your improvements
- Share what works in your environment
- Help others get started faster

---

**Remember: These prompts are training wheels. They help you get started faster, teach you the LOCK pattern, and over time you'll need them less. But they remain useful for complex hunts.**
