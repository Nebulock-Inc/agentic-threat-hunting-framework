"""Render hunt templates with metadata."""

from datetime import datetime
from typing import Optional

from jinja2 import Template

HUNT_TEMPLATE = """---
hunt_id: {{ hunt_id }}
title: {{ title }}
status: {{ status }}
date: {{ date }}
hunter: {{ hunter }}
platform: {{ platform }}
tactics: {{ tactics }}
techniques: {{ techniques }}
data_sources: {{ data_sources }}
related_hunts: []
findings_count: 0
true_positives: 0
false_positives: 0
customer_deliverables: []
tags: {{ tags }}
---

# {{ hunt_id }}: {{ title }}

**Hunt Metadata**

- **Date:** {{ date }}
- **Hunter:** {{ hunter }}
- **Status:** {{ status }}
- **MITRE ATT&CK:** {{ techniques[0] if techniques else '[Primary Technique]' }}

---

## LEARN: Prepare the Hunt

### Hypothesis Statement

{{ hypothesis if hypothesis else '[What behavior are you looking for? What will you observe if the hypothesis is true?]' }}

### Threat Context

{{ threat_context if threat_context else '[What threat actor/malware/TTP motivates this hunt?]' }}

### ABLE Scoping

| **Field**   | **Your Input** |
|-------------|----------------|
| **Actor** *(Optional)* | {{ actor if actor else '[Threat actor or malware family]' }} |
| **Behavior** | {{ behavior if behavior else '[TTP or behavior pattern]' }} |
| **Location** | {{ location if location else '[Systems, networks, or environments to hunt]' }} |
| **Evidence** | {{ evidence if evidence else '[Data sources and key fields to examine]' }} |

### Threat Intel & Research

- **MITRE ATT&CK Techniques:** {{ ', '.join(techniques) if techniques else '[List relevant techniques]' }}
- **CTI Sources & References:** [Links to reports, blogs, etc.]

### Related Tickets

| **Team** | **Ticket/Details** |
|----------|-------------------|
| **SOC/IR** | [Ticket numbers or N/A] |

---

## OBSERVE: Expected Behaviors

### What Normal Looks Like

[Describe legitimate activity that should not trigger alerts]

### What Suspicious Looks Like

[Describe adversary behavior patterns to hunt for]

### Expected Observables

- **Processes:** [Process names, command lines]
- **Network:** [Connections, protocols, domains]
- **Files:** [File paths, extensions, sizes]
- **Registry:** [Registry keys if applicable]
- **Authentication:** [Login patterns if applicable]

---

## CHECK: Execute & Analyze

### Data Source Information

- **Index/Data Source:** {{ data_sources[0] if data_sources else '[SIEM index or data source]' }}
- **Time Range:** [Date range for hunt]
- **Events Analyzed:** [Approximate count]
- **Data Quality:** [Assessment of data completeness]

### Hunting Queries

#### Initial Query

```
[Your initial query]
```

**Query Notes:**
- [What did this query return?]
- [What worked? What didn't?]

### Query Performance

**What Worked Well:**
- [Effective filters or techniques]

**What Didn't Work:**
- [Challenges or limitations]

**Iterations Made:**
- [Document query evolution]

---

## KEEP: Findings & Response

### Executive Summary

[Concise summary of hunt results and key findings]

### Findings

| **Finding** | **Ticket** | **Description** |
|-------------|-----------|-----------------|
| [Type] | [Ticket] | [Description] |

**True Positives:** 0
**False Positives:** 0

### Lessons Learned

**What Worked Well:**
- [Successes]

**What Could Be Improved:**
- [Areas for improvement]

**Telemetry Gaps Identified:**
- [Missing data sources or visibility gaps]

### Follow-up Actions

- [ ] [Action item 1]
- [ ] [Action item 2]

---

**Hunt Completed:** [Date]
**Next Review:** [Date for recurring hunt if applicable]
"""


def render_hunt_template(
    hunt_id: str,
    title: str,
    technique: Optional[str] = None,
    tactics: Optional[list] = None,
    platform: Optional[list] = None,
    data_sources: Optional[list] = None,
    hunter: str = "[Your Name]",
    hypothesis: Optional[str] = None,
    threat_context: Optional[str] = None,
    actor: Optional[str] = None,
    behavior: Optional[str] = None,
    location: Optional[str] = None,
    evidence: Optional[str] = None,
) -> str:
    """Render a hunt template with provided metadata.

    Args:
        hunt_id: Hunt identifier (e.g., H-0001)
        title: Hunt title
        technique: Primary MITRE technique (e.g., T1003.001)
        tactics: List of MITRE tactics
        platform: List of platforms (Windows, Linux, macOS, Cloud)
        data_sources: List of data sources
        hunter: Hunter name
        hypothesis: Hypothesis statement
        threat_context: Threat context description
        actor: Threat actor (for ABLE)
        behavior: Behavior description (for ABLE)
        location: Location/scope (for ABLE)
        evidence: Evidence description (for ABLE)

    Returns:
        Rendered hunt markdown content
    """
    # Build techniques list
    techniques_list = [technique] if technique else []

    # Format lists as YAML arrays
    tactics_str = f"[{', '.join(tactics)}]" if tactics else "[]"
    platform_str = f"[{', '.join(platform)}]" if platform else "[]"
    data_sources_str = f"[{', '.join(data_sources)}]" if data_sources else "[]"
    tags_str = "[]"

    template = Template(HUNT_TEMPLATE)

    return template.render(
        hunt_id=hunt_id,
        title=title,
        status="planning",
        date=datetime.now().strftime("%Y-%m-%d"),
        hunter=hunter,
        platform=platform_str,
        tactics=tactics_str,
        techniques=techniques_list,
        data_sources=data_sources_str,
        tags=tags_str,
        hypothesis=hypothesis,
        threat_context=threat_context,
        actor=actor,
        behavior=behavior,
        location=location,
        evidence=evidence,
    )
