# Example: PROMOTE Verdict (Zero TPs, TEST Deployment)

**Hunt:** H-0060 - Browser Extension Installer Technique  
**Verdict:** PROMOTE  
**Deployment Status:** TEST (30-day soak required)  
**BASE Score:** 4.0  *(G 1.0 + A 1.0 + T 0.5 + E 1.0 + S 0.5)*

---

## Summary

Hunt validated detection logic via emulation but found 0 true positives across a multi-billion-event Windows sample (7 days). Volume and FP rate unmeasured. No gates FAILED → score 4.0 → PROMOTE verdict. Deploys to TEST (not PRODUCTION) for 30-day soak to validate operational assumptions before graduating to PRODUCTION.

---

## BASE Criteria Scoring

**G - Generalizable: ✅ PASS**

Behavioral pattern (browser extension abuse via headless Chrome), not IOC-based. Repeatable across different adversaries using browser-as-platform techniques.

Evidence:
- Technique: T1176.001 (Browser Extensions)
- Pattern: Headless Chrome + extension loading flags
- Detection angles: 5 different approaches documented
- All behavioral, zero IOCs embedded

**A - Additive: ✅ PASS**

Fills T1176.001 gap (browser extension abuse). No existing coverage for this technique. Zero TPs is valid - proactive detection for emerging attack pattern documented in public ClickFix campaign reporting.

**T - Tunable: ⚠️ PARTIAL**

FP rate unvalidated. Tuning possible (specific flags/parent process) but unmeasured → PARTIAL.

> Missing measurement = **PARTIAL**, not UNKNOWN (UNKNOWN has no point value).

**E - Exposure-tested: ✅ PASS**

Five angles: headless Chrome flags, browser→script chain, user-data-dir manipulation, extension artifacts, C2 domains. Emulation validated on synthetic ClickFix chain.

**S - Sustainable: ⚠️ PARTIAL**

Volume unmeasured (projected 10-50/day). Allowlist burden unknown - TEST soak validates.

---

## Verdict Rationale

No gates FAILED → score 4.0 → PROMOTE verdict. Deploys to TEST (not PRODUCTION) because T and S are PARTIAL (unmeasured). ADVANCED-S soak validates volume assumptions before PRODUCTION graduation.

**ADVANCED-S Requirements:**
1. 30-day TEST soak measuring alert volume
2. Build developer tool allowlist (Puppeteer, Playwright, Selenium)
3. Confirm post-filter volume <10/day
4. Graduate to PRODUCTION after successful soak

---

## Deployment Plan

**Phase 1 (TEST - 30 days):** Deploy angle 1 (headless Chrome + extension flags), measure volume, build allowlist from observed legitimate use. Target: <10/day post-filter.

**Phase 2 (PRODUCTION):** If soak successful (FPs reduced >90%), deploy angles 2-4. IOC angle 5 deploys separately as threat intel becomes available.

---

## Key Lesson

**Zero TPs + unmeasured volume = PROMOTE to TEST** - sound detection logic with proactive value. No gates FAILED (T and S are PARTIAL, not FAIL), so score 4.0 → PROMOTE verdict. Deployment status = TEST (not PRODUCTION). ADVANCED-S soak validates operational assumptions (volume, allowlist burden) before graduating to PRODUCTION. 

**Two-tier validation:** BASE tier asserts detection quality → verdict. ADVANCED tier demonstrates operational viability → TEST → PRODUCTION graduation.
