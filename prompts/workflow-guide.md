# AI-Assisted Threat Hunting Workflow Guide

**Level:** 2 (Augmented) - AI with Memory
**Audience:** Threat hunters using Claude Code, GitHub Copilot, Cursor, or similar AI tools
**Prerequisites:** Completed Level 1 (have hunt repository with AGENTS.md)

---

## Overview

This guide provides step-by-step workflows for using AI tools to accelerate threat hunting while maintaining quality and safety. Each workflow follows the LOCK pattern and leverages repository memory.

**Expected Time Savings:** 70-80% reduction in documentation and research time

---

## Setup (One-Time)

### Step 1: Choose Your AI Tool

| Tool | Best For | Cost | Setup Link |
|------|----------|------|------------|
| **Claude Code** | Deep code/doc analysis, long context | ~$20/mo | [docs.anthropic.com/claude-code](https://docs.anthropic.com/claude/docs/claude-code) |
| **GitHub Copilot** | GitHub integration, inline suggestions | ~$10/mo | [docs.github.com/copilot](https://docs.github.com/en/copilot) |
| **Cursor** | Full IDE experience, chat + completions | ~$20/mo | [cursor.sh](https://cursor.sh/docs) |

**Recommendation:** Start with whatever your organization already licenses. All work well with ATHF.

### Step 2: Open Your Hunt Repository

```bash
cd /path/to/your/hunt/repository
code .  # VS Code + Copilot/Cursor
# OR
# Open in your AI-enabled editor
```

### Step 3: Verify AI Can Read Files

Test AI access:
```
You: "Read AGENTS.md and summarize what data sources we have"
AI: [Should list your SIEM, EDR, and other sources from AGENTS.md]
```

If AI can't read files, check:
- File permissions
- AI tool settings (some require explicit folder access)
- Workspace configuration

---

## Core Workflows

### Workflow 1: Threat Intel-Driven Hunt (Most Common)

**Scenario:** You receive threat intelligence about adversary TTPs or emerging attack patterns

**Total Time:** 5-10 minutes

#### Step 1: Check Memory (2 min)

**What to ask:**
```
Check if we've hunted T1003.001 (LSASS credential dumping) before. Search:
1. hunts/ folder for this TTP
2. Any related past hunts for credential dumping behaviors
3. Lessons learned from similar hunts
```

**Expected Response:**
- "No past hunts found for this TTP" → Proceed to Step 2
- "Found H-0022 which hunted this 6 months ago" → Review that hunt first, then proceed

**Why this matters:** Avoids duplicate work, applies lessons learned, reuses false positive filters

#### Step 2: Validate Environment (1 min)

**What to ask:**
```
Read environment.md and tell me:
1. Do we have visibility into this behavior?
2. What data sources can we use to hunt this TTP?
3. Any telemetry gaps that would limit this hunt?
```

**Expected Response:**
- Lists relevant data sources (e.g., "Yes, you have Sysmon Event ID 10 for process access")
- Identifies specific indexes/tables (e.g., "You can use index=winlogs and index=edr")
- Flags gaps (e.g., "Note: No command-line logging on legacy servers")

**Decision point:** If critical telemetry is missing, document gap and reconsider hunt feasibility

#### Step 3: Generate Hypothesis (2 min)

**What to ask:**
```
Generate a LOCK-structured hypothesis for T1003.001 (LSASS credential dumping).
Use the system prompt from prompts/hypothesis-generator-v2.md.
This is a proactive hunt (not incident response).
```

**Expected Response:**
- Complete hypothesis in LOCK format
- References YOUR data sources from environment.md
- Includes past hunt lessons if applicable (especially FP filters)
- Suggests time range and query approach

**Review checklist:**
- [ ] Hypothesis is testable and specific
- [ ] Data sources match environment.md
- [ ] Time range is reasonable and bounded
- [ ] ATT&CK mapping is correct

#### Step 4: Create Hunt File (1 min)

**What to ask:**
```
Create this hypothesis as H-XXXX.md in the hunts/ folder.
[Specify the next available hunt number, e.g., H-0025]
```

**AI will:** Create the file with properly formatted markdown

**Verify:** File exists at `hunts/H-XXXX.md`

#### Step 5: Generate Query (2-3 min)

**What to ask:**
```
Based on this hypothesis, generate a Splunk query with:
1. Time bounds (last 14 days as specified in hypothesis)
2. Result limits (head 1000)
3. False positive filters from past similar hunts
4. Save as queries/H-XXXX.spl
```

**Expected Response:**
- Safe, bounded query
- Includes FP filters if applicable (e.g., exclude monitoring tools)
- Comments explaining query logic and thresholds

**Review checklist:**
- [ ] Has time bounds (`earliest=-14d`)
- [ ] Has result limit (`| head 1000`)
- [ ] No expensive operations without justification
- [ ] Test query is syntactically valid

**Total time: 5-10 minutes (vs. 20-30 minutes manual)**

---

### Workflow 2: Anomaly Investigation

**Scenario:** SOC alerts you to unusual behavior

**Total Time:** 3-5 minutes

#### Quick Response Steps:

**1. Rapid Context Gathering (1 min)**
```
You: "Search past hunts for [behavior/TTP]. What have we learned about false positives?"
AI: [Summarizes past findings]
```

**2. Incident-Driven Hypothesis (2 min)**
```
You: "Generate incident-response hypothesis for this anomaly:
[paste anomaly description]
Mark as HIGH priority, this is active investigation."
AI: [Generates time-sensitive hypothesis with immediate actions]
```

**3. Immediate Query (1 min)**
```
You: "Draft query for last 24 hours with these specific indicators:
[IOCs from anomaly]
Make it fast - this is incident response."
AI: [Generates focused query for immediate execution]
```

**4. Document As You Go (ongoing)**
```
You: "I'm pasting my query results. Summarize findings in LOCK format for H-XXXX_2024-10-31.md"
AI: [Formats results as execution report]
```

**Key Difference:** Speed over perfection. Document quickly, refine later.

---

### Workflow 3: Proactive TTP Hunting

**Scenario:** Monthly hunt plan, covering MITRE ATT&CK techniques

**Total Time:** 10-15 minutes per hunt

#### Step 1: Coverage Gap Analysis (3 min)

**What to ask:**
```
Analyze our past hunts and tell me:
1. Which tactics have we hunted most/least?
2. What high-priority TTPs have we never covered?
3. Suggest 3 hunts to improve ATT&CK coverage

Consider our environment (read environment.md for tech stack).
```

**Expected Response:**
- Coverage analysis by tactic
- List of never-hunted TTPs relevant to your environment
- Prioritized hunt suggestions

#### Step 2: Select TTP and Research (2 min)

**What to ask:**
```
I want to hunt T1003 (Credential Dumping).
Search past hunts for similar techniques and summarize:
1. What sub-techniques we've covered
2. What sub-techniques we haven't covered
3. Lessons learned about false positives
```

**Expected Response:**
- Past coverage breakdown
- Recommended focus area
- FP patterns to avoid

#### Step 3: Generate Hypothesis (3 min)

Follow Workflow 1, Step 3 (same process)

#### Step 4: Peer Review with AI (2 min)

**What to ask:**
```
Review this hypothesis and critique:
1. Is it testable? Too vague?
2. Are we likely to get high false positives?
3. Is the time range appropriate?
4. What could go wrong with this query?
```

**Expected Response:**
- Constructive critique
- Suggestions for improvement
- Risk assessment

**Iterate:** Refine based on feedback

---

### Workflow 4: Post-Hunt Documentation

**Scenario:** You've executed a hunt and have results

**Total Time:** 5-7 minutes

#### Step 1: Results Summarization (3 min)

**What to ask:**
```
I'm pasting my query results from H-XXXX. Analyze and create:
1. Summary of findings (how many results, patterns observed)
2. True positives vs false positives breakdown
3. Any interesting anomalies worth investigating
4. Recommendations for next actions

[paste query output - first 100 rows if large dataset]
```

**Expected Response:**
- Executive summary of results
- TP/FP analysis
- Recommended follow-up

#### Step 2: Create Execution Report (2 min)

**What to ask:**
```
Using the analysis above, create H-XXXX_2024-10-31.md following the HUNT_EXECUTION template.
Include:
- Query details (runtime, rows returned)
- Findings summary
- Analysis (TPs, FPs, gaps)
- Decision (Accept/Reject/Needs Changes)
- Lessons learned
```

**AI will:** Generate complete execution report

**Review:** Validate findings accuracy, add any missed insights

#### Step 3: Update Hypothesis (if needed) (1 min)

**What to ask:**
```
Based on these results, should we update H-XXXX.md status?
[If found issues] What changes to the hypothesis would improve detection?
```

**Expected Response:**
- Status update recommendation
- Hypothesis refinements if needed

---

## Advanced Workflows

### Workflow 5: Bulk Hypothesis Generation

**Scenario:** Planning next month's hunts

**What to ask:**
```
Generate 5 hypothesis candidates for next month based on:
1. TTPs we haven't covered recently (check past 90 days in hunts/)
2. Recent threat intelligence and security advisories
3. Our threat model (focus on [specify: ransomware, insider threat, etc.])

For each, provide:
- One-sentence hypothesis
- Justification (why this, why now)
- Estimated effort (Quick/Medium/Complex)
```

**Expected Response:**
- 5 prioritized hunt candidates
- Rationale for each
- Effort estimates

**Next step:** Review with team, select top 3, then use Workflow 1 to fully develop

---

### Workflow 6: Hunt Improvement

**Scenario:** Past hunt had too many false positives

**What to ask:**
```
Read H-XXXX and H-XXXX_2024-10-15.md. The hunt found 500 results but 95% were false positives.

Help me refine:
1. What patterns are causing FPs? (analyze results)
2. Suggest query filters to reduce FPs
3. Should we narrow the hypothesis?
4. Generate updated query in queries/H-XXXX_v2.spl
```

**Expected Response:**
- FP pattern analysis
- Suggested filters
- Refined query
- Updated hypothesis if needed

---

## Tool-Specific Tips

### Claude Code

**Strengths:**
- Long context window (great for reading many past hunts)
- Deep analysis capabilities
- Good at explaining reasoning

**Best practices:**
```
✓ Ask for explanations: "Explain why you chose this approach"
✓ Use multi-step requests: "First search, then analyze, then generate"
✓ Reference specific files: "Based on H-0015.md, generate similar hypothesis"
```

### GitHub Copilot

**Strengths:**
- Inline suggestions while typing
- GitHub integration
- Fast responses

**Best practices:**
```
✓ Use Copilot Chat for complex requests
✓ Type hypothesis outline, let Copilot complete
✓ Use inline suggestions for query writing
```

### Cursor

**Strengths:**
- Full IDE experience
- Can edit multiple files
- Code-aware suggestions

**Best practices:**
```
✓ Use Cmd+K for inline edits
✓ Use chat for analysis, inline for writing
✓ Multi-file editing for creating hunt + query + docs simultaneously
```

---

## Common Pitfalls and Solutions

### Pitfall 1: AI Doesn't Remember Past Hunts

**Symptom:** AI suggests hunts you've already done

**Solution:**
- Explicitly ask to search first: "Search hunts/ before suggesting"
- Reference AGENTS.md: "Follow the workflow in AGENTS.md"
- Use AI tools with file access (not just chat-based)

### Pitfall 2: AI Suggests Unrealistic Hunts

**Symptom:** Hypotheses for data sources you don't have

**Solution:**
- Keep environment.md updated
- Remind AI: "Only use data sources from environment.md"
- Review generated hypotheses against your actual capabilities

### Pitfall 3: Generic, Non-Testable Hypotheses

**Symptom:** "Adversaries may use PowerShell maliciously"

**Solution:**
- Ask for specificity: "Make this more specific and testable"
- Provide more context: "Focus on [specific behavior]"
- Use the enhanced prompt from hypothesis-generator-v2.md

### Pitfall 4: AI Forgets Context Mid-Conversation

**Symptom:** AI loses track of what you're working on

**Solution:**
- Use AGENTS.md for persistent context
- Summarize periodically: "We're working on H-0025 (SSH brute force)"
- Keep conversations focused (one hunt per chat session)

### Pitfall 5: Blindly Trusting AI Output

**Symptom:** Running queries without review, accepting all suggestions

**Solution:**
- ALWAYS review queries before running
- Validate data sources against environment.md
- Check ATT&CK mappings
- Test on small time windows first

---

## Quality Checklist

Before finalizing any AI-generated content:

### Hypothesis Quality
- [ ] Specific and testable (not vague)
- [ ] References actual data sources from environment.md
- [ ] Has bounded time range
- [ ] Correct ATT&CK technique mapping
- [ ] Considers false positive rate
- [ ] Builds on past work (if applicable)

### Query Safety
- [ ] Has time bounds (`earliest=-Xd`)
- [ ] Has result limits (`| head N`)
- [ ] No expensive operations without justification
- [ ] Tested for syntax errors
- [ ] Includes comments explaining logic

### Documentation Completeness
- [ ] Hypothesis file (H-XXXX.md) created
- [ ] Query file (queries/H-XXXX.spl) created
- [ ] Execution report (H-XXXX_DATE.md) after hunt
- [ ] Lessons learned captured

---

## Measuring Success

Track these metrics to assess AI tool effectiveness:

**Time Savings:**
- Time to generate hypothesis: Manual (15-20 min) → AI (3-5 min)
- Time to document results: Manual (20-30 min) → AI (5-7 min)
- Total workflow: Manual (45+ min) → AI (10-15 min)

**Quality Improvements:**
- Consistency: Are all hunts following LOCK format?
- Completeness: Are lessons learned captured every time?
- Learning: Are new hunts referencing past hunts?

**Team Adoption:**
- How many team members using AI tools?
- Frequency of hunts (increased with AI assistance?)
- Quality of documentation (improved consistency?)

---

## Next Steps

### Just Starting (Week 1-2)
1. Use Workflow 1 (Threat Intel-Driven) for your next threat intelligence report
2. Compare time vs. manual process
3. Refine your environment.md based on what AI asks for

### Getting Comfortable (Month 1)
1. Try all core workflows
2. Experiment with different AI tools
3. Customize prompts for your team's needs
4. Train team members on workflows

### Advanced Usage (Month 2+)
1. Use bulk generation for hunt planning
2. Build custom prompts for your specific environment
3. Consider Level 3 automation for repetitive tasks
4. Share successful patterns with the ATHF community

---

## Troubleshooting

**Problem:** "AI tool says it can't access files"

**Solutions:**
- Check file permissions
- Verify workspace is open in AI tool
- Some tools require explicit file access grants
- Try reading specific file: "Read hunts/H-0001.md"

---

**Problem:** "AI generates incorrect ATT&CK mappings"

**Solutions:**
- Cross-reference with [attack.mitre.org](https://attack.mitre.org)
- Ask AI to explain: "Why did you choose T1234?"
- Correct and provide feedback: "Actually, this is T5678 because..."

---

**Problem:** "Generated queries don't match our SIEM syntax"

**Solutions:**
- Specify SIEM in request: "Generate Splunk SPL query" or "Generate KQL query"
- Update AGENTS.md with query language details
- Provide example query as reference
- Review and adjust syntax manually

---

## Resources

- **Enhanced Prompt:** [hypothesis-generator-v2.md](hypothesis-generator-v2.md)
- **Query Building:** [query-builder.md](query-builder.md)
- **Documentation:** [summarizer.md](summarizer.md)
- **Examples:** [../examples/cti-to-hypothesis/](../examples/cti-to-hypothesis/)
- **AGENTS.md:** Repository context file for AI

---

## Feedback

Found a workflow that works great? Have suggestions for improvement?

- Open an issue in the ATHF repository
- Share your success stories
- Contribute workflow improvements

**Remember: AI augments, doesn't replace. Always validate, always learn, always improve.**
