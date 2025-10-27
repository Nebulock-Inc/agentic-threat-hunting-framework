# AI Prompt Library

This folder contains prompts to help you move from **Level 0 (Manual)** to **Level 1 (Assisted)** hunting.

## What's Here

### hypothesis-generator.md
Use with ChatGPT, Claude, or other AI assistants to generate behavior-based hunt hypotheses from context like CTI, alerts, or anomalies.

**When to use**: You have context but need help forming a testable hypothesis

### query-builder.md
Use to draft safe, bounded queries for Splunk, KQL, or Elastic from your hypothesis.

**When to use**: You have a hypothesis but need help writing the query

### summarizer.md
Use to help document hunt results and capture lessons learned in LOCK pattern format.

**When to use**: You ran a query and need help writing a concise run note

## How to Use These Prompts

1. **Copy the prompt** from the markdown file
2. **Fill in your context** (hypothesis, data sources, results)
3. **Paste into your AI assistant** (ChatGPT, Claude, etc.)
4. **Review and refine** the output
5. **Test before using** - AI can make mistakes!

## Important Notes

### AI Assistance ≠ Autopilot

- **Always review** AI-generated hypotheses for feasibility
- **Always test** AI-generated queries on small timeframes first
- **Always validate** that queries are safe and bounded
- **Use your judgment** - You know your environment better than AI

### Keep It Simple

These prompts are designed to:
- Help you think through the LOCK pattern systematically
- Reduce writer's block when starting hunts
- Capture lessons more consistently
- NOT to fully automate hunting (that's Level 3-4)

### Learning Tool

Think of these prompts as training wheels:
- They help you get started faster
- They teach you the LOCK pattern structure
- Over time, you'll need them less
- But they remain useful for complex hunts

## Platform-Specific Tips

### For Splunk Users
- Mention "Splunk SPL" in your prompt
- Specify data models when available
- AI knows common Splunk patterns

### For KQL Users
- Mention "KQL for Sentinel" or "KQL for Defender"
- Specify table names (SecurityEvent, DeviceProcessEvents, etc.)
- AI understands Sentinel-specific syntax

### For Elastic Users
- Mention "Elastic EQL" or "Lucene query"
- Specify index patterns
- Note which Elastic stack version

## Customizing Prompts

Feel free to modify these prompts for your environment:

- Add your organization's specific data sources
- Include your ATT&CK coverage gaps
- Reference your baseline automation
- Add your threat model priorities

## Contributing

Have a better prompt? Found a useful variation?
- Submit a PR with your improved prompts
- Share what works in your environment
- Help others move to Level 1 faster

## Next Level: Level 2 (Informed)

Once you have 10-20 completed hunts in `hunts/`, you can enhance these prompts with memory:

- "Check if we've hunted this before: [paste grep results from hunts/]"
- "What lessons from past hunts apply here?"
- "Compare this hypothesis to previous ones: [paste relevant hunt notes]"

Example workflow:
```bash
# Before starting a hunt, search your memory
grep -l "T1110.001" hunts/*.md        # Find by TTP
grep -i "brute force" hunts/*.md      # Find by behavior
grep -i "powershell" hunts/*.md       # Find by technology
grep -i "active directory" hunts/*.md # Find by application
grep -i "privilege escalation" hunts/*.md  # Find by keyword

# Share relevant past hunts with your AI assistant
# Then use the prompts above
```

This simple recall loop makes your AI assistant "remember" past hunts - the first step toward true agentic hunting.
