# Basic Hunt Prompts

**Level:** 0-1 (Manual/Documented)
**Purpose:** Copy-paste prompts for ChatGPT, Claude, or other AI assistants

Use these prompts when you're working outside of an AI-enabled IDE and need quick assistance with hypothesis generation, query building, or documentation.

---

## Section 1: Generate Hypothesis

Use this when you have context (CTI, alerts, anomalies) but need help forming a testable hypothesis.

### Prompt Template

```
You are a threat hunting expert helping generate behavior-based hunt hypotheses.

CONTEXT:
[Paste your context here - CTI snippet, alert, baseline drift, or gap]

RULES:
1. Generate 1-3 tightly scoped hypotheses
2. Each hypothesis must follow this pattern: "Adversaries use [behavior] to [goal] on [target]"
3. Focus on observable behaviors in data, not indicators
4. Include relevant ATT&CK technique (T####)
5. Keep hypotheses specific and testable

OUTPUT FORMAT:
For each hypothesis provide:
- Hypothesis statement
- ATT&CK Technique
- Tactic
- Data sources needed (e.g., "Windows Event Logs, Sysmon")
- Why this is worth hunting now

EXAMPLE OUTPUT:
Hypothesis: "Adversaries use base64-encoded PowerShell commands to establish persistence on Windows servers"
ATT&CK: T1059.001 (PowerShell)
Tactic: TA0003 (Persistence)
Data Needed: Sysmon Event ID 1, PowerShell logs
Why Now: Recent CTI shows APT29 using this technique; baseline shows low historical usage on servers

Generate hypothesis now:
```

### Tips

- **Be specific with context** - More details = better hypotheses
- **Ask for alternatives** - "Give me 3 different approaches"
- **Iterate** - Refine based on what data you actually have
- **Test for specificity** - Can you write a query from this hypothesis?

### Refining Hypotheses

If too broad:

- Add "on [specific target]" (e.g., "on domain controllers")
- Add time constraints (e.g., "during business hours")
- Add environmental context (e.g., "in production network")

If too narrow:

- Remove overly specific indicators
- Focus on behavior pattern, not single event
- Generalize target or timeframe

---

## Section 2: Build Query

Use this when you have a hypothesis and need help drafting a safe, bounded query.

### Prompt Template

```
You are a threat hunting query expert. Help me write a safe, bounded query to test a hunt hypothesis.

HYPOTHESIS:
[Your hypothesis here]

PLATFORM: [Splunk / KQL (Sentinel/Defender) / Elastic]

DATA AVAILABLE:
- Index/Table: [name]
- Sourcetype/DataSource: [name]
- Key fields: [list]

CONSTRAINTS:
1. Time range: earliest=-24h latest=now (adjust as needed)
2. Result cap: head 1000 (or | take 1000 for KQL)
3. Use tstats (Splunk) or summarize (KQL) when possible for performance
4. Include metadata comments with hunt ID and ATT&CK technique
5. Return only essential fields
6. Add eval/extend to tag results with hunt_id and attack_technique

OUTPUT FORMAT:
Provide:
1. The complete query
2. Brief explanation of what it does
3. Expected runtime estimate
4. Suggestions for tuning if results are too noisy

Generate query now:
```

### Query Templates

**Splunk SPL:**

```spl
/* H-#### | ATT&CK: T#### | Purpose: [description]
   Earliest: -24h | Latest: now | Cap: 1000 | Owner: [name] */

| tstats count from datamodel=YourDataModel where
  [your conditions]
  by _time, host, [key_fields] span=5m
| head 1000
| eval hunt_id="H-####", attack_technique="T####"
| fields _time, host, [relevant_fields], hunt_id, attack_technique
```

**KQL:**

```kql
// H-#### | ATT&CK: T#### | Purpose: [description]
// TimeRange: ago(24h) | Cap: 1000 | Owner: [name]

YourTable
| where TimeGenerated >= ago(24h)
| where [your conditions]
| summarize Count=count() by bin(TimeGenerated, 5m), Computer, [key_fields]
| take 1000
| extend HuntId="H-####", AttackTechnique="T####"
```

### Query Best Practices

**Performance:**

- Use data models (Splunk) or summarize (KQL) when possible
- Filter early - most restrictive conditions first
- Limit fields - only return what you need
- Set sensible time ranges - start with 24h, expand if needed

**Safety:**

- Always bound time - never open-ended searches
- Always cap results - protect your SIEM
- Test on small timeframes first - 1 hour before 24 hours
- Use lookups for enrichment - don't join large datasets inline

**Signal Quality:**

- Filter known good - baseline automation, admin tools
- Add context - enrich with asset inventory, user roles
- Look for anomalies - rare processes, unusual times, unexpected hosts
- Use stats wisely - count, distinct count, rare events

### Troubleshooting

**Too many results?**

- Add more specific filters
- Shorten time range
- Filter out known benign activity
- Use rare() or unusual patterns

**Too few results?**

- Broaden conditions
- Check field names and values
- Verify data is actually indexed
- Expand time range

**Query too slow?**

- Use data models/accelerated searches
- Reduce time range
- Remove expensive operations (regex, complex joins)
- Add index= constraints

---

## Section 3: Document Results

Use this after executing a hunt to help write concise findings in LOCK format.

### Prompt Template

```
You are a threat hunting analyst helping document hunt results following the LOCK pattern.

HYPOTHESIS:
[Your hypothesis]

QUERY EXECUTED:
[Paste query]

RESULTS SUMMARY:
- Time range: [earliest to latest]
- Rows examined: [count]
- Rows returned: [count]
- Runtime: [seconds]
- Key findings: [brief description of what you found]

RAW OBSERVATIONS:
[Paste sample results or describe what you saw]

TASK:
Write a concise summary for the KEEP section of my hunt file.
Focus on:
- What we found (2-4 sentences)
- Decision (accept/reject/needs_changes) with reason
- Next steps (one concrete action)
- Lessons learned (one key takeaway)

Keep it to 5-8 sentences total.

Generate summary now:
```

### What Makes Good Documentation

**Be Concise:**

- 5-8 sentences total for findings
- 3 bullet points max per section
- Focus on signal, not every detail

**Be Honest:**

- Accept = Found useful signal or suspicious activity
- Reject = Benign, false positive, or baseline noise
- Needs Changes = Interesting but query needs refinement

Don't be afraid to reject! Useful negatives teach us what's normal.

**Be Specific:**

- ❌ "Found some suspicious stuff, need to investigate"
- ✅ "Found 3 hosts with encoded PowerShell outside business hours; 2 match known deployment patterns, 1 requires IR escalation"

**Capture Lessons:**
This is the most important part - it's what makes the system smarter.

Good lessons:

- "Baseline automation reduced signal-to-noise by 80%"
- "Time-of-day filtering eliminated weekend maintenance jobs"
- "Parent process context critical for distinguishing admin vs adversary"

Avoid vague lessons:

- "Queries should be better"
- "Need more data"
- "This was hard"

---

## Usage Notes

### Workflow

1. **Generate Hypothesis** - Use Section 1 with your context
2. **Build Query** - Use Section 2 with your hypothesis
3. **Execute Hunt** - Run query in your SIEM (test small timeframes first!)
4. **Document Results** - Use Section 3 to capture findings

### Safety Reminders

- **Always review** AI-generated hypotheses for feasibility
- **Always test** AI-generated queries on small timeframes first
- **Always validate** that queries are safe and bounded
- **Use your judgment** - You know your environment better than AI

### Platform-Specific Tips

**Splunk:**

- Mention "Splunk SPL" in your prompt
- Specify data models when available
- AI knows common Splunk patterns

**KQL (Sentinel/Defender):**

- Mention "KQL for Sentinel" or "KQL for Defender"
- Specify table names (SecurityEvent, DeviceProcessEvents, etc.)
- AI understands Sentinel-specific syntax

**Elastic:**

- Mention "Elastic EQL" or "Lucene query"
- Specify index patterns
- Note which Elastic stack version

---

## Next Steps

Once you're comfortable with these basic prompts:

1. **Build your hunt repository** - Document hunts using [templates/HUNT_LOCK.md](../templates/HUNT_LOCK.md)
2. **Progress to Level 2** - Use [ai-workflow.md](ai-workflow.md) for AI tools with repository access
3. **See real examples** - Review [H-0001.md](../hunts/H-0001.md) and [H-0002.md](../hunts/H-0002.md)

---

## Customizing for Your Environment

Feel free to modify these prompts:

- Add your organization's specific data sources
- Include your ATT&CK coverage gaps
- Reference your baseline automation
- Add your threat model priorities
