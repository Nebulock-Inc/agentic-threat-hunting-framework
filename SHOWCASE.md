# ATHF Hunt Showcase

Real hunts from our [hunts/](athf/data/hunts/) directory demonstrating how the LOCK pattern structures threat hunting from hypothesis to detection.

## 🆕 New in v0.3.0: AI-Powered Hunt Capabilities

- **Research Agent:** `athf research new --topic "LSASS dumping"` - 5-skill research (15-20 min) using web search + LLM
- **Hypothesis Generator:** `athf agent run hypothesis-generator --threat-intel "..."` - AI-generated hunt hypotheses

---

## Hunt #1: macOS Information Stealer Detection

**[View full hunt: H-0001.md →](athf/data/hunts/H-0001.md)**

**Hunt ID:** H-0001 | **ATT&CK:** T1005, T1059.002 | **Platform:** macOS | **Status:** ✅ Completed

### Learn

**Context:** Atomic Stealer actively targeting macOS following phishing campaign. Need visibility into file access patterns.

**Threat Actor TTPs:** AppleScript-based collection of Safari cookies, Notes database, documents.

**Knowledge Gap:** No visibility into unsigned process file access patterns.

### Observe

**Hypothesis:** Malicious processes will access browser databases and document directories in unusual patterns, especially unsigned executables.

**Observable Behaviors:**
- Unsigned processes accessing browser data
- Rapid file access (< 5 minutes) spanning multiple sensitive directories
- Network connection attempts from file collection processes

### Check

**Query Evolution:**

**Iteration 1: Broad file access** (247 events - too noisy)
```spl
index=mac_edr
| where file_path LIKE "%Library/Safari%" OR file_path LIKE "%Chrome%"
```
**Problem:** Can't distinguish legitimate from malicious

**Iteration 2: Unsigned processes** (12 events - better)
```spl
index=mac_edr process_signature_status=invalid OR unsigned
| where file_path LIKE sensitive paths AND unique_files > 5
```
**Problem:** False positives from development tools

**Iteration 3: Signature + behavior + timing** (1 TP, 0 FP - success!)
```spl
index=mac_edr process_signature_status!=valid
| where (file_path LIKE sensitive paths)
| stats earliest/latest, unique_files, accessed_files by process
| where unique_files > 3 AND timespan < 300
| lookup threat_intel_hashes
```

### Results

**Detection Timeline:**
- 14:23:18 - Initial detection: unsigned process accessing Safari cookies
- 14:24:15 - EDR blocks network connection
- 14:24:30 - Host auto-isolated
- 14:26:12 - Analyst confirms Atomic Stealer

**Finding:** `SystemHelper` (masquerading), accessed 47 files in 2.5 minutes, attempted C2 connection to `185.220.101.47:443` (blocked).

### Keep

**Confirmed:**
- ✅ Information stealers actively targeting macOS
- ✅ Process signature validation critical
- ✅ Rapid file access (< 5 min) indicates automated collection
- ✅ Multi-factor analysis (file + signature + timing) = near-zero FPs

**Impact:**
- **Detection:** 2 minutes | **Containment:** 4 minutes
- **Results:** 1 TP, 0 FP (down from 247 in iteration 1)
- **Prevented:** 47 documents + browser credentials exfiltrated

**Lessons:**
- Process signature validation essential for macOS
- EDR integration enables sub-5-minute containment
- Combining multiple signals minimizes false positives

**Next Steps:** Extend to Firefox/Brave/Edge, add Keychain detection, create runbook, deploy to remaining 15% of fleet

---

## Hunt #2: Linux Crontab Persistence Detection

**[View full hunt: H-0002.md →](athf/data/hunts/H-0002.md)**

**Hunt ID:** H-0002 | **ATT&CK:** T1053.003 | **Platform:** Linux | **Status:** ✅ Completed

### Learn

**Context:** Q3 2024 cryptomining incident identified cron persistence as coverage gap. APT28, Rocke, TeamTNT actively using cron.

**Threat Actor TTPs:** Unusual schedules, network utilities in commands, base64 encoding, execution from /tmp.

**Knowledge Gap:** No baseline of legitimate cron jobs; 80% production coverage.

### Observe

**Hypothesis:** Adversaries modify crontab files to schedule malicious commands at system startup or defined intervals.

**Observable Behaviors:**
- Crontab modifications outside maintenance windows
- Suspicious patterns (curl, wget, bash -c, base64, /tmp)
- Modifications by non-root users
- New cron files in /etc/cron.d/ with suspicious ownership

### Check

**Query Evolution:**

**Iteration 1: File modification only** (89 events - too broad)
**Problem:** High noise from legitimate automation

**Iteration 2: Pattern matching** (5 events - better)
**Problem:** False positives from backup scripts

**Iteration 3: Behavioral + baseline** (1 TP, 1 FP - success!)
```bash
index=linux sourcetype=auditd earliest=-1h
file_path IN crontab locations, action IN modified/created
| join with cron commands, eval is_suspicious
| where (user!="root" OR is_suspicious="true")
| lookup cron_baseline
```

### Results

**Detection:** User "webadmin" modified crontab with curl to 104.xxx.xxx.23 every 5 minutes. Downloaded cryptominer, matched known campaign (TI-0089).

**False Positive:** Database backup script using curl to S3 (whitelisted).

### Keep

**Confirmed:**
- ✅ Cron persistence actively used
- ✅ Auditd FIM provides real-time visibility
- ✅ Multi-context analysis (file + command + network) reduces FPs
- ✅ Pattern matching on suspicious commands effective

**Impact:**
- **Detection:** 30 minutes | **Containment:** 4.5 hours
- **Results:** 1 TP, 1 FP (easily whitelisted)
- **Prevented:** ~$200/month cloud compute costs
- **Coverage Gap:** Identified 20% gap in dev/staging

**Lessons:**
- Baseline of legitimate cron jobs critical for noise reduction
- User-based filtering (excluding root) significantly reduced FPs
- Threat intel integration confirmed campaign match

**Next Steps:** Deploy auditd to dev/staging, enable bash history logging, implement automated cron inventory

---

## Hunt #3: AWS Lambda Persistence Detection

**[View full hunt: H-0003.md →](athf/data/hunts/H-0003.md)**

**Hunt ID:** H-0003 | **ATT&CK:** T1546.004, T1098 | **Platform:** AWS | **Status:** ✅ Completed

### Learn

**Context:** Compromised service account incident + APT intelligence showing serverless persistence over traditional EC2 backdoors.

**Threat Actor TTPs:** Lambda functions with admin IAM roles, API Gateway backdoors, EventBridge scheduled execution, function name masquerading.

**Knowledge Gap:** No baseline of legitimate Lambda deployment patterns.

### Observe

**Hypothesis:** Attackers create Lambda functions with overly permissive IAM roles, scheduled triggers, or API Gateway integrations for persistent backdoor access.

**Observable Behaviors:**
- Lambda creation events
- IAM role attachment with AdministratorAccess/PowerUserAccess
- API Gateway endpoint creation linked to new functions
- EventBridge rules targeting Lambda
- Activity from compromised service accounts
- Unexpected geolocations (residential ISPs, VPNs)
- Rapid succession of Lambda + IAM + trigger events (< 1 hour)

### Check

**Query Evolution:**

**Iteration 1: All Lambda creations** (89 events/24h - too noisy)
**Problem:** Can't differentiate malicious from DevOps activity

**Iteration 2: Suspicious IAM policies** (8 events - better)
**Problem:** Need to filter known automation accounts

**Iteration 3: Anomaly + permissions + trigger analysis** (2 TP, 0 FP - success!)
```spl
index=aws_cloudtrail (Lambda creation OR function update OR event mapping)
| join lambda_role with AttachRolePolicy (admin policies)
| join function_name with triggers (API Gateway OR EventBridge)
| where NOT in known_automation_accounts
| where time_since_creation < 3600
```

### Results

**Detection Timeline:** 3 minutes from Lambda creation to alert

**Finding #1:** `sys-health-check-v2` (masquerading)
- Admin IAM role + API Gateway (publicly accessible)
- Source IP: residential proxy, CLI from unexpected location
- Code: Base64 reverse shell + env variable exfiltration

**Finding #2:** `cloudwatch-logs-processor`
- ReadOnlyAccess + iam:ListUsers, EventBridge (every 6 hours)
- Purpose: Automated reconnaissance

### Keep

**Confirmed:**
- ✅ Lambda persistence actively used for cloud backdoors
- ✅ IAM role analysis (AdministratorAccess) critical
- ✅ Multi-event correlation (Lambda + IAM + triggers) identifies complete attack chain
- ✅ Temporal analysis (< 1 hour) strong indicator
- ✅ Known automation whitelisting eliminates 87% of FPs

**Impact:**
- **Detection:** 3 minutes | **Containment:** 20 minutes
- **Results:** 2 TP, 0 FP after whitelist
- **Prevented:** Full AWS account compromise (AdministratorAccess available)
- **Cost:** $0.47 in Lambda execution (attacker testing)

**Lessons:**
- Lambda persistence is subtle - functions can remain dormant for weeks
- API Gateway + Lambda = public backdoor if not restricted
- Service account compromise remains primary initial access vector
- SCPs prevent privilege escalation via Lambda IAM roles

**Telemetry Gaps:** No automated Lambda code scanning, execution logs not centralized, API Gateway access logs not enabled

**Next Steps:** Deploy Lambda code scanning, enable API Gateway logging, centralize execution logs, enforce MFA for service accounts

---

## Key Takeaways Across All Hunts

### What Made These Hunts Successful

1. **Iterative Refinement:** Each hunt evolved through 3+ query iterations
2. **Behavioral Focus:** Moved beyond signatures to behavior patterns
3. **Contextual Filtering:** Used whitelists, baselines, and threat intel
4. **Automation-Ready:** Final queries deployed as detection rules
5. **Documented Learning:** Lessons captured for future hunts

### Common Patterns

- **First query:** Always too broad (100+ results)
- **Second query:** Better filtering but still noisy (10-20 results)
- **Final query:** High-confidence detection (0-5 results, minimal FPs)
- **Time to refine:** 2-4 hours per hunt on average

### Framework Benefits Demonstrated

✅ **Memory:** Past hunts informed query evolution
✅ **Iteration:** LOCK pattern structured refinement
✅ **Metrics:** Clear ROI with time saved and FP reduction
✅ **Automation:** Hunts became detection rules
✅ **Knowledge Transfer:** Future analysts learn from documented hunts

---

## Try These Hunts in Your Environment

All hunt templates and queries are available in `hunts/` and `queries/` directories. Adapt to your data sources (Splunk, Sentinel, Elastic, Chronicle) and environment.

**Start with:**
1. Review hunt documentation
2. Understand the LOCK pattern used
3. Modify queries for your SIEM/EDR
4. Run initial baseline to understand your environment
5. Refine based on your findings
6. Document your iterations and lessons learned

**Ready to document your own hunts?** Check out the [Getting Started Guide](athf/data/docs/getting-started.md) and [templates/](athf/data/templates/).
