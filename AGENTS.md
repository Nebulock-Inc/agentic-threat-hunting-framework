# AGENTS.md - Context for AI Assistants

**Purpose:** This file tells AI assistants (GitHub Copilot, Claude Code, Cursor, etc.) what your threat hunting repository contains and how to use it.

**When to create this:** Level 2 (Augmented) - when you add AI integration to your hunting workflow.

**Who reads this:** AI tools that have access to your repository files.

---

## Repository Overview

This repository contains threat hunting hypotheses, execution notes, and lessons learned using the LOCK pattern (Learn → Observe → Check → Keep).

**AI assistants should:**
- Read past hunt notes before suggesting new hypotheses
- Reference lessons learned when generating queries
- Avoid suggesting hunts we've already completed
- Use environment.md and vulnerabilities.md to inform hunt planning

---

## Repository Structure

```
/
├── hunts/              # Hunt hypotheses and execution notes
│   ├── H-XXXX.md       # Hypothesis files
│   └── H-XXXX_DATE.md  # Execution/run notes
├── templates/          # LOCK-structured templates for new hunts
├── prompts/            # AI prompt templates for manual workflows
├── queries/            # Reusable query patterns
├── metrics/            # Performance tracking and memory guidance
├── environment.md      # Tech stack, tools, infrastructure inventory
└── vulnerabilities.md  # CVE tracking and hunt opportunities
```

---

## Environmental Context Files

### environment.md
**Contains:**
- Security tools (SIEM, EDR, firewalls, monitoring platforms)
- Technology stack (languages, frameworks, databases, cloud services)
- Network architecture and infrastructure
- Internal documentation links (wikis, architecture diagrams, asset inventory)

**How AI should use this:**
- Reference when generating hypotheses to ensure hunt is relevant to our tech stack
- Check data sources available before suggesting queries
- Cross-reference CVEs against our actual deployed technologies
- Understand what visibility/telemetry we have for proposed hunts

**Example:**
```
User: "Generate hypothesis for hunting Log4j exploitation"
AI: *checks environment.md* "I see you run Java applications with log aggregation
     in Splunk. Here's a hypothesis targeting your environment..."
```

### vulnerabilities.md
**Contains:**
- Known CVEs affecting our environment (cross-referenced with environment.md)
- Exploit availability and active exploitation status
- Hunt opportunities prioritized by severity + exploit maturity
- Remediation tracking and hunt status

**How AI should use this:**
- Check before suggesting CVE-driven hunts (avoid duplicates)
- Reference past vulnerability hunts when generating new hypotheses
- Suggest updating this file when new CVEs are published for our tech stack
- Use exploit availability data to prioritize hunt suggestions

**Example:**
```
User: "What should we hunt for this week?"
AI: *reads vulnerabilities.md* "Based on open vulnerabilities:
     - CVE-2024-1234 affects your Nginx deployment (exploit published yesterday)
     - CVE-2024-5678 is being actively exploited (CISA KEV listed)
     I recommend prioritizing these two..."
```

---

## Data Sources

**Update this section with your actual data sources:**

### SIEM / Log Aggregation
- **Platform:** [e.g., Splunk Enterprise, Elastic Security, Microsoft Sentinel]
- **Indexes/Tables:** [e.g., `index=winlogs`, `SecurityEvent`, `logs-*`]
- **Retention:** [e.g., 90 days hot, 1 year cold]
- **Query Language:** [SPL, KQL, Lucene, etc.]

### EDR / Endpoint Security
- **Platform:** [e.g., CrowdStrike Falcon, Microsoft Defender, SentinelOne]
- **Telemetry:** [Process execution, network connections, file events]
- **Query Access:** [API, console, integrated with SIEM]

### Network Security
- **Flow Data:** [NetFlow, IPFIX, Zeek logs]
- **Packet Capture:** [Available? Retention period?]
- **Firewall Logs:** [Vendor, where logs are stored]
- **IDS/IPS:** [Snort, Suricata, alerts in SIEM]

### Cloud Security
- **Providers:** [AWS, Azure, GCP]
- **Logging:** [CloudTrail, Azure Monitor, Cloud Logging]
- **Where Stored:** [Centralized in SIEM? Separate platform?]

### Identity & Access
- **Identity Provider:** [Active Directory, Okta, Azure AD]
- **Authentication Logs:** [Where are auth events logged?]
- **MFA Events:** [Available? Where?]

**AI Note:** Always verify data sources exist before generating queries. Reference environment.md for detailed coverage.

---

## Hunting Methodology

This repository follows the **LOCK pattern**:

1. **Learn** - Gather context (CTI, alert, anomaly, vulnerability)
2. **Observe** - Form hypothesis about adversary behavior
3. **Check** - Test with bounded, safe query
4. **Keep** - Record decision and lessons learned

**AI assistants should:**
- Generate hypotheses in LOCK format (see templates/)
- Ensure queries are bounded by time, scope, and impact
- Document lessons learned after hunt execution
- Reference past hunts when suggesting new ones

---

## Guardrails for AI Assistance

### Query Safety
- **Always include time bounds** (e.g., last 7 days, not "all time")
- **Limit result sets** (e.g., `| head 1000`, `TOP 100`)
- **Avoid expensive operations** without explicit approval (stats over 30+ days, full table scans)
- **Test on small windows first** before expanding timeframe

### Hypothesis Validation
- **Check if we've hunted this before** (grep hunts/ folder)
- **Verify data source availability** (reference environment.md)
- **Ensure hypothesis is testable** (can be validated with a query)
- **Consider false positive rate** (will this hunt generate noise?)

### Documentation
- **Use LOCK structure** for all hunt documentation
- **Capture negative results** (hunts that found nothing are still valuable)
- **Record lessons learned** (what worked, what didn't, what to try next time)
- **Link related hunts** (if this builds on past work, reference it)

### Memory and Context
- **Search before suggesting** - Check if we've hunted this TTP/CVE/behavior before
- **Reference environment.md** - Ensure suggestions match our actual tech stack
- **Check vulnerabilities.md** - Don't suggest hunts we've already completed
- **Apply past lessons** - Use outcomes from similar hunts to improve new hypotheses

---

## AI Workflow Examples

### Level 2 (Augmented) - AI with Memory

**User asks:** "Generate hypothesis for hunting Kerberoasting attacks"

**AI should:**
1. Search `hunts/` for past Kerberoasting hunts
2. Check `environment.md` for Active Directory presence and logging capabilities
3. Read any lessons learned from similar hunts (T1558.003, credential access TTPs)
4. Generate LOCK-formatted hypothesis referencing available data sources
5. Suggest query targeting confirmed data sources (e.g., Windows Security Event Logs in Splunk)

**User asks:** "What should we hunt based on recent CVEs?"

**AI should:**
1. Read `vulnerabilities.md` to see open/monitoring CVEs
2. Cross-reference against `environment.md` to confirm affected tech
3. Check `hunts/` to see if we've already hunted these CVEs
4. Prioritize by: Severity + Exploit availability + Not yet hunted
5. Generate hunt suggestions with hypotheses

### Level 3+ (Autonomous) - Scripted Workflows

When building automation scripts, AI should:
- Reference this AGENTS.md file to understand repo structure
- Use environment.md as the tech stack source of truth
- Update vulnerabilities.md when discovering new relevant CVEs
- Follow LOCK structure when auto-generating hunt files
- Include human-in-the-loop validation for high-risk operations

---

## Hypothesis Generation Workflow

This section provides detailed guidance for AI assistants on generating threat hunting hypotheses from threat intelligence. This is the most common Level 2 (Augmented) workflow.

### When to Generate Hypotheses

AI should offer to generate hypotheses when users provide:
- CVE identifiers (e.g., "CVE-2024-1234")
- Threat intelligence reports (APT activity, campaign analysis)
- Detection anomalies ("seeing spike in failed logins")
- TTP references (e.g., "T1003 credential dumping")
- Security news/advisories (CISA alerts, vendor bulletins)

### Step-by-Step Workflow

**Step 1: Check Memory (Avoid Duplicates)**
```
AI Action: Search past hunts before generating anything new
Commands:
- Search hunts/ for similar TTPs, CVEs, or behaviors
- Check vulnerabilities.md for CVE status
- Look for related hypotheses that might be adapted

AI Response: "I found 2 past hunts related to this:
- H-0015 (2024-09-12): Similar TTP, found X
- H-0023 (2024-10-01): Related behavior, learned Y
Should I generate a new hypothesis building on these lessons?"
```

**Step 2: Validate Environment (Ensure Relevance)**
```
AI Action: Confirm we have visibility for this hunt
Commands:
- Read environment.md to check if affected tech exists
- Verify data sources are available for proposed hunt
- Identify telemetry gaps that might limit hunt effectiveness

AI Response: "I see you run [affected technology] with logging to [SIEM].
We have [data source] available for this hunt. Note: [any gaps]"
```

**Step 3: Generate LOCK-Structured Hypothesis**
```
AI Action: Create hypothesis following LOCK pattern
Structure:
- Hypothesis: "Adversaries use [behavior] to [goal] on [target system]"
- Context: Why now? What triggered this hunt?
- ATT&CK: Technique ID and tactic
- Data Needed: Specific indexes/tables from environment.md
- Time Range: Recommended lookback period
- Query: High-level approach (not full query yet)

AI Response: Present complete hypothesis in markdown format
ready to copy into new hunt file (H-XXXX.md)
```

**Step 4: Suggest Next Steps**
```
AI Action: Guide user on what to do next
Options:
- "Would you like me to create the hunt file (H-XXXX.md)?"
- "Should I draft a query for this hypothesis?"
- "Need me to check similar past hunts for lessons learned?"

AI Response: Be proactive but wait for confirmation before creating files
```

### Example Conversations

#### Example 1: CVE-Driven Hypothesis

**User:** "Generate hypothesis for CVE-2024-21412 (Windows SmartScreen bypass)"

**AI Should:**
1. Check vulnerabilities.md for existing entry
2. Read environment.md for Windows deployment details
3. Search hunts/ for past SmartScreen or bypass hunts
4. Generate hypothesis:

```markdown
# H-XXXX | CVE-2024-21412 SmartScreen Bypass Hunt

**Status:** Candidate

## Hypothesis
Adversaries exploit CVE-2024-21412 to bypass Windows SmartScreen by crafting
internet shortcut files that execute malicious payloads without security warnings.

## Context

**Why Now:**
- CVE published 2024-02-13, exploited in-the-wild (CISA KEV)
- PoC available on GitHub
- Affects all Windows systems [check environment.md for versions]

**ATT&CK:** T1204.001 (User Execution: Malicious Link)
**Tactic:** Initial Access

## Data Needed
- **Windows Event Logs:** Sysmon Event ID 1 (Process Creation)
- **EDR Telemetry:** File creation events (*.url, *.lnk files)
- **Network Logs:** HTTP downloads preceding file execution

[Reference environment.md for actual index names]

## Time Range
- Start: 2024-02-13 (CVE public disclosure)
- Recommended: Last 30 days initially

## Query Approach
1. Find execution of processes from user temp directories
2. Preceded by creation of .url or .lnk files
3. Originating from browser downloads
4. Without SmartScreen warnings (absence of expected events)

## Next Steps
- Create query in queries/H-XXXX.spl
- Execute and document in H-XXXX_YYYY-MM-DD.md
```

**AI Should Then Ask:** "Would you like me to:
1. Create this as H-XXXX.md in hunts/ folder?
2. Draft the actual SIEM query?
3. Update vulnerabilities.md with this hunt plan?"

#### Example 2: TTP-Driven Hypothesis

**User:** "We need to hunt for Living off the Land (LOLBins) abuse"

**AI Should:**
1. Search hunts/ for past LOLBins hunts (T1218, T1059, etc.)
2. Check environment.md for EDR/process monitoring availability
3. Ask clarifying questions:

```
AI: "I see we have [EDR platform] with process telemetry.
Before generating the hypothesis, which LOLBins should we focus on?

Options:
1. PowerShell (T1059.001) - Already hunted (H-0012, H-0019)
2. WMIC (T1047) - Not recently hunted
3. Rundll32 (T1218.011) - Never hunted
4. All suspicious built-in tools (broad hunt)

Also, are you investigating a specific incident, or is this proactive?"
```

**User:** "Focus on rundll32 abuse, proactive hunt"

**AI Generates:**
```markdown
# H-XXXX | Rundll32 Living off the Land Hunt

**Status:** Candidate

## Hypothesis
Adversaries abuse rundll32.exe to execute malicious DLLs or bypass
application control by using Windows built-in functionality for payload execution.

## Context

**Why Now:**
- Proactive hunt for common LOLBin abuse
- No recent coverage (last hunt: H-0008, 6 months ago)
- Commonly used post-exploitation (ref: MITRE ATT&CK)

**ATT&CK:** T1218.011 (Signed Binary Proxy Execution: Rundll32)
**Tactic:** Defense Evasion

## Data Needed
- **EDR:** Process execution logs (CommandLine arguments)
- **Sysmon:** Event ID 1 (Process Creation) with parent process context

[Based on environment.md: CrowdStrike Falcon data in Splunk index=edr]

## Time Range
- Last 14 days initially (balance: recent activity vs. noise)

## Query Approach
1. Find rundll32.exe executions
2. Filter for suspicious patterns:
   - Unusual DLL paths (user directories, temp folders)
   - Non-standard export functions
   - Parent processes (Office, browsers, scripting engines)
3. Exclude known-good patterns (Windows updates, legitimate apps)

## Known False Positives (from past hunts)
- H-0008 found: Windows Updates spawn rundll32 frequently
- Common legitimate DLLs: shell32.dll, advpack.dll (standard functions)

## Next Steps
- Draft query with FP filters based on H-0008 lessons
- Execute on 7-day window first
- If results look clean, expand to 14 days
```

**AI Should Then:** "This hypothesis builds on lessons from H-0008 (past rundll32 hunt).
Should I pull those specific false positive filters to include in the query?"

#### Example 3: Anomaly-Driven Hypothesis

**User:** "We're seeing a spike in failed VPN authentications from IP 203.0.113.45"

**AI Should:**
1. Recognize this as incident-driven, not proactive
2. Search for past brute force hunts (T1110)
3. Check environment.md for VPN platform and auth logs
4. Generate time-sensitive hypothesis:

```markdown
# H-XXXX | VPN Brute Force from 203.0.113.45

**Status:** Candidate
**Priority:** HIGH (active incident)

## Hypothesis
Adversary is conducting brute force authentication attempts against VPN
infrastructure from IP 203.0.113.45 to gain initial access.

## Context

**Why Now:**
- Detected anomaly: Spike in failed VPN auth from single IP
- Requires immediate investigation (potential active attack)

**ATT&CK:** T1110.001 (Brute Force: Password Guessing)
**Tactic:** Initial Access

## Data Needed
- **VPN Logs:** Authentication attempts (success/failure)
- **Firewall:** Connection attempts to VPN gateway
- **Identity Provider:** Account lockout events

[Based on environment.md: VPN logs in SIEM, reference actual index]

## Time Range
- **Critical Window:** Last 24 hours (when spike detected)
- **Historical Context:** Past 7 days (establish baseline)

## Query Approach
1. Failed VPN auth from 203.0.113.45
2. Identify targeted usernames
3. Check if any successful auths from same IP
4. Cross-reference with threat intel (IP reputation)
5. Look for distributed attempts (same usernames, different IPs)

## Immediate Actions (before full hunt)
- Block 203.0.113.45 at firewall (if not already done)
- Check for any successful logins from this IP
- Alert affected users if credentials may be compromised

## Next Steps
- Execute query immediately (incident response)
- Document findings in H-XXXX_YYYY-MM-DD.md
- Escalate any successful compromises to IR team
```

**AI Should Emphasize:** "This is incident response, not routine hunting.
Execute query immediately and document as you go. Should I draft the query now?"

### Memory Search Patterns

When users ask to generate hypotheses, AI should automatically search:

**Pattern 1: CVE-Based**
```
Search: grep -l "CVE-YYYY-NNNNN" hunts/*.md vulnerabilities.md
Purpose: Check if we've already hunted or tracked this CVE
```

**Pattern 2: TTP-Based**
```
Search: grep -l "T####" hunts/*.md
Purpose: Find past hunts for same ATT&CK technique
```

**Pattern 3: Behavior-Based**
```
Search: grep -li "keyword" hunts/*.md
Keywords: "brute force", "lateral movement", "credential dump", etc.
Purpose: Find hunts with similar behaviors
```

**Pattern 4: Technology-Based**
```
Search: grep -li "technology" hunts/*.md environment.md
Examples: "VPN", "Active Directory", "AWS S3"
Purpose: Find hunts targeting same systems/platforms
```

### Safety Checks Before Generating

AI should validate before generating hypothesis:

**Check 1: Data Availability**
- Question: "Do we have logs for this hunt?"
- Action: Read environment.md data sources section
- Response: Warn if critical telemetry is missing

**Check 2: Scope Appropriateness**
- Question: "Is this hunt realistic in scope?"
- Action: Consider query complexity vs. environment size
- Response: Suggest narrowing if too broad

**Check 3: Duplication**
- Question: "Have we hunted this before?"
- Action: Search hunts/ and vulnerabilities.md
- Response: Reference past hunts, suggest building on lessons

**Check 4: Testability**
- Question: "Can this hypothesis be tested with a query?"
- Action: Verify hypothesis is concrete, not abstract
- Response: Request clarification if hypothesis is too vague

### Output Format Expectations

All AI-generated hypotheses must follow:

**File Naming:** `H-XXXX.md` (user specifies number, or AI suggests next)

**Required Sections:**
- Hypothesis statement (one sentence, testable)
- Context (Why now, ATT&CK, Tactic)
- Data Needed (specific indexes from environment.md)
- Time Range (bounded, justified)
- Query Approach (high-level steps)

**Optional Sections (include when relevant):**
- Known False Positives (from past similar hunts)
- Priority Level (if incident-driven)
- Immediate Actions (if time-sensitive)
- References (CTI reports, CVE links, past hunt IDs)

**Quality Standards:**
- Hypothesis is specific and testable
- References actual data sources from environment.md
- Includes lessons from past hunts if available
- Has realistic time bounds
- Considers false positive rate

### Common Mistakes to Avoid

**Mistake 1: Generating Without Checking Memory**
❌ Bad: Immediately generate hypothesis without searching
✅ Good: Search hunts/ first, reference if duplicates exist

**Mistake 2: Ignoring Environment Context**
❌ Bad: Suggest hunting Windows events when user only has Linux
✅ Good: Read environment.md, ensure hunt matches tech stack

**Mistake 3: Vague Hypotheses**
❌ Bad: "Adversaries may use PowerShell maliciously"
✅ Good: "Adversaries use base64-encoded PowerShell to download second-stage payloads from external IPs"

**Mistake 4: No Time Bounds**
❌ Bad: "Search all time for suspicious activity"
✅ Good: "Search last 30 days (CVE published date) to present"

**Mistake 5: Forgetting Lessons Learned**
❌ Bad: Generate query that past hunts found generates noise
✅ Good: Reference H-XXXX false positives and pre-filter

---

## ATT&CK Coverage

**Optional - Document your priority TTPs:**

### High Priority TTPs (based on threat model)
- T1003 - Credential Dumping
- T1059 - Command and Scripting Interpreter
- T1110 - Brute Force
- T1078 - Valid Accounts
- [Add your priority TTPs]

### Known Coverage Gaps
- [TTPs you can't currently hunt due to telemetry gaps]
- [Reference environment.md "Known Gaps & Blind Spots" section]

**AI Note:** Prioritize hunt suggestions for high-priority TTPs with available telemetry.

---

## Organization-Specific Context

**Optional - Add details unique to your environment:**

### Threat Model
- [Industry-specific threats you care about]
- [Known adversary groups targeting your sector]
- [Past incidents that inform current focus]

### Business Context
- [Critical applications/services that need extra scrutiny]
- [Compliance requirements affecting hunt scope]
- [Operational constraints (maintenance windows, access restrictions)]

### Team Practices
- [Hunt cadence - daily, weekly, monthly?]
- [Who reviews/approves hunts before execution?]
- [Where do hunt results get reported?]

---

## Memory Scaling (Reference: metrics/README.md)

**Current maturity level:** [0: Ephemeral | 1: Persistent | 2: Augmented | 3: Autonomous | 4: Coordinated]

**Memory approach:**
- **Level 1-2:** Grep-based search across markdown files (no structured memory yet)
- **Level 3+:** [If applicable: SQLite/JSON index for faster search, agent-accessible structured memory]

**When AI needs to recall past hunts:**
- Use grep/search across `hunts/` folder (hunt notes)
- Use grep/search across `environment.md` (tech stack)
- Use grep/search across `vulnerabilities.md` (CVE tracking)
- At Level 3+: Query structured memory if available

---

## Maintenance Notes

**Review this file when:**
- Adding new data sources (update "Data Sources" section)
- Changing AI tools (update "AI Workflow Examples")
- Reaching new maturity level (update "Memory Scaling")
- Discovering AI generates incorrect assumptions (add to "Guardrails")

**Last Updated:** [YYYY-MM-DD]
**Maintained By:** [Team/Individual]
