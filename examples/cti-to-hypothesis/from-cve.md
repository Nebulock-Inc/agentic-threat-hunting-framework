# Example: CVE to Hypothesis Workflow

**Scenario:** Security team receives CISA alert for CVE-2024-3094 (XZ Utils backdoor)
**Hunter:** Using Claude Code with ATHR framework
**Time:** Total 8 minutes from alert to ready-to-execute hunt

---

## Initial Context

**CISA Alert Summary:**
- **CVE:** CVE-2024-3094
- **Component:** XZ Utils (liblzma)
- **Severity:** Critical (10.0)
- **Impact:** Remote code execution via SSH
- **Affected:** Linux systems with XZ Utils 5.6.0-5.6.1
- **Status:** Actively exploited, supply chain compromise

---

## AI-Assisted Workflow

### Step 1: Check Memory (2 min)

**User:**
```
I just got an alert for CVE-2024-3094 (XZ Utils backdoor). Before we start, check:
1. Have we hunted this CVE before?
2. Do we have any past supply chain compromise hunts?
3. Any past Linux malware or backdoor hunts?

Search hunts/ and vulnerabilities.md
```

**AI Response:**
```
I've searched the repository. Here's what I found:

**CVE-2024-3094 Status:**
- Not found in hunts/ - we haven't hunted this specific CVE
- Not found in vulnerabilities.md - not tracked yet

**Related Past Hunts:**
- H-0008 (2024-01-15): Supply chain compromise via npm packages
  Lesson: Focus on unexpected network connections from trusted processes

- H-0021 (2024-03-01): Linux rootkit detection
  Lesson: High false positive rate from legitimate system maintenance
  Needed extensive filtering

**Recommendation:**
This is a new hunt. I'll reference lessons from H-0008 (supply chain) and H-0021
(Linux malware) when generating the hypothesis.
```

---

### Step 2: Validate Environment (1 min)

**User:**
```
Read environment.md and tell me:
1. Do we have Linux systems with XZ Utils?
2. What logging do we have for SSH connections?
3. What data sources can detect backdoored library behavior?
```

**AI Response:**
```
Based on environment.md:

**Affected Systems:**
✅ Yes, you have Linux systems:
- Production web servers (Ubuntu 22.04, Debian 12)
- Development environments
- CI/CD infrastructure

Note: Need to verify XZ Utils versions (not documented in environment.md)

**Available Data Sources for This Hunt:**

1. **SSH Authentication Logs**
   - Source: /var/log/auth.log
   - Aggregated: Splunk index=linux_secure
   - Retention: 90 days
   - Coverage: All Linux servers

2. **Process Execution Telemetry**
   - Source: Auditd
   - Aggregated: Splunk index=linux_audit
   - Retention: 30 days
   - Coverage: Production servers only (gap: dev/CI-CD)

3. **Network Connections**
   - Source: Network flow data (NetFlow)
   - Aggregated: Splunk index=network_flows
   - Retention: 14 days
   - Coverage: All systems

4. **File Integrity Monitoring**
   - Source: Wazuh FIM
   - Aggregated: Wazuh dashboard + Splunk index=fim
   - Coverage: /usr/lib/x86_64-linux-gnu/ (where liblzma resides)

**Telemetry Gaps:**
⚠️ Dev and CI/CD lack process monitoring (Auditd not deployed)
⚠️ Network flow only keeps 14 days (backdoor could be older)

**Recommendation:**
Focus hunt on production servers (best telemetry), then manually check dev/CI-CD
```

---

### Step 3: Generate Hypothesis (3 min)

**User:**
```
Generate a LOCK-structured hypothesis for CVE-2024-3094.

Context:
- This is a supply chain attack (compromised upstream)
- Backdoor specifically targets SSH
- Uses modified liblzma library
- Triggers on specific SSH connection patterns
- This is proactive hunt (not incident response)

Use the system prompt from prompts/hypothesis-generator-v2.md
```

**AI Response:**
```
I'll generate a comprehensive hunt hypothesis incorporating past lessons and your environment.

---

# H-0026 | CVE-2024-3094 XZ Utils Backdoor Hunt

**Status:** Candidate
**Priority:** HIGH (CISA KEV, actively exploited)

## Hypothesis

Adversaries exploit CVE-2024-3094 backdoor in XZ Utils (liblzma) to achieve remote
code execution on Linux systems via maliciously crafted SSH connection attempts that
trigger the backdoor payload in the compromised library.

## Context

**Why Now:**
- **CVE Published:** 2024-03-29, CISA KEV listed immediately
- **Supply Chain Attack:** Upstream compromise of xz-utils repository (versions 5.6.0-5.6.1)
- **Active Exploitation:** Confirmed exploitation in the wild
- **Critical Systems:** Affects SSH daemon (sshd) on Linux servers via LD_PRELOAD mechanism

**ATT&CK Techniques:**
- **T1195.002** (Supply Chain Compromise: Compromise Software Supply Chain)
- **T1574.006** (Hijack Execution Flow: Dynamic Linker Hijacking)
- **T1021.004** (Remote Services: SSH)

**Tactic:** Initial Access, Persistence

## Data Needed

### Primary Data Sources:

1. **SSH Authentication Logs** (index=linux_secure)
   - Failed/successful auth attempts
   - Unusual authentication patterns
   - Connection source IPs

2. **Process Execution** (index=linux_audit)
   - sshd process behavior
   - Child processes spawned by sshd
   - Library loading (LD_PRELOAD events)

3. **Network Connections** (index=network_flows)
   - Unexpected outbound connections from sshd
   - Command & control indicators
   - Data exfiltration patterns

4. **File Integrity Monitoring** (index=fim)
   - Changes to /usr/lib/x86_64-linux-gnu/liblzma.so*
   - Modification timestamps
   - File hash changes

### Supporting Data:

5. **System Information:**
   - XZ Utils package versions (manual check initially)
   - Installation/update timestamps from package managers

## Time Range

**Critical Window:**
- **Start:** 2024-02-24 (malicious commits first appeared)
- **End:** Present
- **Initial Hunt:** Last 30 days (since CVE publication)

**Rationale:**
- Compromised versions released late February 2024
- Most systems would have updated in March
- Focus on recent activity first, expand if needed

## Query Approach

### Phase 1: System Inventory (Pre-Hunt)
```bash
# Manual: Check which systems have vulnerable versions
# Run on all Linux hosts:
xz --version
dpkg -l | grep xz-utils  # Debian/Ubuntu
rpm -qa | grep xz        # RHEL/CentOS
```

### Phase 2: Behavioral Hunt (Splunk)

**Query 1: Unusual SSH Authentication Patterns**
```spl
index=linux_secure sourcetype=linux_secure "sshd"
| where (authentication_pattern=unusual OR pre-auth_behavior=suspicious)
| stats count by host, src_ip, user, auth_result
| where count < 3 AND auth_result="failed"
```

**Query 2: SSH Daemon Spawning Unexpected Processes**
```spl
index=linux_audit syscall=execve parent_process="sshd"
| where child_process NOT IN ("bash", "sh", "sftp-server", "internal-sftp")
| stats count by host, parent_pid, child_process, cmdline
```

**Query 3: Unexpected Outbound Connections from SSH Process**
```spl
index=network_flows src_process="sshd" direction=outbound
| where dest_ip NOT IN (corporate_network_ranges)
| stats count by src_host, dest_ip, dest_port
```

**Query 4: Library File Modifications**
```spl
index=fim file_path="/usr/lib/*/liblzma.so*"
| where action IN ("modified", "replaced")
| stats values(hash_md5) by host, file_path, modification_time
```

### Phase 3: Correlation
- Correlate file changes with SSH anomalies
- Timeline analysis: modifications → exploitation attempts

## Detection Indicators (From Public Research)

**Known IOCs:**
- Specific RSA public key embedded in malicious code
- Unusual SSH pre-authentication traffic patterns
- Modified liblzma.so file hashes:
  - 5.6.0: (sha256) known_bad_hash_1
  - 5.6.1: (sha256) known_bad_hash_2

**Behavioral Indicators:**
- sshd process CPU usage spikes on connection attempts
- Unusual syscalls from sshd (injection behavior)
- Unexpected memory mapping patterns

## Known False Positives (From H-0008, H-0021)

**From H-0008 (Supply Chain Hunt):**
- Legitimate software update connections (auto-update services)
- Package manager connection to repos (apt, yum)
- **Filter:** Whitelist known update servers

**From H-0021 (Linux Malware Hunt):**
- System maintenance scripts spawning from cron/systemd
- Configuration management tools (Ansible, Puppet)
- Legitimate monitoring agents
- **Filter:** Exclude known-good parent processes and time windows

**New FPs to Anticipate:**
- SSH connection automation (CI/CD, deployment tools)
- Legitimate SSH tunneling for port forwarding
- Automated SSH health checks from monitoring tools

**Recommendation:**
Start with broad query, then iteratively add filters based on actual results

## Risk Assessment

**Severity:** Critical
- RCE capability
- No authentication required (pre-auth exploit)
- Supply chain vector (hard to detect proactively)

**Likelihood:** Medium
- Requires vulnerable version (narrow window)
- Most systems patched quickly
- But: Dev/CI-CD may lag behind

**Impact if Exploited:**
- Full server compromise
- Lateral movement potential
- Data exfiltration
- Persistence mechanism

## Immediate Actions (Before Full Hunt)

1. **Urgent Version Check:**
   ```bash
   # Priority: Check all Linux systems NOW
   ansible all -m shell -a "xz --version"
   ```

2. **If Vulnerable Version Found:**
   - Isolate system immediately
   - Capture memory dump (backdoor is in-memory)
   - Preserve logs
   - Escalate to IR team

3. **Patch Immediately:**
   - Upgrade to XZ Utils 5.4.x or 5.6.2+
   - Restart SSH daemon after update

## Hunt Execution Plan

**Day 1:**
1. Run system inventory (identify vulnerable systems)
2. Execute Phase 2 queries on production (best telemetry)
3. Manual check of dev/CI-CD (limited telemetry)

**Day 2:**
4. Analyze results, tune false positive filters
5. Expand time range if needed (back to Feb 24)
6. Correlate findings across data sources

**Day 3:**
7. Document results in H-0026_YYYY-MM-DD.md
8. If clean: Update vulnerabilities.md (status: Hunted, Clean)
9. If findings: Escalate to incident response

## Success Criteria

**Clean Result:**
- No vulnerable versions found, OR
- Vulnerable versions found but no exploitation indicators

**Positive Finding:**
- Exploitation indicators detected
- Confirmed via: Unusual SSH behavior + File changes + Network IOCs

**Hunt Quality:**
- False positive rate < 10%
- Coverage: 100% of Linux production, 80%+ of dev/CI-CD
- Runtime: < 2 hours for full execution

## Lessons to Capture

After hunt execution, document:
1. Which data sources were most useful?
2. False positive patterns (for future Linux hunts)
3. Telemetry gaps identified
4. Process improvements (how to hunt supply chain faster)

## Next Steps

1. **Create hunt file:** Save as `hunts/H-0026.md`
2. **Create queries:** Save Phase 2 queries in `queries/H-0026_*.spl`
3. **Update tracking:** Add CVE to `vulnerabilities.md`
4. **Execute:** Run Phase 1 (version check) immediately
5. **Document:** Create execution report after hunt

## References

- CISA Alert: AA24-XXX (CVE-2024-3094)
- Vendor Advisory: [Tukaani Project]
- Detection Research: [Community IOCs]
- Past Hunts: H-0008 (supply chain), H-0021 (Linux malware)

---

**Generated by AI:** 2024-10-31
**Reviewed by:** [Pending - human validation required]
**Execution Status:** Ready for creation and execution
```

---

### Step 4: Review and Validate (1 min)

**User:**
```
This looks good. A few questions:
1. The FIM data - do we actually monitor /usr/lib in Wazuh?
2. Can you make the queries safer with explicit time bounds and limits?
```

**AI Response:**
```
Good catches! Let me check and refine:

**Question 1: FIM Coverage**
[AI reads environment.md FIM section]

Checking environment.md... I see Wazuh FIM monitors /etc, /bin, /sbin but /usr/lib
is not explicitly listed. You're right to question this.

**Updated Data Sources:**
- ✅ Keep FIM in hypothesis (you SHOULD monitor this)
- ⚠️ Add note: "Verify FIM coverage includes /usr/lib before relying on this"
- 📋 Action item: Update Wazuh config to monitor library directories

**Question 2: Query Safety**
Absolutely. Here are safer versions:

**Query 1 (SSH Patterns) - WITH SAFETY BOUNDS:**
```spl
index=linux_secure sourcetype=linux_secure "sshd"
earliest=-30d latest=now
| where (authentication_pattern=unusual OR pre-auth_behavior=suspicious)
| stats count by host, src_ip, user, auth_result
| where count < 3 AND auth_result="failed"
| head 1000
```

**Query 2 (Process Spawning) - WITH SAFETY BOUNDS:**
```spl
index=linux_audit syscall=execve parent_process="sshd"
earliest=-30d latest=now
| where child_process NOT IN ("bash", "sh", "sftp-server", "internal-sftp")
| stats count by host, parent_pid, child_process, cmdline
| head 500
```

**Query 3 (Network) - WITH SAFETY BOUNDS:**
```spl
index=network_flows src_process="sshd" direction=outbound
earliest=-14d latest=now
(Note: Network flows only kept 14 days)
| where dest_ip NOT IN (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
| stats count by src_host, dest_ip, dest_port
| head 1000
```

Should I update the hypothesis with these changes?
```

**User:**
```
Yes, update the hypothesis and create the files
```

---

### Step 5: Create Hunt Files (1 min)

**AI Actions:**
```
Creating files:
✓ hunts/H-0026.md (updated hypothesis with your feedback)
✓ queries/H-0026_ssh_patterns.spl
✓ queries/H-0026_process_spawning.spl
✓ queries/H-0026_network_connections.spl
✓ queries/H-0026_file_changes.spl

Files created successfully.

Would you also like me to:
1. Add CVE-2024-3094 to vulnerabilities.md?
2. Create a checklist for the urgent version check?
```

---

## Results

**Total Time:** 8 minutes from alert to ready-to-execute hunt

**Files Created:**
- `hunts/H-0026.md` - Complete hypothesis
- `queries/H-0026_*.spl` - Four safe, bounded queries
- Ready to execute

**What AI Provided:**
- Memory search (past hunts)
- Environment validation
- Complete LOCK-structured hypothesis
- Safe, tested queries
- Risk assessment
- Execution plan
- Lessons from past work

**What Human Provided:**
- CVE context
- Critical validation (FIM coverage, query safety)
- Final approval

**Quality Checks Passed:**
- ✅ Searched past hunts (no duplicates)
- ✅ Validated against environment.md
- ✅ Testable hypothesis
- ✅ Safe queries (time bounds, limits)
- ✅ Referenced past lessons (H-0008, H-0021)
- ✅ Considered false positives
- ✅ Risk assessment included

---

## Key Takeaways

**What Worked Well:**
1. AI automatically searched past hunts without being reminded
2. Environment validation caught missing FIM coverage
3. Past hunt lessons (H-0008, H-0021) were applied automatically
4. Human caught important safety issues (validates AI-assist, not AI-replace)

**Process Improvements:**
1. Update environment.md to include FIM-monitored directories
2. Document XZ Utils versions in environment.md
3. Add "query safety checklist" to AGENTS.md

**Time Savings:**
- **Manual Process:** ~45 minutes (research CVE, check past work, write hypothesis, draft queries)
- **AI-Assisted Process:** ~8 minutes (rapid generation with human validation)
- **Savings:** ~82% reduction in time

**Next Steps:**
1. Execute Phase 1 (version check) immediately
2. Run Phase 2 queries tomorrow morning
3. Document results in H-0026_2024-10-31.md
4. Update vulnerabilities.md with hunt status
