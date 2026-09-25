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
| **Negative hunt** | 0 TPs, behavioral pattern tested | Evaluate for proactive deployment or HOLD | H-0060 (browser extension installer) |
| **Risk assessment hunt** | Configuration findings, no behaviors | Document as non-GATES (advisory output) | H-0066 (Camera infrastructure) |
| **Multi-step investigation** | Requires analyst correlation | Classify as RECURRING_HUNT playbook | Asset correlation hunts |
| **Baseline/inventory hunt** | Environmental understanding | Document as knowledge capture (no detection) | Asset inventory, normal behavior mapping |

**Key insight:** Not every hunt produces detections. GATES identifies which hunts should → detections vs. advisories vs. playbooks.

## Framework Reference

**GATES 5+5:** 5 BASE (assert from hunt) + 5 ADVANCED (demonstrate operationally)

**The acronym expands differently per tier, on purpose.** Each letter names a *concern*;
each tier asks a different question about it, so `A` and `S` take a different word in
ADVANCED than in BASE. The table below is the canonical naming — no other expansion of
GATES is current. In particular **"Accuracy", "Telemetry" and "Executability" are not
GATES gates**; if you see them, they're stale.

| Gate | BASE — assert (the word) | ADVANCED — demonstrate (the word) |
|------|--------------------------|-----------------------------------|
| **G** | **Generalizable** — repeatable behavior, or a one-off? | **Generalizable** — cross-fleet + companion rules that generalize the technique? |
| **A** | **Additive** — does it fill a coverage gap? | **Actionable** — is there a validated or automated playbook? |
| **T** | **Tunable** — tell attack from normal? 7- & 30-day look-back, FP rate in range? | **Tunable** — a reusable allowlist other rules can share? |
| **E** | **Exposure-tested** — covered the bypasses, or just the obvious path? | **Exposure-tested** — run emulation; did real telemetry reveal a gap? |
| **S** | **Sustainable** — juice worth the squeeze: can we reliably see it, is the upkeep fair? | **Soaked** — live 48h–7d: performance with concurrent detections, under the volume threshold? |

An unqualified gate name in this skill is always the **BASE** word, because BASE is what
GATES scores. ADVANCED is assessed after deployment and is never scored here.

**"BASE score" means the BASE tier's score** and nothing else: the sum of those five
gates, 0.0–5.0. ADVANCED contributes zero to it — which is exactly why the score carries
a tier name rather than being called "the GATES score".

**Failure modes**, listed in the order they are evaluated — **Step 4 holds the binding
rule; when two gates fail, the one higher in this list decides:**
1. **A fail** → DROP (duplicates existing coverage — nothing to add)
2. **G fail** → TIME_BOX (IOC or one-off, 90-day review)
3. **E fail** → HOLD — expand the detection to cover bypasses, then re-assess
4. **S fail** → RECURRING_HUNT or eng ticket (can't sustain it)
5. **T fail** → CONDITIONAL (tunable with watchlist, deploy after tuning)
6. **no gate failed** → the score band decides (4.0–5.0 PROMOTE, 3.0–3.9 CONDITIONAL, 0.0–2.9 HOLD)

Rows 2 and 4 both mean *carry the rule anyway, on a cycle*. If the hunt found **zero
instances** of the behavior, neither cycle is worth its maintenance → **HOLD**. Row 6 is
the carve-out: with no gate failed, 0 TPs over a clean baseline is a proactive PROMOTE.

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
   - Multi-query correlation required? → RECURRING_HUNT classification

**Decision tree:**
```
Does KEEP propose explicit detections?
├─ YES → Score those detections (Step 2)
└─ NO → Are findings behavioral patterns?
    ├─ YES → Extract detection candidates (Step 1.5)
    └─ NO → Are findings configuration/risk issues?
        ├─ YES → Non-GATES workflow (advisory output)
        └─ NO → Multi-step investigation?
            ├─ YES → RECURRING_HUNT playbook
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

Based on hypothesis, the *potential* of each gate once the hunt has run. This is a
pre-flight sketch, **not a score** — a planning hunt has no evidence, so it gets no
BASE score at all. Write what each gate is blocked on:

- G (Generalizable): [plausible | doubtful] — why
- A (Additive): [plausible | doubtful] — why
- T (Tunable): blocked on — needs a baseline
- E (Exposure-tested): blocked on — needs bypass testing
- S (Sustainable): blocked on — needs volume data

Do **not** write PASS/PARTIAL/FAIL here, and do not sum anything. Those are scoring
tokens and using them pre-execution invites someone to total the row into a verdict.

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

**If NO to Question 3** — the events exist and are visible, but no field separates
attack from benign at a workable rate — that is a `T` FAIL, not a telemetry gap. Score it
and let Step 4 return `CONDITIONAL`: the data is there, the baseline isn't.

**If NO to Question 1 or 2:**
- **Classification:** non-GATES (telemetry gap hunt) — a classification, not a verdict;
  the hunt never reaches the verdict enum because there is nothing scoreable yet
- **Output:** `.md` assessment documenting visibility limitations
- **Recommendations:** Infrastructure improvements (new data source, field population, correlation engine)
- **DO NOT proceed to BASE scoring** - detection is not feasible with current telemetry

**Examples:**
- H-0001 (ATHF Showcase): macOS information stealer detection → Strong EDR telemetry coverage for process execution, file access, and AppleScript events
- Reference: https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/blob/main/hunts/H-0001.md

*Note: Example references public ATHF showcase hunt. Your results will vary based on environment telemetry coverage.*

**Why check first:** a telemetry gap is uncommon but not rare, and catching it here avoids scoring five gates on a detection that cannot be built at all.

---

### Step 1: Hunt Discovery & Content Extraction

```bash
# Find and load the hunt file. Search every hunt location, not just production —
# hunts move test/ → production/, and a planning hunt (which routes to the
# not-ready-for-GATES path) is usually still in test/.
find hunts -name "${HUNT_ID}.md" -type f
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
  - `### Hunting Queries` → `#### Initial Query`, `#### Refined Query` (SQL, process
    searches, network patterns). The refined query is usually the better detection
    candidate: it is the initial one after FP tuning
  - `#### Query Performance` (result counts, time window, volumes)
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
- ✅ If multi-step investigation → still a candidate; it will fail `S` on the automation
  check and Step 4 resolves that to `RECURRING_HUNT`

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
   - If yes: score it — `S` FAILs the automation check, which Step 4 turns into
     `RECURRING_HUNT`. Score it rather than dropping it, so the reason is on record
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
   - **IOC layer** → Score separately (typically TIME_BOX with 90-day refresh)

3. **Score each independently:**
   - Behavioral: G=PASS (repeatable pattern), T/S depend on volume
   - IOC: G=FAIL (campaign-specific), but may TIME_BOX if operationally useful

4. **Output both detections** — one `candidate_id` each, sharing a stem and
   suffixed with the layer (`-behavioral` / `-ioc`). Never `1a`/`1b`: ordinals are
   not stable across runs, see "Candidate identity" in AGENT_MEMORY_SCHEMA.md.
   ```yaml
   detections:
     - candidate_id: powershell-download-cradle-behavioral
       name: "PowerShell Download Cradle (Behavioral)"
       gates_assessment:
         verdict: CONDITIONAL
         
     - candidate_id: powershell-download-cradle-ioc
       name: "Suspicious URI Pattern (IOC)"
       gates_assessment:
         verdict: TIME_BOX
         refresh_cycle: 90_days
   ```

**Why split?** IOC shelf life (90 days) ≠ behavioral logic (durable). Separate verdicts enable proper lifecycle management.

**Hybrid patterns seen in practice:**
- Download cradle behavior (CONDITIONAL) + Known malicious URIs (TIME_BOX)
- Suspicious process chain (PROMOTE) + C2 domain IOCs (TIME_BOX)
- High-volume npm operations (RECURRING_HUNT) + C2 infrastructure IOCs (TIME_BOX)

**Why this matters:** a hybrid that is scored as one candidate gets one verdict, and that verdict is wrong for one of its two halves — either the behavioral logic inherits the IOC's expiry, or the IOC inherits the behavioral rule's permanence.

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

**Output:** List of 1-N detection candidates OR determination that hunt produces no detection artifacts (risk assessment, baseline study, inventory)

### Step 2: BASE Criteria Evaluation

**Fast path — IOC with zero prevalence:**

An IOC-based candidate (`G` = FAIL) in a hunt that found **0 instances** resolves to
`HOLD` by the zero-prevalence rule in Step 4: a watchlist for a campaign that has never
touched this environment is clutter, not early warning. You can recognize that case up
front.

Score the other four gates anyway. The verdict is already known, but the scores are the
record of *why*, and a candidate with no `base_score` can't be compared against the next
one that looks like it. Output is a `.md` assessment, and activation is contingent on
threat intel showing the campaign in scope.

Contrast `H-0065_EXAMPLE.md`: also an IOC watchlist, also a `G` FAIL, but the campaign
*is* present — so it is `TIME_BOX`, not `HOLD`. Prevalence is the whole difference.

---

For each detection candidate (explicit or identified), score all 5 BASE criteria as
✅ PASS, ⚠️ PARTIAL, or ❌ FAIL. There is no fourth value — an unevidenced gate is
PARTIAL, never `UNKNOWN`, because only these three have point values.

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
| **A - Additive** | Does it fill a coverage gap? | **✅ Check:** Technique coverage in detection repo<br>**→ PROMPT USER** if detection repository not available |
| **T - Tunable** | Tell attack from normal? Can FPs be managed? | **✅ If available:** Hunt TP/FP counts from Findings table<br>**⚠️ If unavailable:** Assess from query volumes, documented exclusions, "normal" behaviors<br>**✅ Tunable:** Filters/allowlists documented in hunt<br>**❌ High risk:** Widespread legitimate use, no clear filters<br>**🎯 Clean baseline:** 0 suspicious over a large sample is evidence the gate is satisfiable, so it lifts **T from PARTIAL to PASS**. It is not a separate bonus — there is no `+0.5` to add on top of a gate result<br>**⏱️ The lift is only as good as its window.** A hunt-length sample (≤7 days) shows the pattern *can* be tuned, not that it *is*: event volume is not the same as time coverage, and a clean week says nothing about monthly batch jobs, patch cycles or quarterly automation. Under 30 days the clean baseline holds **T at PARTIAL** and the candidate deploys `EXPERIMENTAL` for a soak — record the window you measured, not just the event count |
| **E - Exposure-tested** | Covered the bypasses, or just the obvious path? | **✅ Multiple angles:** Count of queries/detection layers<br>**✅ Bypass testing:** Documented evasion scenarios<br>**⚠️ Single path:** Only one query pattern tested |
| **S - Sustainable** | Juice worth the squeeze: can we see it, is upkeep fair? | **✅ If available:** Hunt alert volumes from queries<br>**⚠️ If unavailable:** Project from query result counts<br>**✅ Low burden:** Static allowlist, reliable telemetry<br>**❌ High burden:** Dynamic allowlist, requires correlation<br>**📊 VOLUME THRESHOLDS:**<br>- **<10/day:** Sustainable (manual triage feasible)<br>- **10-100/day:** Conditional (requires aggregation/throttling)<br>- **>100/day:** Likely unsustainable unless TP rate >1%<br>**🤖 AUTOMATION CHECK:** Can SOC act without per-alert human context?<br>- ✅ "Is user authorized?" (allowlist lookup = automatable)<br>- ❌ "Does policy allow this tool?" (business judgment = not automatable)<br>- **If per-alert context required:** S-FAIL → RECURRING_HUNT |

### BASE Scoring

Each gate scores:
- **PASS** = 1.0 point (criterion fully met)
- **PARTIAL** = 0.5 points (criterion partially met with caveats)
- **FAIL** = 0.0 points (criterion not met)

**BASE Score** = Sum of gate scores (0.0 to 5.0). Record it as a **float** —
`4.5`, not `"4.5/5"` — because consumers average and threshold it.

**Verdict Mapping:** see **Step 4: Verdict & Output**, which is the single
authoritative statement of how a score and the gate results become a verdict. Do not
score a verdict from this section; the score alone is not sufficient to decide one.

**Examples:**
- All PASS: `5.0`
- 4 PASS + 1 PARTIAL: `4.5`
- 3 PASS + 1 PARTIAL + 1 FAIL: `3.5`
- 4 PASS + 1 FAIL: `4.0` — a high score *with* a FAIL. The FAIL decides the verdict,
  not the 4.0; see Step 4.

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
| **No query volumes** | Project from hunt scope (days × tenants) | S-score: **PARTIAL** — volume is projected, not measured. Recommend EXPERIMENTAL soak to confirm. Never UNKNOWN: it has no point value, so it would silently drop the score |
| **No exclusion filters** | Assess from "normal" behavior descriptions | T-score: PARTIAL if tuning possible, FAIL if no clear filters |
| **Hunt found 0 TPs** | Valid outcome, doesn't fail GATES | G/A/E can still PASS; T/S may be PARTIAL (unvalidated). Step 4's zero-prevalence rule decides: with a `G` or `S` FAIL it is `HOLD`; with no FAIL and a clean baseline it is a proactive `PROMOTE` |
| **Multi-step correlation** | `S` = FAIL (automation check) | Score all five gates; Step 4 resolves the `S` FAIL to `RECURRING_HUNT` |
| **Risk assessment hunt** | No detection artifacts | Document as non-GATES workflow (like H-0066) |

**Key principle:** missing data means **PARTIAL**, not an automatic FAIL. It does not
imply a verdict — the verdict is still Step 4's. Note that PARTIALs do not accumulate
into `CONDITIONAL`: an all-PARTIAL candidate scores 2.5, which is `HOLD`. Document what
is unmeasured and name the validation step that would resolve it.

**Rule type impact on the `G` gate** — rule type determines `G` and nothing else; the
other four gates and the verdict still come from the evidence:
- **BEHAVIORAL**: process patterns, TTPs → `G` PASS
- **TOOL**: tool signatures → `G` PASS
- **IOC**: IPs, domains, hashes → `G` FAIL (→ `TIME_BOX`, or `HOLD` at zero prevalence)
- **HYBRID**: mixed → split into behavioral + IOC candidates and score each
- **MULTI-STEP INVESTIGATION**: Detection requires multiple queries with intermediate results that must be manually correlated → not reducible to a single alert, so `S` FAILs the automation check → `RECURRING_HUNT` (quarterly hunt playbook, not a standing detection)
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

These are the **ADVANCED** words (`A` = Actionable, `S` = Soaked), per the Framework
Reference. They are recommendations only — ADVANCED is never scored into the BASE score.

### Step 4: Verdict & Output

Exactly one verdict per candidate, from the canonical enum:
`PROMOTE | CONDITIONAL | TIME_BOX | RECURRING_HUNT | HOLD | DROP`.

#### Verdict precedence (apply in order, first match wins)

A **gate FAIL names a specific defect** and therefore dictates a specific remedy. A
score band is only a summary. So a FAIL always overrides the band — otherwise a
candidate can score into PROMOTE while failing the gate that says it isn't
deployable at all, and two readers get two different answers.

Evaluate in this order and stop at the first rule that matches:

| # | Condition | Verdict | Why this precedence |
|---|-----------|---------|---------------------|
| 1 | **A = FAIL** | `DROP` (or merge into the existing detection) | Coverage already exists. Nothing to build regardless of how well it scores elsewhere — the strongest veto. |
| 2 | **G = FAIL** | `TIME_BOX` | Campaign- or IOC-specific. Useful now, worthless later — build it with an expiry and a refresh cycle. |
| 3 | **E = FAIL** | `HOLD` + expand the hunt | Not enough angles were tested to *judge* the candidate. This is an epistemic block: any other verdict would be a guess. |
| 4 | **S = FAIL** *and the behavior occurs* | `RECURRING_HUNT` | Real signal, but it cannot run as a standing detection. Re-run it periodically instead. |
| 5 | **T = FAIL** | `CONDITIONAL` | Good logic, too noisy *today*. Deployable once the baseline/allowlist exists. |
| 6 | *no FAIL* | score band below | Nothing is broken; the score decides readiness. |

**Zero prevalence downgrades a deploy-anyway verdict to `HOLD`.** Rows 2 and 4 both say
*carry this rule anyway, on a cycle* — `TIME_BOX` with a refresh, `RECURRING_HUNT` with a
cadence. Neither is worth doing when the hunt found **zero instances** of the behavior: a
campaign watchlist for a campaign that has never touched the environment, and a quarterly
re-run of a query that matches nothing, are both maintenance with no expected yield. In
either case the verdict is `HOLD` — preserve the logic, record why, re-assess when threat
intel moves.

This modifies **only rows 2 and 4**. It does not apply to row 1 (`DROP` means don't even
preserve it — the coverage exists), row 3 (`HOLD` already), or row 5 (a `CONDITIONAL`
prerequisite is worth building regardless of current prevalence). Critically, it does
**not** apply to a candidate with no FAIL at all: a generalizable, well-baselined, quiet
detection that found 0 TPs is a **proactive `PROMOTE`** — a clean baseline over a large
sample *and a long enough window* is exactly what buys you the confidence to deploy
ahead of the threat. Under 30 days it is still `PROMOTE` (4.5, `T` PARTIAL), but as an
`EXPERIMENTAL` soak rather than a settled rule.

Two or more FAILs: the earliest matching row wins. It is the one that has to be
solved first, and solving it changes the assessment of the rest.

**Why `G` outranks `E` and `S`.** A `G` FAIL is a statement about the candidate's
*kind*, not a defect in it: it is an IOC or campaign rule. Rules of that kind are
single-dimensional and short-lived **by construction**, so they will almost always
trip `E` and `S` too. Those aren't three independent problems to solve — they are
one fact reported three times, and `TIME_BOX` is already the mitigation for all
three. Reading `E` first would send every IOC watchlist to `HOLD` and the skill
would never emit `TIME_BOX` at all.

`A` still outranks `G`: if the coverage already exists, don't build a time-boxed
copy of it either.

#### Score band (only when no gate FAILed)

Contiguous and total — every score from 0.0 to 5.0 maps to exactly one verdict:

| BASE score | Verdict |
|------------|---------|
| **4.0 – 5.0** | ✅ `PROMOTE` — deploy as a standing detection |
| **3.0 – 3.9** | ⚠️ `CONDITIONAL` — deploy after prerequisites |
| **0.0 – 2.9** | ❌ `HOLD` — record the reasoning, build nothing |

With no FAILs the floor is 2.5 (five PARTIALs), so the 0.0–2.9 row is reachable only
by an all-PARTIAL candidate. Score bands do not produce `TIME_BOX`,
`RECURRING_HUNT` or `DROP` — those come from the precedence table above, and only
from it.

#### Worked examples

| Criteria | Score | Band says | FAIL rule says | **Verdict** |
|----------|-------|-----------|----------------|-------------|
| G,A,T,E,S all PASS | 5.0 | PROMOTE | — | `PROMOTE` |
| 4 PASS + E PARTIAL | 4.5 | PROMOTE | — | `PROMOTE` |
| G FAIL, rest PASS | 4.0 | PROMOTE | #2 TIME_BOX | `TIME_BOX` |
| T FAIL, S PARTIAL, rest PASS | 3.5 | CONDITIONAL | #5 CONDITIONAL | `CONDITIONAL` |
| S FAIL, T PARTIAL, rest PASS | 3.5 | CONDITIONAL | #4 RECURRING_HUNT | `RECURRING_HUNT` |
| S FAIL, A+T PARTIAL, 0 hits found | 3.0 | CONDITIONAL | #4, zero prevalence | `HOLD` |
| G FAIL, rest PASS, 0 hits found | 4.0 | PROMOTE | #2, zero prevalence | `HOLD` |
| T+S FAIL, rest PASS | 3.0 | CONDITIONAL | #4 RECURRING_HUNT | `RECURRING_HUNT` |
| G+E+S FAIL, A+T PASS | 2.0 | HOLD | #2 TIME_BOX | `TIME_BOX` |
| A FAIL, rest PASS | 4.0 | PROMOTE | #1 DROP | `DROP` |

Every row except the first two is a case where the band and the gates disagree.
Before this rule they were genuinely undecidable, and a consumer building from the
document would take a different action depending on which section it read. The last
two rows are the multi-FAIL cases — note that neither is decided by the highest
count of FAILs or by the score, only by which row matches first.

**Generate output based on verdict:**

### Smart Single-File Strategy

**This table routes on the *hunt-level* verdict, not a candidate's.** The hunt-level
verdict picks the file; each candidate keeps its own verdict inside that file. So a
PROMOTE hunt's `.yaml` legitimately contains TIME_BOX, HOLD or DROP candidates
alongside the deployable ones — that is not a contradiction, and a consumer must handle
every verdict it finds inside a `.yaml`, not only the deployable ones. See the
hunt-level vs candidate-level table in `AGENT_MEMORY_SCHEMA.md`.

| Hunt-level verdict | File Generated | Purpose | Contains |
|--------------------|----------------|---------|----------|
| **PROMOTE / CONDITIONAL** | `H-XXXX_GATES.yaml` | Deployment + learning | Structured data, narrative (embedded), deployment templates, agent-queryable metadata |
| **HOLD / DROP / TIME_BOX / RECURRING_HUNT** | `H-XXXX_GATES.md` | Analysis only | Narrative verdict, reasoning, recommendations (no deployment) |
| **Risk Assessment / Non-GATES** | `H-XXXX_ASSESSMENT.md` | Advisory | Client advisory, remediation guidance (not detection) |

**Result:** exactly **one file per hunt** — never one per detection — and the extension
tells a consumer whether there is anything deployable inside.

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

### Markdown Structure (when verdict = HOLD/DROP/TIME_BOX or non-GATES)

Lightweight narrative report:
```markdown
# GATES Validation: H-XXXX

**Verdict:** <one of ❌ HOLD, ⏱️ TIME_BOX, 🔄 RECURRING_HUNT, 🚫 DROP>
**BASE Score:** X.X

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

Verdict: <hunt-level verdict> (<N> candidates)

File: hunt-promotion-analysis/H-XXXX_GATES.yaml
      (or H-XXXX_GATES.md if HOLD, or H-XXXX_ASSESSMENT.md if non-GATES)

Next: [Deploy to detection repository | Build baseline | Convert to recurring hunt]
```

---

## Scoring Examples Reference

**Detailed examples:** `examples/README.md`

**Quick pattern recognition:**

| Rule Pattern | Typical Score | Common Verdict | Example |
|--------------|---------------|----------------|---------|
| Behavioral (process) | 4.5-5.0 | ✅ PROMOTE | Process injection, credential-store access |
| Known-offensive-tool signature | 4.5-5.0 | ✅ PROMOTE | Named post-exploitation or C2 frameworks |
| IOC (domain/IP) | 1.0-2.0 | TIME_BOX, or HOLD at zero prevalence | Campaign C2 domains, single-campaign IPs |
| High-volume API | 2.0-3.0 | CONDITIONAL/HOLD | A cloud control-plane call at thousands/day |
| Hybrid (behavioral+IOC) | scored per layer | *split into two candidates* | Connection pattern + domain IOC — score each half separately; neither `SPLIT LAYERS` nor `HYBRID` is a verdict |
| Baseline-required | 2.0-3.0 | CONDITIONAL | Per-entity anomaly detection — a missing baseline is a `T` FAIL (row 5), not an `S` one |
| Duplicate coverage | Varies | DROP | Overlapping rules on the same technique |

*Scores are typical, not prescriptive — score the evidence you actually have, then apply
the Step 4 precedence rule.*

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
- T: ❌ FAIL (every one of the 12 events is a known partner — without the allowlist
  there is nothing left to alert on)
- E: ⚠️ PARTIAL (only FTP tested, HTTP separate)
- S: ✅ PASS (low volume, static allowlist)

**BASE Score:** 3.5  *(G 1.0 + A 1.0 + T 0.0 + E 0.5 + S 1.0)*

**Verdict:** ⚠️ CONDITIONAL — the `T` FAIL pins it (precedence #5). Build the 3-destination
allowlist, then re-score `T`.

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

**BASE Score:** 5.0  *(all five PASS)*

**Verdict:** ✅ PROMOTE

### Example 3: Hunt Produces No Detection Artifacts

**Hunt:** Camera/NVR infrastructure security assessment

**Findings:** Flat network segmentation, prohibited-vendor hardware, no external exposure

**Detection extraction:** None - findings are configuration states, not behavioral events

**GATES classification:** NOT APPLICABLE (risk assessment hunt, not detection hunt)

**Outcome:** Client advisories + remediation plan (not GATES validation)

### Example 4: Multi-Step Investigation Hunt

**KEEP phase finding:**
> "Query 1: List users with MFA changes (37 users). Query 2: For those users, check concurrent sessions (analyst manually correlates). Query 3: For suspicious pairs, investigate login history."

**Detection extraction:** Attempted, but requires analyst correlation between steps

**Verdict:** 🔄 `RECURRING_HUNT` — the correlation between steps is analyst judgment, so
`S` FAILs (precedence #4) and the behavior does occur, so it is not `HOLD`. Convert to a
quarterly hunt playbook. There is no "not a detection" verdict: a candidate that can't be
automated is still recorded, with the reason.

---

## Remediation: what the narrative must state when a gate FAILs

The verdict itself comes from Step 4. This section is only about what the write-up has
to *say* so the reader can act on it. Write prose — there is no template to fill in.

| Gate | Verdict (Step 4) | State in the narrative |
|------|------------------|------------------------|
| **G** | `TIME_BOX` | Where the IOCs came from and their refresh cadence; the review date (creation + 90 days); the behavioral companion rule to build so coverage outlives the campaign |
| **A** | `DROP` | Which existing rule already covers this, and whether anything here is meaningfully different (data source, FP rate, tuning). If the two are better as one rule, recommend merging into the existing one rather than building this |
| **T** | `CONDITIONAL` | The FP sources observed; whether the allowlist is static or dynamic, its size, and who maintains it. Name the promotion criterion — the measurement that would move this to `PROMOTE` |
| **E** | `HOLD` | The specific bypasses not covered, how trivial each is to perform, and the emulation needed to close them (Atomic Red Team test IDs where they exist) |
| **S** | `RECURRING_HUNT`, or `HOLD` at zero prevalence | Alert volume per day, the maintenance burden, and whether throttling is possible. For `RECURRING_HUNT`: the execution cadence, and why analyst judgment is required instead of a standing rule |

Three bright lines make these calls non-arbitrary:

**Volume (S).** <10/day is sustainable — manual triage is feasible. 10–100/day needs
aggregation or throttling first. >100/day is unsustainable as a standing detection
unless the TP rate exceeds 1%.

**Allowlist feasibility (T).** Under ~10 entries and static is manageable; over ~100,
or needing monthly updates, is not. A dynamic allowlist is an ongoing maintenance
commitment rather than a one-time build, so it costs `S` as well as `T`.

**Automation (S).** Can the SOC act without per-alert human context? "Is this user
authorized?" is an allowlist lookup and automatable. "Does policy permit this tool?"
is business judgment and is not. If every alert needs the latter, `S` FAILs.

### T - Tunable: scope drift check

**Problem:** a detection scoped wider than what the hunt actually tested carries
unvalidated FP risk. The hunt's baseline only covers the tested scope; anything wider
introduces FP sources nobody has looked at.

Compare the **queries executed** in CHECK against the **detection logic proposed** in
KEEP. Drift looks like:

- tested one file → proposed the whole directory (untested paths)
- tested `process.name = 'specific.exe'` → proposed `LIKE '%specific%'` (untested matches)
- tested one cloud region → proposed all regions (untested environments)

Score the drift: minor (10–20% wider) is `PARTIAL`; moderate (2–5×) or major (10×+, or
fundamentally different) is `FAIL`. Either way, say so explicitly — "detection scope
exceeds hunt test scope" — and state that a baseline at the *proposed* scope is required
before deployment, after which `T` can be re-scored.

---

## Worked example

`examples/outputs/H-0062_EXAMPLE.yaml` is a complete conformant output: four candidates,
two verdicts, per-gate criteria that sum to the stated `base_score`, and a hunt-level
verdict that is deliberately not an aggregate of the candidate ones.

Read that file rather than a walkthrough reproduced here. Two copies of the same artifact
drift — that is how three of the examples in this skill ended up with scores their own
criteria didn't add up to.

## ATHF/ADEF Integration

A `.yaml` output is the handoff artifact for ADEF, whose FORGE lifecycle picks up where
GATES stops:

```
ATHF LOCK (Hunt) → GATES (Validate) → ADEF FORGE (Engineer)
     KEEP        → BASE assessment  →  F - FIND
```

```bash
adef hunt-promote --gates ~/athf-workspace/hunt-promotion-analysis/H-0062_GATES.yaml
# --dry-run first to see what it would mint
```

Each deployable candidate lands at the Find stage with its own `D-XXXX`, catalog record
and journal, keyed by `hunt_ref: "<hunt_id>#<candidate_id>"` — which is why
`candidate_id` has to be stable across re-runs (see AGENT_MEMORY_SCHEMA.md). Archival
candidates are reported as skipped rather than minted.

A `.md` output has nothing for ADEF to import by design: the verdict says build nothing
yet. It stays in the ATHF workspace as the record of why.

---


