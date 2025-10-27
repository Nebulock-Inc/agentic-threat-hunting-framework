# Hunt Summarizer Prompt

Use this prompt to help write concise run notes and capture lessons learned (Level 1: Assisted).

## Prompt

```
You are a threat hunting analyst helping document hunt results following the LOCK Loop framework.

HYPOTHESIS:
[Your hypothesis]

QUERY EXECUTED:
[Paste query or reference query file]

RESULTS SUMMARY:
- Time range: [earliest to latest]
- Rows examined: [count]
- Rows returned: [count]
- Runtime: [seconds]
- Key findings: [brief description of what you found]

RAW OBSERVATIONS:
[Paste sample results or describe what you saw]

TASK:
Write a concise run note following the LOCK Loop structure. Keep the review section to 5-8 sentences maximum.

OUTPUT FORMAT:

### 🔒 L — Learn (What We Knew)
[Brief context that prompted this hunt]

### 🔒 O — Observe (Hypothesis)
[Restate the hypothesis clearly]

### 🔒 C — Check (Test Results)
- Query runtime, rows examined/returned
- Key findings (2-4 sentences)
- Notable observations (3 bullet points max)

### 🔒 K — Keep (Decision & Lessons)
- Decision: accept | reject | needs_changes
- Why: [1-2 sentence explanation]
- Next Step: [One concrete action]
- Lessons Learned: [One key takeaway for future hunts]

Generate run note now:
```

## What Makes a Good Run Note

### Be Concise
- **Review section**: 5-8 sentences total
- **Bullet points**: 3 max per section
- **Focus on signal**: Not every detail, just what matters

### Be Honest
- **Accept** = Found useful signal or suspicious activity
- **Reject** = Benign, false positive, or baseline noise
- **Needs changes** = Interesting but query needs refinement

Don't be afraid to reject! Useful negatives teach us what's normal.

### Be Specific
❌ "Found some suspicious stuff, need to investigate"
✅ "Found 3 hosts with encoded PowerShell outside business hours; 2 match known deployment patterns, 1 requires IR escalation"

### Capture Lessons
This is the most important part - it's what makes the system smarter.

**Good lessons:**
- "Baseline automation reduced signal-to-noise by 80%"
- "Time-of-day filtering eliminated weekend maintenance jobs"
- "Parent process context critical for distinguishing admin vs adversary"
- "Query performance improved 10x using tstats instead of raw search"

**Avoid vague lessons:**
- "Queries should be better"
- "Need more data"
- "This was hard"

## Example Run Note

### 🔒 L — Learn (What We Knew)
Recent CTI report indicated APT29 using base64-encoded PowerShell for persistence on Windows servers. Baseline shows historically low usage of `-encodedcommand` on server assets.

### 🔒 O — Observe (Hypothesis)
Adversaries use base64-encoded PowerShell commands to establish persistence on Windows servers.

### 🔒 C — Check (Test Results)
**Query**: `queries/H-0001.spl`
**Time Range**: -24h to now
**Runtime**: 8.3 seconds
**Rows Examined**: 2,847
**Rows Returned**: 12

**Findings**: Query identified 12 instances across 3 server hosts. Ten events matched known deployment automation (SRV-APP-01, SRV-APP-02). One event on SRV-WEB-05 occurred at 02:17 AM from non-standard user account, attempting to download and execute from external URL. Decoded command structure matches APT29 TTPs from CTI.

Key observations:
- 83% of results were benign automation
- SRV-WEB-05 event outside business hours with suspicious parent process
- Time-of-day context significantly improved signal quality

### 🔒 K — Keep (Decision & Lessons)
**Decision**: Accept

**Why**: Found one high-confidence indicator requiring IR escalation. Two hosts show expected patterns that need baselining.

**Next Step**: Escalate SRV-WEB-05 to incident response. Create allowlist for deployment automation paths. Draft detection rule for encoded PowerShell from non-SYSTEM accounts on servers outside business hours.

**Lessons Learned**: Baseline automation is critical - without it, signal-to-noise is poor. Time-of-day filtering and parent process context should be standard in future PowerShell hunts.

## Tips

### For Accepts
- Clearly state what suspicious activity was found
- Include confidence level (high/medium/low)
- Specify next steps for IR or detection engineering
- Note what made this a true positive

### For Rejects
- Explain why results were benign
- Document any allowlists or baselines needed
- Note if hypothesis was wrong or query needs refinement
- Still capture what you learned

### For Needs Changes
- Specify what needs to change in the query
- Note if more data sources are needed
- Indicate if hypothesis should be refined
- Plan to rerun after changes

## Common Mistakes

❌ **Too long** - Run notes that require scrolling
✅ **Right length** - Fits on one screen, 5-8 sentences

❌ **No decision** - "We should investigate further"
✅ **Clear decision** - Accept/Reject/Needs Changes with reason

❌ **Vague lessons** - "This was interesting"
✅ **Actionable lessons** - "Parent process filtering reduced FPs by 70%"

❌ **No next step** - Just describes findings
✅ **Concrete action** - "Add to baseline" or "Escalate to IR" or "Refine query"

## Building Memory

After completing your hunt note, save it to `hunts/H-XXXX_YYYY-MM-DD.md`.

Your `hunts/` folder becomes your memory. Before starting new hunts, grep through past hunts to avoid duplicates and apply lessons learned:

```bash
grep -l "T1059.001" hunts/*.md      # Find similar TTPs
grep "Decision: Accept" hunts/*.md  # See what worked
```

This recall discipline is what enables Level 2 (Informed) hunting.
