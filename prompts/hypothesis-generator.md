# Hypothesis Generator Prompt

Use this prompt with your AI assistant to generate threat hunting hypotheses (Level 1: Assisted).

## Prompt

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

## Tips

- **Be specific with context** - More details = better hypotheses
- **Ask for alternatives** - "Give me 3 different approaches"
- **Iterate** - Refine based on what data you actually have
- **Test for specificity** - Can you write a query from this hypothesis?

## Example Usage

**Input Context:**
> "Noticed spike in failed login attempts from internal IPs during off-hours. No corresponding help desk tickets. Multiple user accounts affected."

**Expected Output:**
> Hypothesis: "Adversaries use password spraying from compromised internal hosts to gain access to additional accounts during low-activity windows"
> ATT&CK: T1110.003 (Password Spraying)
> ...

## Refining Hypotheses

If the hypothesis is too broad:
- Add "on [specific target]" (e.g., "on domain controllers")
- Add time constraints (e.g., "during business hours")
- Add environmental context (e.g., "in production network")

If the hypothesis is too narrow:
- Remove overly specific indicators
- Focus on behavior pattern, not single event
- Generalize target or timeframe
