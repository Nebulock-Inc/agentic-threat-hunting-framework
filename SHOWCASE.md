# ATHF Hunt Showcase

This showcase highlights real hunts from our [hunts/](hunts/) directory, demonstrating how the LOCK pattern structures threat hunting from hypothesis to detection rule deployment.

Each example shows query evolution, results, and impact - proving the framework's practical value for security practitioners.

---

## Hunt #1: macOS Information Stealer Detection

**[View full hunt: H-0001.md →](hunts/H-0001.md)**

**Hunt ID:** H-0001
**MITRE ATT&CK:** T1005 (Data from Local System), T1059.002 (AppleScript)
**Platform:** macOS
**Status:** Completed

---

### Learn

**Context:** Atomic Stealer and similar macOS information stealers were actively targeting organizations. Following a phishing campaign, the security team needed visibility into file access patterns on macOS endpoints.

**Threat Actor TTPs:** Adversaries use AppleScript to automate collection of sensitive data from infected macOS systems:
- Safari cookies (session tokens, authentication)
- Notes database (credentials, sensitive text)
- Document directories (intellectual property)

**Available Telemetry:**
- macOS Unified Logging
- EDR process/file access logs
- Network connection attempts

**Knowledge Gap:** No visibility into unsigned process file access patterns; unable to distinguish malicious from legitimate applications.

---

### Observe

**Hypothesis:** Malicious processes will access Safari databases, Chrome profiles, and document directories in unusual patterns, especially unsigned or recently downloaded executables.

**Observable Behaviors:**
- Unsigned/invalid processes accessing browser data
- Rapid file access (< 5 minutes) spanning multiple sensitive directories
- Network connection attempts from file collection processes
- AppleScript (`osascript`) running file duplication commands

---

### Check

**Query Evolution:**

**Iteration 1: Broad file access monitoring (Too noisy)**
```spl
index=mac_edr
| where file_path LIKE "%Library/Safari%" OR file_path LIKE "%Library/Application Support/Google/Chrome%"
| stats count by process_name, file_path
```
**Results:** 247 events - overwhelming noise from legitimate browser activity, system processes, backup tools
**Problem:** Can't distinguish malicious from legitimate file access
**Refinement needed:** Focus on unsigned processes

**Iteration 2: Focus on unsigned processes (Better)**
```spl
index=mac_edr process_signature_status=invalid OR process_signature_status=unsigned
| where file_path LIKE "%Library/Safari/Cookies%" OR file_path LIKE "%Google/Chrome%" OR file_path LIKE "%Documents%"
| stats dc(file_path) as unique_files, values(file_path) as files by process_name, process_hash
| where unique_files > 5
```
**Results:** 12 events - includes developer tools, legitimate unsigned apps
**Problem:** False positives from development environments
**Refinement needed:** Add timing analysis, network correlation

**Iteration 3: Final - signature + behavior + timing (Success!)**
```spl
index=mac_edr process_signature_status!=valid
| where (file_path LIKE "%Library/Safari%" OR file_path LIKE "%Chrome%" OR file_path LIKE "%Documents%")
| stats earliest(_time) as first_seen, latest(_time) as last_seen,
        dc(file_path) as unique_files, values(file_path) as accessed_files
        by process_name, process_path, process_hash
| where unique_files > 3
| eval timespan=last_seen-first_seen
| where timespan < 300
| lookup threat_intel_hashes.csv process_hash OUTPUT threat_name, threat_family
```
**Results:** 1 true positive, 0 false positives
**Success!** Query ready for detection rule

### Detection Results

**Timeline:**
- 2025-11-15 14:23:18 - Initial detection: unsigned process accessing Safari cookies
- 2025-11-15 14:23:45 - EDR behavioral analysis confirms data collection pattern
- 2025-11-15 14:24:15 - EDR blocks network connection attempt
- 2025-11-15 14:24:30 - Host automatically isolated
- 2025-11-15 14:26:12 - Analyst confirms Atomic Stealer

**Finding Details:**
- **Process:** `SystemHelper` (masquerading as legitimate process)
- **Hash:** `a3f8bc2d9e1f4a5b6c7d8e9f0a1b2c3d`
- **Signature Status:** Unsigned
- **Behavior:** Accessed 47 files in 2.5 minutes
  - Safari cookies database
  - Chrome saved passwords
  - Documents folder (`.pdf`, `.docx`, `.txt`)
  - Keychain access attempts (blocked by macOS)
- **Network Activity:** Attempted connection to `185.220.101.47:443` (blocked by EDR)
- **Threat Intel Match:** Atomic Stealer v2.1

### Impact Metrics

- **Time to Detection:** 2 minutes from initial execution
- **Time to Containment:** 4 minutes (automated isolation)
- **Analyst Time Saved:** 45 minutes (behavioral detection + auto-response)
- **Data Protected:** 47 documents, browser cookies, saved passwords
- **Exfiltration Prevented:** Yes - EDR blocked C2 connection before data loss

---

### Keep

**What We Confirmed:**
- ✅ Information stealers actively targeting macOS in our environment
- ✅ Process signature validation is critical for macOS threat hunting
- ✅ Rapid file access patterns (< 5 minutes) indicate automated collection
- ✅ Combining file access + signature + timing reduces false positives to near-zero

**True Positives:**
- 1 confirmed Atomic Stealer infection
- Detected within 2 minutes of execution
- Prevented exfiltration of 47 documents + browser credentials
- Action: Host isolated, process terminated, forensics complete

**False Positives:**
- 0 after iteration 3 (down from 247 in iteration 1)

**Automated Response:**
- EDR behavioral prevention blocked network connection
- Host auto-isolated from network
- Ticket created in SOAR with full context
- User notified via Slack
- Security team alerted for forensic investigation

**Impact Metrics:**
- **Time to Detection:** 2 minutes from execution
- **Time to Containment:** 4 minutes (automated)
- **Analyst Time Saved:** 45 minutes per incident
- **Data Protected:** 47 documents, cookies, passwords
- **Exfiltration Prevented:** Yes

**Lessons Learned:**
- Process signature validation essential for macOS threat hunting
- Rapid file access patterns (< 5 minutes) indicate automated tools
- Combining file access + signature + timing = minimal false positives
- EDR integration enables sub-5-minute containment
- Threat intel hash matching confirms malware family

**Next Steps:**
- Extend detection to other browser data (Firefox, Brave, Edge)
- Add detection for Keychain access attempts
- Create runbook for macOS information stealer response
- Deploy EDR to remaining 15% of macOS fleet

**Hunt Status:** ✅ Completed - Detection rule deployed and validated

---

## Hunt #2: Linux Crontab Persistence Detection

**[View full hunt: H-0002.md →](hunts/H-0002.md)**

**Hunt ID:** H-0002
**MITRE ATT&CK:** T1053.003 (Scheduled Task/Job: Cron)
**Platform:** Linux
**Status:** Completed

---

### Learn

**Context:** Following a Q3 2024 cryptomining incident on dev servers, the security team identified cron-based persistence as a coverage gap. Recent threat intelligence indicated APT groups (APT28, Rocke, TeamTNT) actively using cron for persistence in Linux environments.

**Threat Actor TTPs:** Adversaries abuse cron to maintain access after initial compromise. Common patterns include:
- Unusual cron schedules (every minute, odd timing)
- Network utilities in commands (curl, wget, nc, socat)
- Obfuscated or base64-encoded commands
- Execution from temporary directories (/tmp, /dev/shm)

**Available Telemetry:**
- Auditd file integrity monitoring
- Syslog / Linux Secure logs
- Cron daemon process execution logs

**Knowledge Gap:** No baseline of legitimate cron jobs for comparison; 80% production coverage (dev/staging lacked auditd monitoring).

---

### Observe

**Hypothesis:** Adversaries will modify crontab files to achieve persistence on Linux hosts by scheduling malicious commands or scripts to execute at system startup or on defined intervals.

**Observable Behaviors:**
- Crontab file modifications outside maintenance windows
- Suspicious command patterns (curl, wget, bash -c, base64, /tmp)
- Modifications by non-root/non-admin users
- New cron files created in /etc/cron.d/ with suspicious ownership
- Cron daemon spawning unexpected network utilities

---

### Check

**Query Evolution:**

**Iteration 1: File modification-only detection (Too broad)**
```bash
index=linux sourcetype=auditd
file_path IN ("/etc/crontab", "/etc/cron.d/*", "/var/spool/cron/crontabs/*")
action IN ("modified", "created", "written")
```
**Results:** 89 events - many legitimate user cron updates
**Problem:** High noise from legitimate automation, package managers, certbot
**Refinement needed:** Add user filtering, pattern matching for suspicious commands

**Iteration 2: Pattern matching on suspicious commands (Better)**
```bash
index=linux (sourcetype=linux_secure OR sourcetype=syslog) ("CRON" OR "crontab")
| rex field=_raw "(?<cron_command>.*)"
| search cron_command IN ("*curl*", "*wget*", "*nc *", "*bash -c*", "*base64*", "*/tmp/*")
```
**Results:** 5 events - included backup scripts and monitoring tools
**Problem:** False positives from legitimate scripts using similar commands
**Refinement needed:** Add behavioral context, network correlation, baseline comparison

**Iteration 3: Behavioral analysis with context (Success!)**
```bash
index=linux sourcetype=auditd earliest=-1h
file_path IN ("/etc/crontab", "/etc/cron.d/*", "/var/spool/cron/crontabs/*")
action IN ("modified", "created")
| join type=left host [
    search index=linux sourcetype=syslog "CRON"
    | rex field=_raw "(?<cron_command>.+)"
    | eval is_suspicious=if(match(cron_command, "curl|wget|nc|base64|/tmp"), "true", "false")
]
| where (user!="root" AND process_name!="certbot") OR is_suspicious="true"
| lookup cron_baseline host, user OUTPUT is_baseline
| where isnull(is_baseline)
```
**Results:** 1 true positive (cryptominer), 1 false positive (backup script)
**Success!** Query ready for automated detection rule

### Detection Results

**Timeline:**
- 2025-11-17 03:42:15 - Suspicious crontab modification detected (user "webadmin")
- 2025-11-17 03:42:30 - Pattern analysis identifies curl to external IP
- 2025-11-17 03:45:00 - First cron execution observed, reverse shell attempt
- 2025-11-17 04:12:18 - SOC investigation begins (SOC-2901)
- 2025-11-17 04:30:00 - Containment complete (entry removed, host isolated)

**Findings:**
- **True Positive:** User "webadmin" modified personal crontab with curl command to 104.xxx.xxx.23
  - Schedule: Every 5 minutes
  - Downloaded cryptominer script
  - Matched known campaign (TI-0089)
  - Persistence duration: ~48 hours
  - Action: Cron entry removed, account reset, host isolated

- **False Positive:** Database backup script using curl to upload to S3 (legitimate but flagged)

### Impact Metrics

- **Time to Detection:** 30 minutes from crontab modification
- **Time to Containment:** 4.5 hours total
- **Cryptominer Prevented:** Est. $200/month in cloud compute costs
- **False Positives:** 1 (backup script - easily whitelisted)
- **Coverage Identified:** 20% gap in dev/staging environments

### Automated Detection Rule

Deployed final query as 5-minute scheduled search:
- Alert on crontab modifications by non-root users
- Pattern match suspicious commands (curl, wget, nc, base64, /tmp)
- Correlate with network connections from cron processes
- Compare against baseline of 200 known-good cron jobs
- Auto-response: Create ticket, snapshot crontab, alert SOC

---

### Keep

**What We Confirmed:**
- ✅ Cron persistence actively used by adversaries in our environment
- ✅ Auditd FIM provides real-time visibility into crontab modifications
- ✅ Multi-context analysis (file + command + network) reduces false positives
- ✅ Pattern matching on suspicious commands effectively identifies high-risk entries

**True Positives:**
- 1 confirmed cryptominer persistence via cron
- Detected within 30 minutes of crontab modification
- Prevented $200/month in cloud compute costs
- Action: Contained within 4.5 hours, forensics complete

**False Positives:**
- 1 backup script using curl (added to whitelist)

**Automated Detection:**
- Deployed real-time detection rule (5-minute schedule)
- Alert criteria: Suspicious crontab + command patterns + network activity
- Auto-response: Ticket creation, crontab snapshot, SOC alert
- False positive rate: ~2% (easily whitelisted)

**Impact Metrics:**
- **Time to Detection:** 30 minutes from modification
- **Time to Containment:** 4.5 hours
- **Coverage Improvement:** Identified 20% auditd gap in dev/staging
- **Baseline Created:** 200 known-good cron jobs documented

**Lessons Learned:**
- Auditd FIM essential for real-time crontab monitoring
- Baseline of legitimate cron jobs critical for reducing noise
- Multi-query approach (file + command + process) provides defense-in-depth
- User-based filtering (excluding root) significantly reduced false positives
- Threat intel integration confirmed cryptomining campaign match

**Telemetry Gaps:**
- Dev/staging environments lack auditd (only 80% production coverage)
- Bash history logging inconsistently enabled
- No automated cron job inventory for baseline comparison

**Next Steps:**
- Deploy auditd to dev/staging environments
- Enable bash history logging across all Linux servers
- Implement automated cron inventory for baseline maintenance
- Document playbook for SOC analyst triage
- Schedule recurring monthly hunt

**Hunt Status:** ✅ Completed - Detection rule deployed and validated

---

## Hunt #3: AWS Lambda Persistence Detection

**[View full hunt: H-0003.md →](hunts/H-0003.md)**

**Hunt ID:** H-0003
**MITRE ATT&CK:** T1546.004 (Event Triggered Execution), T1098 (Account Manipulation)
**Platform:** AWS Cloud
**Status:** Completed

---

### Learn

**Context:** Following increased cloud-focused threat intelligence and a compromised service account incident, the security team needed visibility into Lambda-based persistence mechanisms. Recent APT activity showed adversaries favoring serverless persistence over traditional EC2 backdoors.

**Threat Actor TTPs:** Adversaries abuse AWS Lambda for persistence by:
- Creating functions with administrative IAM roles (`AdministratorAccess`)
- Configuring API Gateway for public HTTP backdoors
- Using EventBridge for scheduled recon/execution
- Masquerading function names as legitimate services

**Available Telemetry:**
- AWS CloudTrail (Lambda API calls)
- IAM policy change events
- API Gateway creation events
- EventBridge rule configurations

**Knowledge Gap:** No baseline of legitimate Lambda deployment patterns; unable to distinguish DevOps automation from malicious persistence.

---

### Observe

**Hypothesis:** Attackers with initial access will create Lambda functions with overly permissive IAM roles, scheduled triggers, or API Gateway integrations for persistent backdoor access.

**Observable Behaviors:**
- Lambda creation events in CloudTrail
- IAM role attachment with `AdministratorAccess` or `PowerUserAccess`
- API Gateway endpoint creation linked to new Lambda functions
- EventBridge rules targeting Lambda functions
- Activity from compromised service accounts
- Source IPs from unexpected geolocations (residential ISPs, VPNs)
- Rapid succession of Lambda + IAM + trigger events (< 1 hour)

---

### Check

**Query Evolution:**

**Iteration 1: Monitor all Lambda creations (Too noisy)**
```spl
index=aws_cloudtrail eventName="CreateFunction"
| stats count by userIdentity.principalId, requestParameters.functionName
```
**Results:** 89 events in 24 hours - legitimate DevOps activity, CI/CD pipelines, infrastructure as code deployments
**Problem:** Can't differentiate malicious from legitimate Lambda deployments
**Refinement needed:** Focus on IAM policy analysis, filter known automation accounts

**Iteration 2: Focus on suspicious IAM policies (Better)**
```spl
index=aws_cloudtrail (eventName="CreateFunction" OR eventName="UpdateFunctionConfiguration")
| spath input=requestParameters.role output=lambda_role
| join lambda_role [search index=aws_cloudtrail eventName="PutRolePolicy" OR eventName="AttachRolePolicy"
  | spath input=requestParameters.policyDocument output=policy]
| where policy="*" OR policy LIKE "%AdministratorAccess%" OR policy LIKE "%iam:*%"
| stats values(eventName) as events,
        values(requestParameters.functionName) as functions,
        values(sourceIPAddress) as source_ips
        by userIdentity.principalId, lambda_role
```
**Results:** 8 events - includes some legitimate admin Lambda functions for automation
**Problem:** Need to filter known automation accounts
**Refinement needed:** Add trigger analysis, whitelist automation, temporal correlation

**Iteration 3: Final - anomaly + permissions + trigger analysis (Success!)**
```spl
index=aws_cloudtrail (eventName="CreateFunction" OR eventName="UpdateFunctionConfiguration" OR eventName="CreateEventSourceMapping")
| spath input=requestParameters.role output=lambda_role
| eval function_name=coalesce('requestParameters.functionName', 'requestParameters.FunctionName')
| join lambda_role [search index=aws_cloudtrail eventName="AttachRolePolicy"
  | spath input=requestParameters.policyArn output=policy_arn
  | where policy_arn LIKE "%AdministratorAccess%" OR policy_arn LIKE "%PowerUserAccess%"]
| join function_name [search index=aws_cloudtrail eventName="CreateEventSourceMapping" OR eventName="CreateApi"
  | stats values(eventName) as triggers by requestParameters.functionName]
| where NOT [| inputlookup known_automation_accounts.csv | fields userIdentity.principalId]
| eval time_since_creation=now()-_time
| where time_since_creation < 3600
| stats values(eventName) as events,
        values(function_name) as functions,
        values(lambda_role) as roles,
        values(triggers) as trigger_methods,
        values(sourceIPAddress) as source_ips,
        values(userAgent) as user_agents
        by userIdentity.principalId, userIdentity.arn
```
**Results:** 2 true positives, 0 false positives
**Success!** Query ready for automated detection rule

---

### Detection Results

**Timeline:**
- 2025-11-28 03:15:42 - Suspicious Lambda function created: `sys-health-check-v2`
- 2025-11-28 03:16:18 - IAM role attached with `AdministratorAccess` policy
- 2025-11-28 03:17:05 - API Gateway created and linked to Lambda
- 2025-11-28 03:18:33 - Detection alert triggered
- 2025-11-28 03:22:15 - Incident response engaged
- 2025-11-28 03:35:47 - Lambda function deleted, IAM role removed
- 2025-11-28 04:12:22 - Compromised IAM user credentials rotated

**Finding #1: Persistence Lambda (Confirmed Malicious)**
- **Function Name:** `sys-health-check-v2` (masquerading as legitimate monitoring)
- **Runtime:** Python 3.11
- **IAM Role:** `lambda-admin-role-temp` with `AdministratorAccess`
- **Trigger:** API Gateway endpoint (publicly accessible)
- **Source IP:** `103.253.145.22` (residential proxy - suspicious)
- **User Agent:** `aws-cli/2.13.5 Python/3.11.4` (CLI from unexpected location)
- **Creator:** `arn:aws:iam::123456789012:user/developer-jenkins` (compromised service account)
- **Function Code Analysis:** Base64 reverse shell with environment variable exfiltration

**Finding #2: Scheduled Recon Lambda (Confirmed Malicious)**
- **Function Name:** `cloudwatch-logs-processor`
- **Runtime:** Python 3.9
- **IAM Role:** `lambda-recon-role` with `ReadOnlyAccess` + `iam:ListUsers`
- **Trigger:** EventBridge scheduled rule (every 6 hours)
- **Purpose:** Automated reconnaissance - enumerate IAM users, roles, S3 buckets
- **Same attacker:** Matched source IP and user agent patterns

### Impact Metrics

- **Time to Detection:** 3 minutes from Lambda creation
- **Time to Containment:** 20 minutes (manual IR response)
- **Potential Blast Radius:** Full AWS account compromise prevented
- **Affected Resources:** 2 Lambda functions, 2 IAM roles, 1 API Gateway, 1 EventBridge rule
- **Credential Exposure:** 1 service account compromised (credential rotation completed)
- **Cost of Attack:** $0.47 in Lambda execution charges (attacker testing persistence)

### Remediation Actions

1. Deleted malicious Lambda functions
2. Removed associated IAM roles and policies
3. Deleted API Gateway endpoint
4. Removed EventBridge scheduled rules
5. Rotated credentials for compromised service account
6. Implemented SCPs (Service Control Policies) to restrict Lambda IAM role permissions
7. Enhanced monitoring for IAM role creation and modification

---

### Keep

**What We Confirmed:**
- ✅ Lambda persistence actively used for cloud backdoors
- ✅ IAM role analysis (AdministratorAccess detection) is critical
- ✅ Multi-event correlation (Lambda + IAM + triggers) identifies complete attack chain
- ✅ Temporal analysis (< 1 hour) strong indicator of malicious activity
- ✅ Known automation whitelisting eliminates 87% of false positives

**True Positives:**
- 2 confirmed malicious Lambda functions for persistence
- Detection within 3 minutes of Lambda creation
- Prevented full AWS account compromise (AdministratorAccess available)
- Affected resources: 2 Lambdas, 2 IAM roles, 1 API Gateway, 1 EventBridge rule
- Action: All resources deleted, credentials rotated, SCPs implemented

**False Positives:**
- 0 after automation whitelist applied

**Automated Detection:**
- Deployed real-time CloudWatch Logs Insights rule (5-minute schedule)
- Alert criteria: Lambda + admin IAM + public/scheduled trigger
- Lambda trigger for automated containment (disable function, create ticket, notify SOC)
- False positive rate: <1%

**Impact Metrics:**
- **Time to Detection:** 3 minutes from Lambda creation
- **Time to Containment:** 20 minutes (manual IR response)
- **Blast Radius Prevented:** Full AWS account compromise
- **Credential Exposure:** 1 service account compromised (rotated)
- **Cost of Attack:** $0.47 in Lambda execution (attacker testing)

**Lessons Learned:**
- Lambda persistence is subtle - functions can remain dormant for weeks
- IAM role analysis critical - focus on overly permissive policies
- API Gateway + Lambda = public backdoor if not restricted
- Service account compromise remains primary initial access vector
- Lambda function code analysis needed for IOCs (base64, reverse shells)
- SCPs prevent privilege escalation via Lambda IAM roles

**Telemetry Gaps:**
- No automated Lambda function code scanning
- Lambda execution logs not centralized in SIEM
- API Gateway access logs not enabled (no invocation visibility)
- EventBridge rule invocations not logged

**Next Steps:**
- Deploy Lambda function code scanning for IOCs
- Enable API Gateway access logging
- Centralize Lambda execution logs
- Enforce MFA for all service accounts
- Implement short-lived credentials for CI/CD

**Hunt Status:** ✅ Completed - Detection rule deployed and validated

---

## Key Takeaways Across All Hunts

### What Made These Hunts Successful

1. **Iterative Refinement:** Each hunt evolved through 3+ query iterations
2. **Behavioral Focus:** Moved beyond simple signatures to behavior patterns
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
✅ **Iteration:** LOCK pattern structured refinement process
✅ **Metrics:** Clear ROI with time saved and FP reduction
✅ **Automation:** Hunts became detection rules
✅ **Knowledge Transfer:** Future analysts can learn from documented hunts

---

## Try These Hunts in Your Environment

All hunt templates and queries are available in the `hunts/` and `queries/` directories. Adapt them to your:
- Data sources (Splunk, Sentinel, Elastic, Chronicle)
- Environment specifics (platforms, tools, baselines)
- Organizational context (known service accounts, approved tools)

**Start with:**
1. Review the hunt documentation
2. Understand the LOCK pattern used
3. Modify queries for your SIEM/EDR
4. Run initial baseline to understand your environment
5. Refine based on your findings
6. Document your iterations and lessons learned

---

**Ready to document your own hunts?** Check out the [Getting Started Guide](docs/getting-started.md) and [templates/](templates/).
