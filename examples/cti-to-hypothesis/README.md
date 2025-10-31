# CTI to Hypothesis - Real-World Examples

This folder contains complete, real-world examples showing how to use AI tools (Claude Code, GitHub Copilot, Cursor) with the ATHR framework to rapidly convert threat intelligence into actionable hunt hypotheses.

---

## What These Examples Show

Each example demonstrates:
- Complete conversation flow between human and AI
- Memory searches (checking past hunts)
- Environment validation (checking data sources)
- Hypothesis generation following LOCK pattern
- Query creation with safety bounds
- Human validation and refinement
- Time savings vs. manual process

**These are not toy examples** - they show realistic workflows with real decisions, trade-offs, and challenges.

---

## Examples

### 1. [from-cve.md](from-cve.md) - CVE-Driven Hunt

**Scenario:** CISA alert for CVE-2024-3094 (XZ Utils backdoor)

**Hunt Type:** Proactive, intelligence-driven

**Time:** 8 minutes (vs. 45+ minutes manual)

**Key Lessons:**
- How AI searches past hunts automatically
- Environment validation catches missing telemetry
- Human validation critical for query safety
- Past hunt lessons (H-0008, H-0021) applied automatically

**Best For:** Learning the standard CVE → hypothesis workflow

**Complexity:** ⭐⭐⭐ Medium

---

### 2. [from-apt-report.md](from-apt-report.md) - APT Campaign Hunt

**Scenario:** Threat intel report about APT29 targeting cloud infrastructure

**Hunt Type:** Intelligence-driven, multi-TTP campaign

**Time:** 12 minutes (vs. 90+ minutes manual)

**Key Lessons:**
- Scoping complex threat intel (5 TTPs → focus on 2)
- Pragmatic trade-offs (3-week plan → 2-day execution)
- IaC/automation false positive handling
- Baseline requirements (when needed vs. acceptable to skip)

**Best For:** Learning to handle complex threat intelligence

**Complexity:** ⭐⭐⭐⭐ Advanced

---

### 3. [from-anomaly.md](from-anomaly.md) - Incident Response

**Scenario:** SOC alert for VPN brute force (active attack)

**Hunt Type:** Incident response, time-critical

**Time:** 6 minutes (alert to containment)

**Key Lessons:**
- Speed over perfection in incident response
- AI provides instant baseline comparison
- Decision trees (IF compromise THEN escalate)
- Documentation during incident (not after)

**Best For:** Learning incident response workflows

**Complexity:** ⭐⭐ Easy (but high pressure)

---

## How to Use These Examples

### For Learning

1. **Read in order:** from-cve.md → from-apt-report.md → from-anomaly.md
   - Builds from simple to complex
   - Shows different hunt types

2. **Note the patterns:**
   - AI always searches past hunts first
   - Environment validation happens early
   - Human catches safety issues AI misses
   - Iteration and refinement is normal

3. **Try it yourself:**
   - Open your AI tool in your hunt repository
   - Find a recent CVE or alert
   - Follow the workflow from the examples
   - Compare your results

### For Reference

**When you receive a CVE alert:**
→ Use [from-cve.md](from-cve.md) as a template

**When threat intel shares an APT report:**
→ Use [from-apt-report.md](from-apt-report.md) for scoping guidance

**When SOC pages you about an anomaly:**
→ Use [from-anomaly.md](from-anomaly.md) for rapid response

### For Training

**Training new team members:**
1. Have them read all three examples
2. Practice with past CVEs (simulate the workflow)
3. Pair with experienced hunter on first real incident
4. Review their AI-generated hypotheses before execution

**Training AI to work better:**
- Show these examples to your AI tool
- Reference them: "Generate hypothesis like the CVE example"
- Use as templates for your organization's specific needs

---

## Common Patterns Across All Examples

### The AI Workflow (Consistent)

**Step 1: Check Memory**
- Search hunts/ for similar past work
- Check vulnerabilities.md for CVE status
- Reference lessons learned from past hunts

**Step 2: Validate Environment**
- Read environment.md for affected tech
- Verify data sources are available
- Identify telemetry gaps

**Step 3: Generate Hypothesis**
- LOCK-structured markdown
- References YOUR data sources
- Includes past hunt lessons
- Considers false positives

**Step 4: Create Queries**
- Safe, bounded queries
- Time limits and result caps
- False positive filters from past work

**Step 5: Documentation**
- Execution reports after hunt
- Lessons learned captured
- Follow-up hunts identified

### Human's Critical Role (Consistent)

**Validation:**
- Check query safety (time bounds, limits)
- Verify data sources are correct
- Validate ATT&CK mappings

**Context:**
- Provide threat intel details
- Clarify scope and urgency
- Make risk/effort trade-offs

**Decisions:**
- Accept/reject generated hypotheses
- Choose which TTPs to hunt first
- Determine execution timeline

**Refinement:**
- Request more specificity
- Add false positive filters
- Adjust for organizational constraints

---

## Time Savings Summary

| Hunt Type | Manual Time | AI-Assisted Time | Savings |
|-----------|-------------|------------------|---------|
| **CVE Hunt** | 45 min | 8 min | 82% |
| **APT Report** | 90 min | 12 min | 87% |
| **Incident Response** | 20-30 min | 6 min | 70-80% |

**Average time savings: 80%**

**What you do with saved time:**
- Execute more hunts (quantity)
- More thorough analysis (quality)
- Better documentation (learning)
- Follow-up hunts (depth)

---

## Key Success Factors

All three examples succeeded because:

1. **AGENTS.md exists** - Provides AI context about repo and environment
2. **Past hunts documented** - AI references H-0015, H-0008, etc. automatically
3. **environment.md complete** - AI validates against actual tech stack
4. **LOCK structure** - Consistent format AI understands
5. **Human validation** - AI generates, human validates and decides

**Without these:** AI would generate generic, unrealistic hypotheses.

**With these:** AI generates environment-specific, actionable hypotheses in minutes.

---

## Adapting for Your Organization

These examples show generic environments. For your organization:

### Customize environment.md
```markdown
## Data Sources (YOUR specifics)
- SIEM: Splunk Enterprise (index=winlogs, index=proxysg, index=firewall)
- EDR: CrowdStrike Falcon (API access, 14-day retention)
- Cloud: AWS only (CloudTrail to S3)
```

### Build Your Hunt History
- Document hunts in LOCK format
- Capture lessons learned (especially FPs)
- AI will automatically reference these

### Customize Prompts
- Add your organization's threat model to AGENTS.md
- Document your priority TTPs
- Include your naming conventions

### Train Your Team
- Share these examples in team wiki
- Practice on past CVEs (retroactive learning)
- Build team-specific examples (your environment, your past hunts)

---

## What's NOT in These Examples

**By Design, these examples skip:**
- Query execution results (varies by environment)
- Specific FP tuning (depends on your systems)
- Organizational approval processes (your workflow)
- Tool-specific setup (covered in workflow-guide.md)

**Why:** To keep examples portable and focused on the AI-assisted workflow, not environment-specific details.

---

## Troubleshooting

**Problem:** "My AI doesn't generate hypotheses like these examples"

**Solutions:**
1. Ensure AI can read your hunts/ folder and AGENTS.md
2. Use the enhanced prompt from `prompts/hypothesis-generator-v2.md`
3. Provide more context (threat intel details, urgency level)
4. Show AI these examples as reference

---

**Problem:** "AI generates hypotheses for data sources I don't have"

**Solutions:**
1. Check environment.md is complete and accurate
2. Explicitly remind AI: "Only use data sources from environment.md"
3. Update AGENTS.md with clearer data source definitions
4. After query generation, validate against your actual SIEM

---

**Problem:** "Time savings not as high as examples show"

**Possible Reasons:**
1. Learning curve (first few hunts take longer)
2. Complex environment (more validation needed)
3. Incomplete environment.md (AI asks more questions)
4. No past hunts to reference (AI starts from scratch)

**Solutions:**
- Practice with 5-10 hunts to build speed
- Invest time in thorough environment.md
- Document every hunt (builds AI memory)
- Use examples as templates initially

---

## Next Steps

**After reading these examples:**

1. **Try the workflow:**
   - Pick a recent CVE or security advisory
   - Follow the from-cve.md workflow
   - Generate your first AI-assisted hypothesis

2. **Review your own workflow:**
   - How long does hypothesis generation take manually?
   - What parts could AI accelerate?
   - What validation steps must remain human?

3. **Customize for your team:**
   - Adapt examples to your environment
   - Build team-specific templates
   - Train team on AI-assisted workflows

4. **Build your library:**
   - Document every hunt in LOCK format
   - Capture lessons learned (especially FPs)
   - AI will automatically improve as library grows

---

## Resources

**Prompts:**
- [hypothesis-generator-v2.md](../../prompts/hypothesis-generator-v2.md) - Enhanced prompt with examples
- [workflow-guide.md](../../prompts/workflow-guide.md) - Step-by-step AI tool usage

**Framework:**
- [AGENTS.md](../../AGENTS.md) - Context file for AI assistants
- [README.md](../../README.md) - ATHR framework overview
- [templates/](../../templates/) - LOCK-structured templates

**Community:**
- Open issues for questions
- Share your own examples
- Contribute improvements

---

## Feedback

Found these examples helpful? Have suggestions?

- Share your success stories
- Contribute your own examples
- Report issues or improvements

**Remember:** These examples show Level 2 (Augmented) workflows. Most teams operate at Level 1-2. You don't need Level 3+ automation to get significant value from AI assistance.

**The goal: 80% time savings with 100% human validation. AI generates, you decide.**
