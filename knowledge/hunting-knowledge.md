# Threat Hunting Brain - Core Knowledge Base

**Purpose:** This document embeds expert threat hunting knowledge into Claude's reasoning process. Read and internalize these frameworks before generating hypotheses, analyzing findings, or making hunting decisions.

**Last Updated:** 2025-11-17
**Maintained By:** ATHF Framework

---

## Section 1: Hypothesis Generation Knowledge

### Pattern-Based Hypothesis Generation

Hypotheses can emerge from four primary trigger patterns:

#### 1.1 TTP-Driven (Technique-First)

Start with MITRE ATT&CK technique, work backward to observables.

**Pattern:** "Adversaries use [specific technique behavior] to [achieve goal] on [target environment]"

**Example:**

- TTP: T1003.001 (LSASS Memory)
- Hypothesis: "Adversaries access lsass.exe process memory to extract credentials for lateral movement on Windows servers"
- Why good: Specific behavior, clear goal, scoped target

#### 1.2 Actor-Driven (Threat Intel)

Start with adversary profile/campaign, identify likely TTPs for your environment.

**Pattern:** "[Actor/Campaign] will likely [behavior] because [environmental factor/target value]"

**Example:**

- Intel: APT29 phishing campaign targeting healthcare
- Hypothesis: "APT29 will use COVID-themed phishing with macro-enabled documents to gain initial access to clinical workstations"
- Why good: Actor-specific, environment-aware, timely context

#### 1.3 Behavior-Driven (Anomaly Detection)

Start with unusual baseline deviation, form hypothesis about adversary intent.

**Pattern:** "Unusual [observable pattern] may indicate [adversary technique] attempting [objective]"

**Example:**

- Anomaly: Spike in failed SSH attempts across dev servers
- Hypothesis: "Automated credential stuffing attacks target development infrastructure using compromised credential lists" (See H-0001.md)
- Why good: Based on real anomaly, testable, actionable

#### 1.4 Telemetry Gap-Driven (Coverage Improvement)

Start with detection blind spot, hypothesize what adversaries could do undetected.

**Pattern:** "Given lack of [telemetry type] visibility, adversaries could [technique] without detection on [target]"

**Example:**

- Gap: No cron job monitoring on Linux servers
- Hypothesis: "Adversaries establish persistence via malicious cron jobs on Linux systems without triggering alerts" (See H-0002.md)
- Why good: Gap-aware, motivates visibility improvement

### What Makes a Good Hypothesis

**Quality Criteria (Use as Checklist):**

1. **Falsifiable** - Can be proven true or false with data
   - Good: "PowerShell downloads from temp directories indicate malware staging"
   - Bad: "Attackers might use PowerShell" (too vague to test)

2. **Scoped** - Bounded by target, timeframe, or behavior
   - Good: "Domain controllers accessed via non-admin accounts during off-hours"
   - Bad: "Unusual authentication activity" (unbounded)

3. **Observable** - Tied to specific log sources and fields
   - Good: "Sysmon Event ID 10 shows lsass.exe access with 0x1010 permissions"
   - Bad: "Credential theft is occurring" (no observable specified)

4. **Actionable** - Can inform detection or response
   - Good: "Base64-encoded commands in PowerShell logs correlate with C2 callback behavior"
   - Bad: "Attackers are sophisticated" (not actionable)

5. **Contextual** - References environment, threat landscape, or business risk
   - Good: "Given recent Log4j exploitation, webservers will show outbound LDAP connections"
   - Bad: "Generic RCE attempts" (no context)

### Hypothesis Quality Examples

#### Exemplar Good Hypotheses

**H1: Credential Dumping via LSASS Access**
"Adversaries access lsass.exe process memory using mimikatz or similar tools to extract plaintext credentials and Kerberos tickets for lateral movement across Windows domain systems."

Why excellent:

- Falsifiable: Check Sysmon Event ID 10 for lsass.exe TargetImage
- Scoped: Windows domain, specific target process
- Observable: ProcessAccess events with specific GrantedAccess values (0x1010, 0x1fffff)
- Actionable: Can build detection, identify lateral movement candidates
- Contextual: Common post-exploitation technique in domain environments

**H2: SSH Brute Force from Internet Sources**
"Automated tools from internet-based sources attempt password guessing against SSH services, targeting common usernames (root, admin) with high attempt rates (>10 attempts/5min) to gain initial access to Linux systems."

Why excellent:

- Falsifiable: Check auth.log for failed SSH attempts by source IP
- Scoped: External IPs, SSH service, specific threshold
- Observable: Linux auth logs, failed authentication events
- Actionable: Can block source IPs, implement rate limiting
- Contextual: Common internet scanning/attack pattern (See H-0001.md)

**H3: Living-Off-the-Land Binary (LOLBin) Abuse**
"Adversaries execute malicious commands via legitimate Windows binaries (certutil, bitsadmin, mshta) to download payloads or execute code, evading application whitelisting controls on corporate workstations."

Why excellent:

- Falsifiable: Check command-line arguments for download/execute patterns
- Scoped: Legitimate binaries, corporate workstations, specific behaviors
- Observable: Process creation logs with suspicious command-line flags
- Actionable: Alert on unusual usage patterns, restrict parameters
- Contextual: Common AV/EDR evasion technique

**H4: Cron Job Persistence on Linux Servers**
"Adversaries modify crontab files to execute malicious scripts at regular intervals, maintaining persistent access on compromised Linux servers through scheduled task abuse."

Why excellent:

- Falsifiable: Check cron file modifications and scheduled command content
- Scoped: Linux servers, specific persistence mechanism
- Observable: File integrity monitoring on /etc/crontab, /var/spool/cron
- Actionable: Can detect, remediate, baseline legitimate cron jobs
- Contextual: Common Linux persistence technique (See H-0002.md)

**H5: Kerberoasting Service Principal Name (SPN) Enumeration**
"Adversaries with valid domain credentials enumerate service accounts with registered SPNs, request Kerberos TGS tickets, and perform offline password cracking to escalate privileges within the Active Directory environment."

Why excellent:

- Falsifiable: Check Windows Event 4769 (TGS Request) for unusual patterns
- Scoped: Active Directory, specific attack chain steps
- Observable: TGS requests for service accounts from user workstations
- Actionable: Detect unusual TGS volume, audit service account passwords
- Contextual: Common AD privilege escalation technique

#### Anti-Patterns: Bad Hypotheses + Fixes

**Bad H1: "Attackers are using PowerShell"**
Problems:

- Too vague (which attackers? what PowerShell activity?)
- Not falsifiable (PowerShell is used legitimately constantly)
- No scope (all PowerShell everywhere?)
- Not observable (which specific indicators?)

**Fixed:** "Adversaries use obfuscated PowerShell commands with encoded parameters (detected via ScriptBlockLogging Event 4104) to download second-stage payloads from external IPs on Windows endpoints during after-hours periods."

---

**Bad H2: "There might be malware on the network"**
Problems:

- Completely vague
- Not testable
- No behavior specified
- No data source identified

**Fixed:** "Malware beaconing is occurring via periodic HTTP POST requests to non-corporate domains at fixed intervals (every 60 seconds), observable in proxy logs as repetitive connections with small payload sizes (<500 bytes) from infected endpoints."

---

**Bad H3: "Suspicious activity in Active Directory"**
Problems:

- Not specific
- No behavior described
- "Suspicious" is subjective
- No observables

**Fixed:** "Adversaries are conducting AD reconnaissance using BloodHound-style LDAP queries, observable as high-volume LDAP searches (Event 1644) for sensitive attributes (adminCount, member, servicePrincipalName) from non-admin user accounts."

---

**Bad H4: "Cloud accounts might be compromised"**
Problems:

- Vague target
- No specific compromise indicator
- Not testable
- No scope

**Fixed:** "Cloud administrator accounts are accessed from impossible travel locations (sign-in from geographically distant IPs within 1 hour), indicating credential compromise or session hijacking in Azure AD/AWS IAM."

---

**Bad H5: "Lateral movement is happening"**
Problems:

- No technique specified
- No observables
- Too broad
- Not actionable

**Fixed:** "Adversaries are using Pass-the-Hash to move laterally via SMB (T1550.002), observable as NTLM authentication events (Event 4624 Logon Type 3) with matching source/destination workstation names and NTLMv1 protocol usage across multiple endpoints within short timeframes."

### Hunt Seed Conversion Framework

**Hunt Seeds** are raw inputs that need refinement into testable hypotheses.

#### Seed Type 1: Threat Intelligence Report

**Raw Seed:** "APT28 is using Zebrocy malware in recent campaigns"

**Conversion Process:**

1. Extract TTPs: What does Zebrocy do? (C2 via HTTP, uses scheduled tasks, harvests files)
2. Map to your environment: Do we have targets APT28 cares about?
3. Identify observables: What logs would show Zebrocy behavior?
4. Add scope: Which systems, timeframe, priority?

**Refined Hypothesis:** "APT28-affiliated actors may deploy Zebrocy malware on external-facing web servers, establishing C2 via HTTP to rare/suspicious domains and persisting via scheduled tasks, observable in proxy logs (unusual user-agent strings) and Windows Task Scheduler logs (Event 4698)."

#### Seed Type 2: Vulnerability/CVE Announcement

**Raw Seed:** "Log4Shell (CVE-2021-44228) allows RCE in Java applications"

**Conversion Process:**

1. Identify affected systems: What Java apps do we run? (Elasticsearch, Tomcat, custom apps)
2. Determine exploitation observables: What would exploitation look like? (JNDI lookup strings in logs)
3. Consider post-exploitation: What would attacker do next? (Web shell, reverse shell)
4. Scope by criticality: Which systems are most targeted?

**Refined Hypothesis:** "Adversaries are exploiting Log4Shell in our public-facing Elasticsearch instances, observable as HTTP requests containing JNDI LDAP lookup strings (${jndi:ldap://) in User-Agent or request parameters, followed by outbound connections to attacker-controlled LDAP servers."

#### Seed Type 3: SOC Alert / Anomaly

**Raw Seed:** "Alert: Unusual process execution on WEB-SERVER-03"

**Conversion Process:**

1. Characterize anomaly: What's unusual? (Process: whoami.exe from w3wp.exe parent)
2. Determine technique: What attack does this suggest? (Web shell execution, T1505.003)
3. Identify related observables: What else would we see? (File writes, network connections)
4. Scope investigation: Is this isolated or campaign?

**Refined Hypothesis:** "A web shell has been deployed on WEB-SERVER-03, observable as IIS worker process (w3wp.exe) spawning reconnaissance commands (whoami, ipconfig, net user) and potentially establishing outbound connections, indicating post-exploitation activity from successful web application exploitation."

#### Seed Type 4: Detection Gap Identification

**Raw Seed:** "We don't monitor Docker API calls"

**Conversion Process:**

1. Assess risk: What could adversary do undetected? (Deploy malicious containers)
2. Map to technique: Which ATT&CK techniques apply? (T1610 Deploy Container)
3. Hypothesize abuse: How would adversary leverage this?
4. Define what good detection looks like

**Refined Hypothesis:** "Adversaries with access to Docker hosts could deploy malicious containers with privileged flags (--privileged, --pid=host) to escape container isolation and access the underlying host, undetected due to lack of Docker API monitoring."

---

## Section 2: Behavioral Models

### ATT&CK TTP → Observable Log Artifacts

This section maps techniques to specific log evidence. Use this to translate abstract TTPs into concrete hunting targets.

#### Tactic: Initial Access (TA0001)

**T1078 - Valid Accounts**

- Observable: Successful authentication (Windows Event 4624, Linux auth.log, VPN logs)
- Key Fields: username, source IP, logon type, timestamp
- Suspicious Patterns:
  - Logon from unusual geographic location
  - Logon at unusual time (off-hours for that user)
  - Multiple concurrent logons from different IPs
  - First-time logon from external IP
- Benign Baseline: Business hours, corporate IP ranges, consistent source IPs

**T1190 - Exploit Public-Facing Application**

- Observable: Web server logs, IDS/IPS alerts, application errors
- Key Fields: request URI, HTTP method, user-agent, response codes, POST data
- Suspicious Patterns:
  - SQL injection attempts (UNION SELECT, ' OR '1'='1)
  - Directory traversal (../, %2e%2e%2f)
  - Serialization exploits (JNDI, pickle, yaml.load)
  - Unusual POST data sizes or binary content
- Benign Baseline: Normal application traffic patterns, known vulnerability scanners (Shodan)

**T1566.001 - Phishing: Spearphishing Attachment**

- Observable: Email gateway logs, endpoint file creation, process execution
- Key Fields: sender, recipient, attachment name/hash, process parent chain
- Suspicious Patterns:
  - Macro-enabled document from external sender
  - Office process (WINWORD.exe) spawning cmd.exe/powershell.exe
  - File written to Temp folder then executed
  - Suspicious attachment extensions (.scr, .pif, double extensions)
- Benign Baseline: Internal document sharing, known business partners

#### Tactic: Execution (TA0002)

**T1059.001 - Command and Scripting Interpreter: PowerShell**

- Observable: PowerShell operational logs (Event 4103, 4104), process creation (Sysmon Event 1)
- Key Fields: ScriptBlockText, CommandLine, ExecutionPolicy bypass flags
- Suspicious Patterns:
  - Encoded commands (-enc, -EncodedCommand)
  - Download cradles (IEX, Invoke-WebRequest, Net.WebClient)
  - Execution policy bypass (-Exec Bypass, -EP Bypass)
  - Obfuscation (backticks, string concatenation, character substitution)
  - Suspicious parent process (Excel, Outlook, browser)
- Benign Baseline: Admin scripts from specific paths, scheduled task PowerShell, known automation tools

**T1059.003 - Command and Scripting Interpreter: Windows Command Shell**

- Observable: Process creation logs (Sysmon Event 1, Windows Event 4688)
- Key Fields: CommandLine, ParentImage, User
- Suspicious Patterns:
  - cmd.exe with /c flag from non-shell parent
  - Reconnaissance commands (whoami, net user, ipconfig, tasklist)
  - Redirection operators (>, >>, |) from suspicious parent
  - Execution from Office/browser processes
- Benign Baseline: Admin scripts, software installers, scheduled tasks

**T1059.004 - Command and Scripting Interpreter: Unix Shell**

- Observable: Bash history, auditd logs, process execution logs
- Key Fields: command, working_directory, user, parent_process
- Suspicious Patterns:
  - wget/curl downloading to /tmp or /dev/shm
  - chmod +x followed by execution
  - Base64 encoding/decoding in command chain
  - Reverse shell patterns (bash -i >& /dev/tcp/, nc -e)
  - History manipulation (history -c, unset HISTFILE)
- Benign Baseline: Admin tasks from known users, package management, scheduled jobs

#### Tactic: Persistence (TA0003)

**T1053.005 - Scheduled Task/Job: Scheduled Task (Windows)**

- Observable: Windows Event 4698 (Task Created), Sysmon Event 1 (schtasks.exe execution)
- Key Fields: TaskName, ActionCommand, Author, Trigger schedule
- Suspicious Patterns:
  - Task created by non-admin user
  - Task executing from Temp directories
  - Task with encoded PowerShell command
  - Task author different from creator
  - Unusual schedule (every minute, at logon)
- Benign Baseline: System maintenance tasks, software update tasks, known scheduled jobs

**T1053.003 - Scheduled Task/Job: Cron (Linux)**

- Observable: Crontab file modifications, cron execution logs (/var/log/cron)
- Key Fields: user, cron_command, schedule, file_path
- Suspicious Patterns:
  - Cron command containing curl/wget
  - Commands executing from /tmp or /dev/shm
  - Base64 encoding in cron commands
  - Reverse shell syntax (bash -i, nc -e)
  - Non-admin user creating cron jobs (See H-0002.md)
- Benign Baseline: Logrotate, backups, system monitoring, package updates

**T1547.001 - Boot or Logon Autostart Execution: Registry Run Keys**

- Observable: Registry modification logs (Sysmon Event 13), Windows Event 4657
- Key Fields: TargetObject (registry path), Details (value data)
- Suspicious Patterns:
  - HKCU\Software\Microsoft\Windows\CurrentVersion\Run modifications
  - HKLM\...\Run modifications by non-admin
  - Executable in Temp/AppData locations
  - Suspicious file paths or encoded commands
- Benign Baseline: Legitimate software installations, user preferences

#### Tactic: Privilege Escalation (TA0004)

**T1055 - Process Injection**

- Observable: Sysmon Event 8 (CreateRemoteThread), Event 10 (ProcessAccess with suspicious permissions)
- Key Fields: SourceImage, TargetImage, GrantedAccess, CallTrace
- Suspicious Patterns:
  - Suspicious process accessing high-privilege process (lsass, services)
  - Unusual GrantedAccess masks (0x1F0FFF, 0x1410, 0x1FFFFF)
  - CreateRemoteThread from non-system process
  - Missing or invalid digital signatures on SourceImage
- Benign Baseline: EDR/AV tools, debuggers (Visual Studio), system management tools

**T1134 - Access Token Manipulation**

- Observable: Windows Event 4672 (Special Privileges Assigned), API calls logged by EDR
- Key Fields: Subject (user), Privileges (SeDebugPrivilege, SeImpersonatePrivilege)
- Suspicious Patterns:
  - SeImpersonatePrivilege used by IIS worker process
  - SeDebugPrivilege assigned to non-admin user
  - Token manipulation from web shells
- Benign Baseline: Backup software, security tools, SQL Server service accounts

#### Tactic: Credential Access (TA0006)

**T1003.001 - OS Credential Dumping: LSASS Memory**

- Observable: Sysmon Event 10 (ProcessAccess to lsass.exe), memory dumps detected by EDR
- Key Fields: SourceImage, TargetImage (lsass.exe), GrantedAccess, CallTrace
- Suspicious Patterns:
  - Access to lsass.exe with 0x1010 (PROCESS_VM_READ)
  - Access from unsigned binaries
  - Access from Temp/AppData directories
  - Processes named mimikatz, procdump, dumpert (See H-0001.md example translated)
- Benign Baseline: EDR agents, Windows Defender, SCOM monitoring agents

**T1110.001 - Brute Force: Password Guessing**

- Observable: Failed authentication logs (Windows Event 4625, Linux auth failures, app-specific)
- Key Fields: source IP, target username, failure count, timestamp
- Suspicious Patterns:
  - High volume failed attempts (>10) from single source
  - Multiple usernames tried from same source
  - Rapid attempt rate (>1/min indicates automation)
  - Failed attempts followed by successful auth (See H-0001.md)
- Benign Baseline: Legitimate user password mistyping (low count, followed by success)

**T1558.003 - Steal or Forge Kerberos Tickets: Kerberoasting**

- Observable: Windows Event 4769 (Kerberos TGS Request)
- Key Fields: Service Name, Ticket Encryption Type, Client Address
- Suspicious Patterns:
  - TGS requests with RC4 encryption (0x17) for service accounts
  - High volume TGS requests from single user
  - TGS requests for services user doesn't normally access
  - Requests from workstations for unusual SPNs
- Benign Baseline: Normal service access patterns, automated service authentication

#### Tactic: Discovery (TA0007)

**T1087 - Account Discovery**

- Observable: Command execution logs (net user, net group, whoami, id)
- Key Fields: CommandLine, User, ParentImage
- Suspicious Patterns:
  - "net user /domain" from non-admin workstation
  - "whoami /all" after suspicious parent process
  - LDAP queries for all users (dsquery, PowerView)
  - Enumeration shortly after initial access
- Benign Baseline: Admin troubleshooting, help desk activities, security tools

**T1083 - File and Directory Discovery**

- Observable: Process execution (dir, ls), file access patterns
- Key Fields: CommandLine, files_accessed, recursion_depth
- Suspicious Patterns:
  - Recursive directory listing (dir /s)
  - Searching for specific file types (*.pdf, *.docx, password*)
  - Accessing sensitive directories (C:\Users\, /home/, /etc/)
  - Unusual process performing file discovery (web server, Office app)
- Benign Baseline: User file browsing, backup software, indexing services

**T1082 - System Information Discovery**

- Observable: Command execution (systeminfo, uname, ipconfig, ifconfig)
- Key Fields: CommandLine, User, timestamp_relative_to_access
- Suspicious Patterns:
  - Multiple discovery commands in rapid sequence
  - System info gathering from web server process
  - Discovery commands from Office/browser child processes
  - Combination: whoami && ipconfig && systeminfo
- Benign Baseline: Admin diagnostics, monitoring agents, inventory tools

#### Tactic: Lateral Movement (TA0008)

**T1021.001 - Remote Services: Remote Desktop Protocol**

- Observable: Windows Event 4624 (Logon Type 10), Event 4778 (RDP session reconnect)
- Key Fields: source IP, target account, logon timestamp
- Suspicious Patterns:
  - RDP from workstation to workstation (not jump box)
  - RDP at unusual hours for that account
  - RDP session followed by suspicious process execution
  - Multiple RDP connections in short timeframe (lateral spread)
- Benign Baseline: Admin access via jump servers, help desk remote support

**T1021.002 - Remote Services: SMB/Windows Admin Shares**

- Observable: Windows Event 5140 (Share access), 4624 (Logon Type 3), SMB traffic logs
- Key Fields: share_name (\\target\ADMIN$, \\target\C$), source_ip, account
- Suspicious Patterns:
  - Access to ADMIN$ or C$ from non-server sources
  - Lateral movement pattern across multiple hosts
  - Share access followed by service creation (Event 7045)
  - Account used outside normal scope
- Benign Baseline: Admin tools (SCCM, GPO deployment), file servers

**T1021.004 - Remote Services: SSH**

- Observable: SSH authentication logs (auth.log, syslog), network connections
- Key Fields: source_ip, target_user, authentication_method
- Suspicious Patterns:
  - SSH from one internal server to another (lateral movement)
  - SSH key usage from unexpected hosts
  - SSH connections to multiple internal IPs in sequence
  - SSH after suspicious activity on source host
- Benign Baseline: Admin access from jump hosts, orchestration tools (Ansible)

#### Tactic: Collection (TA0009)

**T1005 - Data from Local System**

- Observable: File access logs, process file operations
- Key Fields: file_path, process_name, operation_type
- Suspicious Patterns:
  - Access to Documents, Desktop, sensitive directories
  - File search patterns (dir *.pdf /s)
  - Compression tools (7z.exe, WinRAR.exe) run from unusual locations
  - Archive creation with multiple file types
- Benign Baseline: Backup software, user file management, sync clients

**T1113 - Screen Capture**

- Observable: Process execution logs (screencapture, snippet, screenshot utilities)
- Key Fields: process_name, command_line, output_file_path
- Suspicious Patterns:
  - Screenshot tools from Office/browser child processes
  - Screenshots saved to Temp directories
  - Automated screenshot tools (scheduled or loop)
- Benign Baseline: User-initiated Snipping Tool, legitimate screen recording software

#### Tactic: Command and Control (TA0011)

**T1071.001 - Application Layer Protocol: Web Protocols**

- Observable: Proxy logs, firewall logs, DNS queries, TLS certificates
- Key Fields: destination_domain, user_agent, bytes_out, bytes_in, frequency
- Suspicious Patterns:
  - Regular beaconing (connections every 60s, 300s exactly)
  - Small payload sizes (<500 bytes) repeated
  - Unusual user agents or missing user agents
  - Connections to newly registered domains
  - TLS certificates with mismatched CN or self-signed
- Benign Baseline: Application legitimate traffic, software update checks

**T1573 - Encrypted Channel**

- Observable: Network traffic analysis, TLS session details
- Key Fields: destination, port, encryption_type, certificate_issuer
- Suspicious Patterns:
  - TLS to non-standard ports (not 443)
  - Connections to IP addresses (not domains) over TLS
  - Invalid or self-signed certificates
  - High volume encrypted traffic to suspicious destinations
- Benign Baseline: Corporate VPN, cloud services, SaaS applications

#### Tactic: Exfiltration (TA0010)

**T1041 - Exfiltration Over C2 Channel**

- Observable: Network flow data, proxy logs, firewall logs
- Key Fields: bytes_out, destination, duration, protocol
- Suspicious Patterns:
  - Large upload volumes (>100MB) to non-corporate destinations
  - Upload volume anomaly for user/host
  - Uploads during off-hours
  - Uploads to suspicious TLDs (.xyz, .tk, .ru)
- Benign Baseline: Cloud backups, file sharing services, video conferencing uploads

**T1567.002 - Exfiltration to Cloud Storage**

- Observable: Proxy logs, DNS queries, firewall logs
- Key Fields: destination_domain (dropbox, mega, anonfiles), bytes_out, user
- Suspicious Patterns:
  - Uploads to personal cloud storage from corporate systems
  - First-time access to file sharing services
  - Large uploads to rare cloud storage providers
  - Access to cloud storage from servers (not workstations)
- Benign Baseline: Sanctioned cloud storage (corporate OneDrive, Google Drive)

### Behavior-to-Telemetry Translation Guide

**Question:** "How do I know if this behavior is happening?"
**Answer:** Map behavior → required logs → key fields

| Adversary Behavior | Required Telemetry | Key Fields | Query Starting Point |
|-------------------|-------------------|------------|---------------------|
| Process execution | Sysmon Event 1, Windows Event 4688, auditd exec | process_name, command_line, parent_process, user, hash | index=windows EventCode=1 |
| File creation/modification | Sysmon Event 11, FIM logs, auditd file | file_path, action, process_name, user, hash | index=windows EventCode=11 |
| Registry modification | Sysmon Event 12/13/14, Windows Event 4657 | registry_path, registry_value, process_name | index=windows EventCode=13 |
| Network connection | Sysmon Event 3, netflow, firewall logs | source_ip, dest_ip, dest_port, process_name | index=network dest_port=* |
| DNS query | DNS logs, Sysmon Event 22, proxy logs | query_name, answer, source_ip | index=dns query=* |
| Authentication | Windows Event 4624/4625, auth.log, VPN logs | user, source_ip, logon_type, result | index=auth action=* |
| Service creation | Windows Event 7045, 4697 | service_name, service_path, user | index=windows EventCode=7045 |
| Scheduled task creation | Windows Event 4698, schtasks.exe execution | task_name, action_command, trigger | index=windows EventCode=4698 |
| PowerShell execution | Event 4103, 4104, 4105/4106 | script_block_text, command_line | index=powershell EventCode=4104 |
| Process injection | Sysmon Event 8, 10 | source_image, target_image, granted_access | index=windows EventCode=10 |
| WMI activity | Sysmon Event 19/20/21, Windows Event 5857/5858/5859 | wmi_consumer, wmi_filter, command | index=windows EventCode=19 |
| Driver load | Sysmon Event 6 | image_loaded, signature, signed | index=windows EventCode=6 |

### SPL Query Optimization Best Practices

**Core Principle:** Filter early, let the indexers do the heavy lifting.

When crafting SPL queries for threat hunting, the placement of your filters dramatically impacts performance. Always apply filters as early as possible in your search—ideally in the base search before any pipe commands. This allows Splunk to push filtering logic down to the indexers, reducing the amount of data that needs to be processed by the search heads.

#### The Efficiency Question: One Fat Search vs Multiple Skinny Ones

**Option A: Early Filtering (RECOMMENDED)**

```spl
index=edr_mac sourcetype=process_execution
(process_name="osascript" OR process_name="AppleScript")
(command_line="*duplicate file*" OR command_line="*Cookies.binarycookies*" OR command_line="*NoteStore.sqlite*")
| stats count by _time, hostname, user, process_name, command_line, parent_process
| sort -_time
```

**Why this works:**

- All filters applied in base search (before first pipe)
- Indexers can filter data at source, reducing network transfer
- Search heads receive only relevant events
- CPU cycles focused on meaningful data
- Efficiency score: 💪 10/10

**Option B: Late Filtering (AVOID)**

```spl
index=edr_mac sourcetype=process_execution
| search (process_name="osascript" OR process_name="AppleScript")
| search (command_line="*duplicate file*" OR command_line="*Cookies.binarycookies*" OR command_line="*NoteStore.sqlite*")
| stats count by _time, hostname, user, process_name, command_line, parent_process
| sort -_time
```

**Why this fails:**

- Base search pulls all `process_execution` events (potentially millions)
- Filtering happens post-indexing on search heads
- Massive unnecessary data transfer from indexers
- Search heads waste CPU on irrelevant events
- Like sifting gold through a spaghetti strainer
- Efficiency score: 😩 3/10

#### SPL Query Optimization Rules

**Rule 1: Base Search Should Be Specific**

- Good: `index=windows sourcetype=sysmon EventCode=1 process_name="powershell.exe"`
- Bad: `index=windows | search EventCode=1 | search process_name="powershell.exe"`

**Rule 2: Combine Related Filters with Boolean Logic**

- Good: `(field1="value1" OR field1="value2") (field2="*pattern*")`
- Bad: Multiple sequential `| search` commands

**Rule 3: Time Range Filters Are Free**

- Always specify appropriate time ranges (earliest/latest)
- Indexers handle time filtering natively without performance cost
- Example: `index=windows earliest=-24h latest=now`

**Rule 4: Use NOT Carefully**

- NOT filters still require indexers to evaluate, but better in base search
- Example: `index=windows NOT user="SYSTEM"` (in base search, not `| search NOT`)

**Rule 5: Stats and Aggregations After Filtering**

- Always filter first, then aggregate
- Good: `index=... filters... | stats count by field`
- Bad: `index=... | stats count by field | search count>10` (aggregate then filter)

#### Common Anti-Patterns to Avoid

**Anti-Pattern 1: The Kitchen Sink Search**

```spl
index=* sourcetype=*
| search index=windows
| search EventCode=4688
```

Problem: Searches all indexes then filters (massive waste)

**Anti-Pattern 2: Sequential Search Commands**

```spl
index=windows EventCode=4688
| search process_name="cmd.exe"
| search command_line="*whoami*"
| search user!="SYSTEM"
```

Problem: Each `| search` is a post-processing step (combine into base search)

**Anti-Pattern 3: Stats Then Filter**

```spl
index=windows EventCode=4625
| stats count by src_ip
| search count>20
```

Problem: Aggregates all failed auths, then filters by count (wasteful)
Better: Use `where` after stats or filter before stats if possible

#### Hunt Performance Guidelines

**For Large Environments (>1TB/day):**

- Every filter in base search saves minutes of search time
- Avoid wildcards at start of strings when possible (`*value` slower than `value*`)
- Use tstats for pre-aggregated data when available

**For Complex Hunts:**

- Break into multiple targeted searches rather than one massive search
- Example: Hunt for 5 different TTPs separately, not one search with OR for all

**For Iterative Hunting:**

- Start with broad base search to understand data volume
- Progressively add filters to base search (not as `| search` commands)
- Monitor search job inspector to verify indexer vs search head CPU usage

#### Verification: Is Your Query Efficient?

Check Splunk's Job Inspector after running search:

- **Good:** High % of time in "indexers"
- **Bad:** High % of time in "search head" with simple filters
- **Goal:** Indexers filter 95%+ of events, search heads only process relevant data

**Example Application to Hunt:**

When hunting for suspicious osascript usage (macOS):

```spl
# Efficient Hunt Query
index=edr_mac sourcetype=process_execution
process_name IN ("osascript", "AppleScript")
(command_line="*duplicate file*" OR command_line="*Cookies.binarycookies*" OR command_line="*NoteStore.sqlite*")
earliest=-7d latest=now
| stats count, values(command_line) as commands by hostname, user, parent_process
| where count>5
| sort -count
```

This query:

- Filters at indexer level (process_name, command_line patterns, time)
- Minimizes data transfer to search heads
- Aggregates only relevant events
- Applies post-aggregation filter with `where` (appropriate use case)

### Common Detection Blind Spots by Domain

#### Windows/Active Directory Blind Spots

- **Gap:** PowerShell v2 execution (bypasses ScriptBlock logging)
  - **Risk:** Can execute malicious scripts without logging
  - **Mitigation:** Disable PowerShell v2, log module loads

- **Gap:** Processes without command-line logging (pre-Win10 or not enabled)
  - **Risk:** Can't detect malicious arguments to legitimate tools
  - **Mitigation:** Enable Event 4688 with command-line logging

- **Gap:** NTLM authentication (no visibility into hash usage)
  - **Risk:** Can't detect Pass-the-Hash attacks
  - **Mitigation:** Enable NTLM auditing, force Kerberos where possible

- **Gap:** No EDR on Domain Controllers
  - **Risk:** Can't see attacker activity on most critical systems
  - **Mitigation:** Deploy EDR/Sysmon on DCs, enable full audit policy

#### Linux Blind Spots

- **Gap:** No auditd or auditd rules incomplete
  - **Risk:** No process execution, file access, or network visibility
  - **Mitigation:** Deploy comprehensive auditd ruleset

- **Gap:** Cron job monitoring absent
  - **Risk:** Persistence mechanism undetected (See H-0002.md)
  - **Mitigation:** FIM on crontab files, log cron execution

- **Gap:** No eBPF/kernel-level monitoring
  - **Risk:** Rootkits, kernel module loading undetected
  - **Mitigation:** Deploy Falco, osquery, or kernel monitoring

- **Gap:** Container/Docker activity unlogged
  - **Risk:** Malicious container deployment, escape attempts undetected
  - **Mitigation:** Log Docker API calls, container runtime events

#### Cloud (AWS/Azure/GCP) Blind Spots

- **Gap:** CloudTrail/Azure Activity Logs not centralized or incomplete
  - **Risk:** API calls, privilege escalation, resource modification undetected
  - **Mitigation:** Enable all logging, centralize in SIEM

- **Gap:** Instance/VM telemetry not collected
  - **Risk:** What happens inside the instance is invisible
  - **Mitigation:** Deploy agents (CloudWatch, Azure Monitor, Stackdriver)

- **Gap:** Storage bucket access logging disabled
  - **Risk:** Data exfiltration via direct bucket access undetected
  - **Mitigation:** Enable S3/Blob/GCS access logging

- **Gap:** Identity Provider (Okta, Azure AD) logs not monitored
  - **Risk:** Account compromise, MFA bypass undetected
  - **Mitigation:** Integrate IdP logs into SIEM, alert on anomalies

#### SaaS Application Blind Spots

- **Gap:** Application audit logs not exported
  - **Risk:** Data access, sharing, exfiltration undetected
  - **Mitigation:** Enable and export audit logs (Microsoft 365, Google Workspace)

- **Gap:** Third-party app OAuth grants unmonitored
  - **Risk:** Malicious apps granted access to corporate data
  - **Mitigation:** Monitor OAuth consent events, review app permissions

### Expected "Normal" Baselines by Domain

#### Active Directory Normal Baselines

- **Authentication:**
  - Business hours (7am-7pm) majority of activity
  - Source IPs from corporate ranges, VPN gateway
  - Logon Type 2 (Interactive) from workstations, Type 3 (Network) from servers
  - Failed authentication <3 attempts followed by success (typo correction)

- **Account Activity:**
  - Admin accounts only from jump boxes or specific admin workstations
  - Service accounts: static source IPs, repetitive patterns
  - Standard users: consistent workstation, no server access

- **Group Changes:**
  - Rare events (weekly/monthly)
  - Performed by specific admin accounts
  - During change windows or documented tickets

#### Linux Server Normal Baselines

- **Process Execution:**
  - System daemons (httpd, sshd, cron) from init/systemd parents
  - Admin commands (sudo, apt, yum) during business hours
  - Shell sessions from specific admin users via SSH

- **File Changes:**
  - Config changes (/etc/) during maintenance windows
  - Log rotation predictable times
  - Package updates specific times/days

- **Network Connections:**
  - Web servers: inbound 80/443 from internet, outbound to DB servers
  - DB servers: inbound 3306/5432 from app servers, no outbound internet
  - SSH: inbound from jump hosts only

#### Cloud (AWS) Normal Baselines

- **API Calls:**
  - ec2:DescribeInstances from monitoring tools (predictable source IPs)
  - s3:GetObject from application roles (consistent patterns)
  - iam:GetUser from IdP integration (regular intervals)

- **Resource Creation:**
  - EC2 instances: during business hours by automation or devs
  - S3 buckets: rare events, specific authorized users
  - IAM roles: very rare, during architecture changes

- **Authentication:**
  - Console login: specific admin users, business hours, MFA always
  - API keys: from CI/CD systems, static source IPs
  - Role assumption: from known services (Lambda, ECS)

#### SaaS (Microsoft 365) Normal Baselines

- **Email Activity:**
  - Send patterns: business hours, consistent volume per user
  - Receive patterns: predictable inbound sources
  - Mailbox access: from user's typical devices/IPs

- **File Sharing:**
  - SharePoint/OneDrive: internal sharing common, external sharing rare
  - Link creation: standard users occasional, admins rare
  - Large downloads: individual files common, bulk downloads rare

### Suspicious vs Benign Indicators by Context

| Indicator | Suspicious Context | Benign Context |
|-----------|-------------------|----------------|
| PowerShell.exe execution | Parent: winword.exe, outlook.exe, browser<br>Args: -enc, -exec bypass, download cradle | Parent: sccm.exe, scheduled task<br>Args: known admin script paths |
| cmd.exe /c execution | Parent: w3wp.exe, javaw.exe<br>Commands: whoami, net user, ipconfig | Parent: msiexec.exe, installer<br>Commands: documented install scripts |
| lsass.exe access | Source: unknown binary from Temp<br>Access: 0x1010 (VM_READ) | Source: CrowdStrike, Defender, SCOM<br>Access: legitimate monitoring |
| Failed SSH attempts | Source: External IP<br>Count: 20+ attempts, multiple usernames | Source: Internal jump host<br>Count: 3 attempts, single user (typo) |
| crontab modification | User: www-data, non-admin<br>Command: curl to external IP | User: root<br>Command: /usr/bin/backup-script.sh |
| Scheduled task creation | Author: SYSTEM, Creator: user123<br>Action: powershell.exe from AppData | Author: admin, Creator: admin<br>Action: C:\Scripts\maintenance.ps1 |
| LDAP queries | Source: Workstation<br>Attributes: adminCount, member, SPN | Source: Azure AD Connect server<br>Attributes: standard sync attributes |
| Cloud API calls | Source: New IP, unusual geo<br>Action: iam:CreateAccessKey | Source: Known CI/CD IP<br>Action: ec2:DescribeInstances |
| Large file upload | Destination: mega.nz, anonfiles<br>Size: 5GB, Time: 2am | Destination: corporate SharePoint<br>Size: 100MB, Time: 10am |

---

## Section 3: Pivot Logic

### Standard Artifact Pivot Chains

Pivoting is the process of following evidence from one artifact to related artifacts. Think of it as "pulling the thread" to uncover the full attack chain.

#### Chain 1: Suspicious Process → Full Attack Context

**Starting Point:** Suspicious process execution detected

**Pivot Sequence:**

1. **Process Details**
   - Collect: process_name, command_line, parent_process, user, hash, start_time
   - Questions: Is this process legitimate? Expected parent? Known hash?

2. **Parent Process Chain**
   - Pivot to: All ancestors (grandparent, great-grandparent)
   - Look for: Initial access point (browser, Office, email client, web server)
   - Stop when: Reach system process (services.exe, init) or remote connection (sshd, winlogon)

3. **Child Processes**
   - Pivot to: All processes spawned by suspicious process
   - Look for: Reconnaissance (whoami, net, ipconfig), lateral movement, data staging
   - Flag: Multiple discovery commands = attacker oriented themselves

4. **Network Connections**
   - Pivot to: Network connections initiated by process or its children
   - Look for: External IPs, unusual ports, C2 indicators (regular beaconing)
   - Flag: Connection before/after process start = C2 callback or download

5. **File Operations**
   - Pivot to: Files created, modified, or deleted by process
   - Look for: Staged data (archives in Temp), persistence (startup folders), tools (mimikatz)
   - Flag: Files in Temp then executed = multi-stage attack

6. **Registry Modifications**
   - Pivot to: Registry keys modified by process
   - Look for: Run keys, service entries, debugging tools persistence
   - Flag: Persistence mechanism = attacker plans to return

7. **Authentication Events**
   - Pivot to: Logon events around same timeframe, same user
   - Look for: How did attacker get credentials? Lateral movement targets?
   - Flag: Multiple systems accessed = campaign, not isolated

**Example Pivot Chain (Web Shell):**

```
1. Alert: w3wp.exe spawned cmd.exe
   ↓
2. Pivot to cmd.exe children: whoami, ipconfig, net user /domain
   ↓
3. Pivot to network: cmd.exe parent (w3wp) has connection from external IP
   ↓
4. Pivot to file ops: w3wp wrote file to webroot: /uploads/shell.aspx
   ↓
5. Pivot to file access: shell.aspx accessed via HTTP POST (web logs)
   ↓
6. Pivot to user: after shell, new logon Event 4624 from compromised creds
   ↓
7. Conclusion: Web shell deployed, creds harvested, lateral movement began
```

#### Chain 2: Suspicious Network Traffic → Source Identification

**Starting Point:** Unusual network connection detected (e.g., beaconing, large upload)

**Pivot Sequence:**

1. **Connection Details**
   - Collect: source_ip, dest_ip, dest_port, dest_domain, protocol, bytes
   - Questions: Known malicious destination? Unusual port? Beaconing pattern?

2. **DNS Query**
   - Pivot to: DNS query for dest_domain from source_ip
   - Look for: Domain generation algorithm (DGA) patterns, newly registered domains
   - Flag: Domain registered in last 30 days = likely malicious infra

3. **Source Process**
   - Pivot to: Process on source_ip that initiated connection
   - Look for: Legitimate process (browser) or suspicious (powershell, rundll32)
   - Flag: Unusual process for network activity = infected or malicious

4. **Process Lineage**
   - Pivot to: Parent process chain (see Chain 1)
   - Look for: How did this process start? Scheduled task? User double-click? Remote execution?

5. **User Activity**
   - Pivot to: User logged into source_ip at time of connection
   - Look for: Was user account compromised? Multiple concurrent sessions?

6. **Other Connections**
   - Pivot to: All connections from source_ip in time window
   - Look for: Multiple C2 domains? Lateral movement attempts (SMB to other IPs)?

7. **Cross-Host Correlation**
   - Pivot to: Same dest_ip/domain from other internal hosts
   - Look for: Campaign scale? Multiple infected systems?

#### Chain 3: Compromised Account → Lateral Movement Tracking

**Starting Point:** Account suspected compromised (password spray success, phishing)

**Pivot Sequence:**

1. **Authentication Events**
   - Collect: All logon events (4624) for compromised account
   - Look for: Unusual source IPs, logon types, timeframes

2. **Initial Compromise Host**
   - Pivot to: First suspicious logon source (workstation where phishing occurred)
   - Look for: Credential harvesting tools, keystroke loggers, suspicious processes

3. **Lateral Movement Path**
   - Pivot to: Subsequent logons to other systems (servers, workstations)
   - Look for: Privilege escalation (admin logons), access to critical systems (DCs, databases)
   - Map: source → target1 → target2 → target3 (movement graph)

4. **Actions on Each System**
   - Pivot to: Process execution, file operations, network connections per target
   - Look for: Discovery commands, data access, tool deployment

5. **Credential Harvesting**
   - Pivot to: LSASS access, Kerberos ticket requests, credential files accessed
   - Look for: Additional accounts compromised (domain admin, service accounts)

6. **Persistence Mechanisms**
   - Pivot to: Scheduled tasks, services, registry run keys on accessed systems
   - Look for: How will attacker maintain access?

7. **Data Staging and Exfiltration**
   - Pivot to: Large file operations, compression tools, unusual uploads
   - Look for: What was the objective? Data theft? Ransomware staging?

#### Chain 4: Suspicious File → Infection Chain

**Starting Point:** Suspicious file detected (malware sandbox alert, unusual hash)

**Pivot Sequence:**

1. **File Origin**
   - Collect: File path, hash, creation time, size, signature
   - Questions: Where did file come from? Email attachment? Download? Network share?

2. **File Creation Event**
   - Pivot to: Process that created/wrote the file
   - Look for: Browser download? Email client save? Copy from network share?

3. **File Execution**
   - Pivot to: Process execution of the file (if executed)
   - Look for: Direct user execution? Scheduled task? Auto-start mechanism?

4. **Process Behavior**
   - Pivot to: Child processes, network connections, file operations
   - Look for: Second-stage downloads, C2 callbacks, persistence installation

5. **Related Files**
   - Pivot to: Other files created by same parent process or in same timeframe
   - Look for: Malware components, dropped tools, staged data

6. **Distribution**
   - Pivot to: Same file hash on other systems
   - Look for: How widespread? Network share propagation? Worm behavior?

7. **User Context**
   - Pivot to: User who executed or received file
   - Look for: Targeted user? Phishing campaign? Multiple users affected?

### Pivot Playbooks by Threat Type

#### Ransomware Hunt Pivot Playbook

**Starting Indicator:** File encryption activity, ransom note, suspicious PowerShell

**Pivot Priority Order:**

1. **Identify Patient Zero** (Initial infection host)
   - Look for: Email with malicious attachment, RDP brute force, web exploit
   - Timeframe: 1-7 days before encryption event

2. **Map Lateral Movement**
   - Look for: SMB/RDP connections from patient zero to other systems
   - Flag: Access to admin shares (\\target\C$), remote service execution

3. **Identify Dropped Tools**
   - Look for: PsExec, Cobalt Strike, Mimikatz, file encryption tools
   - Locations: Temp, ProgramData, user AppData

4. **Track Credential Harvesting**
   - Look for: LSASS access, credential file access (SAM, NTDS.dit)
   - Accounts compromised: Likely domain admin for wide impact

5. **Identify Staging and Backup Deletion**
   - Look for: vssadmin delete shadows, bcdedit /set recoveryenabled no
   - File staging: Large archives before encryption

6. **Determine Encryption Scope**
   - Look for: File rename operations (add extension .encrypted, .locked)
   - Systems impacted: File servers, databases, workstations

**Pivot Stop Criteria:**

- Found initial access vector
- Identified all compromised accounts
- Mapped full lateral movement path
- Located all dropped tools
- Determined encryption scope

#### APT Campaign Hunt Pivot Playbook

**Starting Indicator:** Targeted phishing, unusual persistent C2, data exfiltration

**Pivot Priority Order:**

1. **Identify Initial Compromise**
   - Look for: Spearphishing email, watering hole visit, stolen VPN credentials
   - Timeframe: Could be weeks/months before detection

2. **Map Long-Term Persistence**
   - Look for: Services, scheduled tasks, WMI subscriptions, webshells
   - Systems: Multiple systems for redundancy

3. **Track Internal Reconnaissance**
   - Look for: AD queries, network scanning, file share enumeration
   - Goal: Understand what attacker learned about environment

4. **Identify Privilege Escalation**
   - Look for: Kerberoasting, token manipulation, vulnerability exploitation
   - Flag: Domain admin or enterprise admin compromise

5. **Map Data Access**
   - Look for: Access to file shares, databases, email mailboxes
   - Focus: Sensitive data (IP, PII, credentials, business plans)

6. **Track Data Staging and Exfiltration**
   - Look for: Large file copies to attacker-controlled systems, archiving, encryption
   - Destinations: Cloud storage, external IPs, compromised internal systems

7. **Identify All C2 Infrastructure**
   - Look for: Multiple domains/IPs for redundancy, DGA domains, compromised websites
   - Goal: Full IOC list for blocking

**Pivot Stop Criteria:**

- Identified initial access vector and timeframe
- Mapped all compromised systems and accounts
- Located all persistence mechanisms
- Determined what data was accessed/exfiltrated
- Generated complete IOC list

#### Insider Threat Hunt Pivot Playbook

**Starting Indicator:** Data exfiltration, policy violation, access to unauthorized systems

**Pivot Priority Order:**

1. **Identify User and Establish Baseline**
   - Collect: User's normal authentication patterns, data access, work hours
   - Goal: Understand deviation from normal

2. **Track Authentication Anomalies**
   - Look for: Access at unusual times, from unusual locations, to unusual systems
   - Flag: Access to systems outside job role

3. **Identify Data Access**
   - Look for: File access to sensitive directories, database queries, email access
   - Volume: Unusual spike in access (mass download)

4. **Track Data Movement**
   - Look for: Files copied to USB, uploaded to personal cloud, emailed externally
   - Methods: Cloud storage (Dropbox, personal Gmail), USB drives, print to PDF

5. **Identify Covering Tracks**
   - Look for: Log deletion, history clearing, file deletion, encryption
   - Tools: CCleaner, secure delete tools, encryption software

6. **Cross-Reference with HR/Security Events**
   - Look for: Recent termination notice, PIP, access to competitor info, resignation
   - Timeline: Activity spike before departure?

**Pivot Stop Criteria:**

- Established baseline vs. anomalous behavior
- Identified all data accessed
- Tracked all exfiltration methods
- Determined motive and timeline
- Preserved evidence for legal action

### Decision Framework: When to Pivot vs When to Collapse

**Pivot** (Continue Investigation) When:

- New evidence contradicts initial hypothesis → explore alternative explanations
- Finding is high severity (domain admin compromise, data exfil) → full scope required
- Pattern suggests broader campaign → must find all affected systems
- Clear path to next artifact (process → child → network → C2)
- Confidence is medium/high that pivot will yield valuable context
- Still within scope and time budget for hunt

**Collapse Back to Hypothesis** (Stop Pivoting) When:

- Evidence clearly proves/disproves hypothesis → document and conclude
- Reached pivot dead-end (no related artifacts found)
- Evidence is benign/false positive → update hunt notes, refine query
- Diminishing returns (each pivot yields less value)
- Time/resource budget exhausted
- Pivots diverge too far from original hypothesis (scope creep)

**Decision Tree:**

```
Suspicious Finding Detected
    ↓
Is it high severity? (data exfil, domain admin compromise, multiple systems)
    YES → Pivot aggressively, full investigation
    NO → Continue...
    ↓
Is there clear next artifact? (process → parent, IP → domain, user → logons)
    YES → Pivot to next artifact
    NO → Collapse, document findings
    ↓
Does pivot provide new high-value context?
    YES → Continue pivot chain
    NO → Collapse, avoid diminishing returns
    ↓
Are you still within hunt scope/objective?
    YES → Pivot if valuable
    NO → Collapse, document for future hunt
```

**Example Decision: To Pivot or Not**

**Scenario 1: Suspicious PowerShell Execution**

- Finding: powershell.exe -enc <base64> from WINWORD.exe
- Severity: High (document spawning encoded PS = likely malware)
- Decision: **PIVOT**
  1. Decode base64 → reveals download cradle
  2. Pivot to network connections → identifies C2 domain
  3. Pivot to file operations → finds dropped payload
  4. Pivot to other systems → checks if C2 domain contacted elsewhere
  5. Full incident response initiated

**Scenario 2: Unusual File Access**

- Finding: User accessed 50 files in sensitive share (normal: 5-10 per day)
- Severity: Medium (could be insider threat or legitimate project)
- Decision: **PIVOT CAUTIOUSLY**
  1. Check user context → finds user recently joined project requiring access
  2. Cross-reference with access request ticket → approved access for project
  3. Decision: **COLLAPSE** → False positive, benign activity, document baseline change

**Scenario 3: Failed Authentication Spike**

- Finding: 100 failed SSH attempts from external IP
- Severity: Low (internet background noise, no successful auth)
- Decision: **COLLAPSE QUICKLY**
  1. Check for successful auth → None found
  2. Check source IP reputation → Known scanner (Shodan)
  3. Decision: **COLLAPSE** → Benign internet scanning, block IP, document baseline (See H-0001.md pattern)

### Pivot Dead-Ends and When to Stop

**Recognize Pivot Dead-Ends:**

1. **No Related Artifacts Found**
   - Pivoted to network connections → No connections logged
   - Pivoted to child processes → Process exited immediately, no children
   - **Action:** Document gap, move to different artifact type or collapse

2. **Logs Don't Exist or Are Incomplete**
   - Pivoted to file operations → No FIM deployed on system
   - Pivoted to authentication events → Logs rotated, outside retention
   - **Action:** Document telemetry gap for future improvement, collapse

3. **Too Much Noise, No Signal**
   - Pivoted to user activity → Thousands of events, all appear benign
   - Pivoted to network → Normal application traffic, can't distinguish malicious
   - **Action:** Refine pivot query, or collapse and try different angle

4. **Circular Reference (Loop)**
   - Pivoted A → B → C → back to A
   - Example: process → parent → same process (service restart loop)
   - **Action:** Break loop, document finding, collapse

5. **Benign Root Cause Identified**
   - Pivoted back to origin → Finds legitimate admin action
   - Pivoted to user → Confirmed authorized activity with ticket
   - **Action:** Mark false positive, update baseline, collapse

**When to Definitively Stop:**

- Reached root cause (initial access identified)
- Reached known good (legitimate system process, approved action)
- Exhausted relevant pivot options (no more artifacts to check)
- Answered hypothesis question (proved or disproved)
- Evidence clearly shows false positive
- Time budget exhausted (document progress, schedule follow-up if needed)

---

## Section 4: Analytical Rigor

### Confidence Scoring Rubric

**Use this rubric to assign confidence levels to findings. Prevents overconfidence and anchoring bias.**

#### Low Confidence (30-50%)

**Characteristics:**

- Single weak indicator
- High false positive potential
- Missing corroborating evidence
- Behavioral baseline unknown
- Alternative benign explanations exist

**Examples:**

- "Single failed authentication attempt from external IP" → Could be typo, scanner, or attacker
- "PowerShell executed on system" → PowerShell is legitimate tool, need context
- "File created in Temp directory" → Many legitimate processes use Temp

**Language to Use:**

- "May indicate..."
- "Potentially suspicious..."
- "Requires additional investigation..."
- "Could be consistent with..."

**Action:** Continue investigation, gather corroborating evidence, avoid escalation without more data

#### Medium Confidence (55-75%)

**Characteristics:**

- Multiple weak indicators OR one strong indicator
- Some corroborating evidence
- Known attack pattern but alternative explanations possible
- Context suggests suspicious but not definitive

**Examples:**

- "PowerShell with encoded command from suspicious parent (Office app) + no business justification found"
- "20 failed SSH attempts from single external IP within 5 minutes" (See H-0001.md)
- "File created in webroot with .aspx extension by IIS process during unusual request"

**Language to Use:**

- "Likely indicates..."
- "Consistent with..."
- "Strong indication of..."
- "Probably related to..."

**Action:** Escalate for further analysis, implement containment if risk is high, gather additional evidence

#### High Confidence (80-95%)

**Characteristics:**

- Multiple strong indicators
- Corroborating evidence across multiple data sources
- Matches known attack pattern with high fidelity
- Alternative benign explanations ruled out
- Context and timeline support malicious intent

**Examples:**

- "Encoded PowerShell from WINWORD.exe + outbound C2 connection + known-bad domain + file dropped in Temp + child process cmd.exe with reconnaissance commands"
- "LSASS process access by unsigned binary from Temp directory + subsequent Kerberos ticket requests + lateral RDP to multiple servers"
- "Failed SSH brute force followed by successful authentication + suspicious commands (whoami, curl to external IP, cron job creation)"

**Language to Use:**

- "Confirms..."
- "Definitively indicates..."
- "Strong evidence of..."
- "Highly likely..."

**Action:** Escalate to incident response immediately, initiate containment, preserve evidence

#### Very High Confidence (95-100%)

**Characteristics:**

- Overwhelming evidence from multiple sources
- Known malicious artifacts (malware hash, validated IOC)
- Direct observation of adversary tools (mimikatz.exe, Cobalt Strike beacon)
- Confirmed by multiple investigators or tools
- No plausible alternative explanation

**Examples:**

- "Known ransomware hash executed + file encryption operations observed + ransom note created + shadow copies deleted"
- "Confirmed web shell code in webroot + active HTTP requests executing commands + attacker IP traced"
- "mimikatz.exe executed with command-line 'sekurlsa::logonpasswords' + LSASS access logged + subsequent Pass-the-Hash lateral movement confirmed"

**Language to Use:**

- "Confirmed malicious activity"
- "Definitive evidence"
- "Verified compromise"
- "Confirmed IOC match"

**Action:** Full incident response, containment, eradication, legal/regulatory notification if required

### Evidence Strength Framework

**Direct Evidence** (Strongest)

- Observes the actual malicious action
- Example: Process execution log showing mimikatz.exe with credential dumping command
- Example: Packet capture showing exfiltration of sensitive file
- Example: File hash matching known malware in malware database

**Circumstantial Evidence** (Moderate)

- Suggests malicious activity but doesn't directly observe it
- Example: LSASS access by unknown process (suggests credential dumping attempt)
- Example: High-volume failed authentication (suggests brute force attempt)
- Example: Encoded PowerShell command (suggests obfuscation, but could be legitimate)

**Inferential Evidence** (Weaker)

- Requires assumption or correlation to indicate malicious activity
- Example: Network traffic to newly registered domain (could be legitimate new service)
- Example: File in Temp directory (common for both malware and legitimate software)
- Example: Process execution at unusual hour (could be automation or attacker)

**Evidence Combination Strategy:**

- **1 Direct** = High Confidence finding
- **1 Circumstantial + 2-3 Supporting Circumstantial** = Medium-High Confidence
- **Multiple Inferential** = Low-Medium Confidence (requires more investigation)
- **1 Direct + Multiple Circumstantial** = Very High Confidence

### Cognitive Bias Checklist

**Use this checklist to avoid common analytical biases during hunts.**

#### 1. Confirmation Bias

**Risk:** Seeking evidence that confirms hypothesis while ignoring contradictory evidence

**Mitigation:**

- Actively seek disconfirming evidence: "What would prove this is benign?"
- Challenge hypothesis: "Could this be legitimate activity?"
- Review alternative explanations before concluding
- Have peer review findings before high-confidence escalation

**Example:**

- Hypothesis: "This PowerShell execution is malicious"
- Bias: Focus on encoded command, ignore that it's scheduled task from known admin script
- Mitigation: Check process parent, command context, scheduled task author → Find benign

#### 2. Anchoring Bias

**Risk:** Over-relying on first piece of information (initial alert, first indicator)

**Mitigation:**

- Treat initial alert as starting point, not conclusion
- Collect full context before forming opinion
- Re-evaluate initial indicator in light of additional evidence
- Be willing to change assessment as evidence accumulates

**Example:**

- Anchor: "Alert says 'Suspicious PowerShell'"
- Bias: Assume malicious without investigation
- Mitigation: Investigate parent process, command content, user context → May find false positive

#### 3. Availability Bias

**Risk:** Overestimating likelihood of recent or memorable attacks (recency effect)

**Mitigation:**

- Base assessment on evidence, not recent headlines
- Don't assume every phishing attempt is APT just because recent news
- Use base rates: Most alerts are false positives, not sophisticated APT

**Example:**

- Recent news: "Ransomware surge in healthcare"
- Bias: Treat every suspicious file as ransomware precursor
- Mitigation: Assess each finding on its own merits, not recent trends

#### 4. Base Rate Neglect

**Risk:** Ignoring probability of event (most alerts are false positives)

**Mitigation:**

- Remember: ~90%+ of alerts are false positives in most environments
- Apply Bayesian thinking: Prior probability + evidence = posterior probability
- Don't escalate low-quality evidence as high confidence

**Example:**

- Finding: Unusual process execution
- Bias: Assume compromise (ignoring that unusual ≠ malicious usually)
- Mitigation: Check base rate of this process, investigate context

#### 5. Hindsight Bias

**Risk:** After finding root cause, assuming it was "obvious all along"

**Mitigation:**

- Document reasoning process, not just conclusion
- Capture what was unclear at time of analysis
- Learn from difficult-to-detect cases (improve future hunts)

**Example:**

- Post-IR: "The web shell was obviously suspicious"
- Bias: Forgetting that it wasn't obvious until investigation
- Mitigation: Document the actual investigation path, what was hard

#### 6. Attribution Bias

**Risk:** Jumping to conclusions about who/why before sufficient evidence

**Mitigation:**

- Focus on what happened (TTPs, IOCs) before why/who
- Attribution is difficult, requires extensive evidence
- Avoid labeling "APT" or specific group without high confidence

**Example:**

- Finding: Sophisticated lateral movement
- Bias: "This must be nation-state APT"
- Mitigation: Document TTPs, avoid premature attribution, consider alternatives (ransomware gang, insider)

### Suspicious vs Benign Behavior Rules of Thumb

**Use these heuristics for rapid triage (but always investigate further):**

#### Rule 1: Context is King

- **Same behavior, different context = different verdict**
- PowerShell from scheduled task by admin account = Likely benign
- PowerShell from Excel process by user account = Suspicious

#### Rule 2: Timing Matters

- Activity during business hours = Lower suspicion
- Activity at 2am on weekend = Higher suspicion (unless known maintenance)
- But: Advanced attackers work business hours to blend in

#### Rule 3: Parent Process Reveals Intent

- cmd.exe parent = explorer.exe (user double-click) = Context dependent
- cmd.exe parent = w3wp.exe (web server) = Highly suspicious
- cmd.exe parent = svchost.exe (service) = Likely benign

#### Rule 4: Rare ≠ Malicious

- First time user accessed system = Investigate, but not automatically bad
- New process on network = Check purpose, not automatically malicious
- Unusual ≠ Unauthorized

#### Rule 5: Clusters Increase Confidence

- 1 reconnaissance command = Low suspicion
- 5 reconnaissance commands in sequence = High suspicion (whoami && ipconfig && net user && net group)

#### Rule 6: Legitimate Tools Used Maliciously

- certutil.exe downloading file = Suspicious (LOLBin abuse)
- certutil.exe checking certificate = Benign (normal function)
- Same tool, different arguments = different risk

#### Rule 7: Obfuscation = Red Flag

- Clear readable script = Lower suspicion (still investigate)
- Base64 encoded / heavily obfuscated = Higher suspicion
- Adversaries obfuscate, admins rarely do (without good reason)

#### Rule 8: Persistence = Intention to Return

- One-off execution = Could be testing or transient
- Scheduled task / service creation = Adversary planning to persist
- Persistence mechanism = Escalate priority

#### Rule 9: Network Context

- Connection to known corporate domain = Benign
- Connection to newly registered domain (<30 days) = Suspicious
- Connection to IP (not domain) over HTTPS = Suspicious

#### Rule 10: Credential Context

- Service account authentication pattern = Benign (regular interval)
- Service account authentication from workstation = Suspicious
- User account authentication from server = Investigate (admin action or compromise?)

### "Stop vs Continue" Criteria for Hunts

**Stop Hunting (Conclude Hunt) When:**

1. **Hypothesis Answered**
   - Collected sufficient evidence to prove or disprove hypothesis
   - Example: "Hypothesis: Kerberoasting occurring" → No TGS requests with unusual patterns found → Hypothesis disproved

2. **Clear False Positive**
   - Investigation reveals benign activity with documentation
   - Example: "Suspicious PowerShell" → Found scheduled task with approved change ticket → False positive

3. **Time/Resource Budget Exhausted**
   - Allocated hunt time spent, document progress for future iteration
   - Example: 4-hour hunt block complete, findings documented, no critical issues

4. **Diminishing Returns**
   - Additional investigation yields no new valuable information
   - Example: Reviewed 1000 events, all benign, no new patterns emerging

5. **Scope Creep**
   - Investigation diverged from original hypothesis significantly
   - Example: Started hunting SSH brute force, now investigating unrelated DNS anomaly → Refocus or create new hunt

6. **Escalated to Incident Response**
   - Found definitive compromise, now IR team's responsibility
   - Example: Confirmed web shell → IR takes over, hunt concluded as successful detection

**Continue Hunting (Keep Investigating) When:**

1. **Promising Lead Not Fully Explored**
   - Found interesting artifact but haven't pivoted fully
   - Example: Found suspicious process, haven't checked network connections yet

2. **Conflicting Evidence**
   - Some evidence suggests malicious, some suggests benign → Investigate further
   - Example: Unusual authentication pattern but user has legitimate reason → Verify with user

3. **Medium Confidence Finding**
   - Not certain enough to escalate or dismiss
   - Example: Unusual file creation, need to check if file was executed

4. **Pattern Emerging**
   - Multiple weak signals correlating into stronger signal
   - Example: 3 separate minor anomalies on same host within 1 hour → Investigate as potential campaign

5. **High-Risk Scope**
   - Investigating critical systems (DC, financial DB) where thoroughness is required
   - Example: Unusual activity on domain controller → Investigate exhaustively

6. **Learning Opportunity**
   - False positive is complex enough that understanding it improves future hunts
   - Example: New automation process generating alerts → Document for baseline, improve filters

### How to Handle Contradictory Evidence

**Scenario:** Evidence points both toward malicious and benign explanations

**Approach:**

1. **Document Both Sides**
   - List evidence supporting malicious interpretation
   - List evidence supporting benign interpretation
   - Don't ignore contradictions

2. **Seek Tie-Breaker Evidence**
   - What additional artifact would resolve contradiction?
   - Example: Process looks suspicious but if signed by Microsoft = Benign
   - Go find that artifact (check digital signature)

3. **Apply Occam's Razor**
   - Simplest explanation usually correct
   - Malicious: "Attacker compromised system, installed sophisticated evasion, mimicking normal activity"
   - Benign: "Legitimate software behaving as designed"
   - If both fit, benign usually more likely (but verify)

4. **Consider Base Rates**
   - How common is this behavior in environment?
   - If seen 1000 times before and always benign → Likely benign now
   - If first time ever → Requires more investigation

5. **Escalate for Peer Review**
   - When you can't resolve, get second opinion
   - Fresh eyes may spot what you missed
   - Collaboration reduces bias

6. **Document Uncertainty**
   - It's OK to say "Unclear, requires monitoring"
   - Don't force conclusion if evidence insufficient
   - Set up alert for recurrence, revisit with more data

**Example:**

- Finding: PowerShell execution with encoded command
- Malicious Evidence: Encoding, unusual parent process (browser)
- Benign Evidence: Digital signature valid, common user account, business hours
- Tie-Breaker: Decode command → Reveals legitimate software update script
- Conclusion: Benign, update baseline to expect this

---

## Section 5: Framework Mental Models

### Pyramid of Pain (David Bianco)

**Purpose:** Understand the relative value of different indicator types. Focus hunting on high-value indicators that are painful for adversaries to change.

**The Pyramid (Bottom to Top, Least to Most Painful):**

#### Level 1: Hash Values (Trivial Pain)

**Definition:** File hashes (MD5, SHA1, SHA256)

**Value:** LOW

- Adversary can change with trivial effort (recompile, add byte)
- Useful for known malware detection (signature-based)
- Not useful for hunting (adversary already moved on)

**Example:**

- Detecting: "Block SHA256: abc123... (known malware)"
- Evasion: Adversary changes one byte, new hash
- Hunt Value: Only if hunting for specific known malware sample

**ATHF Application:**

- Don't build hunts around hashes unless hunting specific known campaign
- Use hashes for confirmation, not discovery
- Focus on behaviors that produce the files, not files themselves

#### Level 2: IP Addresses (Easy Pain)

**Definition:** Network indicators (IPs, domains)

**Value:** LOW-MEDIUM

- Adversary can change easily (new VPS, domain)
- Useful for blocking active C2
- Limited hunt value (IPs change frequently)

**Example:**

- Detecting: "Block connections to 1.2.3.4 (known C2)"
- Evasion: Adversary spins up new infrastructure at 5.6.7.8
- Hunt Value: Find other systems communicating with known-bad IP (campaign scope)

**ATHF Application:**

- Use IPs to pivot (IP → systems that contacted it)
- Hunt for behavioral patterns (beaconing, not specific IP)
- Don't rely on IP blocklists alone (they're point-in-time)

#### Level 3: Domain Names (Simple Pain)

**Definition:** Domains used for C2, phishing, hosting

**Value:** MEDIUM

- More painful than IPs (cost, registration, reputation)
- Adversary can change but with more effort
- Better hunt value (domains persist longer)

**Example:**

- Detecting: "Block malicious-domain.xyz"
- Evasion: Adversary registers new-domain.tk
- Hunt Value: Find DGA patterns, newly registered domains, suspicious TLDs

**ATHF Application:**

- Hunt for domain characteristics (age, TLD, length, entropy)
- Identify C2 domains by behavior (beaconing pattern), not just name
- Pivot: Find all systems that resolved/connected to suspicious domain (See H-0001.md IP pivot example)

#### Level 4: Network/Host Artifacts (Annoying Pain)

**Definition:** Patterns and artifacts adversary leaves behind

**Value:** MEDIUM-HIGH

- Requires adversary to change tools or techniques
- Examples: User-agent strings, URI patterns, registry keys, file paths

**Example:**

- Detecting: "Alert on User-Agent: 'Mozilla/5.0 (Cobalt Strike)'"
- Evasion: Adversary changes beacon profile, new user-agent
- Hunt Value: Find variations of tools (same family, different config)

**ATHF Application:**

- Hunt for artifact patterns, not exact matches
- Example: PowerShell download cradles (many variations, same pattern)
- Example: Cron job with curl pattern (See H-0002.md)
- Look for file paths (C:\ProgramData\malware.exe), registry keys (Run keys)

#### Level 5: Tools (Challenging Pain)

**Definition:** Attacker tools and utilities

**Value:** HIGH

- Painful to change (development effort, testing, operational familiarity)
- Examples: mimikatz, Cobalt Strike, custom malware families

**Example:**

- Detecting: "Detect Cobalt Strike beacon behavior"
- Evasion: Adversary must switch to different C2 framework (Meterpreter, Sliver)
- Hunt Value: Force adversary to change toolset, disrupt operations

**ATHF Application:**

- Hunt for tool behaviors, not just signatures
- Example: mimikatz → Hunt LSASS access patterns, not binary name
- Example: Cobalt Strike → Hunt named pipe patterns, injection techniques
- Focus on "how the tool works" not "tool file detected"

#### Level 6: TTPs (Tactics, Techniques, Procedures) (Tough Pain)

**Definition:** The adversary's methods and behaviors (MITRE ATT&CK)

**Value:** HIGHEST

- Most painful for adversary to change (requires operational overhaul)
- Fundamental to how adversary operates
- TTPs persist across campaigns, tools, infrastructure

**Example:**

- Detecting: "Detect credential dumping behavior (T1003)"
- Evasion: Adversary must find entirely different technique for credential access
- Hunt Value: Detects adversary regardless of tools, IPs, domains

**ATHF Application:**

- BUILD HUNTS AROUND TTPs, not indicators
- Example: Hunt "process injection behavior" not "specific tool"
- Example: Hunt "living-off-the-land binary abuse" not "specific binary"
- Focus on MITRE ATT&CK techniques (See all ATHF hunt examples)
- This is the CORE PRINCIPLE of ATHF

**Pyramid Application to Hypothesis Generation:**

**Bad Hypothesis (Bottom of Pyramid):**
"Hunt for hash abc123 on endpoints"

- Problem: Trivial to evade, limited value

**Better Hypothesis (Middle of Pyramid):**
"Hunt for connections to domain malicious.xyz"

- Better: Some value, but adversary changes easily

**Best Hypothesis (Top of Pyramid):**
"Hunt for credential dumping via LSASS process access (T1003.001)"

- Best: Behavior-based, hard to evade, high value

**ATHF Mandate:** All hunts should target Level 4-6 of Pyramid (Artifacts/Tools/TTPs), never Level 1-2 (Hashes/IPs) alone.

### Diamond Model (Sergio Caltagirone, Andrew Pendergast, Chris Betz)

**Purpose:** Understand relationships between four core features of intrusion analysis. Use to pivot between detection points and understand adversary operations.

**The Four Points:**

#### 1. Adversary

**Who is conducting the activity?**

- Attribution (often difficult, not always necessary)
- Adversary capabilities, motivations, intent
- Operator (human) and Customer (who benefits)

**Hunt Application:**

- Usually unknown at hunt start
- May be inferred from TTPs (APT29 uses technique X)
- Don't fixate on attribution; focus on stopping behavior

#### 2. Capability

**What tools, malware, exploits are used?**

- Malware families, tools (mimikatz, Cobalt Strike)
- Exploits (Log4Shell, EternalBlue)
- TTPs and techniques

**Hunt Application:**

- Start here when hunting tool-specific behavior
- Example: "Hunt for Cobalt Strike beaconing"
- Pivot: Capability → Infrastructure (what C2 does it connect to?)

#### 3. Infrastructure

**What systems, IPs, domains does adversary use?**

- C2 servers, phishing domains, compromised websites
- Hosting providers, IP ranges, ASNs

**Hunt Application:**

- Pivot point for scope assessment
- Example: Found malicious domain → Find all systems that contacted it
- Infrastructure is often shared across campaigns (hunt for reuse)

#### 4. Victim

**Who or what is being targeted?**

- Targeted systems, users, data
- Organizations, industries, geographies

**Hunt Application:**

- Understand what adversary wants (target selection)
- Example: All victims are finance dept → Adversary wants financial data
- Prioritize protection of high-value targets

**The Model Relationships:**

```
        Adversary
           / \
          /   \
         /     \
   Capability—Infrastructure
         \     /
          \   /
           \ /
         Victim
```

**Core Insight:** These four features are connected. Finding one allows you to pivot to others.

**Pivot Examples:**

**Starting Point: Capability (Malware detected)**

- Capability → Infrastructure: What C2 does this malware connect to?
- Capability → Victim: What other systems have this malware?
- Capability → Adversary: What group is known to use this malware?

**Starting Point: Infrastructure (Suspicious domain detected)**

- Infrastructure → Victim: What systems in our network contacted this domain?
- Infrastructure → Capability: What malware uses this C2?
- Infrastructure → Adversary: Who operates this infrastructure?

**Starting Point: Victim (Compromised user account)**

- Victim → Capability: What tools were used to compromise account?
- Victim → Infrastructure: Where did malicious authentication come from?
- Victim → Adversary: Why was this user/system targeted? (job role, access)

**ATHF Application:**
Use Diamond Model to structure pivots:

- Start with what you know (usually Capability or Infrastructure from detection)
- Pivot to Victim (scope of compromise)
- Pivot to Infrastructure (other adversary resources)
- Pivot to Capability (other tools adversary has)
- Optionally: Consider Adversary (attribution, if relevant)

**Example Hunt Using Diamond Model:**

1. **Start:** Suspicious PowerShell execution detected (Capability)
2. **Pivot:** PowerShell connects to suspicious domain (Infrastructure)
3. **Pivot:** Find all internal systems that contacted same domain (Victim scope)
4. **Pivot:** Examine those systems for same capability (other malware instances)
5. **Analyze:** What do victim systems have in common? (target selection pattern)
6. **Optional:** Do TTPs match known adversary? (Attribution)

### Cyber Kill Chain (Lockheed Martin)

**Purpose:** Understand attack progression stages. Hunt at early stages to prevent later-stage impact.

**The Seven Stages:**

#### 1. Reconnaissance

**Adversary researches target**

- Examples: Port scanning, OSINT, social media scraping, employee enumeration
- Hunt Opportunity: External honeypots, perimeter scanning detection (often not internal hunt)

#### 2. Weaponization

**Adversary creates exploit/payload**

- Examples: Malicious document creation, exploit development
- Hunt Opportunity: Limited (happens on adversary infrastructure)

#### 3. Delivery

**Adversary delivers weapon to target**

- Examples: Phishing email, watering hole, exploit kit
- **Hunt Opportunity: HIGH** - Detect delivery before execution
- Observables: Email attachments, suspicious downloads, web exploitation

#### 4. Exploitation

**Weapon exploits vulnerability**

- Examples: Macro execution, vulnerability trigger, user double-click
- **Hunt Opportunity: HIGH** - Detect exploitation before persistence
- Observables: Process execution from Office apps, web server spawning shells

#### 5. Installation

**Adversary establishes persistence**

- Examples: Scheduled tasks, services, registry run keys, cron jobs
- **Hunt Opportunity: CRITICAL** - Detect before long-term access established
- Observables: Scheduled task creation, service installation, cron modifications (See H-0002.md)

#### 6. Command and Control (C2)

**Adversary establishes communication channel**

- Examples: HTTP beaconing, DNS tunneling, encrypted channels
- **Hunt Opportunity: HIGH** - Detect before adversary takes action
- Observables: Beaconing patterns, unusual network connections, DGA domains

#### 7. Actions on Objectives

**Adversary achieves goal**

- Examples: Data exfiltration, ransomware encryption, system destruction
- **Hunt Opportunity: LAST RESORT** - Detect damage in progress, minimize impact
- Observables: Large data uploads, file encryption, credential harvesting

**ATHF Hunt Prioritization by Stage:**

**Highest Value Hunts:**

- **Delivery (Stage 3):** Phishing detection, exploit detection
- **Exploitation (Stage 4):** Suspicious process execution, vulnerability exploitation
- **Installation (Stage 5):** Persistence mechanism detection
- **C2 (Stage 6):** Beaconing detection, network anomalies

**Lower Value (Later Stage):**

- **Actions on Objectives (Stage 7):** Damage already in progress, but can minimize impact

**Hunt Strategy:**

- Build detections for Stages 3-6 (Delivery through C2)
- Earlier detection = more adversary effort wasted
- "Shift left" → Catch adversaries as early as possible

**Example: SSH Brute Force Hunt (H-0001.md) Mapped to Kill Chain:**

- Stage 3 (Delivery): SSH authentication attempts delivered
- Stage 4 (Exploitation): Password guessing exploitation attempt
- Stage 5 (Installation): If successful, adversary establishes SSH key persistence
- Hunt catches at Stage 3-4, before Installation (early detection)

**Example: Cron Persistence Hunt (H-0002.md) Mapped to Kill Chain:**

- Assumes adversary already at Stage 5 (Installation via cron)
- Hunt detects persistence before Stage 6 (C2) or Stage 7 (Actions)
- Still valuable, but later stage than ideal

**ATHF Recommendation:**

- Focus hypothesis generation on Stages 3-6
- Build hunts that catch adversaries before Actions on Objectives
- When you detect Stage 7, pivot back to understand Stages 3-6 (IR mode)

### Hunt Maturity Model

**Purpose:** Understand your organization's hunting maturity. Set realistic goals for capability development.

**Maturity Levels (HMM):**

#### HMM0: Initial (Ad-Hoc)

**Characteristics:**

- Reactive hunting, triggered by alerts or incidents
- No formal process, inconsistent execution
- Limited documentation
- Tools: Manual queries, basic SIEM searches

**ATHF Equivalent:** Not using framework, hunting when incidents occur

**Progression Goal:** Establish process, begin documentation (adopt ATHF Level 1)

#### HMM1: Minimal (Documented)

**Characteristics:**

- Documented hunt hypotheses (LOCK pattern)
- Repeatable process exists
- Learning captured in hunt documentation
- Still largely reactive, but systematic

**ATHF Equivalent:** ATHF Level 1 (Documented) - Using templates, writing hunts

**Progression Goal:** Move to regular cadence, build hypothesis backlog

#### HMM2: Procedural (Scheduled)

**Characteristics:**

- Regular hunt cadence (weekly, monthly)
- Hunt hypothesis backlog maintained
- Team collaboration on hunts
- Metrics tracked (hunts completed, findings)

**ATHF Equivalent:** ATHF Level 2 (Searchable) - AI-assisted, memory-enabled

**Progression Goal:** Proactive hunting, threat-informed priorities

#### HMM3: Innovative (Proactive)

**Characteristics:**

- Threat intelligence driving hunt priorities
- Proactive TTP coverage (not just reactive)
- Hunt outcomes feed detection engineering
- Continuous improvement of hunt techniques

**ATHF Equivalent:** ATHF Level 3 (Generative) - AI generates hunt ideas based on TI

**Progression Goal:** Automation of routine hunts, advanced analytics

#### HMM4: Leading (Automated)

**Characteristics:**

- Automated hunt execution for routine hypotheses
- Advanced analytics (ML, behavioral baselining)
- Hunt program influences industry (research, sharing)
- Adversary TTP research informs hunt development

**ATHF Equivalent:** ATHF Level 4 (Agentic) - Automated hunt execution, AI orchestration

**Progression Goal:** Maintain leadership, continuous innovation

**ATHF Maturity Alignment:**

| ATHF Level | HMM Level | Key Capability |
|-----------|-----------|---------------|
| Level 0 (Manual) | HMM0 (Initial) | Ad-hoc hunting |
| Level 1 (Documented) | HMM1 (Minimal) | Process + templates |
| Level 2 (Searchable) | HMM2 (Procedural) | Memory + AI assistance |
| Level 3 (Generative) | HMM3 (Innovative) | AI-generated hunts |
| Level 4 (Agentic) | HMM4 (Leading) | Automated execution |

**Maturity Progression Strategy:**

- Start at Level 1: Use ATHF templates, document hunts
- Grow to Level 2: Enable AI memory, search past hunts
- Advance to Level 3: AI generates hypotheses from TI
- Reach Level 4: Automate routine hunts, focus humans on novel hunts

**Current ATHF User:** Likely Level 1-2 (using this knowledge base = Level 2 capability)

### Data Quality Dimensions

**Purpose:** Assess data quality for hunting. Poor data quality = unreliable findings.

**Five Dimensions:**

#### 1. Completeness

**Definition:** Do we have all the data we need?

**Assessment Questions:**

- Are all systems sending logs?
- Are all relevant log sources ingested (process, network, auth)?
- Are there coverage gaps (some servers not monitored)?

**Impact on Hunting:**

- Incomplete data = blind spots
- Can't hunt TTPs where telemetry doesn't exist
- May miss adversary activity on unmonitored systems

**Example:**

- Hypothesis: "Hunt for lateral movement via SMB"
- Problem: Only 60% of servers logging SMB access
- Impact: Can only hunt 60% of environment, false confidence

**ATHF Application:**

- Check environment.md for known gaps before hunting
- Document telemetry gaps found during hunting
- Prioritize visibility improvements

#### 2. Timeliness

**Definition:** How quickly does data arrive for analysis?

**Assessment Questions:**

- What is log ingestion latency? (Real-time? 5 min? 1 hour?)
- Are there delays in specific data sources?
- Can we hunt "right now" or only historical data?

**Impact on Hunting:**

- Delayed data = slower detection
- Real-time hunting requires real-time ingestion
- IR response time depends on data timeliness

**Example:**

- Hypothesis: "Detect active C2 beaconing"
- Problem: Network logs delayed 30 minutes
- Impact: By the time we see beaconing, adversary already took action

**ATHF Application:**

- Understand data latency when scoping hunt timeframes
- Near real-time hunts require real-time data sources
- Historical hunts less affected by latency

#### 3. Fidelity

**Definition:** Level of detail in data (granularity)

**Assessment Questions:**

- Is command-line logging enabled? (High fidelity)
- Are only summary events logged? (Low fidelity)
- Do we have packet captures? (Highest fidelity)

**Impact on Hunting:**

- High fidelity = can detect specific behaviors
- Low fidelity = only coarse-grained detection
- Fidelity determines what hypotheses are testable

**Example:**

- Hypothesis: "Hunt for encoded PowerShell commands"
- High Fidelity: ScriptBlock logging (Event 4104) shows full command
- Low Fidelity: Only Event 4103 (module logging), can't see command
- Impact: Need high fidelity to test hypothesis

**ATHF Application:**

- Match hypothesis to available data fidelity
- Don't build hypothesis requiring high fidelity if you have low fidelity data
- Prioritize data source improvements for high-value hunts

#### 4. Accuracy

**Definition:** Is the data correct and reliable?

**Assessment Questions:**

- Are timestamps accurate? (NTP sync?)
- Are field mappings correct? (source_ip actually source?)
- Are there data collection errors? (truncated logs, parsing failures)

**Impact on Hunting:**

- Inaccurate data = false positives/negatives
- Timestamp errors break timeline analysis
- Field mapping errors cause missed detections

**Example:**

- Hypothesis: "Correlate network connection with process execution"
- Problem: System clocks out of sync by 5 minutes
- Impact: Can't accurately correlate, false negatives

**ATHF Application:**

- Validate data accuracy before trusting findings
- If timeline doesn't make sense, check timestamps
- Test queries on known-good data to verify accuracy

#### 5. Consistency

**Definition:** Is data format and collection uniform across environment?

**Assessment Questions:**

- Do all Windows systems log the same events?
- Are Linux systems using same syslog format?
- Are cloud environments logging consistently?

**Impact on Hunting:**

- Inconsistent data = hunt only works on subset of systems
- Query works on some hosts, not others (frustrating)
- Can't build universal detection rules

**Example:**

- Hypothesis: "Hunt for Sysmon Event ID 10 (ProcessAccess)"
- Problem: Sysmon deployed on only 50% of Windows endpoints
- Impact: Hunt only covers half the environment, inconsistent

**ATHF Application:**

- Document which systems have which data sources (environment.md)
- Scope hunts to systems with consistent data
- Standardize logging for future hunt coverage

**Data Quality Pre-Hunt Checklist:**

Before hunting, verify:

- [ ] **Completeness:** All required data sources present?
- [ ] **Timeliness:** Data latency acceptable for hunt timeframe?
- [ ] **Fidelity:** Data detail sufficient to test hypothesis?
- [ ] **Accuracy:** Data reliable (timestamps, fields correct)?
- [ ] **Consistency:** All target systems logging uniformly?

If data quality is insufficient:

- **Option 1:** Refine hypothesis to match available data quality
- **Option 2:** Improve data quality first, then hunt
- **Option 3:** Document gap, hunt partial environment

---

## Using This Knowledge Base

**How to Apply These Five Sections:**

**Before Generating Hypothesis:**

- Review Section 1 (Hypothesis Generation) for patterns and quality criteria
- Review Section 2 (Behavioral Models) to map TTP → Observables
- Review Section 5 (Frameworks) - Apply Pyramid of Pain (target TTPs not hashes)

**During Hunt Execution:**

- Review Section 3 (Pivot Logic) to follow evidence chains
- Review Section 4 (Analytical Rigor) to assess confidence and avoid bias

**After Hunt Completion:**

- Review Section 4 (Analytical Rigor) to score confidence appropriately
- Review Section 5 (Frameworks) - Assess maturity, data quality, kill chain stage

**When Stuck or Uncertain:**

- Re-read relevant section
- Apply decision frameworks (pivot vs collapse, confidence scoring)
- Check for cognitive biases

**Integration with ATHF Files:**

- This document = The "brain" (knowledge)
- AGENTS.md = The "instructions" (how to use the brain)
- templates/HUNT_LOCK.md = The "format" (how to document)
- hunts/ = The "memory" (past experiences)
- environment.md = The "context" (your specific environment)

**Final Principle:**
Think like a threat hunter who has internalized these frameworks. Don't just mention "Pyramid of Pain" - apply it. Don't just say "high confidence" - show why using the rubric. This knowledge base should become second nature in your analytical reasoning.

---

**End of Hunting Brain Knowledge Base**
