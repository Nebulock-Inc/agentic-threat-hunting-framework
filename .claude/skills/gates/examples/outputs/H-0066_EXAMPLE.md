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

### Finding 1: Flat Network Segmentation
**Issue:** ~300 workstations share L2 with camera fleet  
**Why not a detection:** This is a **network topology state**, not a behavioral event  
**Output:** Remediation guidance (VLAN segmentation)

### Finding 2: NDAA Compliance Violation
**Issue:** Hikvision/Dahua cameras present with federal nexus  
**Why not a detection:** This is **vendor identification**, not malicious behavior  
**Output:** Vendor replacement plan, compliance advisory

### Finding 3: CVE Exposure
**Issue:** Cameras vulnerable to KEV CVEs (CVE-2021-36260)  
**Why not a detection:** This is **vulnerability presence**, not active exploitation  
**Output:** Patch guidance, disable default credentials

### Finding 4: No External Exposure
**Issue:** 0 cameras exposed on public IPs (Shodan validated)  
**Why not a detection:** This is **positive assurance**, not threat detection  
**Output:** Client advisory (perimeter is clean)

---

## Hypothetical: If Behavioral Detections Had Been Proposed

### Hypothetical Detection: Camera-to-Workstation SMB Pivot

**Pattern:** Camera IP initiating SMB to non-VMS host

**Why it would FAIL GATES:**
- **G:** ⚠️ Partial (pattern is generalizable)
- **A:** ✅ Pass (lateral movement gap)
- **T:** ❌ FAIL (requires per-tenant camera/VMS inventory - high maintenance)
- **E:** ⚠️ Partial (no evasion testing)
- **S:** ❌ FAIL (camera + VMS inventory updates on every camera deployment)

**Verdict:** ❌ RECURRING HUNT (too much operational overhead for standing detection)

**Better approach:** Quarterly manual assessment

---

## Correct Output: Client Advisory

### Client: Organization A

**Findings:**
- HIGH: Flat network (~300 workstations share L2 with cameras)
- MEDIUM: NDAA compliance violation (federal nexus confirmed)
- MEDIUM: Camera server lateral movement (SMB reach to 30+ hosts)

**Remediation Plan:**
1. Priority 1: VLAN segmentation (isolate camera subnet)
2. Priority 2: Audit camera server connections (principle of least privilege)
3. Priority 3: Vendor replacement plan (NDAA compliance)

**Timeline:** Quarterly re-assessment

---

### Client: Organization B

**Findings:**
- POSITIVE: Properly segmented (cameras on routed VLAN)
- POSITIVE: No external exposure (Shodan validated)

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
