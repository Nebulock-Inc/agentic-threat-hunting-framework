# GATES Dual-Purpose YAML Schema

**Purpose:** Serve BOTH agent knowledge base AND deployment automation

**Updated:** 2026-09-22

## Design Principles

1. **Agent Knowledge Base:**
   - Structured for querying ("show me all T1567 detections")
   - Captures patterns and learnings ("what tuning works for cloud storage?")
   - Historical reference ("why did this fail T-gate?")

2. **Deployment Automation:**
   - Valid detection templates (ready for automation tools)
   - Complete operational parameters
   - No manual YAML writing needed

3. **Output Format by Verdict:**
   - **PROMOTE/CONDITIONAL** → YAML format (`H-XXXX_GATES.yaml`) - deployment-ready
   - **HOLD/TIME_BOX/RECURRING_HUNT** → Markdown format (`H-XXXX_GATES.md`) - analysis/guidance
   - Single file per hunt, format determined by the **hunt-level** verdict

## This document is the contract

Consumers parse these files. Anything not defined here is not guaranteed to exist,
and anything defined here must not change shape without a version bump.

`SKILL.md` contains an abbreviated output template for the authoring agent. That
template is an **instance** of this schema, not a second schema — where the two ever
disagree, this document wins and SKILL.md is the bug. Field names are identical in
both by construction.

## Hunt-level vs candidate-level verdicts

There are **two** verdicts in every document and they are not the same thing:

| Field | Scope | What it drives |
|-------|-------|----------------|
| `gates_validation.verdict` | the whole hunt | which **file** gets written (`.yaml` vs `.md`) |
| `detections[].gates_assessment.verdict` | one candidate | what the consumer **does** with that candidate |

A hunt whose verdict is PROMOTE writes a `.yaml`, and that file may legitimately
contain candidates verdicted TIME_BOX, HOLD or DROP — a strong hunt routinely
produces one good detection and two rejected ideas. **Consumers must handle every
verdict inside a `.yaml`, not only the deployable ones.**

Do not infer one verdict from the other. `gates_validation.verdict` is the hunt's
headline, not a max() or a mode() over the candidates.

## Canonical enums

Single source of truth. These are closed sets — a value outside them is invalid,
not an extension point. Uppercase, underscores, no hyphens and no spaces.

```yaml
# Verdict (both hunt-level and candidate-level)
PROMOTE         # ready to build now
CONDITIONAL     # build after stated prerequisites are met
TIME_BOX        # build with an expiry date (IOC-shelf-life logic)
RECURRING_HUNT  # do not build a standing detection; re-run as a periodic hunt
HOLD            # not ready; reasoning recorded, nothing to build
DROP            # do not build; already covered or not worth covering

# Criteria result (per BASE gate)
PASS | PARTIAL | FAIL

# Deployment status
EXPERIMENTAL | ACTIVE | INACTIVE

# Engine — the detection engines the receiving framework can execute.
# Adding a value here is a breaking change and requires a matching change
# downstream; ADEF CI-enforces exactly this set.
sigma | sql | sch_sql | composite
```

`RECURRING_HUNT` is a first-class verdict, not a `HOLD` with an annotation. Prior
drafts had no slot for it and forced authors to write `verdict: HOLD` plus a
free-form `classification` field; consumers then had to read two fields to learn
one fact. Read `verdict` and nothing else.

## Candidate identity

**GATES does not assign detection IDs.** At validation time it is not yet known
which candidates become detections — that is the whole point of the verdict — so
minting a durable detection identifier here would name things that will never
exist. The detection system downstream owns its own IDs (ADEF mints `D-XXXX`) and
is solely responsible for them.

What GATES owns is a **stable handle for a candidate within its hunt**:

```yaml
detections:
  - candidate_id: megasync-process-execution   # kebab-case, hunt-scoped, required
```

Rules:

1. **Derive it from the candidate's behavior, never its position.** Earlier drafts
   used a bare ordinal (`1`, `2`, `3`). Ordinals are not stable: the list gets
   reordered by score or priority between runs (an earlier example emitted them in
   the order 2, 1, 4, 3), so a consumer keyed on the ordinal silently re-attributes
   candidate 2's history to candidate 1. A slug survives reordering, insertion and
   deletion of siblings.
2. **Keep it byte-identical when GATES is re-run on an edited hunt.** This is the
   only thing that makes re-import idempotent: a consumer matches on
   `(hunt_id, candidate_id)`, so a changed slug reads as a brand-new candidate.
3. **Change it only when the candidate's meaning changes** — at which point it *is*
   a new candidate and a new slug is correct.
4. **Hybrid decomposition** (one finding split into behavioral + IOC layers, see
   SKILL.md) shares a stem and suffixes the layer:
   `powershell-download-cradle-behavioral` / `powershell-download-cradle-ioc`.
   This replaces the old `1a` / `1b` ordinal variants.

A slug is not a perfect key — renaming the candidate breaks the match. That is the
intended trade: a rename is a visible, deliberate edit that a human can reconcile,
whereas an ordinal reshuffle is invisible and corrupts silently.

## Required fields

A candidate whose verdict is **deployable** — PROMOTE, CONDITIONAL, or TIME_BOX —
is a promise that something can be built from it, so it MUST carry:

- `candidate_id`
- `name`
- `gates_assessment.verdict`
- `deployment.engine`
- `deployment.detection_logic.query`

A candidate verdicted RECURRING_HUNT, HOLD or DROP needs no `deployment` block at
all; omit it rather than emitting an empty one.

## Schema Structure

```yaml
# =============================================================================
# SECTION 1: HUNT METADATA (for agent indexing/querying)
# =============================================================================
hunt_metadata:
  hunt_id: H-XXXX
  title: "Hunt title"
  date: 2026-MM-DD
  hunter: "Name"
  
  # For agent queries: "Find hunts covering T1567"
  techniques:
    - T1567.002  # Exfiltration to Cloud Storage
    - T1053.005  # Scheduled Task/Job: Scheduled Task
  
  tactics:
    - exfiltration
    - persistence
  
  # Which OS/platform the candidates target. REQUIRED when any candidate is
  # deployable: a detection has to be filed against a platform, and a consumer
  # that has to infer one from field names is guessing. Use a single-element list
  # for the common case; multiple entries mean genuinely cross-platform logic.
  platforms:
    - windows   # windows | macos | linux | cloud | network | saas | container
  
  # Hunt outcomes (for pattern analysis)
  hunt_outcomes:
    true_positives: 0
    false_positives: 14
    findings_count: 3
    hunt_window_days: 30
    events_analyzed: 70000000000  # round order-of-magnitude, not a verbatim production count
    data_sources:
      - ClickHouse unified_events
      - Microsoft Defender EDR

# =============================================================================
# SECTION 2: GATES VALIDATION SUMMARY (for agent learning)
# =============================================================================
gates_validation:
  # --- REQUIRED ---------------------------------------------------------------
  # The hunt-level verdict. Drives the .yaml-vs-.md file choice and nothing else;
  # see "Hunt-level vs candidate-level verdicts". Canonical enum only.
  verdict: PROMOTE
  
  # --- OPTIONAL ---------------------------------------------------------------
  date: 2026-MM-DD
  validator: "Agent/Human name"
  framework_version: "2.0"
  
  # Overall hunt classification (for agent categorization)
  hunt_classification:
    type: behavioral_detection  # behavioral_detection | risk_assessment | multi_step | baseline | telemetry_gap
    detections_proposed: 3
  
  # Per-verdict candidate counts. Keys are the canonical verdict enum; omit the
  # zeroes if you like. This is derived data — `detections` is authoritative, and
  # a consumer that disagrees with these counts should trust `detections`.
  #
  # This is the ONLY place per-verdict counts live. Earlier drafts also carried
  # `detections_promoted` / `detections_conditional` under `hunt_classification`,
  # which meant two independently-maintained tallies of the same fact and no rule
  # for which won when they disagreed — and they did disagree (one example counted
  # its single CONDITIONAL candidate as `detections_promoted: 1`, telling a
  # consumer a detection was deploy-ready when none was). A closed enum keyed map
  # also can't drift as verdicts are added; a field-per-verdict can.
  verdict_breakdown:
    PROMOTE: 2
    CONDITIONAL: 1
  
  # Mean of the candidates' base_score values. Float. Derived and purely
  # informational — it is NOT a hunt-level score and nothing may be verdicted from
  # it. A hunt with one 5.0 and one 0.0 candidate averages 2.5, which describes
  # neither candidate.
  base_score_average: 4.5   # (5.0 + 5.0 + 3.5) / 3 — the three candidates below
  
  # NEW: Fast-path decisions
  # true when the hunt found 0 instances of the behavior AND the deciding gate is
  # G or S, i.e. the zero-prevalence rule under Step 4's precedence table: a
  # TIME_BOX refresh cycle and a RECURRING_HUNT cadence are both maintenance with
  # no expected yield when the behavior does not occur here, so both resolve to
  # HOLD. Do NOT set this for a candidate with no FAIL — 0 TPs over a clean
  # baseline is a proactive PROMOTE, which is the opposite call.
  fast_path_hold: false
  
  # NEW: Proactive deployment confidence (for zero-TP hunts)
  proactive_deployment_confidence: "HIGH"  # HIGH | MEDIUM | LOW | N/A
  proactive_justification: "0 suspicious events in ~1B baseline events = high FP-free confidence"
  
  # NEW: Automation feasibility (S-gate enhancement)
  automation_feasibility: "PASS"  # PASS | FAIL | CONDITIONAL
  automation_assessment: "SOC can act on alert without per-alert business context"
  
  # NEW: Telemetry gaps (if Step 0.5 identified limitations)
  telemetry_gaps: []
    # - gap: "EUID field unpopulated - cannot detect UID transitions"
    #   impact: "Linux LPE exploits undetectable"
    #   recommendation: "Ingest auditd/eBPF data"
  
  # NEW: Prerequisites blocking promotion
  prerequisites: []
    # - type: "tooling"
    #   requirement: "Run overlap validation"
    #   blocker: true
    #   effort: "1 day"
  
  # NEW: False positive sources (service accounts, automation, dev tools)
  false_positive_sources: []
    # - category: "service_accounts"
    #   examples: ["Active Directory Agent", "JAMF MDM"]
    #   volume: 67
    #   mitigation: "Service account allowlist required"
  
  # Aggregate learnings (for agent pattern recognition)
  key_learnings:
    - "Tool signatures with low volume (<2/day) typically score 5.0"
    - "Cloud service detections require per-tenant baseline"
    - "Scheduled task detections have zero FP rate when specific to tool name"
    - "Zero-baseline proactive hunts (0 suspicious / large sample) boost T-gate confidence"
    - "IOC-based detections with 0 TPs → automatic HOLD (no operational need)"
  
  # Pattern metadata (for agent queries: "Show me all process_execution patterns")
  detection_patterns:
    - pattern_type: process_execution
      verdict: PROMOTE
      base_score: 5.0
      typical_fp_rate: low
    - pattern_type: scheduled_task
      verdict: PROMOTE
      base_score: 5.0
      typical_fp_rate: very_low
    - pattern_type: network_connection
      verdict: CONDITIONAL
      base_score: 3.5   # must match the candidate below, not a rounded 3
      typical_fp_rate: high

# =============================================================================
# SECTION 3: DETECTION DEFINITIONS (for deployment automation)
# =============================================================================
detections:
  
  # Detection 1
  - candidate_id: megasync-process-execution
    name: "MEGAsync Process Execution Detection"
    
    # GATES metadata (for agent learning)
    gates_assessment:
      # Canonical verdict enum — see "Canonical enums". No other value is valid.
      verdict: PROMOTE
      # Float on a 0.0-5.0 scale. PASS=1.0, PARTIAL=0.5, FAIL=0.0, summed over the
      # five BASE gates. Never the "5/5" string form — consumers do arithmetic on it.
      base_score: 5.0
      criteria:
        generalizable: PASS    # Behavioral pattern, repeatable
        additive: PASS          # Fills T1567.002 gap
        tunable: PASS           # Low volume, no allowlist needed
        exposure_tested: PASS   # Multiple angles tested
        sustainable: PASS       # <2/day, no maintenance
      
      # Compact rationale (agents learn patterns)
      scoring_rationale:
        g_evidence: "Tool signature (MEGAsync.exe), not IOC-based"
        a_evidence: "No existing cloud storage process detection for T1567.002"
        t_evidence: "1 event/month observed, specific process name"
        e_evidence: "Hunt tested process + network + scheduled task angles"
        s_evidence: "1/month volume sustainable, no allowlist maintenance"
      
      # Learning for future hunts
      pattern_learned: "Tool-specific process detection with low volume scores high on T and S gates"
      recommended_for_similar: "Other cloud sync tools (Dropbox, Box, OneDrive personal)"
    
    # Deployment template (ready for automation).
    # REQUIRED whenever the verdict is PROMOTE | CONDITIONAL | TIME_BOX.
    # Omit entirely for RECURRING_HUNT | HOLD | DROP.
    deployment:
      engine: sql  # sigma | sql | sch_sql | composite — closed set, see "Canonical enums"
      status: EXPERIMENTAL  # EXPERIMENTAL | ACTIVE | INACTIVE
      severity: medium
      
      # Always these two keys, for every engine. `query` is an opaque string in
      # whatever language `engine` names — consumers store it verbatim and must not
      # have to branch on engine to find it. A sigma candidate puts its rule body
      # here as a block scalar; it does NOT inline `selection:`/`condition:` as
      # sibling mapping keys.
      detection_logic:
        query: |
          `process.name` = 'MEGAsync.exe'
        description: |
          Detects MEGAsync process execution. MEGAsync is a MEGA cloud storage 
          sync client that can be used for data exfiltration (T1567.002).
      
      entities:
        - name: endpoint.uid
          type: endpoint
        - name: actor.user.name
          type: user
        - name: process.name
          type: other
        - name: process.file.path
          type: other
      
      alert_configuration:
        throttle:
          entity: endpoint.uid
          duration: 86400  # 1 day in seconds
        enrichment_fields:
          - process.file.path
          - process.command_line
          - parent.process.name
      
      operational_parameters:
        expected_volume: "~1 event/month (30 days: 1 event)"
        fp_rate: "Very low (1/month, all explainable as sanctioned use)"
        tuning_required: false
        allowlist_needed: false
        soak_period_days: 7
        soak_validation_criteria:
          - "FP rate <5/day"
          - "Alert volume <10/day"
          - "Query performance <30s"
      
      mitre_attack:
        - T1567.002  # Exfiltration to Cloud Storage
        - T1036.005  # Masquerading: Match Legitimate Name or Location
      
      references:
        - "Hunt H-0063: MEGAsync as Exfiltration Channel"
        - "GATES validation: hunt-promotion-analysis/H-0063_GATES.yaml"
  
  # Detection 2
  - candidate_id: megasync-scheduled-task-persistence
    name: "MEGAsync Scheduled Task Persistence"
    
    gates_assessment:
      verdict: PROMOTE
      base_score: 5.0
      criteria:
        generalizable: PASS
        additive: PASS
        tunable: PASS
        exposure_tested: PASS
        sustainable: PASS
      
      scoring_rationale:
        g_evidence: "Scheduled task pattern, tool-specific"
        a_evidence: "Fills T1053.005 gap for cloud storage persistence"
        t_evidence: "0 FPs in 30 days (2.67M task names checked)"
        e_evidence: "Hunt tested registry, file, and schtasks.exe creation"
        s_evidence: "Zero FP rate, no maintenance burden"
      
      pattern_learned: "Tool-specific scheduled task detection with zero FP rate is ideal PROMOTE candidate"
    
    deployment:
      engine: sql
      status: EXPERIMENTAL
      severity: high
      
      detection_logic:
        query: |
          `scheduled_task.name` ILIKE '%MEGAsync%'
        description: |
          Detects scheduled tasks with 'MEGAsync' in the name. Adversaries may 
          use MEGAsync for persistence and automated exfiltration (T1053.005).
      
      entities:
        - name: endpoint.uid
          type: endpoint
        - name: actor.user.name
          type: user
      
      alert_configuration:
        throttle:
          entity: endpoint.uid
          duration: 86400
      
      operational_parameters:
        expected_volume: "0 events/30 days in hunt"
        fp_rate: "Zero (0 FPs in 30-day retrohunt)"
        tuning_required: false
        allowlist_needed: false
        soak_period_days: 7
      
      mitre_attack:
        - T1053.005  # Scheduled Task/Job: Scheduled Task
        - T1567.002  # Exfiltration to Cloud Storage
  
  # Detection 3
  - candidate_id: browser-connection-to-mega
    name: "Browser Connection to MEGA Cloud Storage"
    
    gates_assessment:
      # T=FAIL forces CONDITIONAL regardless of the score band — see the verdict
      # precedence rule in SKILL.md. The 3.5 score happens to agree here; when a
      # gate failure and the band disagree, the gate failure wins.
      verdict: CONDITIONAL
      base_score: 3.5
      criteria:
        generalizable: PASS
        additive: PASS
        tunable: FAIL        # High FP risk without baseline
        exposure_tested: PASS
        sustainable: PARTIAL  # High volume without baseline
      
      scoring_rationale:
        g_evidence: "Behavioral pattern (browser → MEGA domain)"
        a_evidence: "Fills web-based exfiltration gap"
        t_evidence: "706 events/30 days (23/day), all legitimate observed"
        e_evidence: "Hunt tested DNS, HTTP, HTTPS angles"
        s_evidence: "23/day manageable IF baselined per-user"
      
      pattern_learned: "Cloud service network detections require per-user baseline to manage legitimate usage FPs"
      failure_mode: "T-fail due to high legitimate usage (no clear filter without baseline)"
      
      conditional_requirements:
        - "Customer policy clarification: Is personal MEGA use sanctioned?"
        - "30-day per-user baseline: Identify power users of MEGA"
        - "Dynamic allowlist: Exclude sanctioned MEGA users"
        - "Deploy only after baseline built and allowlist configured"
    
    deployment:
      engine: sql
      status: EXPERIMENTAL
      severity: medium
      
      detection_logic:
        query: |
          (
            `dns.query.name` ILIKE '%.mega.nz'
            AND `process.name` IN ('chrome.exe', 'msedge.exe', 'firefox.exe')
          )
        description: |
          Detects browser connections to MEGA cloud storage (*.mega.nz). 
          Requires per-user baseline to distinguish sanctioned from unauthorized use.
      
      entities:
        - name: endpoint.uid
          type: endpoint
        - name: actor.user.name
          type: user
      
      alert_configuration:
        throttle:
          entity: actor.user.name
          duration: 86400
        baseline_required: true
        baseline_query: |
          -- 30-day per-user baseline
          SELECT `actor.user.name`, COUNT(*) as connection_count
          FROM unified_events
          WHERE `dns.query.name` ILIKE '%.mega.nz'
          AND time >= now() - INTERVAL 30 DAY
          GROUP BY `actor.user.name`
          ORDER BY connection_count DESC
      
      operational_parameters:
        expected_volume: "~23/day (706 events/30 days)"
        fp_rate: "HIGH without baseline (100% observed were legitimate)"
        tuning_required: true
        allowlist_needed: true
        allowlist_type: "dynamic_per_user_baseline"
        soak_period_days: 30  # Longer soak to build baseline
        
        deployment_prerequisites:
          - "Customer policy: Clarify if personal MEGA use is sanctioned"
          - "Build 30-day baseline of MEGA users"
          - "Configure dynamic allowlist excluding sanctioned users"
      
      mitre_attack:
        - T1567.002  # Exfiltration to Cloud Storage

# =============================================================================
# SECTION 4: AGGREGATE INSIGHTS (for agent learning)
# =============================================================================
aggregate_insights:
  
  # What worked well (agents learn success patterns)
  successful_patterns:
    - pattern: "Tool-specific process execution with low volume"
      gates_scores: "Typically 5.0"
      example: "MEGAsync.exe: 1/month volume, no tuning needed"
    
    - pattern: "Tool-specific scheduled task detection"
      gates_scores: "Typically 5.0 if task name is specific"
      example: "Task name contains 'MEGAsync': 0 FPs in 30 days"
  
  # What required tuning (agents learn conditional patterns)
  conditional_patterns:
    - pattern: "Network connection to cloud storage domains"
      gates_scores: "Typically 3.0 (T FAIL, S PARTIAL) — the T FAIL is what makes it CONDITIONAL"
      reason: "High legitimate usage, requires per-user baseline"
      solution: "Build 30-day baseline, dynamic allowlist"
      example: "Browser → *.mega.nz: 23/day, needs baseline"
  
  # Reusable tuning strategies (agents apply to future hunts)
  tuning_strategies:
    - strategy: "Per-user baseline for cloud services"
      applicability: "Any detection on SaaS/cloud storage (Dropbox, Box, MEGA)"
      implementation: "30-day query → build allowlist → deploy with exclusions"
    
    - strategy: "Tool-specific signatures beat generic patterns"
      applicability: "When tool name is stable (not easily changed by adversary)"
      implementation: "Detect 'MEGAsync.exe' vs 'any cloud sync process'"
  
  # Cross-hunt recommendations (agents suggest to users)
  related_detections_to_build:
    - "Dropbox process execution (same pattern as Detection 1)"
    - "Box Sync process execution (same pattern as Detection 1)"
    - "OneDrive personal process execution (same pattern as Detection 1)"
    - technique: T1567.002
      rationale: "Same exfiltration technique, same detection pattern"
  
  # NEW: Proactive deployment patterns (learned from 43-hunt validation)
  proactive_deployment_patterns:
    - pattern: "Zero baseline with strong behavioral pattern"
      # A clean baseline is evidence that the T gate is satisfiable, so it lifts T
      # from PARTIAL to PASS. It does not license a new score token: the only gate
      # results are PASS | PARTIAL | FAIL. The lift needs a >=30-day window, not
      # just a big event count — see the T row in SKILL.md Step 2. Under 30 days,
      # T stays PARTIAL and the candidate soaks as EXPERIMENTAL.
      confidence_boost: "T-gate PARTIAL → PASS when 0 suspicious over a >=30-day baseline"
      examples:
        - "0 hits over 30 days of web server account creation → 4.5, PROMOTE"
        - "0 hits over 30 days of AV-process events spawning shells → 4.5, PROMOTE"
        - "0.1/day remote dev-tunnel creation over 30 days → 4.5, PROMOTE"
      frequency: "~35% of hunts in the corpus this skill was built from"
      learning: "Zero-TP proactive hunts with clean baseline = high deployment confidence"
  
  # NEW: Detection decomposition patterns
  detection_decomposition:
    pattern: "Hybrid behavioral + IOC detections"
    action: "Split into layers with independent verdicts"
    why: "IOC shelf life (90 days) != behavioral logic (durable)"
    examples:
      - "H-0028: download cradle (CONDITIONAL) + URI pattern (TIME_BOX)"
      - "H-0037: Python chain (PROMOTE) + C2 domains (TIME_BOX)"
      - "H-0038: npm shell spawn (RECURRING_HUNT) + C2 domains (TIME_BOX)"
    frequency: "~7% of hunts (3/43)"
  
  # NEW: Recurring hunt patterns
  recurring_hunt_patterns:
    - trigger: "Detection requires policy/business context per alert"
      action: "Convert to quarterly hunt playbook, not 24/7 alerting"
      examples:
        - "H-0027: AI agent installs (requires org policy check)"
        - "H-0041: MCP servers (1,487/day, 0.004% TP rate, requires approval context)"
      frequency: "~5% of hunts (2/43)"
    
    - trigger: "High volume + low TP rate (>100/day, <1% TP)"
      action: "Quarterly execution instead of standing detection"
      examples:
        - "H-0041: 1,487/day, 2 TPs = 0.004% TP rate"
        - "H-0049: 38 endpoints, 100% FP (automation tools)"
      frequency: "~5% of hunts (2/43)"
  
  # NEW: Volume thresholds (S-gate enhancement)
  volume_thresholds:
    sustainable: "<10/day or >1% TP rate"
    conditional: "10-100/day with aggregation/throttling"
    recurring_hunt: ">100/day with <1% TP rate"
    examples:
      - sustainable: "H-0031: 2/day Office lock files on USB"
      - conditional: "H-0048: 997/day lateral movement (IT ops dominant)"
      - recurring_hunt: "H-0041: 1,487/day MCP connections"
  
  # NEW: False positive patterns
  fp_patterns:
    service_accounts:
      pattern: "Service accounts generate high FP rates"
      mitigation: "Requires allowlist before ACTIVE promotion"
      examples:
        - "H-0036: Active Directory Agent (67 FPs)"
        - "H-0048: IT automation tools (997/day)"
    
    dev_heavy_environments:
      pattern: "Zero-TP hunts often miss dev tool FPs"
      mitigation: "Build tool exclusions, monitor EXPERIMENTAL"
      examples:
        - "H-0051: Build systems (31,872 FPs, 70x baseline)"
        - "H-0045: Bazel, Claude Code, Talend (documented exclusions)"
  
  # NEW: Telemetry gap patterns
  telemetry_gap_patterns:
    - gap: "Cannot distinguish legitimate from malicious at telemetry level"
      frequency: "~7% of hunts (3/43)"
      examples:
        - "H-0034: No 'AI-generated command' field → 40K suspicious, 100% FP"
        - "H-0044: EUID unpopulated, AF_ALG invisible → CVE undetectable"
        - "H-0045: Windows COM 30% populated → 3 of 6 tracks blocked"
      action: "Document gap, recommend infrastructure improvement, skip BASE scoring"

# =============================================================================
# SECTION 5: OPERATIONAL HANDOFF (for SOC/engineering)
# =============================================================================
operational_handoff:
  
  next_steps:
    immediate:
      - "Deploy Detection 1 & 2 to EXPERIMENTAL (7-day soak)"
      - "Customer outreach: Clarify MEGA usage policy (for Detection 3)"
    
    week_1:
      - "Monitor FP rate: Target <5/day for Detection 1 & 2"
      - "Run Atomic Red Team T1567.002 tests"
    
    week_2_4:
      - "If soak successful: Promote Detection 1 & 2 to ACTIVE"
      - "Build 30-day baseline for Detection 3 (if deployment approved)"
    
    conditional:
      - "If customer sanctions MEGA: Deploy Detection 3 with baseline allowlist"
      - "If customer blocks MEGA: Consider proxy-level block + bypass alert"
  
  soc_playbook:
    detection_1_triage:
      - "Check if user has legitimate business need for MEGA"
      - "Review recent file access patterns (large file reads?)"
      - "Check for concurrent network exfiltration indicators"
    
    detection_2_triage:
      - "Scheduled task = persistence indicator (escalate immediately)"
      - "Check task schedule: Daily? Frequent? Matches user work hours?"
      - "Review process tree: What created the scheduled task?"
    
    detection_3_triage:
      - "Check user against MEGA baseline: New user or existing?"
      - "Compare volume: Unusually high compared to user's history?"
      - "Correlate with Detection 1 or 2 for stronger signal"
  
  purple_team_validation:
    - technique: T1567.002
      test: "Atomic Red Team: Upload file to MEGA via MEGAsync client"
      expected: "Detection 1 fires, Detection 2 if persistence configured"
    
    - technique: T1053.005
      test: "Create scheduled task named 'MEGAsync Update'"
      expected: "Detection 2 fires"

# =============================================================================
# METADATA FOR YAML FILE ITSELF
# =============================================================================
schema_version: "2.0"
generated_by: "GATES skill v2.0"
last_updated: 2026-09-22
related_files:
  hunt_file: "hunts/production/2026/Q3/H-0063.md"
```

## How Agents Use This

### Knowledge Base Queries

**Query 1:** "Show me all PROMOTE verdicts for T1567"
```python
# Agent searches hunt_metadata.techniques = T1567.002
# Filters gates_assessment.verdict = PROMOTE
# Returns: Detection 1 & 2 from this hunt
```

**Query 2:** "What FP rates are acceptable for process execution?"
```python
# Agent searches detection_patterns.pattern_type = process_execution
# Aggregates typical_fp_rate across all hunts
# Learns: "low" FP rates typical for tool-specific process detections
```

**Query 3:** "What tuning works for cloud storage detections?"
```python
# Agent searches aggregate_insights.conditional_patterns
# Finds: "Per-user baseline for cloud services"
# Applies to new hunt: "Build 30-day baseline before deploying"
```

### Deployment Automation

**Use Case:** "Deploy Detection 1 to detection repository"
```bash
# Agent extracts detections[0].deployment section
# Feeds into detection automation tool
# Example (generic):
detection-tool deploy \
  --from-artifacts H-0063_GATES.yaml \
  --detection-id 1 \
  --repository ../detection-repo
```

**Output:** Valid detection YAML in target repository

## Output Format by Verdict Type

**PROMOTE/CONDITIONAL Verdicts:** YAML file (this schema)
- File: `hunt-promotion-analysis/H-XXXX_GATES.yaml`
- Contains: Deployment templates, agent learning artifacts, operational parameters
- Purpose: Machine-readable, deployment-ready detection rules

**HOLD/TIME_BOX/RECURRING_HUNT Verdicts:** Markdown file
- File: `hunt-promotion-analysis/H-XXXX_GATES.md`
- Contains: Analysis, rationale, activation triggers, strategy documentation
- Purpose: Human-readable guidance and preservation of reasoning

Example Markdown structure (HOLD verdict):

```markdown
# GATES Validation: H-0063

## Verdict: ❌ HOLD

**BASE Score:** 2.0

## Analysis

[Rationale for why this hunt should not proceed to detection...]

## Criteria Failures

**T - Tunable: ❌ FAIL**
- High FP rate observed
- No clear tuning strategy identified

**E - Exposure Tested: ⚠️ PARTIAL**
- Limited bypass scenarios tested

## Recommendations

[Suggestions for improving hunt before re-attempting...]
```

## Benefits of This Approach

1. **Agent Learning:**
   - Query across hunts: "Show me all tool-specific detections"
   - Pattern recognition: "Low volume + specific signature = 5.0"
   - Cross-hunt application: "Use per-user baseline for cloud services"

2. **Deployment Ready:**
   - Extract deployment section → valid YAML
   - No manual rewriting needed
   - Complete operational parameters included

3. **Minimal Duplication:**
   - YAML = structured data + deployment templates
   - MD = narrative + evidence + reasoning
   - Each serves distinct purpose

4. **Historical Reference:**
   - Agents learn from past GATES decisions
   - "Why did similar detection fail T-gate in H-0045?"
   - "What tuning strategy worked before?"

5. **Cross-Hunt Intelligence:**
   - Aggregate insights section synthesizes learnings
   - Recommends related detections to build
   - Captures reusable strategies

## Implementation

Would you like me to:
1. **Update GATES skill** to generate this dual-purpose YAML?
2. **Regenerate artifacts** for H-0060/0061/0063 in this format?
3. **Create agent query examples** showing how to search these?