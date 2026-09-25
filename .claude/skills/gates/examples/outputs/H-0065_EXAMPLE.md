# Example: TIME_BOX Verdict (Campaign-Specific IOC Detection)

**Hunt:** H-0065 - ClickFix C2 Infrastructure Detection  
**Verdict:** TIME_BOX (90-day campaign tracking)  
**BASE Score:** 2.0

---

## Summary

Hunt identified ClickFix campaign C2 domains from threat intelligence. Detection logic is IOC-based (domain watchlist), not behavioral. Appropriate for **time-boxed campaign tracking** with 90-day refresh cycle.

---

## BASE Criteria Scoring

**G - Generalizable: ❌ FAIL**

IOC-based detection (domain watchlist), not behavioral pattern. Expires when campaign ends or adversary rotates infrastructure (typically 30-90 days).

Evidence:
- Detection: `destination.network_endpoint.domain` IN (list of C2 domains)
- IOC type: Domains (bottom of Pyramid of Pain)
- Lifespan: Campaign-specific (ClickFix actors rotate domains monthly)

**A - Additive: ✅ PASS**

Fills T1071.001 (C2: Web Protocols) gap during active campaign. Actionable when IOCs are fresh.

Coverage gap confirmed:
- No behavioral detection for ClickFix clipboard abuse
- IOC watchlist provides immediate value during campaign window
- Complements behavioral Detection 2 (Remote msiexec)

**T - Tunable: ✅ PASS**

Zero FPs expected (malicious C2 domains, not CDNs). Volume depends on campaign targeting.

**E - Exposure-tested: ❌ FAIL**

Single-dimensional (domain match only). Adversary bypasses by:
- Domain rotation (new domains not in watchlist)
- Alternative C2 channels (DNS tunneling, HTTPS)
- IP-based C2 (no domain resolution)

**S - Sustainable: ❌ FAIL**

High maintenance burden:
- IOCs expire in 30-90 days (domain rotation)
- Requires quarterly threat intel refresh
- No long-term value after campaign ends

---

## Verdict Rationale

**TIME_BOX (not PROMOTE) because:**
1. ❌ IOC-based = not generalizable (expires when campaign ends)
2. ❌ Single-dimensional = adversary easily evades (domain rotation)
3. ❌ High maintenance = quarterly IOC refresh required
4. ✅ Immediate value = catches campaign activity while IOCs are fresh
5. ✅ Fast deployment = IOC watchlist deployed in hours, not weeks

**This is distinct from HOLD:**
- Detection has immediate value (not zero TPs)
- Appropriate for campaign tracking (not long-term detection)
- Expires naturally after 90 days (not preserved indefinitely)

---

## Deployment Guidance

### Time-Boxed Deployment (90 Days)

**Activation Date:** 2026-09-20 (ClickFix campaign reported)  
**Expiration Date:** 2026-12-20 (90 days)  
**Review Date:** 2026-12-15 (assess campaign status)

**IOC Watchlist (Domains):**

> ⚠️ **These are illustrative placeholders, written defanged (`[.]`).** Do not paste
> this block into a rule. Defanged strings match nothing — a watchlist deployed with
> `[.]` intact silently never fires, which looks identical to "no activity observed."
> Replace the placeholders with the real domains from your threat intel, convert
> `[.]` → `.`, and confirm the rule fires against a known-good test event before
> trusting its silence.

```yaml
c2_domains:
  # placeholders — substitute real IOCs, un-defanged, before deploying
  - "example-lure-cdn[.]invalid"
  - "example-fake-update[.]invalid"
  - "example-patch-portal[.]invalid"
  - "example-auth-verify[.]invalid"
```

**Refresh Triggers:**
1. New ClickFix domains identified (threat intel update)
2. Campaign ends (all domains sinkholed/dead)
3. 90 days elapse (mandatory review)

---

## IOC Refresh Cycle

### Week 0-4: Active Deployment
- Deploy IOC watchlist to production
- Alert on any domain match (severity: high)
- Daily threat intel monitoring (new domains)

### Week 5-8: Campaign Monitoring
- Update watchlist with new domains (if campaign evolves)
- Track hit rate (are IOCs still active?)
- Coordinate with threat intel team

### Week 9-12: Review and Deactivate
- **Review:** Is campaign still active?
  - **YES:** Extend 90 days, refresh IOCs
  - **NO:** Deactivate detection, archive IOCs

---

## Why Not PROMOTE?

**Comparison: IOC Detection vs Behavioral Detection**

| Criterion | IOC (TIME_BOX) | Behavioral (PROMOTE) |
|-----------|----------------|----------------------|
| **Generalizable** | ❌ NO (campaign-specific) | ✅ YES (repeatable TTP) |
| **Evasion Resistance** | ❌ LOW (domain rotation) | ✅ HIGH (behavior-based) |
| **Maintenance** | ❌ HIGH (quarterly refresh) | ✅ LOW (static logic) |
| **Lifespan** | 90 days | Years |
| **Detection Speed** | Hours (IOC deploy) | Weeks (tuning) |

**IOC detections are appropriate for:**
- Campaign-specific tracking (ClickFix, APT29 infra)
- Immediate threat response (zero-day exploitation)
- Threat intel operationalization (STIX feeds)

**Behavioral detections are appropriate for:**
- Long-term coverage (T1071.001, T1204.001)
- Evasion-resistant patterns (process lineage, command chains)
- Low-maintenance detections (years of value)

---

## Integration with Behavioral Detections

**TIME_BOX IOC detections complement PROMOTE behavioral detections:**

### Detection 1 (TIME_BOX): ClickFix C2 Domain Watchlist
- **Pattern:** Connection to known ClickFix C2 domains
- **Lifespan:** 90 days (campaign-specific)
- **Value:** Immediate hits during campaign window
- **Maintenance:** Quarterly IOC refresh

### Detection 2 (PROMOTE): Remote Package Installer Execution
- **Pattern:** msiexec.exe with `/i http` (behavioral)
- **Lifespan:** Years (repeatable TTP)
- **Value:** Catches ClickFix + future campaigns using same TTP
- **Maintenance:** None (static logic)

**Best practice:** Deploy both
- IOC watchlist provides immediate campaign coverage
- Behavioral detection provides long-term TTP coverage
- IOC expires after 90 days, behavioral detection remains

---

## Activation Triggers

**Deploy TIME_BOX detection when:**
1. Active campaign reported (threat intel)
2. High-confidence IOCs available (domains, IPs, hashes)
3. Campaign targets your customer base
4. Behavioral detection doesn't exist yet (gap fill)

**Deactivate TIME_BOX detection when:**
1. 90 days elapse (mandatory review)
2. Campaign ends (all IOCs dead/sinkholed)
3. Zero hits for 30 days (IOCs expired)
4. Behavioral detection deployed (replaces IOC watchlist)

---

## Key Lesson

**IOC detections have value, but limited lifespan** - they're campaign-specific tools, not standing detections. TIME_BOX verdict acknowledges this: deploy for 90 days, review, extend or deactivate.

**Don't confuse TIME_BOX with HOLD:**
- **TIME_BOX:** Deploy now, expires in 90 days (campaign tracking)
- **HOLD:** Don't deploy now, preserve for future (zero TPs observed)
