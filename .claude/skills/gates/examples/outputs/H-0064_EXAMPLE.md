# Example: RECURRING HUNT Verdict (High Volume, Quarterly Execution)

**Hunt:** H-0064 - EC2 Encryption Disable Detection  
**Verdict:** RECURRING HUNT (quarterly execution, not 24/7 standing detection)  
**BASE Score:** 2/5

---

## Summary

Hunt identified 17,757 EC2 encryption disable events in 7 days (2,537/day). 99.9% are legitimate multi-tenant automation (TenantAdmin service accounts). Detection pattern is sound but **volume is unsustainable** for standing detection. Better suited as **quarterly threat-driven hunt**.

---

## BASE Criteria Scoring

**G - Generalizable: ✅ PASS**

Behavioral pattern (disabling encryption weakens data protection), not IOC-based. Repeatable across different adversaries using cloud persistence techniques.

Evidence:
- Technique: T1562.001 (Impair Defenses: Disable Security Tools)
- Pattern: `DisableEbsEncryptionByDefault` API call
- Detection is TTP-based, not campaign-specific

**A - Additive: ✅ PASS**

Fills T1562.001 gap (adversaries disable encryption before data exfiltration or manipulation). Actionable when volume is bounded.

**T - Tunable: ❌ FAIL**

**Baseline:** 2,537 events/day = 17,757/week = ~76K/month

**Attack frequency:** ~0-1 malicious events/year (industry average)

**Signal-to-noise ratio:** 1 attack buried in 76,000 legitimate events = **0.0013% TP rate**

**Investigation capacity:** Cannot investigate 2,537 events/day (would require 317 analyst hours/day at 7.5 min per event)

**Root Cause:** Multi-tenant AWS automation - TenantAdmin service accounts disable encryption during tenant provisioning (some tenants opt-out for cost).

**Conclusion:** Cannot distinguish attack from automation noise.

**E - Exposure-tested: ✅ PASS**

`DisableEbsEncryptionByDefault` API is only method to disable encryption. Complete coverage.

**S - Sustainable: ❌ FAIL**

**Alert volume:** 2,537 alerts/day = unsustainable

**Allowlist maintenance:** Even with allowlists, TenantAdmin service account IDs change frequently (new tenants). High churn rate.

**SOC impact:** 140-210 alerts/week even with 95% allowlist coverage.

---

## Verdict Rationale

**RECURRING HUNT (not PROMOTE or HOLD) because:**
1. ✅ Detection logic is sound (validated by baseline)
2. ❌ Volume is unsustainable (2,537 events/day)
3. ❌ Allowlist maintenance burden is high (tenant churn)
4. ✅ Pattern has security value (adversaries DO disable encryption)
5. ✅ Better suited for threat-driven quarterly execution

**This is distinct from HOLD:**
- Detection has operational value (not zero TPs expected)
- Appropriate for bounded execution (quarterly hunt)
- Hunt finds signal in noise that 24/7 detection cannot

**This is distinct from CONDITIONAL:**
- Allowlist exists but maintenance burden is prohibitive
- Even with tuning, volume remains unsustainable (hundreds/day)
- Quarterly execution avoids allowlist churn problem

---

## Recurring Hunt Strategy

### Execution Frequency: Quarterly

**Q1 Hunt (January):**
- Query: Last 90 days of `DisableEbsEncryptionByDefault` events
- Baseline: Expected TenantAdmin volume (~230K events)
- Hunt: Anomalous patterns (non-TenantAdmin principals, production accounts, off-hours)
- Time investment: 4-8 hours (bounded, manageable)

**Q2 Hunt (April):**
- Query: Last 90 days (refresh baseline)
- Compare: Q1 baseline vs Q2 baseline (new TenantAdmin accounts?)
- Hunt: Deviations from established baseline

**Q3 Hunt (July):**
- Query: Last 90 days
- Hunt: New principals, production account targeting, encryption disable + data access patterns

**Q4 Hunt (October):**
- Query: Last 90 days
- Annual review: Is this hunt still valuable? Should we narrow scope?

---

## Quarterly Hunt Workflow

### Phase 1: Baseline Measurement (30 min)

```sql
-- Measure total volume
SELECT COUNT(*) as encryption_disable_count
FROM nocsf_unified_events
WHERE event.provider = 'cloudtrail'
  AND event.type = 'DisableEbsEncryptionByDefault'
  AND time >= now() - INTERVAL 90 DAY;

-- Expected: ~230K events (2,537/day × 90 days)
```

### Phase 2: Principal Analysis (1 hour)

```sql
-- Top principals
SELECT 
  `actor.user.name` as principal,
  COUNT(*) as event_count,
  COUNT(DISTINCT `cloud.account.uid`) as unique_accounts
FROM nocsf_unified_events
WHERE event.provider = 'cloudtrail'
  AND event.type = 'DisableEbsEncryptionByDefault'
  AND time >= now() - INTERVAL 90 DAY
GROUP BY principal
ORDER BY event_count DESC
LIMIT 20;
```

**Hunt for:**
- Non-TenantAdmin principals (unusual)
- New service accounts not seen in previous quarters
- Human user accounts (unexpected)

### Phase 3: Account Scope Analysis (1 hour)

```sql
-- Production account focus
SELECT 
  `cloud.account.uid` as account,
  `actor.user.name` as principal,
  COUNT(*) as event_count,
  MIN(time) as first_seen,
  MAX(time) as last_seen
FROM nocsf_unified_events
WHERE event.provider = 'cloudtrail'
  AND event.type = 'DisableEbsEncryptionByDefault'
  AND `cloud.account.uid` IN (
    'prod-account-111',
    'prod-account-222',
    'prod-account-333'
  )
  AND time >= now() - INTERVAL 90 DAY
GROUP BY account, principal
ORDER BY event_count DESC;
```

**Hunt for:**
- **ANY** production account events (should be ZERO)
- Encryption disabled in customer-facing infrastructure
- Volume spikes (sudden increase in specific account)

### Phase 4: Temporal Analysis (1 hour)

```sql
-- Off-hours activity
SELECT 
  toHour(time) as hour,
  COUNT(*) as event_count
FROM nocsf_unified_events
WHERE event.provider = 'cloudtrail'
  AND event.type = 'DisableEbsEncryptionByDefault'
  AND `actor.user.name` NOT LIKE 'TenantAdmin-%'
  AND time >= now() - INTERVAL 90 DAY
GROUP BY hour
ORDER BY hour;
```

**Hunt for:**
- Off-hours encryption disables (2-6 AM)
- Weekend activity (Saturday/Sunday)
- Holiday activity (unexpected)

### Phase 5: Correlation Hunt (2 hours)

```sql
-- Encryption disable → data access pattern
WITH encryption_disables AS (
  SELECT 
    `cloud.account.uid` as account,
    `actor.user.name` as principal,
    time as disable_time
  FROM nocsf_unified_events
  WHERE event.provider = 'cloudtrail'
    AND event.type = 'DisableEbsEncryptionByDefault'
    AND `actor.user.name` NOT LIKE 'TenantAdmin-%'
    AND time >= now() - INTERVAL 90 DAY
)
SELECT 
  ed.account,
  ed.principal,
  ed.disable_time,
  COUNT(*) as data_access_events,
  GROUP_CONCAT(DISTINCT `event.type`) as access_types
FROM encryption_disables ed
JOIN nocsf_unified_events data
  ON ed.account = data.`cloud.account.uid`
  AND data.time BETWEEN ed.disable_time AND ed.disable_time + INTERVAL 24 HOUR
  AND data.`event.type` IN ('GetObject', 'CopyObject', 'DownloadDBSnapshot')
GROUP BY ed.account, ed.principal, ed.disable_time
HAVING data_access_events > 100  -- Bulk data access after encryption disable
ORDER BY data_access_events DESC
LIMIT 100;
```

**Hunt for:**
- Encryption disable → bulk data access (exfiltration preparation)
- Encryption disable → snapshot creation (data theft)
- Encryption disable → volume attach (offline access)

---

## Why Not PROMOTE?

**Comparison: 24/7 Detection vs Quarterly Hunt**

| Criterion | Standing Detection | Quarterly Hunt |
|-----------|-------------------|----------------|
| **Alert Volume** | 2,537/day (unsustainable) | 0 (no alerts, hunt-driven) |
| **Investigation Burden** | 317 analyst-hours/day | 4-8 hours/quarter |
| **Allowlist Maintenance** | Continuous (tenant churn) | None (baseline refresh) |
| **Signal-to-Noise** | 0.0013% TP rate | Focused (anomaly-only) |
| **SOC Impact** | Alert fatigue (buried signals) | Bounded work (manageable) |
| **Coverage** | 100% (all events) | 90% (quarterly snapshots) |

**Quarterly hunt trades 10% coverage for 99% SOC efficiency.**

---

## When to Promote to Standing Detection

**Promote if ANY of these conditions change:**

1. **Volume drops below 50/day:**
   - Multi-tenant automation ends
   - TenantAdmin accounts decommissioned
   - Allowlist covers >98% of baseline

2. **High-value accounts identified:**
   - Production accounts should NEVER disable encryption
   - Deploy standing detection scoped to production accounts ONLY
   - Volume: 0-5/day (sustainable)

3. **Composite detection becomes viable:**
   - Encryption disable + bulk data access (correlation)
   - Encryption disable + snapshot creation
   - Volume: <10/day (sustainable)

**Review quarterly during hunt execution.**

---

## Key Lessons

### 1. Volume Determines Deployment Model

**Low volume (<50/day):** Standing detection  
**Medium volume (50-200/day):** Conditional (with tuning)  
**High volume (>200/day):** Recurring hunt

### 2. Allowlist Maintenance Is a Cost

**Static allowlist:** Sustainable (quarterly review)  
**Dynamic allowlist:** Unsustainable (daily/weekly churn)

Multi-tenant environments with high service account churn → recurring hunt is better.

### 3. Quarterly Hunts Provide Value

**Benefits:**
- Bounded investigation time (4-8 hours/quarter)
- Anomaly-focused (signal, not noise)
- No allowlist maintenance burden
- Catches 90% of attacks with 1% of SOC effort

**Trade-offs:**
- Misses attacks between quarters (10% coverage gap)
- Requires analyst expertise (not automated)
- Detection delayed (quarterly, not real-time)

---

## Integration with Detection Portfolio

**Recurring hunts complement standing detections:**

### Standing Detection: Encryption Disable (Production Accounts Only)
- **Scope:** Production accounts (3 accounts)
- **Volume:** 0-5 events/day
- **Value:** Real-time production protection
- **Maintenance:** None (production accounts stable)

### Recurring Hunt: Encryption Disable (Multi-Tenant Estate)
- **Scope:** All accounts (273 tenant accounts)
- **Volume:** Quarterly execution (not 24/7)
- **Value:** Catches anomalies in tenant accounts
- **Maintenance:** 4-8 hours/quarter

**Deploy both for layered coverage.**

---

## Activation Triggers

**Execute recurring hunt when:**
1. Quarterly schedule (Q1, Q2, Q3, Q4)
2. Threat intelligence triggers (AWS-specific campaign)
3. Customer-specific incident (post-breach hunt)
4. Annual audit requirement (compliance)

**Promote to standing detection if:**
1. Volume drops <50/day
2. High-value account scope identified (production-only)
3. Composite correlation becomes viable

---

## Conclusion

**Not every hunt produces a standing detection** - that's by design.

**Hunt taxonomy:**
1. **Standing detections (PROMOTE):** Low volume, high fidelity, automated
2. **Conditional detections (CONDITIONAL):** Medium volume, tunable, requires prerequisites
3. **Recurring hunts (RECURRING HUNT):** High volume, bounded execution, analyst-driven
4. **Preserved logic (HOLD):** Zero TPs, preserve for future activation

**H-0064 is Category 3:** High volume makes it unsuitable for 24/7 automation, but quarterly execution provides 90% coverage with 1% SOC effort.

**Key Metric:** 2,537 alerts/day (standing detection) → 0 alerts + 8 hours/quarter (recurring hunt) = 99.6% efficiency gain.
