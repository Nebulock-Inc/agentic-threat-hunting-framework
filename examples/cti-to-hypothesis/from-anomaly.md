# Example: Anomaly to Hypothesis Workflow (Incident Response)

**Scenario:** SOC alerts hunter to spike in failed login attempts
**Hunter:** Using Cursor IDE with ATHR framework
**Time:** Total 6 minutes from alert to executing query (URGENT)
**Mode:** Incident Response (not routine hunting)

---

## Initial Alert

**From:** SOC Analyst
**Time:** 2024-10-31 14:23 UTC
**Priority:** HIGH
**Channel:** Slack #security-alerts

```
@threat-hunters - Need eyes on this ASAP

ALERT: Unusual Failed Login Pattern
- Source IP: 185.220.101.47
- Target: VPN gateway (vpn.company.com)
- Failed attempts: 1,247 in last 30 minutes
- Targeted accounts: 15 unique usernames
- Pattern: Password spraying (3-5 attempts per account, rotating)
- Status: ONGOING

Actions taken:
- Monitoring (not blocked yet - need confirmation first)
- No successful logins detected so far

Need threat hunt to:
1. Confirm this is malicious (not FP)
2. Check for any successful authentications we missed
3. Identify if this is part of larger campaign
4. Recommend block/monitor decision
```

---

## AI-Assisted Rapid Response Workflow

### Step 1: Rapid Context (1 min)

**User:**
```
URGENT - Incident response mode

SOC alert: 1,247 failed VPN logins from 185.220.101.47 in 30 minutes.

Quick questions:
1. Search past hunts - have we seen this IP or similar brute force before?
2. What's normal VPN failed login rate? (need baseline fast)
3. Read environment.md - what VPN logging do we have?

Keep responses brief - this is active incident.
```

**AI Response:**
```
**Past Hunts (quick search):**

H-0015 (2024-07-10): VPN brute force from different IP
- Found: Password spraying is common attack pattern
- Learned: Threshold is >100 failed attempts/hour = investigate
- FP: Occasional user lockouts (5-10 attempts)
- Your case: 1,247 in 30 min = WAY above threshold

H-0003 (2024-03-20): General brute force hunt
- Learned: Successful auth within 1 hour of failed attempts = likely compromise

**Baseline (from H-0015):**
Normal VPN failed logins: 20-50/day (typos, expired passwords)
Your alert: 1,247 in 30 min = 2,494/hour (anomalous by 50x)

**Environment (VPN Logging):**
✅ VPN logs → Splunk index=vpn_auth
✅ Retention: 90 days
✅ Fields: src_ip, username, auth_result, timestamp
✅ Also have: Firewall logs (index=firewall) for connection attempts

**Quick Assessment:**
- 🚨 This is malicious (50x normal rate)
- ⚠️ Pattern matches H-0015 (password spraying)
- ✅ Good logging coverage
- ⏱️ URGENT: Check for successful auths NOW

Recommend: Generate incident hypothesis, execute query immediately.
```

---

### Step 2: Rapid Hypothesis Generation (2 min)

**User:**
```
Generate incident-response hypothesis for this. Mark HIGH priority.

Make it focused - I need to execute query in next 5 minutes.

Include:
- Quick hypothesis
- Immediate query to check for successful logins
- Actions to take if we find compromise

Skip: Long context, detailed analysis (do that later)
```

**AI Response:**
```
# H-0028 | VPN Brute Force from 185.220.101.47 (ACTIVE INCIDENT)

**Status:** In Progress
**Priority:** 🚨 CRITICAL (Active Attack)
**Mode:** Incident Response

## Hypothesis (Quick)

Adversary conducting automated password spraying attack against VPN from 185.220.101.47
to gain initial access. Rotating through 15 user accounts to avoid lockout detection.

**ATT&CK:** T1110.003 (Brute Force: Password Spraying)
**Tactic:** Initial Access

## IMMEDIATE ACTIONS (Execute Now)

### Query 1: Check for Successful Logins (CRITICAL)
```spl
index=vpn_auth src_ip="185.220.101.47"
earliest=-2h latest=now
| stats count by username, auth_result
| where auth_result="success"
```
**Run this FIRST** - if any successes, escalate immediately to IR team.

### Query 2: Identify All Targeted Accounts
```spl
index=vpn_auth src_ip="185.220.101.47" auth_result="failed"
earliest=-2h latest=now
| stats count by username
| sort - count
```
**Purpose:** Get list of targeted usernames for forced password resets.

### Query 3: Check if Attack is Distributed
```spl
index=vpn_auth auth_result="failed"
earliest=-2h latest=now
| search username IN (user1, user2, user3, ...)  // Insert from Query 2
| stats dc(src_ip) as unique_ips, count by username
| where unique_ips > 1
```
**Purpose:** Is this one IP or coordinated attack from multiple sources?

### Query 4: Timeline - When Did This Start?
```spl
index=vpn_auth src_ip="185.220.101.47"
earliest=-24h latest=now
| bin _time span=5m
| stats count by _time, auth_result
| sort _time
```
**Purpose:** Understand attack duration and pattern.

## Decision Tree

**IF Query 1 finds successful logins:**
1. 🚨 **IMMEDIATE:** Disable compromised accounts
2. 🚨 **IMMEDIATE:** Block 185.220.101.47 at firewall
3. 🚨 **IMMEDIATE:** Check for lateral movement from compromised account
4. 🚨 **ESCALATE:** Page incident response team
5. Hunt for: What did attacker do after successful login?

**IF Query 1 finds NO successful logins:**
1. ✅ Block 185.220.101.47 at firewall (proactive)
2. ⚠️ Force password resets for targeted accounts (from Query 2)
3. ⚠️ Alert targeted users (phishing attempt likely)
4. 📊 Monitor for attack resumption from different IP
5. Document as attempted compromise (no impact)

**IF Query 3 shows distributed attack (multiple IPs):**
1. 🚨 This is coordinated campaign (more sophisticated)
2. 🚨 Check for successful logins from ALL attacking IPs
3. 🚨 Consider blocking entire IP ranges (ASN-based)
4. 📊 Escalate to ISP/upstream for potential botnet
5. Hunt for: Are other services being targeted? (SSH, RDP, etc.)

## Quick Threat Intel Check

**IP Reputation Check (do this while queries run):**
```
https://www.virustotal.com/gui/ip-address/185.220.101.47
https://www.abuseipdb.com/check/185.220.101.47
```

If IP is known malicious:
- Confirms this is attack (not FP)
- May provide IOCs (related IPs, malware families)
- Can inform blocking decision

## What to Document (After Immediate Response)

Create full execution report later (H-0028_2024-10-31.md) with:
- Timeline of attack
- All targeted usernames
- Any successful authentications
- Actions taken (blocks, resets, escalations)
- Lessons learned

**For now:** Take screenshot of query results, note timestamps.

## Next Steps (After Queries Execute)

**5 minutes from now:**
1. You'll have query results
2. Follow decision tree above
3. Make block/escalate decision
4. Notify SOC of actions taken

**30 minutes from now:**
5. Document incident in H-0028_2024-10-31.md
6. Update vulnerabilities or threats tracking
7. Debrief with SOC on response

**Tomorrow:**
8. Check for attack resumption (different IP)
9. Review VPN logs for related activity
10. Consider adding automated detection rule

---

**Created:** 2024-10-31 14:25 UTC
**Incident Start:** 2024-10-31 13:53 UTC (30 min ago)
**Response Time:** 2 minutes (alert → hypothesis → queries ready)
**Status:** Queries ready to execute - GO!
```

---

### Step 3: Execute and Document (Concurrent - 3 min)

**User:**
```
Running Query 1 now... results:

[pastes results showing 0 successful logins]

No successful authentications found. But Query 3 shows this same username list
is being attacked from 3 other IPs in the last hour:
- 185.220.101.47 (original)
- 198.51.100.23
- 203.0.113.89

This looks coordinated. What do I do?
```

**AI Response:**
```
**Good news:** No successful compromise (yet).
**Bad news:** Coordinated attack from 3+ IPs = sophisticated threat actor.

**IMMEDIATE ACTIONS (Next 5 minutes):**

1. **Block all 3 IPs at firewall NOW:**
   ```
   185.220.101.47
   198.51.100.23
   203.0.113.89
   ```

2. **Find if there are more attacking IPs:**
   Quick query:
   ```spl
   index=vpn_auth auth_result="failed"
   earliest=-1h latest=now
   | where username IN ([list from Query 2])
   | stats count by src_ip
   | where count > 50
   | sort - count
   ```

3. **Force password resets for all 15 targeted accounts:**
   - Send password reset emails NOW
   - Explain: "Your account was targeted in brute force attack"
   - Enable MFA if not already required

4. **Alert SOC:**
   Update Slack with:
   - No successful logins confirmed
   - Distributed attack detected (3+ IPs)
   - Blocking IPs and forcing resets
   - Monitoring for additional IPs

**OPTIONAL (if you have 5 more minutes):**

5. **Check other authentication services:**
   Are they targeting SSH, RDP, O365 too?
   ```spl
   index=* (src_ip="185.220.101.47" OR src_ip="198.51.100.23" OR src_ip="203.0.113.89")
   earliest=-1h
   | stats count by index, src_ip, dest_port
   ```

**Documentation (do this after immediate actions):**

I'll help you create the incident report. Paste your final results and I'll
format into H-0028_2024-10-31.md following LOCK pattern.

**Status Update for SOC:**
```
INCIDENT UPDATE - VPN Brute Force

Status: CONTAINED (no successful logins)
Threat Level: HIGH (coordinated, 3+ IPs)

Actions Taken:
✅ Blocked 185.220.101.47, 198.51.100.23, 203.0.113.89
✅ Forced resets for 15 targeted accounts
✅ Alerted affected users
🔄 Monitoring for additional attacking IPs (ongoing)

Recommendation:
- Continue monitoring VPN logs for 24 hours
- Consider temp MFA requirement for targeted accounts
- Review VPN lockout policies (may need adjustment)

Next Hunt: Investigate if this is precursor to larger campaign
```

**Time Check:**
- Alert received: 14:23
- Hypothesis generated: 14:25 (2 min)
- Query executed: 14:27 (2 min)
- Actions taken: 14:30 (3 min)
- **Total Response Time: 7 minutes** ✅

Well done - fast response prevented compromise.
```

**User:**
```
Blocked all IPs, forced resets sent. Found 2 more attacking IPs with your query.
Blocking those too (5 total now).

Can you document this incident now? I need to send report to SOC lead.
```

---

### Step 4: Rapid Documentation (Concurrent during monitoring)

**AI Response:**
```
Creating incident documentation now...

**File Created: hunts/H-0028_2024-10-31.md**

---

# H-0028 | VPN Password Spraying Incident | 2024-10-31

**Status:** Resolved (No Compromise)
**Priority:** HIGH
**Mode:** Incident Response
**Response Time:** 7 minutes (alert to containment)

## Incident Summary

**What Happened:**
Coordinated password spraying attack against VPN gateway from 5+ attacking IPs.
1,247 failed authentication attempts across 15 user accounts in 30 minutes.
No successful authentications. Attack contained via IP blocks and forced password resets.

**Timeline:**
- **13:53 UTC:** Attack begins (185.220.101.47)
- **14:20 UTC:** Additional IPs join (distributed attack)
- **14:23 UTC:** SOC detects anomaly, alerts threat hunting
- **14:25 UTC:** Hypothesis generated, queries prepared
- **14:27 UTC:** Queries executed, no compromise confirmed
- **14:30 UTC:** All attacking IPs blocked, password resets initiated
- **14:35 UTC:** Attack ceases (IPs blocked successfully)

**Duration:** 42 minutes (attack duration), 7 minutes (response time)

## Hypothesis

Adversaries conducted coordinated password spraying attack against corporate VPN
from multiple IPs (botnet or compromised infrastructure) to gain initial access
via credential compromise.

**ATT&CK:** T1110.003 (Brute Force: Password Spraying)

## Data Sources Used

**Primary:**
- VPN Authentication Logs (index=vpn_auth)
- Firewall Connection Logs (index=firewall)

**Query Runtime:** < 30 seconds per query
**Total Logs Analyzed:** ~50,000 VPN auth events (last 24 hours)

## Findings

### Attack Characteristics

**Attacking IPs:** 5 confirmed
```
185.220.101.47 (primary, 1,247 attempts)
198.51.100.23 (542 attempts)
203.0.113.89 (389 attempts)
192.0.2.15 (156 attempts)
198.51.100.87 (98 attempts)
Total: 2,432 failed attempts
```

**Targeted Accounts:** 15 users
```
[list of usernames - redacted from example]
Pattern: Mix of IT staff, executives, and service accounts
```

**Attack Pattern:**
- Password spraying (3-5 attempts per account to avoid lockout)
- Rotating through account list
- Distributed across 5+ IPs (coordinated)
- Using common/breached passwords (assumption based on pattern)

**Sophistication:** Medium
- Distributed attack (not single source)
- Stayed under lockout threshold (aware of defenses)
- But: No evasion tactics, easily detected, generic passwords

### Threat Intelligence

**IP Reputation (checked during incident):**
- 185.220.101.47: Known malicious (AbuseIPDB confidence: 95%)
  - Previous: SSH brute force, spam
  - ASN: AS64496 (hosting provider, commonly abused)
- Other IPs: Mix of known-bad and residential ISPs (likely botnet)

**Attribution:** Likely opportunistic botnet, not targeted APT

## Analysis

### True Positives: 1 (the incident itself)

**Confirmed Malicious Activity:**
✅ 2,432 failed VPN auth attempts in 42 minutes
✅ From 5+ distributed IPs
✅ All IPs have malicious reputation
✅ Password spraying pattern (clear attack behavior)

**No Compromise Confirmed:**
✅ Zero successful authentications from attacking IPs
✅ Targeted accounts showed no suspicious activity after failed attempts
✅ No lateral movement indicators
✅ No data exfiltration detected

### False Positives: 0

No legitimate activity was flagged. Clear malicious behavior.

**FP Rate:** 0% (incident response - investigating known anomaly)

### Coverage Gaps

**What We Couldn't Detect:**
- Initial reconnaissance (how did attackers get username list?)
- Possible phishing campaign preceding this (credential harvest)
- Whether attackers tried other attack vectors (SSH, RDP, O365)

**Recommendation:** Follow-up hunts for:
1. Email phishing targeting these same 15 users (last 7 days)
2. SSH/RDP brute force from same IPs (cross-service attacks)
3. Account enumeration activity (how they built username list)

## Decision

**ACCEPT - Incident Contained**

**Rationale:**
- No successful compromise occurred
- Attack stopped via IP blocks
- Targeted accounts secured via forced password resets
- Monitoring in place for attack resumption

**Confidence:** High (100% based on log analysis)

## Actions Taken

### Immediate (During Incident):
1. ✅ Blocked 5 attacking IPs at firewall (effective immediately)
2. ✅ Forced password resets for 15 targeted accounts (emails sent 14:31 UTC)
3. ✅ Alerted targeted users of attack (security awareness)
4. ✅ Monitored for additional attacking IPs (found 2 more, blocked)

### Short-Term (Next 24 Hours):
5. 🔄 Monitor VPN logs for attack resumption
6. 🔄 Verify all users completed password resets
7. 🔄 Check for related activity on other services (SSH, RDP, O365)
8. 📋 Update threat intel feeds with attacking IPs

### Long-Term (Next Week):
9. 📋 Review VPN account lockout policies (consider lowering threshold)
10. 📋 Implement rate-limiting on VPN authentication (if not already present)
11. 📋 Consider IP geolocation blocking (if operationally feasible)
12. 📋 Deploy automated detection rule for similar attacks

## Lessons Learned

### What Worked Well:
✅ **Fast Detection:** SOC caught anomaly within 30 min of attack start
✅ **Quick Response:** 7 minutes from alert to containment (excellent)
✅ **Past Hunt Value:** H-0015 provided baseline and false positive guidance
✅ **Good Logging:** VPN logs had all needed data (src_ip, username, result, timestamp)
✅ **AI Assist:** Rapid hypothesis generation and query creation (2 min vs 15+ min manual)

### What Could Improve:
⚠️ **Delayed Detection:** Attack ran 30 min before SOC noticed
  - Fix: Deploy automated detection rule (>100 failed logins/hour = alert)

⚠️ **Username List:** Unknown how attackers obtained our usernames
  - Fix: Hunt for reconnaissance/enumeration activity (follow-up H-0029)

⚠️ **No MFA Required:** VPN doesn't enforce MFA for all accounts
  - Fix: Recommend MFA requirement policy update

⚠️ **Manual Blocking:** Had to manually block each IP
  - Fix: Consider automated blocking for high-confidence threats

### Recommendations:

**Immediate:**
1. Deploy detection rule: Alert on >100 VPN failed auths/hour from single IP
2. Deploy detection rule: Alert on distributed attacks (same usernames, multiple IPs)

**Short-Term:**
3. Require MFA for VPN access (no exceptions)
4. Implement rate-limiting on VPN auth endpoint

**Long-Term:**
5. Deploy deception accounts (honeypot usernames to detect enumeration)
6. Integrate with threat intel feeds for automatic IP blocking
7. Build playbook for this incident type (reusable response)

## Follow-Up Hunts

**Planned:**

**H-0029:** How did attackers get username list?
- Search for: Account enumeration, LDAP queries, email harvesting
- Timeline: Last 30 days
- Priority: Medium

**H-0030:** Were other services targeted?
- Search for: SSH, RDP, O365 brute force from same IPs
- Timeline: Last 7 days
- Priority: High

**H-0031:** Proactive distributed attack detection
- Build: Automated detection for coordinated attacks
- Test: Against last 90 days of VPN logs
- Priority: Medium

## Metrics

**Attack Metrics:**
- Total Failed Attempts: 2,432
- Attacking IPs: 5
- Targeted Accounts: 15
- Attack Duration: 42 minutes
- Successful Compromises: 0

**Response Metrics:**
- Detection Time: 30 minutes (from attack start)
- Analysis Time: 4 minutes (hypothesis + queries)
- Containment Time: 3 minutes (blocks + resets)
- Total Response Time: 7 minutes (alert to containment)

**Outcome:**
✅ Incident contained with zero impact
✅ No data compromise
✅ No system compromise
✅ No business disruption

---

**Incident Lead:** [Your Name]
**Reviewed By:** SOC Lead
**Status:** Closed
**Impact:** None (attack blocked before compromise)
```

**Ready to send to SOC lead. Also created queries in `queries/H-0028_*.spl` for future reference.**

---

## Results Summary

**Total Time:** 6 minutes (alert to executing queries + containment)
**Documentation Time:** +3 minutes (full incident report)

**What AI Provided:**
- Instant baseline comparison (H-0015 reference)
- Rapid hypothesis generation (2 min)
- Ready-to-execute queries (immediate action)
- Decision tree (IF successful logins THEN escalate)
- Structured incident documentation (LOCK format)

**What Human Provided:**
- Initial alert recognition
- Query execution and interpretation
- Blocking decisions (5 IPs)
- Forced password resets
- Tactical responses (finding additional IPs)

**Outcome:**
- ✅ Zero successful compromises
- ✅ 7-minute response time (excellent)
- ✅ Full documentation in LOCK format
- ✅ Lessons learned captured
- ✅ Follow-up hunts identified

---

## Key Takeaways

**Incident Response is Different:**
- **Speed over perfection** - Get queries running fast
- **Document as you go** - Don't wait until after to write report
- **Decision trees** - Have clear IF/THEN actions ready
- **Past hunts critical** - H-0015 baseline saved time

**AI Excels At:**
- Rapid hypothesis generation under pressure
- Remembering past hunts automatically
- Generating queries with safety bounds quickly
- Structuring incident reports (LOCK format)
- Providing decision frameworks

**Human Judgment Essential For:**
- Real-time tactical decisions (block? wait? escalate?)
- Interpreting results (is this normal?)
- Risk assessment (how serious is this?)
- Coordinating response (SOC, users, IR team)

**Process Improvements:**
1. **Pre-build incident templates** - Common scenarios (brute force, phishing, malware)
2. **Automated detection** - Don't rely on manual SOC monitoring (deploy rules)
3. **Runbooks** - Codify this response for future incidents
4. **Continuous learning** - H-0028 lessons inform H-0029+ hunts

**Time Comparison:**
- **Without AI:** 20-30 min (manual query writing, documentation)
- **With AI:** 6-9 min (rapid generation + validation)
- **Savings:** 70-80% time reduction in incident response

**Critical Success Factor:**
Having AGENTS.md and past hunts (H-0015) meant AI could instantly:
- Provide baseline (normal vs. anomalous)
- Generate appropriate queries
- Reference past lessons
- Structure documentation

**This is Level 2 (Augmented) in action for incident response.**
