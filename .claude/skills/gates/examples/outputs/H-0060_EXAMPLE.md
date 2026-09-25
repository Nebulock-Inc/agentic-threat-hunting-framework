# Example: HOLD Verdict (Zero TPs, Preserve Detection Logic)

**Hunt:** H-0060 - Browser Extension Installer Technique  
**Verdict:** HOLD (no operational need, preserve for threat-intel activation)  
**BASE Score:** 3.0  *(G 1.0 + A 0.5 + T 0.5 + E 1.0 + S 0.0)*

---

## Summary

Hunt validated detection logic via emulation but found 0 true positives across a multi-billion-event Windows sample (7 days). Detection pattern is sound but zero prevalence = no operational need. Preserve as quarterly threat-intel-driven hunt.

---

## BASE Criteria Scoring

**G - Generalizable: ✅ PASS**

Behavioral pattern (browser extension abuse via headless Chrome), not IOC-based. Repeatable across different adversaries using browser-as-platform techniques.

Evidence:
- Technique: T1176.001 (Browser Extensions)
- Pattern: Headless Chrome + extension loading flags
- Detection angles: 5 different approaches documented
- All behavioral, zero IOCs embedded

**A - Additive: ⚠️ PARTIAL**

Fills T1176.001 gap (browser extension abuse), BUT zero TPs = no demonstrated operational need.

Coverage gap confirmed:
- No existing browser extension detections
- Technique documented in public ClickFix-style campaign reporting
- Zero observed activity in the hunted environment = no urgency

**T - Tunable: ⚠️ PARTIAL**

No execution results to validate FP rate, and developer workstations make legitimate use of headless Chrome (Puppeteer, Playwright). Tuning is clearly *possible* — the flags and parent process are specific — but unmeasured, so this is PARTIAL, not PASS.

> Missing measurement is **PARTIAL**, never `UNKNOWN`. `UNKNOWN` is not a gate result and has no point value, so scoring it silently drops the total.

**E - Exposure-tested: ✅ PASS**

Five detection angles cover full attack chain:
1. Headless Chrome + extension loading flags
2. Browser → script interpreter chain
3. Browser user-data-dir manipulation
4. Malicious extension artifacts
5. C2 domains (IOC watchlist)

Emulation: ✅ Validated on synthetic ClickFix chain

**S - Sustainable: ❌ FAIL**

Unknown alert volume + potential high allowlist maintenance. Zero TPs = cannot justify investigation burden.

---

## Verdict Rationale

**HOLD (not PROMOTE) because:**
1. ✅ Detection logic is sound (validated by emulation)
2. ❌ Zero prevalence = no operational need (0 hits across the full sample)
3. ❌ Unmeasured FP rate on developer workstations
4. ❌ Cannot justify investigation burden with zero expected yield
5. ✅ Better suited as quarterly threat-intel-driven hunt

**This is distinct from DROP:**
- Detection logic preserved for future activation
- Validated patterns documented
- Fast-track deployment plan ready

**Why HOLD and not RECURRING_HUNT, given S FAILed?**

The `S` FAIL → RECURRING_HUNT mapping assumes the behavior *happens* and is merely too
noisy for 24/7 alerting — so you trade coverage for cadence and run it periodically.
Here the behavior does not occur at all (0 hits). Periodic execution would have the same
zero yield as standing deployment, so there is nothing to trade. Zero prevalence
resolves an `S` FAIL to HOLD instead: preserve the logic, re-assess when threat intel
moves. Note the score (3.0) sits in the CONDITIONAL band — the `S` FAIL overrides it,
exactly as Step 4 of `SKILL.md` requires.

---

## Preserved Detection Logic

### Detection Angle 5: C2 Domain IOC Watchlist (Fast-Track)

**Pattern:** Connection to campaign C2 domains

**Deployment timeline:**
- Day 0: Threat intel triggers (campaign activity reported)
- Day 1-7: Deploy IOC watchlist (immediate value)
- Day 7-14: Deploy behavioral detection after dev tool allowlist
- Day 14-30: Expand to full 5-angle coverage

**Why preserve:** If threat landscape changes, this detection can deploy in 1 week.

---

## Activation Triggers

Deploy detections if:
1. Campaign activity reported against similar organizations
2. Associated domains observed in DNS logs
3. Peer victimization reported
4. A specific threat model requires browser-extension monitoring

**Quarterly recurring hunt:** Re-run every Q to monitor for emergence (30-day window, expand to macOS Chromium).

---

## Key Lesson

**Zero TPs is valid HOLD outcome** - not every validated detection needs immediate deployment. Preserve logic, monitor threat landscape, activate when operational need appears.
