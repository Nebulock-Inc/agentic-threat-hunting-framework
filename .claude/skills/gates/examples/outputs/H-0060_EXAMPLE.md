# Example: HOLD Verdict (Zero TPs, Preserve Detection Logic)

**Hunt:** H-0060 - EDGECUTION Browser Extension Installer Technique  
**Verdict:** HOLD (no operational need, preserve for threat-intel activation)  
**BASE Score:** 2/5

---

## Summary

Hunt validated detection logic via emulation but found 0 true positives across ~8 billion Windows events (enterprise environment, 7 days). Detection pattern is sound but zero prevalence = no operational need. Preserve as quarterly threat-intel-driven hunt.

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
- Technique documented in UNC6692 campaigns
- Fleet has zero observed activity = no urgency

**T - Tunable: ❌ UNKNOWN**

No execution results to validate FP rate. Dev-heavy fleet has legitimate headless Chrome use (Puppeteer, Playwright). Unknown FP risk without real TPs to justify tuning effort.

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
2. ❌ Zero prevalence = no operational need (0 hits / ~8B events)
3. ❌ Unknown FP rate in dev-heavy environment
4. ❌ Cannot justify investigation burden with zero expected yield
5. ✅ Better suited as quarterly threat-intel-driven hunt

**This is distinct from DROP:**
- Detection logic preserved for future activation
- Validated patterns documented
- Fast-track deployment plan ready

---

## Preserved Detection Logic

### Detection Angle 5: C2 Domain IOC Watchlist (Fast-Track)

**Pattern:** Connection to known EDGECUTION C2 domains

**Deployment timeline:**
- Day 0: Threat intel triggers (UNC6692 activity reported)
- Day 1-7: Deploy IOC watchlist (immediate value)
- Day 7-14: Deploy behavioral detection after dev tool allowlist
- Day 14-30: Expand to full 5-angle coverage

**Why preserve:** If threat landscape changes, this detection can deploy in 1 week.

---

## Activation Triggers

Deploy detections if:
1. UNC6692 activity reported against similar organizations
2. ClickFix domains observed in DNS logs
3. Peer victimization reported
4. Customer-specific threat model requires EDGECUTION monitoring

**Quarterly recurring hunt:** Re-run every Q to monitor for emergence (30-day window, expand to macOS Chromium).

---

## Key Lesson

**Zero TPs is valid HOLD outcome** - not every validated detection needs immediate deployment. Preserve logic, monitor threat landscape, activate when operational need appears.
