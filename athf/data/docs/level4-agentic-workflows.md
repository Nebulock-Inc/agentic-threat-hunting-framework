# Level 4: Agentic Workflows

At Level 4, you move from **reactive assistance** to **proactive automation**. Instead of asking your AI for help with each task, you deploy autonomous agents that monitor, reason, and act based on objectives you define.

**The key difference from Level 3:** Agents operate autonomously rather than waiting for your prompts. They detect events, make decisions within guardrails, and coordinate with each other through shared memory (your LOCK-structured hunts).

---

## What Changes at Level 4

### Level 3 vs. Level 4

**Level 3 (Interactive):**

- You: "Execute hunt H-0042"
- Claude: [Runs query, creates ticket, updates hunt]
- **Pattern:** You direct every action

**Level 4 (Autonomous):**

- Agent: [Monitors CTI feed every 6 hours]
- Agent: [Detects new Qakbot campaign, searches past hunts]
- Agent: [Generates draft hunt H-0156.md, flags for review]
- Agent: [Posts to Slack: "New hunt ready for review"]
- **Pattern:** Agent acts on objectives, you validate

### Success at Level 4

- Agents **monitor** CTI feeds without your intervention
- Agents **generate** draft hunts based on new threats
- Agents **coordinate** through shared LOCK memory
- You **validate and approve** rather than create from scratch

---

## Multi-Agent Architecture

At Level 4, multiple specialized agents work together, coordinating through your LOCK-structured hunt repository.

### Example Agent Roles

#### CTI Monitor Agent

**Role:** Watch threat feeds and identify relevant TTPs

**Triggers:**

- Scheduled: Every 6 hours
- Webhook: New threat intel published

**Actions:**

1. Query CTI feeds (MISP, AlienVault OTX, vendor feeds)
2. Extract MITRE ATT&CK techniques
3. Search past hunts: "Have we covered this technique?"
4. If new technique → trigger Hypothesis Generator Agent

#### Hypothesis Generator Agent

**Role:** Create draft hunt files in LOCK format

**Triggers:**

- Agent event from CTI Monitor: "New technique detected"

**Actions:**

1. Search past hunts for related TTPs
2. Review lessons learned from similar hunts
3. Generate LOCK-formatted hypothesis
4. Validate query syntax
5. Create draft hunt file (hunts/H-XXXX.md)
6. Trigger Validator Agent

#### Validator Agent

**Role:** Review draft hunts for feasibility

**Triggers:**

- Agent event from Hypothesis Generator: "Draft ready"

**Actions:**

1. Check query against data sources (from AGENTS.md)
2. Validate MITRE technique IDs
3. Verify data source availability
4. Flag issues or approve for review
5. Trigger Notifier Agent

#### Notifier Agent

**Role:** Alert analysts when human review is needed

**Triggers:**

- Agent event from Validator: "Review needed"

**Actions:**

1. Post to Slack (#threat-hunting channel)
2. Create GitHub issue with label "hunt-review"
3. Send email summary to security team
4. Update hunt tracking dashboard

---

## Example Multi-Agent Workflow

### Scenario: New Qakbot Campaign Detected

**1. CTI Monitor Agent (Autonomous - 06:00 UTC)**

```
[Agent runs scheduled job]
- Queries MISP feed for new indicators
- Detects: Qakbot campaign using T1059.003 (Windows Command Shell)
- Searches past hunts: grep "T1059.003" hunts/*.md
- Result: No prior coverage of this sub-technique
- Decision: New threat detected, trigger Hypothesis Generator
```

**2. Hypothesis Generator Agent (06:02 UTC)**

```
[Triggered by CTI Monitor]
- Reviews similar hunts: H-0042 (PowerShell), H-0089 (Process Execution)
- Extracts lessons: "Include parent-child process chains", "Filter System32 parents"
- Generates LOCK hypothesis:

  Learn: Qakbot campaign using T1059.003 detected in CTI
  Observe: Adversaries spawn cmd.exe from suspicious parents (Office, browsers)
  Check: [Generated Splunk query with bounds and limits]
  Keep: [Placeholder for execution results]

- Creates: hunts/H-0156.md
- Validates query syntax
- Decision: Draft ready, trigger Validator
```

**3. Validator Agent (06:03 UTC)**

```
[Triggered by Hypothesis Generator]
- Reads AGENTS.md for data source availability
- Checks: index=sysmon exists ✓
- Checks: EventCode=1 available ✓
- Validates: MITRE technique T1059.003 format ✓
- Reviews: Query has time bounds ✓
- Reviews: Query has result limits ✓
- Decision: Hunt validated, trigger Notifier
```

**4. Notifier Agent (06:04 UTC)**

```
[Triggered by Validator]
- Posts to Slack #threat-hunting:
  "🔍 New hunt H-0156 ready for review
  - Technique: T1059.003 (Windows Command Shell)
  - Threat: Qakbot campaign
  - Status: Draft generated, validation passed
  - Review: https://github.com/org/hunts/pull/156"

- Creates GitHub issue #156:
  Title: "Review hunt H-0156: Qakbot T1059.003 detection"
  Labels: hunt-review, auto-generated
  Assigned: @security-team

- Decision: Notification sent, workflow complete
```

**5. You Wake Up (08:30 UTC)**

```
Slack notification: "3 new draft hunts created overnight"

You review H-0156.md:
- Learn section: Clear threat context ✓
- Observe section: Specific hypothesis ✓
- Check section: Well-bounded query ✓
- Data sources: Available in our environment ✓

Decision: Approve and execute

You: "Execute hunt H-0156"
Claude: [Runs via Splunk MCP, finds 2 suspicious events, creates tickets]
```

**Result:** From threat detection to actionable investigation in under 3 hours, most of it automated.

---

## Example Agent Configuration

Below is a **conceptual example** showing how agents could be configured. This is not included in the repository - it represents a pattern you would implement using your chosen agent framework.

```yaml
# Example: config/agent_workflow.yaml
# Conceptual configuration for autonomous agents

agents:
  - name: cti_monitor
    role: Watch CTI feeds and identify relevant threats
    triggers:
      - schedule: "every 6 hours"
      - webhook: "/api/cti/new"
    actions:
      - search_hunts(technique_id)  # Check if we've hunted this before
      - trigger_agent("hypothesis_generator") if new_technique
    guardrails:
      - log_all_searches: true
      - max_triggers_per_day: 10

  - name: hypothesis_generator
    role: Create LOCK-formatted hunt hypotheses
    triggers:
      - agent_event: "cti_monitor.new_technique"
    actions:
      - search_hunts(technique_id)  # Get historical context
      - apply_lessons_learned()
      - generate_lock_hypothesis()
      - validate_query_syntax()
      - create_draft_hunt_file()
      - trigger_agent("validator")
    guardrails:
      - require_data_source_validation: true
      - max_drafts_per_day: 5

  - name: validator
    role: Review and validate draft hunts
    triggers:
      - agent_event: "hypothesis_generator.draft_ready"
    actions:
      - validate_query(query, platform)
      - check_data_source_compatibility()
      - verify_mitre_technique_format()
      - flag_for_human_review() if issues_found
      - trigger_agent("notifier") if validation_passed
    guardrails:
      - block_if_data_source_missing: true
      - require_time_bounds: true

  - name: notifier
    role: Alert analysts when hunts need review
    triggers:
      - agent_event: "validator.review_needed"
      - agent_event: "validator.validation_passed"
    actions:
      - post_to_slack(channel="#threat-hunting", hunt_id)
      - create_github_issue(labels=["hunt-review", "auto-generated"])
      - send_email_summary(recipients=security_team)
    guardrails:
      - rate_limit: "max 20 notifications per day"

# Global Guardrails
guardrails:
  - all_hunts_require_human_approval: true
  - no_automatic_query_execution: true
  - log_all_agent_actions: true
  - daily_summary_report: true
  - halt_on_error: true

# Shared Memory
memory:
  - hunt_repository: "hunts/"
  - context_files: ["AGENTS.md", "knowledge/hunting-knowledge.md"]
  - lessons_learned: "automatically extracted from Keep sections"
```

---

## Implementation Options

Level 4 can be built using various agent frameworks. Choose based on your team's experience and requirements.

### LangGraph

**Best for:** Stateful, multi-step workflows

**Strengths:**

- Built on LangChain ecosystem
- Graph-based workflow definition
- State management between steps
- Good for complex orchestration

**Example use case:** Multi-agent pipeline with conditional branching based on validation results

### CrewAI

**Best for:** Role-based agent collaboration

**Strengths:**

- Define agents by role (researcher, analyst, writer)
- Natural delegation between agents
- Built-in task management
- Good for team-based patterns

**Example use case:** CTI researcher agent + hypothesis writer agent + validator agent working together

### AutoGen

**Best for:** Conversational agent patterns

**Strengths:**

- Microsoft-backed framework
- Multi-agent conversations
- Human-in-the-loop patterns
- Good for collaborative workflows

**Example use case:** Agents discussing and refining hunts through conversation before presenting to humans

### Custom Orchestration

**Best for:** Purpose-built solutions

**Strengths:**

- Full control over architecture
- Integrate exactly your tools
- No framework overhead
- Optimized for your environment

**Example use case:** Simple Python scripts with cron triggers and API calls to your specific stack

---

## Guardrails and Safety

At Level 4, guardrails are critical. Agents operate autonomously, so you must define boundaries.

### Essential Guardrails

**1. Human Approval Required**

```yaml
guardrails:
  - all_hunts_require_human_approval: true
  - no_automatic_query_execution: true
```

Agents can draft hunts, but humans must approve before execution.

**2. Logging Everything**

```yaml
guardrails:
  - log_all_agent_actions: true
  - audit_trail: true
```

Every agent action must be logged for review.

**3. Rate Limiting**

```yaml
guardrails:
  - max_drafts_per_day: 10
  - max_notifications_per_day: 20
```

Prevent runaway agents from flooding your team.

**4. Validation Gates**

```yaml
guardrails:
  - require_data_source_validation: true
  - require_time_bounds_in_queries: true
```

Agents must validate hunts against your environment before flagging for review.

**5. Halt on Error**

```yaml
guardrails:
  - halt_on_error: true
  - notify_on_failure: true
```

If an agent encounters an error, stop the workflow and alert humans.

---

## Getting Started with Level 4

### Phase 1: Planning (Week 1)

1. **Define objectives:** What should agents do autonomously?
2. **Identify workflows:** Which manual tasks are repetitive?
3. **Choose framework:** LangGraph, CrewAI, AutoGen, or custom?
4. **Design guardrails:** What are your safety boundaries?

### Phase 2: Single Agent (Weeks 2-4)

1. **Start simple:** Deploy one monitoring agent (CTI monitor)
2. **Test in sandbox:** Run agent in isolated environment
3. **Validate outputs:** Review agent-generated drafts
4. **Tune parameters:** Adjust triggers and thresholds

### Phase 3: Multi-Agent (Weeks 5-8)

1. **Add second agent:** Hypothesis generator
2. **Test coordination:** Verify agents communicate correctly
3. **Add third agent:** Validator
4. **Complete pipeline:** CTI Monitor → Generator → Validator → Notifier

### Phase 4: Production (Weeks 9-12)

1. **Deploy to production:** Run agents on real CTI feeds
2. **Monitor closely:** Review all agent actions daily
3. **Iterate on guardrails:** Adjust based on false positives
4. **Measure impact:** Track time saved and hunt quality

---

## Success Metrics

Track these metrics to measure Level 4 success:

**Automation Metrics:**

- **Draft hunts generated per week** (target: 3-5)
- **Time from threat detection to hunt draft** (target: <1 hour)
- **Human review time per draft** (target: <10 minutes)

**Quality Metrics:**

- **Draft approval rate** (target: >80%)
- **Query validation success rate** (target: >95%)
- **False positive rate in agent-generated hunts** (target: <20%)

**Impact Metrics:**

- **Total time saved per week** (target: 5-10 hours)
- **Hunts executed per month** (increase over Level 3 baseline)
- **Mean time to detect new threats** (decrease over manual process)

---

## Common Patterns

### Pattern 1: CTI-Driven Hunt Generation

**Flow:** CTI Feed → Technique Extraction → Hunt Generation → Human Review

**Agents:** CTI Monitor + Hypothesis Generator + Validator + Notifier

### Pattern 2: Alert-Driven Investigation

**Flow:** SIEM Alert → Historical Search → Draft Response → Ticket Creation

**Agents:** Alert Monitor + Context Researcher + Response Generator + Ticket Creator

### Pattern 3: Scheduled Hunt Refresh

**Flow:** Daily Schedule → Review Old Hunts → Re-execute Queries → Update Results

**Agents:** Scheduler + Hunt Executor + Results Analyzer + Documentation Updater

---

## Learn More

- **Maturity Model:** [maturity-model.md](maturity-model.md)
- **Level 3 Examples:** [../integrations/README.md](../integrations/README.md)
- **Getting Started:** [getting-started.md](getting-started.md)
- **Integration Catalog:** [../integrations/MCP_CATALOG.md](../integrations/MCP_CATALOG.md)

---

## Remember

**Success can look like many things at Level 4.** You might have agents that autonomously execute queries using MCP servers, or agents that orchestrate multi-step workflows. At this stage, you're mature enough to make architectural decisions based on your team's needs and risk tolerance.

**The key:** All agents share the same memory layer - your LOCK-structured hunts - ensuring consistency and enabling true coordination.
