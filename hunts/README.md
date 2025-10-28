# Hunt Directory

This folder contains your threat hunting hypotheses and execution reports.

## File Structure

```
hunts/
├── H-0001.md                 ← Reusable hypothesis (the "recipe")
├── H-0001_2025-10-22.md     ← First execution report
└── H-0001_2025-10-29.md     ← Second execution report
```

As you add more hunts, your structure will grow:
```
hunts/
├── H-0001.md
├── H-0001_2025-10-22.md
├── H-0001_2025-10-29.md
├── H-0002.md                 ← New hypothesis
└── H-0002_2025-11-05.md     ← Its first execution
```

## How It Works

### 1. Create a Hypothesis

Copy the template to create a new hunt:

```bash
cp templates/HUNT_HYPOTHESIS.md hunts/H-0004.md
```

Fill out:
- Hypothesis (what you're hunting for)
- Context (why now, ATT&CK mapping)
- Data needed (index, fields, time range)

The hypothesis file stays lightweight - just the plan.

### 2. Execute the Hunt

When ready to run the hunt, create a dated execution file:

```bash
cp hunts/H-0004.md hunts/H-0004_$(date +%Y-%m-%d).md
```

Then fill out the execution report with:
- Query results and metrics
- Findings and analysis
- Decision (Accept/Reject/Needs Changes)
- Lessons learned

### 3. Run Again

Keep the original hypothesis file (`H-0004.md`) for future runs. Next time you want to hunt the same behavior:

```bash
cp hunts/H-0004.md hunts/H-0004_2025-11-05.md
```

Apply lessons from previous runs to refine your approach.

## Checking Hunt Status

**See all hypotheses (backlog):**
```bash
ls hunts/H-*.md | grep -v "_"
```

**See if a hunt has been executed:**
```bash
ls hunts/H-0001_*.md  # Shows all execution dates for H-0001
```

**Find completed hunts:**
```bash
grep "Status.*Completed" hunts/H-*_*.md
```

**Find hunts that need refinement:**
```bash
grep "Needs Changes" hunts/H-*_*.md
```

## Memory Building (Level 1: Persistent)

Before starting a new hunt, search past executions to avoid duplicates and apply lessons:

```bash
# Find past hunts for a TTP
grep -l "T1110.001" hunts/H-*_*.md

# Find hunts by behavior
grep -i "brute force" hunts/H-*_*.md

# Find by technology
grep -i "powershell" hunts/H-*_*.md

# Find by application
grep -i "active directory" hunts/H-*_*.md

# Find by keyword
grep -i "privilege escalation" hunts/H-*_*.md

# See what worked
grep "Decision.*Accept" hunts/H-*_*.md

# Learn from past mistakes
grep "Lessons Learned" -A 3 hunts/H-*_*.md
```

This recall discipline is what makes hunting agentic.

## Tips

- **Keep hypothesis files simple** - Just the plan, no results
- **Dated files are comprehensive** - Include everything: findings, analysis, screenshots, lessons
- **Don't delete hypothesis files** - They're your reusable templates
- **Use consistent dating** - YYYY-MM-DD format for easy sorting
- **Reference related hunts** - Link between similar investigations
