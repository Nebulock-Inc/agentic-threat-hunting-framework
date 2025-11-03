# Example: APT Report to Hypothesis Workflow

**Scenario:** Threat intel team shares report about APT29 campaign targeting cloud infrastructure
**Hunter:** Using GitHub Copilot with ATHF framework
**Time:** Total 12 minutes from report to hypothesis

---

## Initial Context

**Threat Intelligence Report Summary:**

**Campaign:** "Cloud Hopper 2.0"
**Threat Actor:** APT29 (Cozy Bear / SVR-backed)
**Target Sector:** Technology, Cloud Service Providers
**Timeline:** Active since Q1 2024

**TTPs Observed:**
- Initial access via phishing with cloud credential harvesting
- Abuse of service principals and API keys
- Lateral movement through cloud management APIs
- Privilege escalation via misconfigured IAM roles
- Data exfiltration to attacker-controlled cloud storage

**MITRE ATT&CK Mapping:**
- T1566.002 (Phishing: Spearphishing Link)
- T1528 (Steal Application Access Token)
- T1078.004 (Valid Accounts: Cloud Accounts)
- T1069.003 (Discovery: Cloud Groups)
- T1567.002 (Exfiltration to Cloud Storage)

**IOCs:**
- Malicious OAuth app names: "Office365-Update-Manager", "Azure-Security-Tool"
- C2 domains: cloud-mgmt-portal[.]com, azure-status-check[.]net
- Unusual API call patterns from service principals

---

## AI-Assisted Workflow

### Step 1: Understanding and Scoping (3 min)

**User:**
```
I have a threat intel report about APT29 targeting cloud infrastructure. Before we generate
a hypothesis, help me scope this:

1. Read our environment.md - do we use the cloud platforms they're targeting?
2. Search past hunts - have we hunted APT29 TTPs before?
3. Which specific TTP should we focus on first? (they list 5)

Here's the report summary: [pastes summary above]
```

**AI Response:**
```
I'll analyze the report against your environment and past hunts.

**Environment Analysis (from environment.md):**

✅ **Cloud Platforms We Use:**
- **Azure:** Primary cloud (Azure AD, Azure DevOps, VMs, Storage)
- **AWS:** Limited use (S3, Lambda for specific projects)
- **GCP:** Not used

✅ **Relevant Security Tools:**
- Azure AD audit logs → Splunk index=azure_ad
- AWS CloudTrail → Splunk index=aws_cloudtrail
- Microsoft 365 audit logs → Splunk index=o365_audit

✅ **IAM Configuration:**
- Service principals in use (documented in environment.md)
- API keys for CI/CD (GitHub Actions, Azure DevOps)

⚠️ **Exposure Areas:**
- External-facing: Azure-hosted web applications
- Third-party integrations: Multiple OAuth apps (Slack, GitHub, monitoring tools)
- Users: 250+ with cloud access

**Past Hunt Analysis (search results):**

Found 3 related past hunts:

**H-0012 (2024-02-15): Office 365 Phishing Detection**
- TTP: T1566 (Phishing)
- Findings: High false positives from legitimate external emails
- Lesson: Focus on credential harvesting indicators, not just phishing emails

**H-0019 (2024-06-20): Azure AD Privilege Escalation**
- TTP: T1078.004 (Valid Accounts: Cloud Accounts)
- Findings: Found 2 overprivileged service principals (fixed)
- Lesson: Service principal abuse is realistic threat in our environment

**H-0023 (2024-08-10): Unusual API Activity Hunt**
- TTP: General API abuse
- Findings: 15% false positive rate from automation scripts
- Lesson: Need to baseline normal API call patterns first

**Recommendation: Focus Priority**

I recommend focusing on **T1078.004 (Valid Accounts: Cloud Accounts) + T1528 (Steal
Application Access Token)** because:

1. **Highest Risk:** We use service principals extensively (H-0019 found issues)
2. **Detectable:** We have good logging (Azure AD, AWS CloudTrail)
3. **Realistic:** APT29 campaigns actively use this TTP
4. **Actionable:** Clear indicators (unusual API calls, geographic anomalies)

**Lower Priority for now:**
- T1566.002 (Phishing): Already hunted recently (H-0012)
- T1567.002 (Exfiltration): Harder to detect, needs baseline first

Should I generate a hypothesis focusing on cloud account and service principal abuse?
```

**User:**
```
Yes, focus on service principal and API key abuse. Generate hypothesis.
```

---

### Step 2: Generate Hypothesis (4 min)

**User:**
```
Using the enhanced prompt from hypothesis-generator-v2.md, generate a LOCK-structured
hypothesis for hunting APT29-style service principal and API key abuse in our Azure
and AWS environments.

Context:
- APT29 known to abuse OAuth apps and service principals
- They use stolen tokens for lateral movement and privilege escalation
- Geographic anomalies common (access from unusual locations)
- This is proactive threat hunt based on CTI

Reference past hunt H-0019 (Azure privilege escalation) for lessons learned.
```

**AI Response:**
```
Generated comprehensive hypothesis: H-0027 | APT29-Style Cloud Service Principal Abuse Hunt

**Hypothesis Structure (LOCK format):**
- Testable statement about adversary behavior (service principal/OAuth app abuse)
- Context (APT29 threat intel, past H-0019 findings, technology sector targeting)
- ATT&CK mapping (T1078.004, T1528, T1069.003)
- Data sources (Azure AD logs, CloudTrail - matched to environment.md)
- Time range (90 days, phased approach)

**Query Package (6 queries):**
- Phase 1: Service principal anomalies (geographic, off-hours, permission escalation)
- Phase 2: OAuth app detection (suspicious names, excessive permissions)
- Phase 3: AWS key abuse (privilege escalation API calls)
- Phase 4: Correlation logic (multi-indicator scoring)

**Detection Approach:**
- APT29-specific IOCs (malicious app names, C2 domains from threat intel)
- Behavioral indicators (geographic anomalies, API burst patterns)
- False positive filters (referenced H-0019, H-0023 lessons)

**Execution Plan:**
- 3-week timeline (1 week baseline, 1 week execution, 1 week analysis)
- Baseline requirements for service principals and API patterns
- Success criteria (< 15% FP rate, 100% coverage)

[See templates/hypothesis-template.md for full LOCK hypothesis structure]
```

---

### Step 3: Clarification and Refinement (3 min)

**User:**
```
This is comprehensive but I have concerns:

1. We don't have 3 weeks to spend on this hunt. Can you simplify to a 2-day execution?
2. The baseline requirement - can we hunt without establishing baseline first?
3. Query 3 (permission escalation) - will this catch our legitimate IAC (Infrastructure as Code) that assigns roles via Terraform?
```

**AI Response:**
```
Excellent questions. Let me address each and provide a simplified approach:

**1. Simplified 2-Day Execution Plan:**

You're right - the 3-week plan is too much for initial hunt. Here's a focused 2-day version:

**Day 1: High-Confidence Indicators Only**
- Focus on IOC-based detection (malicious app names from threat intel)
- Geographic anomalies for service principals (not users)
- New OAuth apps created in last 90 days (manual review)
- Estimated time: 4-6 hours

**Day 2: Analysis & Documentation**
- Review findings (expect 10-50 items to triage)
- Document in H-0027_YYYY-MM-DD.md
- Quick wins: Remove unauthorized OAuth apps if found
- Estimated time: 4-6 hours

**Defer to future hunts:**
- API pattern baseline (requires 2 weeks of data analysis)
- Continuous monitoring setup (separate project)
- Comprehensive service principal audit (ongoing security work)

**2. Hunt Without Baseline (Modified Approach):**

Yes, you can hunt without baseline by focusing on high-confidence indicators:

**Replace baseline queries with:**
- IOC matching (malicious app names, C2 domains)
- Extreme anomalies (100+ API calls/minute - clearly abnormal)
- Known-bad patterns (geographic: Russia, North Korea unless you do business there)

**Add manual whitelist:**
- List your known-good service principals in environment.md
- Exclude those from results manually
- Accept slightly higher false positive rate (20-25%)

**Trade-off:**
- ✅ Faster execution (2 days vs 3 weeks)
- ⚠️ Higher false positive rate
- ⚠️ May miss subtle anomalies

For APT29 threat hunt, this is acceptable. You're looking for active compromise, not subtle deviations.

**3. Terraform/IaC False Positives:**

Yes, Query 3 will absolutely catch Terraform role assignments. Here's the fix:

**Updated Query 3 - IaC-Aware:**
```kql
AuditLogs
| where TimeGenerated > ago(90d)
| where OperationName == "Add member to role"
| where TargetResources[0].type == "ServicePrincipal"
| where TargetResources[0].modifiedProperties[0].newValue contains "Admin"
      OR TargetResources[0].modifiedProperties[0].newValue contains "Owner"
// Filter out known IaC service principals
| where InitiatedBy.app.displayName !contains "Terraform"
      AND InitiatedBy.app.displayName !contains "Azure DevOps"
      AND InitiatedBy.app.appId !in ("<your-terraform-app-id>",
                                       "<your-azdo-app-id>")
// Also filter known deployment times
| extend Hour = datetime_part("hour", TimeGenerated)
| where NOT (Hour >= 14 AND Hour <= 16)  // Your deployment window 2-4 PM
| project TimeGenerated,
          Initiator=coalesce(InitiatedBy.user.userPrincipalName,
                             InitiatedBy.app.displayName),
          ServicePrincipal=TargetResources[0].displayName,
          RoleAssigned=TargetResources[0].modifiedProperties[0].newValue
```

**Action items for you:**
1. Add Terraform/IaC service principal IDs to environment.md
2. Document deployment windows (when role changes are expected)
3. Update the query with your specific app IDs

**Updated recommendation:** Start with simplified 2-day hunt focused on IOCs and extreme anomalies. Baseline establishment can be a separate continuous monitoring project.

Should I update the hypothesis with the 2-day execution plan?
```

**User:**
```
Yes, update with 2-day plan and create all the files
```

---

### Step 4: File Creation (2 min)

**AI Actions:**
```
Updating hypothesis with:
✓ Simplified 2-day execution plan
✓ No-baseline-required approach (high-confidence IOCs only)
✓ IaC-aware queries with your filter logic
✓ Realistic false positive expectations (20-25%)

Creating files:
✓ hunts/H-0027.md (updated hypothesis)
✓ queries/H-0027_geographic_anomalies.kql
✓ queries/H-0027_oauth_suspicious_apps.kql
✓ queries/H-0027_permission_escalation.kql (with IaC filters)
✓ queries/H-0027_aws_key_abuse.spl

All queries include:
- Time bounds (earliest=-90d for Splunk, ago(90d) for KQL)
- Result limits (| head 1000 or | take 1000)
- IaC/automation filters where applicable

Next steps:
1. Add your Terraform/IaC app IDs to environment.md
2. Review and execute queries tomorrow
3. Budget 2 days for full execution and documentation

Would you also like me to:
- Create a checklist for the 2-day execution?
- Add APT29 campaign to a threat tracking file?
```

---

## Results

**Total Time:** 12 minutes from threat intel report to actionable hunt

**Files Created:**
- `hunts/H-0027.md` - Comprehensive but pragmatic hypothesis
- `queries/H-0027_*.kql` and `*.spl` - Five queries with safety bounds
- Ready for 2-day execution

**Key Decisions Made:**
- Simplified from 3-week to 2-day execution (pragmatic scoping)
- Deferred baseline to future work (acceptable trade-off)
- Added IaC-aware filters (prevented major FP source)
- Focused on high-confidence IOCs first

**AI Value-Add:**
1. Connected threat intel to past hunts (H-0019, H-0023)
2. Validated against environment (Azure/AWS usage)
3. Identified FP sources proactively (IaC, CI/CD)
4. Provided realistic execution timeline
5. Adapted plan based on user constraints

**Human Value-Add:**
1. Challenged unrealistic 3-week timeline
2. Questioned baseline requirement (pragmatic prioritization)
3. Caught Terraform FP issue before execution
4. Final scoping decisions (risk vs. effort trade-offs)

---

## Key Takeaways

**APT Report Hunts Are Different:**
- More complex than CVE hunts (multiple TTPs)
- Require environmental understanding (cloud vs. on-prem)
- Need scoping decisions (which TTPs to hunt first)
- Balancing comprehensiveness vs. pragmatism

**AI Strengths:**
- Translating threat intel to actionable hunts
- Cross-referencing past hunts automatically
- Generating query logic quickly
- Providing comprehensive starting point

**Human Judgment Critical For:**
- Scoping (3 weeks → 2 days)
- Prioritization (which TTPs matter most)
- Risk acceptance (higher FPs acceptable for APT threat)
- Environmental context (IaC deployment patterns)

**Process Improvements:**
1. Document IaC service principals in environment.md (caught this late)
2. Document deployment windows (helps with FP filtering)
3. Create "threat actor profile" section in AGENTS.md (APT29 characteristics)
4. Build reusable query templates for cloud hunts

**Time Savings:**
- **Manual Process:** ~90 minutes (understand report, scope TTPs, research queries, write hypothesis)
- **AI-Assisted Process:** ~12 minutes (rapid generation with iterative refinement)
- **Savings:** ~87% reduction

**Next Actions:**
1. Execute 2-day hunt tomorrow
2. Document lessons learned (especially FP patterns)
3. Consider recurring hunt (monthly APT TTP coverage)
4. Share findings with threat intel team (feedback loop)
