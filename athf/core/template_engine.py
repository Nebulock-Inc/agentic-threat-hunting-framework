"""Render hunt templates with metadata."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from jinja2 import Template

from athf.core.verdicts import UNFILLED_HUNTER

# Default bundled template - used when no custom template exists
HUNT_TEMPLATE = """---
hunt_id: {{ hunt_id }}
title: {{ title }}
status: {{ status }}
date: {{ date }}
hunter: {{ hunter }}
{% if hunt_type %}hunt_type: {{ hunt_type }}
{% endif %}platform: {{ platform }}
tactics: {{ tactics }}
techniques: {{ techniques }}
data_sources: {{ data_sources }}
related_hunts: []
{% if spawned_from %}spawned_from: {{ spawned_from }}
{% endif %}{% if hypothesis_duration_minutes %}hypothesis_duration_minutes: {{ hypothesis_duration_minutes }}
{% endif %}findings_count: 0
findings: []
ruled_out: []
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
{% if spawned_from %}- **Research Document:** See [{{ spawned_from }}](../research/{{ spawned_from }}.md) for detailed pre-hunt research
{% endif %}

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

Things you're reporting as malicious. Only `confirmed` and `suspected` belong here.

| **Verdict** | **Subject** | **Ticket** | **Evidence** | **Independent Confirmation** |
|-------------|-------------|-----------|--------------|------------------------------|
| `confirmed` | [Host, account, or resource] | [INC-####] | [Telemetry that surfaced it] | [What established root cause outside the logs] |
| `suspected` | [Host, account, or resource] | [INC-####] | [Telemetry that surfaced it] | None — telemetry only |

**The evidence gate:** `confirmed` requires telemetry **plus** something from outside the log
corpus — controlled reproduction, host forensics, or configuration review. Telemetry alone never
reaches `confirmed`. If you couldn't confirm, the verdict is `suspected`.

### Ruled Out

Results that closed the question. `attempted_not_vulnerable` is often the most valuable row in a
customer-facing report.

| **Verdict** | **Subject** | **What Closed It** |
|-------------|-------------|--------------------|
| `attempted_not_vulnerable` | [Host, account, or resource] | [Name the control that held and how you verified it] |
| `benign` | [Host, account, or resource] | [The legitimate activity that explains it] |
| `inconclusive` | [Host, account, or resource] | [Which telemetry was missing or too sparse] |

**Counts:** `confirmed` [N] · `suspected` [N] · `attempted_not_vulnerable` [N] · `benign` [N] · `inconclusive` [N]

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


def yaml_str(value: object) -> str:
    """Return ``value`` as a double-quoted YAML scalar.

    A JSON string literal is also a valid YAML double-quoted scalar, so this
    covers colons, commas, brackets, quotes and newlines in one move. Unlike
    Jinja's ``tojson`` it does not HTML-escape or ``\\u``-escape: hunt files are
    markdown people read, diff and grep, so ``café`` and ``AT&T`` stay as typed.
    """
    return json.dumps(str(value), ensure_ascii=False)


def yaml_flow_seq(values: Optional[Iterable[object]]) -> str:
    """Render ``values`` as a YAML flow sequence with every element quoted.

    Unquoted elements fail silently: ``[EDR - Fields: process.name, CloudTrail, S3]``
    parses as a mapping and two strings, not three strings, and nothing raises.
    """
    if not values:
        return "[]"
    return "[" + ", ".join(yaml_str(v) for v in values) + "]"


def _load_hunt_template() -> str:
    """Load hunt template, preferring workspace custom template over bundled default.

    Checks for a Jinja2 template at ./templates/HUNT_TEMPLATE.j2 first.
    Falls back to the bundled HUNT_TEMPLATE constant.

    Returns:
        Jinja2 template string
    """
    custom_template = Path("templates") / "HUNT_TEMPLATE.j2"
    if custom_template.exists():
        try:
            content = custom_template.read_text(encoding="utf-8")
            # Basic sanity check: must contain Jinja2 syntax
            if "{{" in content and "}}" in content:
                return content
        except (OSError, UnicodeDecodeError):
            pass  # Fall through to default
    return HUNT_TEMPLATE


_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)


def _ensure_frontmatter_field(rendered: str, key: str, value: str) -> str:
    """Insert ``key: value`` into rendered YAML frontmatter if it is absent.

    Workspaces snapshot the hunt template into ``templates/HUNT_TEMPLATE.j2``
    at ``athf init`` time, and that snapshot wins over the bundled template.
    A snapshot taken before a field existed silently drops it, so the value
    the user chose on the command line would never reach the file. Fields
    the template already emits (even as an empty value) are left alone.
    """
    match = _FRONTMATTER_RE.match(rendered)
    if not match:
        return rendered
    block = match.group(1)
    if re.search(rf"^{re.escape(key)}\s*:", block, re.M):
        return rendered
    # Prefer to sit after the hunter line (mirrors the bundled template);
    # otherwise append to the end of the frontmatter.
    hunter_line = re.search(r"^hunter\s*:[^\n]*\n", block, re.M)
    if hunter_line:
        insert_at = match.start(1) + hunter_line.end()
        return rendered[:insert_at] + f"{key}: {value}\n" + rendered[insert_at:]
    insert_at = match.end(1)
    return rendered[:insert_at] + f"\n{key}: {value}" + rendered[insert_at:]


def _quote_frontmatter_scalar(rendered: str, key: str, value: str) -> str:
    """Quote ``key``'s value in rendered frontmatter when it was emitted bare.

    Same snapshot problem as :func:`_ensure_frontmatter_field`, different
    symptom: a snapshot taken while the template wrote ``title: {{ title }}``
    keeps writing it bare after the bundled template is fixed, so a colon in
    the title still breaks the document for every workspace that ran ``init``.

    Fixing the rendered output rather than the template covers every snapshot,
    old or new, without an upgrade step. The repair is exact: it only fires
    when the line holds ``value`` verbatim and unquoted — which is what the
    old template produced — and leaves alone anything a custom template
    already quoted or reshaped.
    """
    match = _FRONTMATTER_RE.match(rendered)
    if not match:
        return rendered
    block = match.group(1)
    line = re.search(rf"^{re.escape(key)}:[ \t]*", block, re.M)
    if not line:
        return rendered
    start = line.end()
    end = start + len(value)
    if block[start:end] != value or block[end : end + 1] not in ("", "\n", "\r"):
        return rendered
    offset = match.start(1)
    return rendered[: offset + start] + yaml_str(value) + rendered[offset + end :]


def render_hunt_template(
    hunt_id: str,
    title: str,
    technique: Optional[str] = None,
    tactics: Optional[list] = None,
    platform: Optional[list] = None,
    data_sources: Optional[list] = None,
    hunter: str = UNFILLED_HUNTER,
    hypothesis: Optional[str] = None,
    threat_context: Optional[str] = None,
    actor: Optional[str] = None,
    behavior: Optional[str] = None,
    location: Optional[str] = None,
    evidence: Optional[str] = None,
    spawned_from: Optional[str] = None,
    hypothesis_duration_minutes: Optional[float] = None,
    hunt_type: Optional[str] = None,
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
        spawned_from: Research document ID (e.g., R-0001) that this hunt is based on
        hypothesis_duration_minutes: Time spent generating hypothesis (from athf agent run)
        hunt_type: Hunt category (hypothesis | baseline | model-assisted); omitted if None

    Returns:
        Rendered hunt markdown content
    """
    # Build techniques list
    techniques_list = [technique] if technique else []

    # Format lists as YAML flow sequences. Elements are quoted because they are
    # free text: a data source like "EDR - Fields: process.name" or a platform
    # like "CloudTrail, S3" would otherwise change the shape of the parsed list
    # without an error. Pre-formatting here (rather than in the template) means
    # workspace snapshots of older templates get the fix too.
    tactics_str = yaml_flow_seq(tactics)
    platform_str = yaml_flow_seq(platform)
    data_sources_str = yaml_flow_seq(data_sources)
    tags_str = "[]"

    template = Template(_load_hunt_template())

    rendered = str(template.render(
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
        spawned_from=spawned_from,
        hypothesis_duration_minutes=hypothesis_duration_minutes,
        hunt_type=hunt_type,
    ))

    if hunt_type:
        rendered = _ensure_frontmatter_field(rendered, "hunt_type", hunt_type)

    # Prose fields. A colon in a title is ordinary ("Technique: Variant") and
    # breaks the document when written bare; the default hunter placeholder
    # "[Your Name]" written bare is a one-element list, not a string.
    rendered = _quote_frontmatter_scalar(rendered, "title", title)
    rendered = _quote_frontmatter_scalar(rendered, "hunter", hunter)

    return rendered
