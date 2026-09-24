---
name: gates
description: GATES method validation for hunt-derived detections. Evaluates hunt KEEP phase against 5 BASE + 5 ADVANCED criteria to determine if findings are production-ready.
---

# GATES Hunt Detection Validator

Apply GATES (Generalizable, Additive, Tunable, Exposure-tested, Sustainable) method to hunt KEEP phase outputs.

## When to Use

- After completing any hunt (with or without explicit detection logic)
- To identify which hunt findings would make good detections
- To validate detection quality meets operational thresholds
- To determine if hunt should produce detections vs. advisories vs. recurring playbook

## Usage

`/gates --hunt H-XXXX`

## Hunt Output Types & GATES Applicability

GATES adapts to different hunt outcomes:

| Hunt Type | Output | GATES Action | Example |
|-----------|--------|--------------|---------|
| **Behavioral detection hunt** | Explicit detection rules proposed | Score those rules | H-0062 (ClickFix), H-0063 (MEGAsync) |
| **Exploration hunt** | Queries + observations, no rules | Extract detection candidates from patterns | H-0061 (Zeek inspection) |
| **Negative hunt** | 0 TPs, behavioral pattern tested | Evaluate for proactive deployment or HOLD | H-0060 (EDGECUTION) |
| **Risk assessment hunt** | Configuration findings, no behaviors | Document as non-GATES (advisory output) | H-0066 (Camera infrastructure) |
| **Multi-step investigation** | Requires analyst correlation | Classify as RECURRING HUNT playbook | Asset correlation hunts |
| **Baseline/inventory hunt** | Environmental understanding | Document as knowledge capture (no detection) | Asset inventory, normal behavior mapping |

**Key insight:** Not every hunt produces detections. GATES identifies which hunts should → detections vs. advisories vs. playbooks.

## Framework Reference

**GATES 5+5:** 5 BASE (assert from hunt) + 5 ADVANCED (demonstrate operationally)

| Gate | BASE — assert | ADVANCED — demonstrate |
|------|---------------|------------------------|
| **G - Generalizable** | Repeatable behavior, or a one-off? | Cross-fleet + companion rules that generalize the technique? |
| **A - Additive** | Does it fill a coverage gap? | Actionable: is there a validated or automated playbook? |
| **T - Tunable** | Tell attack from normal? 7- & 30-day look-back — FP rate in range? | A reusable allowlist other rules can share? |
| **E - Exposure-tested** | Covered the bypasses, or just the obvious path? | Run emulation — did real telemetry reveal a gap? |
| **S - Sustainable / Soaked** | Juice worth the squeeze: can we reliably see it, is the upkeep fair? | Soaked live 48h–7d — Performance with concurrent detections under the volume threshold? |

**Failure modes:**
- **G fail** →  TIME-BOX (IOC or one-off, 90-day review)
- **A fail** → Drop or merge (duplicates coverage)
- **T fail** →  CONDITIONAL (tunable with watchlist, deploy after tuning)
- **E fail** → Expand detection to cover bypasses OR log for next hunt
- **S fail** → RECURRING HUNT or eng ticket (can't sustain it)
- **5/5** → ✅ PROMOTE (ship as standing detection)

## Workflow

### Pre-Flight: Determine Hunt Output Type

Before scoring, classify the hunt:

1. **Read full hunt file** (all phases: LEARN → OBSERVE → CHECK → KEEP)
2. **Identify hunt goal:**
   - Detect active threat? → Behavioral detection hunt
   - Assess security posture? → Risk assessment hunt
   - Understand environment? → Baseline/inventory hunt
   - Investigate specific finding? → May be multi-step investigation
3. **Check KEEP phase:**
   - Detection rules explicitly proposed? → Score those (Step 2)
   - Findings without detection logic? → Extract candidates (Step 1.5)
   - Configuration/exposure findings only? → Non-GATES workflow
   - Multi-query correlation required? → RECURRING HUNT classification

**Decision tree:**
```
Does KEEP propose explicit detections?
├─ YES → Score those detections (Step 2)
└─ NO → Are findings behavioral patterns?
    ├─ YES → Extract detection candidates (Step 1.5)
    └─ NO → Are findings configuration/risk issues?
        ├─ YES → Non-GATES workflow (advisory output)
        └─ NO → Multi-step investigation?
            ├─ YES → RECURRING HUNT playbook
            └─ NO → Baseline/inventory (knowledge capture)
```

### Step 0.5: Check Hunt Status

Read hunt frontmatter `status` field:

- **`planning`** → Generate planning assessment (not full GATES)
  - Hunt hypothesis exists but not yet executed
  - Provide execution guidance and detection potential assessment
  - Output: `H-XXXX_PLANNING_ASSESSMENT.md`
  
- **`completed`** → Proceed to full GATES validation
  - Hunt has CHECK and KEEP phases documented
  - Findings and detections are ready for scoring
  
- **`in-progress`** → Wait for completion
  - Hunt is actively being executed
  - Return: "Hunt not ready for GATES validation. Complete CHECK and KEEP phases first."

**Planning Assessment Output:**

For planning-phase hunts, generate `H-XXXX_PLANNING_ASSESSMENT.md`:

```markdown
# H-XXXX Planning Assessment

**Status:** Planning (not executed)

## GATES Applicability

NOT READY FOR GATES VALIDATION

Hunt is in planning phase. GATES requires completed CHECK/KEEP phases with findings.

## Pre-Assessment (Detection Potential)

Based on hypothesis, estimated BASE score potential:
- G (Generalizable): [LIKELY PASS | PARTIAL | UNKNOWN]
- A (Additive): [LIKELY PASS | PARTIAL | UNKNOWN]
- T (Tunable): [UNKNOWN - requires baseline]
- E (Exposure-tested): [UNKNOWN - requires testing]
- S (Sustainable): [UNKNOWN - requires volume data]

## Recommendations for Execution

1. Execute hunt queries
2. Document findings in KEEP phase
3. Return to GATES for full validation
```

---

### Step 0.6: Telemetry Sufficiency Check (CRITICAL)

**Before scoring BASE criteria, verify telemetry can distinguish attack from legitimate activity.**

Ask these questions:

1. **Can telemetry differentiate malicious from benign?**
   - Example FAIL: Process telemetry cannot distinguish "user-typed command" from "AI agent-generated command"
   - Example PASS: Process + command-line args distinguish "browser → legitimate extension" from "browser → malicious extension"

2. **Are critical attack phases observable?**
   - Example FAIL: EDR sees preparation (file write) but not execution (pre-boot rootkit)
   - Example PASS: EDR captures full attack chain (initial access → credential dump → lateral movement)

3. **Can FP rate be tuned below sustainable threshold?**
   - Example FAIL: 40,000 suspicious events, 100% FP rate, no distinguishing field available
   - Example PASS: 1,000 suspicious events → 10 after filters (dev tool allowlist applied)

**If NO to Question 1 or 2:**
- **Verdict:** NON-GATES (Telemetry Gap Hunt)
- **Output:** `.md` assessment documenting visibility limitations
- **Recommendations:** Infrastructure improvements (new data source, field population, correlation engine)
- **DO NOT proceed to BASE scoring** - detection is not feasible with current telemetry

**Examples:**
- H-0001 (ATHF Showcase): macOS information stealer detection → Strong EDR telemetry coverage for process execution, file access, and AppleScript events
- Reference: https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/blob/main/hunts/H-0001.md

*Note: Example references public ATHF showcase hunt. Your results will vary based on environment telemetry coverage.*

**Pattern learned:** ~7% of hunts (3/43) reveal telemetry gaps that block detection. Catching this early prevents wasted BASE scoring effort.

---

### Step 1: Hunt Discovery & Content Extraction

```bash
# Find and load hunt file
find hunts/production -name "${HUNT_ID}.md" -type f
```

Parse YAML frontmatter: `hunt_id`, `techniques`, `tactics`, `findings_count`, `true_positives`, `false_positives` (if present)

Load hunt content from all phases:
- **KEEP phase** (`## KEEP: Findings & Response`):
  - Executive Summary
  - Findings (table format OR prose descriptions)
  - Detection Logic (if explicitly proposed)
  - Follow-up Actions (may contain detection recommendations)
  - Lessons Learned
- **CHECK phase** (`## CHECK: Execute & Analyze`):
  - Query Plan (approved queries)
  - Queries executed (SQL, process searches, network patterns)
  - Query results and volumes
  - Behavioral patterns observed
- **OBSERVE phase** (`## OBSERVE: Expected Behaviors`):
  - "What Suspicious Looks Like" (detection candidates)
  - Expected observables (what telemetry would show)
- **LEARN phase** (`## LEARN: Prepare the Hunt`):
  - Hypothesis statement (attack behaviors)
  - Threat context (TTPs, tools, techniques)

**Flexible evidence extraction:**
- ✅ If Findings table exists with TP/FP counts → use directly
- ✅ If prose findings without counts → extract behavioral patterns
- ✅ If detection logic explicitly proposed in KEEP → score those
- ✅ If NO detection logic proposed → identify opportunities from queries/observations
- ✅ If multi-step investigation → classify as RECURRING HUNT

### Step 1.5: Detection Opportunity Identification

**If hunt explicitly proposes detections in KEEP → skip to Step 2 (score those)**

**If hunt does NOT explicitly propose detections → identify opportunities:**

Extract detection candidates from hunt content by analyzing:

1. **Behavioral patterns observed:**
   - Process execution chains (parent → child relationships)
   - Command-line patterns (suspicious flags, encoded payloads)
   - File operations (writes to sensitive paths, unusual extensions)
   - Network connections (unusual ports, suspicious domains, C2 patterns)
   - Registry modifications (persistence mechanisms, configuration changes)
   - API calls or system events (unusual combinations, privilege escalation)

2. **Query patterns that returned results:**
   - Which queries found suspicious activity? (even if FP)
   - What volumes were observed? (helps assess sustainability)
   - What filters were applied during hunt? (shows tuning potential)
   - What exclusions were documented? (seed for allowlists)

3. **"What Suspicious Looks Like" section:**
   - Each bullet point may be a detection candidate
   - Behavioral descriptions → Sigma/SQL rule patterns
   - Tool/technique names → detection signatures

4. **Findings without TP/FP counts:**
   - Risk findings: Configuration issues, exposure → NOT detections (document as non-detectable)
   - Behavioral findings: Attack patterns, suspicious activity → Detection candidates
   - Hygiene findings: Cleartext creds, deprecated protocols → Informational signals

5. **Multi-step investigations:**
   - Does finding require: Query 1 → analyst review → Query 2 → correlation?
   - If yes: NOT a detection candidate → RECURRING HUNT playbook
   - If no: Can be reduced to single alert → Detection candidate

**For each candidate, document:**
- **Pattern:** What behavior would the detection look for?
- **Telemetry:** What data source(s) provide visibility?
- **Volume:** What's the expected alert rate? (from hunt queries if available)
- **Tuning:** What filters/exclusions would reduce FPs? (from hunt observations)
- **Hunt outcome:** TPs observed (if documented), FPs observed, or unknown

**Detection Decomposition (Hybrid Rules):**

If detection mixes **behavioral + IOC components**, split into independent layers:

1. **Identify hybrid pattern:**
   - Example: PowerShell download cradle (behavioral) + URI pattern `/api/installer/script` (IOC)
   - Example: Python→OpenSSL chain (behavioral) + C2 domain list (IOC)

2. **Split into layers:**
   - **Behavioral layer** → Score as standalone detection (typically CONDITIONAL/PROMOTE)
   - **IOC layer** → Score separately (typically TIME-BOX with 90-day refresh)

3. **Score each independently:**
   - Behavioral: G=PASS (repeatable pattern), T/S depend on volume
   - IOC: G=FAIL (campaign-specific), but may TIME-BOX if operationally useful

4. **Output both detections:**
   ```yaml
   detections:
     - detection_id: 1a
       name: "PowerShell Download Cradle (Behavioral)"
       gates_assessment:
         verdict: CONDITIONAL
         
     - detection_id: 1b
       name: "Suspicious URI Pattern (IOC)"
       gates_assessment:
         verdict: TIME-BOX
         refresh_cycle: 90_days
   ```

**Why split?** IOC shelf life (90 days) ≠ behavioral logic (durable). Separate verdicts enable proper lifecycle management.

**Examples:**
**Hybrid Detection Patterns:**
- Download cradle behavior (CONDITIONAL) + Known malicious URIs (TIME-BOX)
- Suspicious process chain (PROMOTE) + C2 domain IOCs (TIME-BOX)
- High-volume npm operations (RECURRING_HUNT) + C2 infrastructure IOCs (TIME-BOX)

*Note: Patterns generalized from production validation. ~7% of production hunts propose hybrid detections requiring decomposition.*

**Pattern learned:** ~7% of hunts (3/43) propose hybrid detections requiring decomposition.

---

**External Reference Extraction:**

If hunt KEEP phase references external detection artifacts (commit hash, PR, file):

1. **DO NOT just link** - Extract actual detection logic
2. **Read referenced source:**
   - Detection repository commits (if accessible)
   - Signal rule YAML files
   - GitHub PRs with detection logic
3. **Document logic in output** - Include `selection`, `condition`, filters
4. **Score what's documented** - Don't score placeholder references

**Example:** Hunt references "detection repo commit abc1234" → Agent must read commit, extract detection rules, document logic (selection criteria, conditions, filters), then score each rule independently.

*Note: When hunts reference external detection artifacts, always extract and document the actual detection logic rather than scoring placeholder references.*

**Output:** List of 1-N detection candidates OR determination that hunt produces no detection artifacts (risk assessment, baseline study, inventory)

### Step 2: BASE Criteria Evaluation

**G-gate Fast-Path (IOC + Zero TPs):**

Before full BASE scoring, check for automatic HOLD:

```
IF detection is IOC-based (G=FAIL) AND hunt found 0 TPs:
  → Verdict: HOLD (skip remaining gates)
  → Rationale: Campaign-specific IOCs with no operational need = dead rule clutter
  → Activation: Deploy only if threat intel shows campaign resurgence
  → Output: .md assessment (not .yaml)
```

**Example:**
- H-0032: Registry paths + RMM keys (IOC) + 0 TPs across 16 orgs → **HOLD**

*Note: Example H-0032 and statistics like "~2% of hunts (1/43)" are from internal validation corpus; your results may vary.*

**Pattern learned:** ~2% of hunts (1/43) hit this fast-path

**Why this helps:** Prevents agents from scoring 4 additional gates for IOC rules that have no operational value. Saves time, reduces YAML output clutter.

---

For each detection candidate (explicit or identified), score 5 BASE criteria (✅ PASS / ❌ FAIL):

**A (Additive) User Verification:**
If detection repository is not accessible (no ATHF/ADEF integration, external repo, etc.), prompt user:

```
A - Additive Verification:

Do you have existing detection coverage for:
- Technique: [T1XXX from hunt]
- Behavior: [detection pattern]
- Data source: [EDR/CloudTrail/etc.]

Questions:
1. Does this detection duplicate any existing rule? (Y/N)
2. Does this fill a gap in your current detection portfolio? (Y/N)
3. If similar detection exists, what's different about this one?

→ User input required to score A criterion
```

If detection repository IS accessible (ATHF/ADEF integrated), automatically check for overlaps.

| Gate | BASE Question | Evidence from Hunt (Flexible) |
|------|---------------|-------------------|
| **G - Generalizable** | Repeatable behavior, or a one-off? | **✅ Available:** Techniques (T1XXX), pattern vs. IOC, behavior chains<br>**❌ IOC pattern:** Domain literals, specific IPs, campaign hashes → G-fail |
| **A - Additive** | Does it fill a coverage gap? | **✅ Check:** Technique coverage in detection repo<br>**→ PROMPT USER** if detection repository not available<br>**✅ Actionable:** Single alert = clear action (not multi-step) |
| **T - Tunable** | Tell attack from normal? Can FPs be managed? | **✅ If available:** Hunt TP/FP counts from Findings table<br>**⚠️ If unavailable:** Assess from query volumes, documented exclusions, "normal" behaviors<br>**✅ Tunable:** Filters/allowlists documented in hunt<br>**❌ High risk:** Widespread legitimate use, no clear filters<br>**🎯 PROACTIVE BOOST:** Zero-baseline hunts (0 suspicious / large sample) → +0.5 confidence<br>**Example:** 0 suspicious events in 1B+ baseline = high deployment confidence |
| **E - Exposure-tested** | Covered the bypasses, or just the obvious path? | **✅ Multiple angles:** Count of queries/detection layers<br>**✅ Bypass testing:** Documented evasion scenarios<br>**⚠️ Single path:** Only one query pattern tested |
| **S - Sustainable** | Juice worth the squeeze: can we see it, is upkeep fair? | **✅ If available:** Hunt alert volumes from queries<br>**⚠️ If unavailable:** Project from query result counts<br>**✅ Low burden:** Static allowlist, reliable telemetry<br>**❌ High burden:** Dynamic allowlist, requires correlation<br>**📊 VOLUME THRESHOLDS:**<br>- **<10/day:** Sustainable (manual triage feasible)<br>- **10-100/day:** Conditional (requires aggregation/throttling)<br>- **>100/day:** Likely unsustainable unless TP rate >1%<br>**🤖 AUTOMATION CHECK:** Can SOC act without per-alert human context?<br>- ✅ "Is user authorized?" (allowlist lookup = automatable)<br>- ❌ "Does policy allow this tool?" (business judgment = not automatable)<br>- **If per-alert context required:** S-FAIL → RECURRING HUNT |

### BASE Scoring

Each gate scores:
- **PASS** = 1.0 point (criterion fully met)
- **PARTIAL** = 0.5 points (criterion partially met with caveats)
- **FAIL** = 0.0 points (criterion not met)

**BASE Score** = Sum of gate scores (0.0 to 5.0)

**Verdict Mapping:**
- **4.0-5.0**: PROMOTE (strong deployment candidate)
- **3.0-3.5**: CONDITIONAL (prerequisites required)
- **2.0-2.5**: HOLD or TIME-BOX (context-dependent)
- **0.0-1.5**: HOLD (significant gaps)

**Note:** PARTIAL scores enable fine-grained assessment. A detection with 4 PASS (4.0) and 1 PARTIAL (0.5) = 4.5 total, still qualifies for PROMOTE.

**Examples:**
- All PASS: 5.0/5
- 4 PASS + 1 PARTIAL: 4.5/5
- 3 PASS + 1 PARTIAL + 1 FAIL: 3.5/5
- 4 PASS + 1 FAIL: 4.0/5

**When to score PARTIAL:**
- Detection has the concept but incomplete (T: tunable but needs allowlist)
- Coverage exists but has gaps (E: tested main path, not bypasses)
- Meets threshold with caveats (S: sustainable IF maintenance plan exists)
- Gate is mostly satisfied but has known limitations

**Handling Missing Data:**

When hunt doesn't provide explicit TP/FP counts or detection logic:

| Missing Data | How to Score | Guidance |
|--------------|--------------|----------|
| **No TP/FP table** | Use query volumes + findings descriptions | T-score: PARTIAL if volumes manageable but unvalidated<br>S-score: PARTIAL if volume unknown, project from query results |
| **No detection logic proposed** | Identify from queries/observations (Step 1.5) | Score the behavioral patterns you extract |
| **No query volumes** | Project from hunt scope (days × tenants) | S-score: Mark as UNKNOWN, recommend EXPERIMENTAL soak |
| **No exclusion filters** | Assess from "normal" behavior descriptions | T-score: PARTIAL if tuning possible, FAIL if no clear filters |
| **Hunt found 0 TPs** | Valid outcome, doesn't fail GATES | G/A/E can still PASS; T/S may be PARTIAL (unvalidated)<br>Consider: Is this HOLD (no operational need) vs PROMOTE (proactive)? |
| **Multi-step correlation** | Not a detection candidate | Classify as RECURRING HUNT, don't score GATES |
| **Risk assessment hunt** | No detection artifacts | Document as non-GATES workflow (like H-0066) |

**Key principle:** Missing data → PARTIAL scores or CONDITIONAL verdict (not automatic FAIL). Document uncertainty and recommend validation steps.

**Rule type impact on verdict:**
- **BEHAVIORAL**: Process patterns, TTPs → Expected 5/5, G-pass
- **TOOL**: Tool signatures → Expected 5/5, G-pass
- **IOC**: IPs, domains, hashes → G-fail → TIME-BOX (90-day review)
- **HYBRID**: Mixed → Split into behavioral + IOC layers
- **MULTI-STEP INVESTIGATION**: Detection requires multiple queries with intermediate results that must be manually correlated → Not actionable as single alert → RECURRING HUNT (quarterly threat hunt, not standing detection)
  - Examples: Query 1 outputs list → Query 2 uses that list → Query 3 correlates results → Analyst decides if suspicious
  - Cannot be reduced to one alert with clear action
  - Requires hunt methodology, not alerting

### Step 3: ADVANCED Criteria (Operational Validation)

ADVANCED criteria are **PENDING** until deployment. Provide recommendations:

| Gate | ADVANCED Question | Recommendation |
|------|------------------|----------------|
| **G - Generalizable** | Cross-fleet + companion rules? | Test cross-OS/provider, build companion rules to generalize |
| **A - Actionable** | Validated or automated playbook? | SOC walkthrough, wire auto-enrichment |
| **T - Tunable** | Reusable allowlist? | Build shared allowlist other rules can reference |
| **E - Exposure-tested** | Run emulation — gap revealed? | Atomic Red Team, purple team validation |
| **S - Soaked** | Performance with concurrent detections? | 48h–7d EXPERIMENTAL soak, volume < threshold |

### Step 4: Verdict & Output

**Verdict logic per failure mode:**

**Verdict by BASE Score:**
- **4.0-5.0** → ✅ PROMOTE (deploy as standing detection)
- **3.0-3.9** → ⚠️ CONDITIONAL (deploy after prerequisites)
- **0.0-2.9** → ❌ HOLD, TIME-BOX, or RECURRING HUNT (based on context)

**Per-gate failure modes:**
- **G fail** →  **TIME-BOX** (IOC or one-off, 90-day review)
- **A fail** → **Drop or merge** (duplicates coverage)
- **T fail** →  **CONDITIONAL** (deploy after tuning/allowlist)
- **E fail** → Expand detection to cover bypasses OR log for next hunt
- **S fail** → **RECURRING HUNT** or eng ticket (can't sustain)

**Generate output based on verdict:**

### Smart Single-File Strategy

| Verdict | File Generated | Purpose | Contains |
|---------|----------------|---------|----------|
| **PROMOTE / CONDITIONAL** | `H-XXXX_GATES.yaml` | Deployment + learning | Structured data, narrative (embedded), deployment templates, agent-queryable metadata |
| **HOLD / DROP / TIME-BOX** | `H-XXXX_GATES.md` | Analysis only | Narrative verdict, reasoning, recommendations (no deployment) |
| **Risk Assessment / Non-GATES** | `H-XXXX_ASSESSMENT.md` | Advisory | Client advisory, remediation guidance (not detection) |

**Result:** ~1 file per hunt, extension indicates deployability

### YAML Structure (when verdict = PROMOTE/CONDITIONAL)

See `AGENT_MEMORY_SCHEMA.md` for complete schema. Key sections:

1. **hunt_metadata** - Techniques, tactics, outcomes (for agent indexing)
2. **gates_validation** - Verdict, classifications, key learnings (for pattern recognition)
3. **narrative_analysis** - Embedded markdown string with full BASE criteria evidence (human-readable)
4. **detections[]** - Each with:
   - `gates_assessment` - Scoring rationale, patterns learned
   - `deployment` - Engine, query, entities, operational params (ready to deploy)
5. **aggregate_insights** - Successful patterns, tuning strategies (cross-hunt learning)
6. **operational_handoff** - SOC playbook, next steps, purple team validation

### Markdown Structure (when verdict = HOLD/DROP/TIME-BOX or non-GATES)

Lightweight narrative report:
```markdown
# GATES Validation: H-XXXX

**Verdict:** ❌ HOLD / TIME-BOX / DROP
**BASE Score:** X/5

## Summary
[One paragraph: why this verdict]

## Reasoning
[BASE criteria scoring with evidence]

## Recommendations
[What to do instead: recurring hunt, IOC refresh, merge with existing rule]
```

**Present summary:**
```
GATES Validation Complete: H-XXXX

Verdict: ✅ PROMOTE (2 detections) | ⚠️ CONDITIONAL | ❌ HOLD

File: hunt-promotion-analysis/H-XXXX_GATES.yaml
      (or H-XXXX_GATES.md if HOLD, or H-XXXX_ASSESSMENT.md if non-GATES)

Next: [Deploy to detection repository | Build baseline | Convert to recurring hunt]
```

---

## Scoring Examples Reference

**Detailed examples:** `examples/README.md`

**Quick pattern recognition:**

| Rule Pattern | Expected Score | Common Verdict | Example |
|--------------|----------------|----------------|---------|
| Behavioral (process) | 5/5 | ✅ PROMOTE | Process injection, LSASS access |
| Tool signature | 5/5 | ✅ PROMOTE | Mimikatz, Cobalt Strike |
| IOC (domain/IP) | 1-2/5 | TIME-BOX | GenieLocker C2, ClickFix IPs |
| High-volume API | 2-3/5 | CONDITIONAL/HOLD | EC2 DisableEbs (2,537/day) |
| Hybrid (behavioral+IOC) | 2-3/5 | SPLIT LAYERS | Connection + domain IOC |
| Baseline-required | 2-3/5 | RECURRING HUNT | Per-entity anomaly detection |
| Duplicate coverage | Varies | DROP/MERGE | Overlapping LSASS rules |

See `examples/README.md` for detailed scoring examples across all verdict types (PROMOTE, CONDITIONAL, HOLD, TIME-BOX, RECURRING HUNT).

---

## Detection Extraction Examples (Generic Hunts)

### Example 1: Hunt with No Explicit Detection Logic

**Hunt:** Investigated cleartext credential transmission via FTP/HTTP

**KEEP phase finding (prose only):**
> "Found 12 FTP authentication events to partner file servers (benign), 3 HTTP basic auth to internal admin panels (sanctioned), 0 adversary credential theft."

**Detection extraction:**
1. **Pattern identified:** FTP cleartext authentication events
2. **Telemetry:** Network logs, protocol inspection
3. **Volume:** 12 events over hunt window → ~1.7/day
4. **Tuning:** Exclude known FTP partners (3 destinations documented)
5. **Hunt outcome:** 0 TPs, 12 benign (all explainable)

**GATES scoring:**
- G: ✅ PASS (behavioral pattern, not IOC)
- A: ✅ PASS (fills cleartext credential gap)
- T: ⚠️ PARTIAL (12 benign events, requires partner allowlist)
- E: ⚠️ PARTIAL (only FTP tested, HTTP separate)
- S: ✅ PASS (low volume, static allowlist)

**Verdict:** ⚠️ CONDITIONAL (deploy with FTP partner allowlist)

### Example 2: Hunt with Queries But No Proposed Rules

**CHECK phase query:**
```sql
-- Found 47 MEGAsync process executions
SELECT endpoint.uid, actor.user.name, process.file.path
WHERE process.name = 'MEGAsync.exe'
AND time >= now() - INTERVAL 30 DAY
```

**Detection extraction:**
1. **Pattern identified:** MEGAsync process execution
2. **Telemetry:** EDR process events
3. **Volume:** 47 events / 30 days → ~1.5/day
4. **Tuning:** No exclusions needed (low volume, specific process)
5. **Hunt outcome:** 0 TPs (no exfiltration observed, but coverage gap confirmed)

**GATES scoring:**
- G: ✅ PASS (behavioral, tool-based detection)
- A: ✅ PASS (fills T1567.002 exfiltration gap)
- T: ✅ PASS (low volume, specific signature)
- E: ✅ PASS (hunt tested process + network + scheduled task angles)
- S: ✅ PASS (1.5/day sustainable, no maintenance)

**Verdict:** ✅ PROMOTE

### Example 3: Hunt Produces No Detection Artifacts

**Hunt:** Camera/NVR infrastructure security assessment

**Findings:** Flat network segmentation, NDAA vendor presence, no external exposure

**Detection extraction:** None - findings are configuration states, not behavioral events

**GATES classification:** NOT APPLICABLE (risk assessment hunt, not detection hunt)

**Outcome:** Client advisories + remediation plan (not GATES validation)

### Example 4: Multi-Step Investigation Hunt

**KEEP phase finding:**
> "Query 1: List users with MFA changes (37 users). Query 2: For those users, check concurrent sessions (analyst manually correlates). Query 3: For suspicious pairs, investigate login history."

**Detection extraction:** Attempted, but requires analyst correlation between steps

**GATES classification:** RECURRING HUNT (not automatable detection)

**Verdict:** ❌ NOT A DETECTION - Convert to quarterly hunt playbook

---

## Remediation Framework: What to Do When Criteria Fail

When a detection fails BASE criteria, provide **specific, actionable recommendations** following these patterns:

### G - Generalizable FAILS → TIME-BOX Recommendations

**When it fails:** IOC-based detection (domains, IPs, hashes, campaign-specific filenames)

**Immediate Actions (30 days):**
1. **Schedule 90-day review cycle:**
   - Set review date (creation_date + 90 days)
   - Define review criteria: Is campaign still active? New IOCs observed?
2. **Monitor threat intelligence:**
   - Check if campaign is active (threat intel feeds, vendor reports)
   - Track for new variants/IOCs from same threat actor
3. **Document IOC source:**
   - Where did IOCs come from? (Threat report, customer incident, hunt finding)
   - What's the refresh cadence? (Vendor updates? Internal IR?)

**Long-Term Strategy (90+ days):**
1. **Build behavioral companion rule:**
   - Extract behavioral pattern from IOC context
   - Example: Instead of "detect domain cdn-fix.click" → "detect suspicious connection + unusual parent process"
2. **IOC refresh or retire:**
   - **If campaign active:** Update IOCs with new variants
   - **If campaign ended:** Retire rule to avoid dead IOC clutter
3. **Document shelf life:**
   - How long is this IOC expected to be valid?
   - What triggers IOC refresh? (New campaign activity, threat intel update)

**Recommendation Template:**
```
Verdict: ⏱️ TIME-BOX (90-day review, IOC with limited shelf life)

Rationale:
- IOC-based detection (literal [domains/IPs/filenames]) = campaign-specific
- High value during active [campaign name] campaign
- Limited shelf life: adversary will rotate [IOCs] when campaign evolves

Operational Notes:
- 90-day review cycle required:
  1. Check if [campaign] still active
  2. Update [IOC type] if new variants observed (check [threat intel source])
  3. RETIRE rule if campaign has ended (avoid dead IOC clutter)

Companion detection needed:
- Build behavioral detection for [attack pattern] (not IOC-based)
- Pattern: [behavioral description without IOCs]

Review date: [creation_date + 90 days]
```

---

### A - Additive FAILS → DROP or MERGE Recommendations

**When it fails:** Duplicate detection, overlapping coverage, no gap filled

**Immediate Actions:**
1. **Identify overlapping rules:**
   - Search detection repo for technique coverage (T1XXX)
   - Query: Which rules already detect this behavior?
2. **Compare detection logic:**
   - What's different? (Data source, query logic, severity, entities)
   - Is the difference meaningful? (Better coverage? Lower FP rate?)
3. **Assess value-add:**
   - Does new rule provide additional value? (Different data source, better tuning, more specific)
   - Or is it truly redundant? (Same pattern, same FP rate, same coverage)

**Long-Term Strategy:**
1. **If truly duplicate → DROP:**
   - Document why existing rule covers this
   - Reference existing rule in hunt notes
2. **If overlapping but different → MERGE:**
   - Combine into single rule with broader coverage
   - Example: Two LSASS dumping rules → One comprehensive LSASS access rule
3. **If niche improvement → CONDITIONAL:**
   - Deploy only if existing rule has known gap
   - Example: Existing rule has high FP rate, new rule adds tuning filter

**Recommendation Template:**
```
Verdict: ❌ DROP (duplicates existing coverage) or MERGE

Rationale:
- Existing rule [rule-id] already detects [behavior]
- Overlap: [percentage]% detection logic overlap
- No additional value: Same technique coverage, same data source

Comparison:
| Aspect | Existing Rule | New Rule | Winner |
|--------|---------------|----------|--------|
| Coverage | [description] | [description] | [existing/new/tie] |
| FP Rate | [rate] | [rate] | [existing/new/unknown] |
| Tuning | [description] | [description] | [existing/new/tie] |

Recommendation:
- [DROP]: Use existing rule [rule-id], document in hunt notes
- [MERGE]: Combine into single rule covering [combined scope]
- [CONDITIONAL]: Deploy only if existing rule has [specific gap]
```

---

### T - Tunable FAILS → CONDITIONAL Recommendations

**When it fails:** High FP rate, cannot distinguish attack from normal, requires extensive allowlist

**Immediate Actions (30 days):**
1. **Monitor FP rate for 30 days:**
   ```sql
   SELECT COUNT(*), 
          [key_field_1], 
          [key_field_2], 
          [key_field_3]
   FROM alerts 
   WHERE detection_id = '[rule-uuid]'
   AND time >= now() - INTERVAL 30 DAY
   GROUP BY [key_field_1], [key_field_2], [key_field_3]
   ORDER BY COUNT(*) DESC
   LIMIT 20
   ```
2. **Identify FP patterns:**
   - What are top FP sources? (Processes, users, hosts, tools)
   - Are FPs predictable? (Same tool/user/host repeatedly)
3. **Assess allowlist feasibility:**
   - Is allowlist static or dynamic? (Known tools vs. changing tools)
   - How many items? (<10 = manageable, >100 = unsustainable)
   - Allowlist churn rate? (Monthly updates = high burden)

**Long-Term Strategy:**
1. **Build allowlist for legitimate patterns:**
   ```yaml
   filter_legitimate:
     [field_name]:
       - [known_good_value_1]
       - [known_good_value_2]
       # ... all legitimate patterns
   ```
2. **Consider severity downgrade:**
   - If FP rate >5/day and severity is Critical → downgrade to High/Medium
   - Match severity to investigation burden (Critical = immediate response, High = same-day)
3. **Add enrichment fields:**
   - Capture additional context to aid triage (parent process, command line, file path)
   - Enable per-field allowlisting (not just blanket exclusions)
4. **Correlation opportunities:**
   - Combine with other signals for composite detection
   - Example: Process execution + network connection = higher confidence

**Recommendation Template:**
```
Verdict: ⚠️ CONDITIONAL (deploy with monitoring, build allowlist)

Rationale:
- High FP risk: [reason - widespread legitimate usage, etc.]
- Cannot distinguish attack from normal without [context]
- Requires [extensive/moderate/minimal] allowlist

Operational Concerns:
1. [Unknown/High] FP rate ([documented rate or "unknown from hunt"])
2. [Critical/High] severity + no throttle = [X] alerts/day investigation burden
3. Legitimate use case exists: [describe legitimate scenario]
4. [Additional concern]

Recommendations:

1. Monitor FP rate for 30 days:
   [SQL query to analyze signals]

2. Build allowlist for legitimate [patterns]:
   - Identify top FP [sources]
   - Examples: [tool1, tool2, tool3]
   - Allowlist [field]: [known-good values]

3. Consider severity downgrade:
   - Current: [severity]
   - If FP rate >[threshold]/day → downgrade to [new severity]

4. Add [enrichment field] for triage:
   - Capture [specific field] to distinguish attack from normal
   - Enable per-[field] allowlisting

5. [Optional] Correlation opportunity:
   - Rule 1: [this detection]
   - Rule 2: [complementary signal]
   - Composite: Alert only when BOTH fire
   - Benefit: Confirms [attack activity], reduces FPs

Deployment Guidance:
- ✅ Deploy in: [environments where this works]
- ❌ Do NOT deploy in: [environments with high FP risk]
- ⚠️ Requires: [prerequisites before deployment]
```

---

#### T - Tunable: Scope Drift Check

**Problem:** Detection scope wider than tested scope = unvalidated FP risk

**Check:**

Compare:
- **Queries executed** in CHECK phase (actual tested scope)
- **Detection logic proposed** in KEEP phase (deployment scope)

Examples of scope drift:
- Hunt tested: `/Users/*/Library/Safari/Cookies`
- Proposed detection: `/Users/*/Library/*` ← WIDER (untested paths)

- Hunt tested: `process.name = 'specific.exe'`
- Proposed detection: `process.name LIKE '%specific%'` ← FUZZIER (untested matches)

- Hunt tested: Single cloud region (us-east-1)
- Proposed detection: All regions ← BROADER (untested environments)

**Scoring:**

If **proposed scope > tested scope**:
1. **Flag as potential FP risk** - "Detection scope exceeds hunt test scope"
2. **Request baseline validation** - "Run queries at proposed scope before deployment"
3. **Score appropriately:**
   - **Minor drift** (10-20% wider): PARTIAL
   - **Moderate drift** (2-5x wider): FAIL
   - **Major drift** (10x+ or fundamentally different): FAIL

**Rationale:** The hunt's baseline FP validation only covers the tested scope. Wider scope = new FP sources not evaluated.

**Example:**
```
Hunt CHECK queries:
  - SELECT * WHERE file_path LIKE '/Users/%/Documents/malware.txt'
  
Proposed detection:
  - SELECT * WHERE file_path LIKE '/Users/%/Documents/%'
  
Scope drift: 
  - Hunt: 1 specific file
  - Detection: ALL files in Documents/
  - Drift factor: 1 file → ~10,000+ files
  - FP risk: CRITICAL (untested)
  - T-gate score: FAIL (requires baseline for full Documents/ scope)
```

**Remediation:**
- Run baseline query at proposed scope
- Document new FP rate
- Adjust detection or accept higher FP rate
- Re-score T-gate with new baseline data

---

### E - Exposure-tested FAILS → EXPAND Recommendations

**When it fails:** Only tested obvious path, bypasses not covered, evasion scenarios missing

**Immediate Actions:**
1. **List specific bypasses not covered:**
   - Alternative tools/methods (what else can achieve same goal?)
   - Obfuscation techniques (encoding, compression, renaming)
   - Alternative paths (different APIs, different files, different persistence mechanisms)
2. **Assess bypass likelihood:**
   - Are bypasses trivial? (rename file, change one parameter)
   - Are bypasses documented? (public evasion guides, red team tools)
   - Are bypasses in the wild? (observed in threat intel, other hunts)

**Long-Term Strategy:**
1. **Atomic Red Team test plan:**
   - Test primary detection path (confirm rule fires)
   - Test documented bypasses (confirm gaps)
   - Document findings: Which bypasses are NOT detected?
2. **Expand detection to cover bypasses:**
   - Add alternative tool names (if tool-based)
   - Add alternative file paths (if file-based)
   - Add alternative command patterns (if command-based)
3. **Build companion rules for alternative attack paths:**
   - Example: Detect scheduled task creation via file write AND schtasks.exe AND registry
   - Layered defense: Multiple detection points for same objective

**Recommendation Template:**
```
Verdict: ⚠️ PARTIAL PASS (covers primary path, bypasses not tested)

Rationale:
- Covers primary attack path: [describe what's covered]
- Bypasses NOT explicitly covered: [list gaps]

Bypasses NOT covered:
1. [Alternative tool/method]: [description]
2. [Obfuscation technique]: [description]
3. [Alternative path]: [description]
4. [Timing/order bypass]: [description]
5. [Detection blind spot]: [what's not visible]

Assessment:
- Bypass likelihood: [trivial/moderate/sophisticated]
- Bypass documentation: [public guides/none observed]
- Real-world usage: [observed in wild/theoretical]

Recommendations:

1. Atomic Red Team test plan:
   - Test: [primary detection path - confirm rule fires]
   - Test: [bypass 1 - alternative tool]
   - Test: [bypass 2 - obfuscation]
   - Test: [bypass 3 - alternative path]
   - Document: Which bypasses are NOT detected?

2. Expand detection to cover bypasses:
   [Specific additions to detection logic]

3. Build companion rules for alternative paths:
   - Companion 1: [alternative detection point]
   - Companion 2: [another alternative]
   - Result: Layered defense for [attack objective]

4. Monitor for evasion attempts:
   - Watch for [specific bypass indicators]
   - If observed: Expand detection immediately

Decision:
- [PROMOTE if bypasses are sophisticated/unlikely]
- [EXPAND before promoting if bypasses are trivial]
- [CONDITIONAL with monitoring if bypass likelihood unclear]
```

---

## Full Workflow Example (Generic Hunt)

**Scenario:** Hunt H-XXXX investigates suspicious PowerShell execution but doesn't propose explicit detections.

### Step 0: Read Hunt File

```
## OBSERVE: Expected Behaviors

### What Suspicious Looks Like
- PowerShell launched by non-admin processes (not typical IT tools)
- Encoded commands in PowerShell command line (-EncodedCommand flag)
- PowerShell connecting to external IPs on non-standard ports

## CHECK: Execute & Analyze

### Queries Executed
- Q1: PowerShell with -EncodedCommand (47 events/7 days)
- Q2: PowerShell spawned by Office apps (3 events, all Outlook/Word)
- Q3: PowerShell outbound connections to port 443 (2,341 events, mostly sanctioned)

## KEEP: Findings & Response

### Findings
- 3 suspicious: Word → powershell.exe -EncodedCommand (TP suspected but unconfirmed)
- 44 benign: IT admin scripts with -EncodedCommand
- Tuning: Exclude known admin users + specific script paths

### Follow-up Actions
- Validate 3 suspicious events with user interviews
- Consider detection for Office → PowerShell encoded commands
```

### Step 1: Pre-Flight Classification

- **Goal:** Detect suspicious PowerShell usage
- **KEEP content:** Findings + observations, NO explicit detection logic
- **Finding type:** Behavioral patterns (process chains)
- **Classification:** Behavioral detection hunt → Extract candidates (Step 1.5)

### Step 1.5: Extract Detection Candidates

**Candidate 1:** Office app spawning PowerShell with encoded commands
- **Pattern:** parent.process.name IN (winword.exe, outlook.exe, excel.exe) AND process.name = powershell.exe AND process.command_line CONTAINS '-EncodedCommand'
- **Telemetry:** EDR process events
- **Volume:** 3 events / 7 days → ~0.4/day
- **Tuning:** Already filtered for Office parents
- **Hunt outcome:** 3 suspected TPs (unconfirmed), 0 confirmed FPs

**Candidate 2:** PowerShell with -EncodedCommand (any parent)
- **Pattern:** process.name = powershell.exe AND process.command_line CONTAINS '-EncodedCommand'
- **Telemetry:** EDR process events
- **Volume:** 47 events / 7 days → ~6.7/day
- **Tuning:** Requires admin user allowlist + script path exclusions (44 benign from IT)
- **Hunt outcome:** 3 suspected TPs, 44 confirmed benign

**Candidate 3:** PowerShell outbound connections (non-standard ports)
- **Pattern:** process.name = powershell.exe AND destination.port NOT IN (80, 443, 53)
- **Telemetry:** EDR network events
- **Volume:** Unknown (not tested in hunt)
- **Tuning:** Unknown
- **Hunt outcome:** Not tested

**Decision:** Score Candidate 1 (best signal), note Candidate 2 as CONDITIONAL alternative

### Step 2: Score Candidate 1

**Detection:** Office → PowerShell -EncodedCommand

| Gate | Score | Evidence |
|------|-------|----------|
| **G** | ✅ PASS | Behavioral pattern (parent-child + command flag), not IOC |
| **A** | ✅ PASS | Fills T1566.001 (spearphishing attachment) gap, actionable single alert |
| **T** | ✅ PASS | Low volume (0.4/day), specific pattern, no allowlist needed |
| **E** | ⚠️ PARTIAL | Covers Office apps, but not other delivery mechanisms (browser downloads, ZIP files) |
| **S** | ✅ PASS | 0.4/day sustainable, static logic (no maintenance) |

**BASE Score:** 4.5/5 (E is partial but acceptable)

**Verdict:** ✅ **PROMOTE** (with recommendation to expand coverage in future)

### Step 3: Generate Output (Smart Single File)

**Verdict:** ✅ PROMOTE (4.5/5) → Generate YAML

**File:** `hunt-promotion-analysis/H-XXXX_GATES.yaml`

```yaml
# =============================================================================
# GATES Validation Output
# =============================================================================
# Hunt ID: H-XXXX
# Verdict: [PROMOTE|CONDITIONAL|HOLD|TIME-BOX|RECURRING HUNT]
# BASE Score: X.X/5
# Status: [Ready for detection engineering|Prerequisites required|Preserved for future]
# 
# WORKFLOW: ATHF → GATES → ADEF
#   1. ✅ Hunt executed (ATHF LOCK methodology)
#   2. ✅ Detection validated (GATES BASE criteria)
#   3. ⏭️  NEXT: Engineer production rule (ADEF FORGE methodology)
#
# DETECTION ENGINEERING WITH ADEF:
#
#   Installation:
#     pip install agentic-detection-engineering-framework
#
#   Workflow:
#     # 1. Stay in ATHF workspace - GATES already completed
#     # 2. Switch to ADEF workspace
#     cd ~/adef-workspace/
#     # 3. Run ADEF FORGE with path to this GATES output
#     adef forge --input ~/athf-workspace/hunt-promotion-analysis/H-XXXX_GATES.yaml
#
#   ADEF Repository:
#     https://github.com/Nebulock-Inc/agentic-detection-engineering-framework
#
# FILE STRUCTURE:
#   - hunt_metadata: Hunt context, MITRE mapping, traceability
#   - gates_validation: Quality scores, verdict, BASE criteria results
#   - narrative_analysis: Human-readable scoring rationale
#   - detections: Validated detection logic (input for ADEF F-FIND phase)
#
# VERDICT GUIDANCE:
#   - PROMOTE: Proceed to ADEF immediately (high quality, 4-5/5)
#   - CONDITIONAL: Complete prerequisites first, then ADEF (3/5, see prerequisites)
#   - HOLD: Not ready for production (0-2/5, see narrative for strategy)
#   - TIME-BOX: IOC-based detection with expiration (see narrative for timeline)
#   - RECURRING HUNT: High volume, periodic execution (see narrative for schedule)
#
# =============================================================================

hunt_metadata:
  hunt_id: H-XXXX
  title: "PowerShell Encoded Command Execution from Office Apps"
  techniques: [T1566.001, T1059.001]
  tactics: [initial-access, execution]
  hunt_outcomes:
    true_positives: 3
    false_positives: 0

gates_validation:
  verdict: PROMOTE
  base_score: 4.5
  detections_promoted: 1
  key_learnings:
    - "Office → PowerShell -EncodedCommand has low FP rate (0.4/day)"
    - "No allowlist needed when parent process is specific (Office apps only)"

# Human-readable narrative embedded
narrative_analysis: |
  ## Detection: Office → PowerShell -EncodedCommand
  
  ### BASE Criteria Scoring
  
  **G - Generalizable: ✅ PASS**
  Evidence from CHECK phase:
  - Query Q1: 3 suspicious events (Word/Outlook → powershell -EncodedCommand)
  - Query Q2: 44 benign events (IT admin scripts, different parents)
  - Pattern is behavioral (parent-child + command flag), not IOC
  
  **A - Additive: ✅ PASS**
  Coverage gap: No existing T1566.001 Office macro/spawning detection.
  Actionable: Single alert = clear investigation path.
  
  **T - Tunable: ✅ PASS**
  Volume: 3 events / 7 days = 0.4/day (sustainable)
  FP rate: 0 FPs when filtered to Office parents only
  No allowlist required.
  
  **E - Exposure-tested: ⚠️ PARTIAL**
  Covers: Office apps spawning PowerShell
  Missing: Browser downloads, ZIP attachments, other delivery mechanisms
  Recommendation: Expand in future hunt.
  
  **S - Sustainable: ✅ PASS**
  0.4/day volume, static logic, no maintenance burden.
  
  ### Verdict Rationale
  4.5/5 score supports PROMOTE. E is partial but acceptable - covers 
  primary Office-based delivery path. Recommend expanding to other 
  delivery mechanisms in future hunt.

detections:
  - detection_id: 1
    name: "Office Application Spawning Encoded PowerShell"
    
    gates_assessment:
      verdict: PROMOTE
      base_score: 4.5
      criteria:
        generalizable: PASS
        additive: PASS
        tunable: PASS
        exposure_tested: PARTIAL
        sustainable: PASS
      
      pattern_learned: "Office parent process filter eliminates IT admin FPs"
      recommended_for_similar: "Other Office → scripting combinations"
    
    deployment:
      engine: sigma
      status: EXPERIMENTAL
      severity: high
      
      detection_logic:
        selection:
          parent.process.name:
            - winword.exe
            - excel.exe
            - outlook.exe
            - powerpnt.exe
          process.name: powershell.exe
          process.command_line|contains: '-EncodedCommand'
        condition: selection
        
        description: |
          Detects Microsoft Office applications spawning PowerShell with 
          encoded commands. Common in spearphishing attachments (T1566.001).
      
      entities:
        - name: endpoint.uid
          type: endpoint
        - name: actor.user.name
          type: user
      
      operational_parameters:
        expected_volume: "~0.4 alerts/day (7-day hunt: 3 events)"
        fp_rate: "0 FPs (all 3 events were suspicious)"
        tuning_required: false
        soak_period_days: 7
      
      mitre_attack:
        - T1566.001  # Phishing: Spearphishing Attachment
        - T1059.001  # Command and Scripting Interpreter: PowerShell

aggregate_insights:
  successful_patterns:
    - pattern: "Parent process filtering for Office apps"
      gates_impact: "Eliminated 44 IT admin FPs, achieved T-gate PASS"

operational_handoff:
  next_steps:
    immediate:
      - "Deploy to detection repository (EXPERIMENTAL status)"
      - "7-day soak validation"
    week_1:
      - "Monitor FP rate (target: <5/day)"
      - "Run Atomic Red Team T1566.001 test"
    future:
      - "Expand: Browser download → PowerShell detection"
      - "Expand: ZIP extraction → PowerShell detection"
```

**Summary output:**
```
GATES Validation Complete: H-XXXX

Detection Extracted: Office → PowerShell -EncodedCommand
BASE Score: 4.5/5
Verdict: ✅ PROMOTE

File: hunt-promotion-analysis/H-XXXX_GATES.yaml
      (dual-purpose: agent learning + deployment template)

Next: Deploy to detection repository (EXPERIMENTAL), 7-day soak, test bypass scenarios
```

---

### S - Sustainable FAILS → MONITOR or RECURRING HUNT Recommendations

**When it fails:** Unknown FP volume, high maintenance burden, alert fatigue risk, multi-step investigation required

**Immediate Actions:**
1. **Assess alert volume impact:**
   - Query alerts table: How many alerts in 7/30 days?
   - Project daily rate: X alerts/day sustainable? (SOC capacity)
   - Compare to existing workload: Does this add significant burden?
2. **Evaluate maintenance burden:**
   - Is allowlist static or dynamic?
   - How often does allowlist need updates? (Monthly, quarterly, never)
   - Who maintains allowlist? (Security team, engineering, automated)
3. **Check for throttling:**
   - Does rule have throttle? (per-endpoint, per-user, per-entity)
   - If not: Can throttling be added? (Sigma = no, SQL-based detections = yes)

**Long-Term Strategy:**
1. **If unsustainable as standing detection → RECURRING HUNT:**
   - Convert detection logic to hunt playbook
   - Schedule quarterly execution (or as-needed)
   - Document: Why quarterly hunt vs. standing detection? (multi-step correlation, requires analyst judgment)
2. **If high maintenance → CONDITIONAL:**
   - Deploy only in environments with low churn (minimal allowlist updates)
   - Document prerequisites: Allowlist infrastructure, asset inventory, dedicated owner
3. **If volume manageable but unknown → EXPERIMENTAL soak:**
   - Deploy in EXPERIMENTAL status (shadow mode, no production findings)
   - Monitor for 30 days: Actual FP rate, alert volume, SOC triage time
   - Promote to ACTIVE if thresholds pass

**Recommendation Template:**
```
Verdict: ❌ RECURRING HUNT (unsustainable as standing detection)
         or ⚠️ CONDITIONAL (deploy with prerequisites)
         or ⚠️ EXPERIMENTAL (soak period required)

Rationale:
- [Unknown/High] FP volume ([documented or projected rate])
- High maintenance burden: [specific burden]
- [Alert fatigue/Multi-step correlation/No throttling] risk

Sustainability Concerns:
1. Alert volume: [X/day] ([manageable/high/unknown])
2. Maintenance: [static/dynamic] allowlist, [frequency] updates
3. Throttling: [none/per-endpoint/per-user]
4. SOC impact: [X hours/week investigation burden]

Recommendations:

[If unsustainable → RECURRING HUNT]
Convert to quarterly hunt playbook:
- Detection logic: [preserve query logic]
- Execution cadence: Quarterly (or as-needed based on threat intel)
- Why hunt vs. detection: [multi-step correlation/analyst judgment required/too noisy]
- Playbook location: [document in hunt vault]

[If high maintenance → CONDITIONAL]
Deploy only with prerequisites:
- Prerequisite 1: [allowlist infrastructure exists]
- Prerequisite 2: [asset inventory with role tagging]
- Prerequisite 3: [dedicated owner for allowlist maintenance]
- Best fit: [environments with low churn]
- Poor fit: [environments with high churn]

[If unknown volume → EXPERIMENTAL soak]
Deploy in EXPERIMENTAL for 30-day soak:
- Monitor: Actual FP rate, alert volume, SOC triage time
- Promotion criteria:
  - FP rate <[threshold]/day
  - Alert volume <[threshold]/day
  - Triage time <[X] min/alert
- After soak: Promote to ACTIVE or adjust to CONDITIONAL
```

---

## Case-by-Case Assessment Questions

When evaluating a detection for GATES, ask these questions to generate specific recommendations:

### Before Scoring (Data Collection)
1. **Hunt context:**
   - What were the hunt results? (TP/FP counts, baseline rates)
   - Were FPs documented and analyzed?
   - What tuning was applied during the hunt?
2. **Detection metadata:**
   - Author notes: What operational concerns were documented?
   - Known FPs: What legitimate use cases exist?
   - Performance notes: Any retrohunt timeouts or volume concerns?
3. **Deployment status:**
   - Is rule already ACTIVE? (If yes, check for soak metrics)
   - Has rule been soaked? (30-day FP rate from production)
   - What's current severity? (Critical = higher burden)

### During Scoring (Per Criterion)

**G - Generalizable:**
- Is this behavioral or IOC-based?
- Does pattern repeat across threat actors or is it campaign-specific?
- Are there IOCs embedded in "behavioral" logic? (domain literals, specific filenames)
- If IOC: What's the expected shelf life? (Campaign duration, IOC rotation cadence)

**A - Additive:**
- Does existing coverage exist for this technique?
- If overlap: What's different about this rule? (Better coverage, lower FP, different data source)
- If no overlap: Verify this is truly a gap (search technique in detection repo)
- Is detection actionable? (Single alert = clear action, or multi-step investigation required?)

**T - Tunable:**
- What's the documented FP rate from hunt? (If none: FLAG as unknown risk)
- Can attack be distinguished from normal? (With allowlist? With context? Not at all?)
- What FP patterns exist? (Tools, users, hosts, legitimate workflows)
- Is allowlist static (one-time build) or dynamic (frequent updates)?
- What's the maintenance burden? (Hours/month, owner, update frequency)

**E - Exposure-tested:**
- What was tested during hunt? (Primary path only? Bypass scenarios?)
- What bypasses are possible? (Alternative tools, obfuscation, alternative paths)
- How likely are bypasses? (Trivial, documented in red team guides, observed in wild)
- Are companion rules needed? (Alternative detection points for same objective)

**S - Sustainable:**
- What's the expected alert volume? (From hunt or projection)
- Is volume manageable for SOC? (<10/day = yes, >50/day = high burden)
- Is there throttling? (Check rule for alert.throttle configuration)
- What's maintenance burden over time? (Allowlist updates, tuning, review cycles)

### After Scoring (Verdict Selection)

**Score 5/5 or 4/5 → PROMOTE**
- Verify: FP rate is low (<5/day) or documented
- Verify: Operational burden is manageable (allowlist is static or small)
- Document: Any minor gaps (E is PARTIAL but acceptable)

**Score 3/5 → CONDITIONAL**
- Identify: Which criterion failed and why
- Provide: Specific allowlist to build OR monitoring plan OR prerequisites
- Define: Promotion criteria (what would move this to PROMOTE?)

**Score 1-2/5 → TIME-BOX or DROP**
- If IOC-based: TIME-BOX with 90-day review
- If duplicate: DROP with reference to existing rule
- If multi-step: RECURRING HUNT with playbook

**Multi-step investigation → RECURRING HUNT**
- Identify: Does detection require analyst to correlate multiple queries?
- Define: Hunt playbook (query sequence, correlation logic)
- Schedule: Quarterly or as-needed (based on threat intel)

---

## ATHF/ADEF Integration

Outputs feed ADEF **F - FIND** phase:

```
ATHF LOCK (Hunt) → GATES (Validate) → ADEF (Engineer)
     KEEP        → BASE assessment →    F - FIND
```

---


