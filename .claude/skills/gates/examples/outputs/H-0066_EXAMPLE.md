# Example: Risk Assessment (Non-GATES Workflow)

**Hunt:** H-0066 - IP Camera/NVR/VMS Infrastructure Security Assessment  
**Classification:** Risk Assessment (not behavioral detection hunt)  
**Output Type:** Advisory (non-GATES)

---

## Why Non-GATES?

This hunt assessed infrastructure security posture, not adversary behaviors. All 7 findings are **configuration states** and **exposure issues**, not behavioral patterns that can be automated into detections.

**GATES decision tree:** 
```
Hunt proposes explicit detections? → NO
Are findings behavioral patterns? → NO
Are findings configuration/risk issues? → YES
→ Non-GATES workflow (advisory output)
```

---

## Findings (Not Detectable)

> The findings below are paraphrased and de-identified. A risk assessment's output is
> a list of a specific organization's *unremediated* weaknesses, so the details are
> more sensitive than a detection rule's — publish the shape of the finding, never the
> environment that has it.

### Finding 1: Flat Network Segmentation
**Issue:** General-purpose workstations share an L2 segment with the camera fleet  
**Why not a detection:** This is a **network topology state**, not a behavioral event  
**Output:** Remediation guidance (VLAN segmentation)

### Finding 2: Prohibited-Vendor Hardware
**Issue:** Camera models from a vendor barred by the organization's procurement policy  
**Why not a detection:** This is **vendor identification**, not malicious behavior  
**Output:** Vendor replacement plan, compliance advisory

### Finding 3: CVE Exposure
**Issue:** Camera firmware vulnerable to a KEV-listed CVE  
**Why not a detection:** This is **vulnerability presence**, not active exploitation  
**Output:** Patch guidance, disable default credentials

### Finding 4: No External Exposure
**Issue:** No cameras reachable from the public internet (externally validated)  
**Why not a detection:** This is **positive assurance**, not threat detection  
**Output:** Client advisory (perimeter is clean)

---

## Hypothetical: If Behavioral Detections Had Been Proposed

### Hypothetical Detection: Camera-to-Workstation SMB Pivot

**Pattern:** Camera IP initiating SMB to non-VMS host

**Why it would FAIL GATES:**
- **G:** ⚠️ PARTIAL (0.5) — the pivot pattern generalizes, but the host roles don't
- **A:** ✅ PASS (1.0) — lateral movement gap
- **T:** ❌ FAIL (0.0) — requires a per-environment camera/VMS inventory to tell a pivot from normal VMS traffic
- **E:** ⚠️ PARTIAL (0.5) — no evasion testing
- **S:** ❌ FAIL (0.0) — that inventory has to be re-derived on every camera deployment

**BASE Score:** 2.0

**Verdict:** ❌ RECURRING_HUNT (too much operational overhead for standing detection)

Two gates FAILed. `S` (row 4) is evaluated before `T` (row 5), so RECURRING_HUNT wins
over CONDITIONAL — and correctly: an allowlist you must rebuild continuously isn't a
prerequisite you can finish, which is what CONDITIONAL promises.

**Better approach:** Quarterly manual assessment

---

## Correct Output: Client Advisory

### Client: Organization A

**Findings:**
- HIGH: Flat network (workstations share L2 with cameras)
- MEDIUM: Procurement-policy violation (prohibited camera vendor present)
- MEDIUM: Camera server lateral movement (broad SMB reach)

**Remediation Plan:**
1. Priority 1: VLAN segmentation (isolate camera subnet)
2. Priority 2: Audit camera server connections (principle of least privilege)
3. Priority 3: Vendor replacement plan (procurement compliance)

**Timeline:** Quarterly re-assessment

---

### Client: Organization B

**Findings:**
- POSITIVE: Properly segmented (cameras on routed VLAN)
- POSITIVE: No external exposure (externally validated)

**Assessment:** Security best practices demonstrated. Annual validation recommended.

---

## Key Lesson

**Not every hunt produces detections** - that's valid and expected.

**Hunt taxonomy:**
1. **Behavioral detection hunts** → GATES validation → Detection rules
2. **Risk assessment hunts** → Advisory output → Remediation plans
3. **Baseline/inventory hunts** → Knowledge capture → Documentation

Each has value, but only #1 goes through GATES.

---

## GATES Applicability Test

**Questions:**
- Are findings behavioral patterns? NO (configuration states)
- Can findings be automated as alerts? NO (require manual assessment)
- Is output detection rules? NO (client advisories)

**Result:** Non-GATES workflow (correct classification)
