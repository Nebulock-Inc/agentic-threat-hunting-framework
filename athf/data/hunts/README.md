# Hunt Directory

This folder contains your threat hunting investigations using the **LOCK methodology** (Learn-Observe-Check-Keep) with **ABLE scoping** (Actor-Behavior-Location-Evidence).

For template structure details, see [FORMAT_GUIDELINES.md](FORMAT_GUIDELINES.md).

## File Structure

```
hunts/
├── H-0001.md    ← macOS Data Collection via AppleScript Detection (T1005)
├── H-0002.md    ← Linux Crontab Persistence Detection (T1053.003)
├── H-0003.md    ← AWS Lambda Persistence Detection (T1546.004)
└── H-####.md    ← Your next hunt
```

Each file is a complete hunt from planning through execution results.

## Quick Start

### 1. Create a New Hunt

**Using CLI (Recommended):**

```bash
# Interactive mode - prompts you for details
athf hunt new

# Or specify details directly
athf hunt new --technique T1110.001 --title "SSH Brute Force Detection" --platform linux
```

**Manual Method (Alternative):**

Copy the template and fill it out:

```bash
cp ../templates/HUNT_LOCK.md hunts/H-0004.md
```

**Either way, start with the LEARN section:**

- Write your hypothesis
- Fill out ABLE scoping table (Actor, Behavior, Location, Evidence)
- Add threat intel and MITRE ATT&CK context

Set status to **Planning** while developing queries.

### 2. Execute the Hunt

Update the same file as you run your hunt:

- Change status from **Planning** → **In Progress**
- Fill out **CHECK** section with data source details
- Add your queries and results
- Document what worked and what didn't

### 3. Capture Results

Complete the **KEEP** section:

- Executive summary of findings
- True positives / false positives / suspicious events
- Lessons learned
- Follow-up actions and new hunt ideas

Change status to **Completed** when done.

### 4. Iterate

Next time you hunt the same behavior:

- Open the same H-####.md file
- Update queries based on lessons learned
- Re-run and update findings
- Keep refining

The file becomes your evolving playbook for that technique.

## Searching Past Hunts

### Using AI Assistants (Level 2+)

If you're using Claude Code or similar AI tools, just ask:

```
"Have we hunted macOS data collection before?"
"What lessons did we learn from persistence hunts?"
"Find hunts that detected true positives"
"Show me all Linux persistence hunts"
```

The AI will search the hunts/ folder and summarize findings.

### CLI Search (Recommended)

```bash
# Find hunts by MITRE technique
athf hunt list --technique T1110.001

# Find by behavior (full-text search)
athf hunt search "brute force"

# Find by technology
athf hunt search "powershell"

# See completed hunts
athf hunt list --status completed

# Get hunt statistics
athf hunt stats
```

### Manual Grep (Fallback)

```bash
# Find hunts by MITRE technique
grep -l "T1110.001" hunts/H-*.md

# Find by behavior
grep -i "brute force" hunts/H-*.md

# Find by technology
grep -i "powershell" hunts/H-*.md

# See completed hunts
grep "Status.*Completed" hunts/H-*.md

# Learn from past lessons
grep "Lessons Learned" -A 5 hunts/H-*.md
```

## Hunt Status Tracking

```bash
# List all hunts
ls hunts/H-*.md

# Count total hunts
ls hunts/H-*.md | wc -l

# Find in-progress hunts
grep "Status.*In Progress" hunts/H-*.md

# Find hunts that need follow-up
grep "Follow-up Actions" -A 10 hunts/H-*.md | grep "\[ \]"
```

## Level 3: MCP Integration

At Level 3, you can connect MCPs to execute hunts directly through Claude.

### What are MCPs?

MCP (Model Context Protocol) servers let Claude interact with your security tools:

- Execute Splunk queries
- Analyze results automatically
- Create tickets with findings
- Enrich data with threat intel

### Example Workflow

```
User: "Run hunt H-0001"

Claude:
1. Reads H-0001.md hypothesis and queries
2. Executes Splunk query via MCP
3. Analyzes results and identifies TPs/FPs
4. Updates hunt file with findings
5. Creates tickets for true positives

"Hunt completed. Found 3 brute force attempts. Created INC-2847."
```

### Getting Started with MCPs

1. **Setup guide:** [../integrations/README.md](../integrations/README.md)
2. **Splunk walkthrough:** [../integrations/MCP_CATALOG.md](../integrations/MCP_CATALOG.md)
3. **Splunk quickstart:** [../integrations/quickstart/splunk.md](../integrations/quickstart/splunk.md)

### Time Savings

**Without MCPs (Level 2):**

- Manual query execution: ~10 minutes
- Copy/paste results: ~5 minutes
- Analysis and documentation: ~25 minutes
- Ticket creation: ~5 minutes
- **Total:** ~45 minutes per hunt

**With MCPs (Level 3):**

- Claude executes and analyzes automatically
- Results documented in hunt file
- Tickets created with full context
- **Total:** ~5 minutes per hunt

## Tips

**Creating Hunts:**

- Start with ABLE scoping - be specific about Evidence (log sources, key fields, examples)
- Actor is optional - focus on Behavior first
- Use clear MITRE ATT&CK technique IDs in titles

**Executing Hunts:**

- Document query iterations - show what didn't work and why
- Be honest about false positives - they're learning opportunities
- Capture telemetry gaps for engineering follow-up

**Refining Hunts:**

- Update the same file as you iterate
- Keep old queries (comment them out) to show evolution
- Link related hunts in Follow-up Hunts section

**Status Management:**

- **Planning** = Developing hypothesis and queries
- **In Progress** = Actively executing and collecting data
- **Completed** = Results documented, lessons captured

## Example Hunts

- [H-0001.md](H-0001.md) - macOS Data Collection via AppleScript Detection (T1005, T1059.002, T1555.003)
- [H-0002.md](H-0002.md) - Linux Crontab Persistence Detection (T1053.003)
- [H-0003.md](H-0003.md) - AWS Lambda Persistence Detection (T1546.004, T1098)
- [FORMAT_GUIDELINES.md](FORMAT_GUIDELINES.md) - Template structure reference
