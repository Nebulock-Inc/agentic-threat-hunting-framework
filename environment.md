# Environment Profile

**Last Updated:** 2026-01-13
**Review Cadence:** Quarterly
**Maintained By:** Security Operations Team

> **⚠️ SENSITIVE DATA WARNING**
> This file contains technical details about your organization's infrastructure. Treat it with the same security posture as your hunt documentation.

---

## Purpose

This file captures the technical environment context that informs threat hunting decisions. It helps answer:

- What technologies are we running that might be vulnerable?
- Where should we focus hunting efforts based on our attack surface?
- What data sources and tools do we have available for hunts?

---

## Security & Monitoring Tools

### SIEM / Log Aggregation

- **Platform:** SIEM/Log Aggregation Platform (Splunk, Elasticsearch, Sentinel, etc.)
- **Version:** [Specify your platform version]
- **Coverage:**
  - Windows Security Event Logs (Event IDs 4624, 4625, 4648, 4768, 4769, 4771, etc.)
  - Windows System and Application Logs
  - Endpoint telemetry (process execution, network connections, file events)
  - Network flow data (NetFlow, firewall logs)
  - Authentication logs (Active Directory, VPN, cloud services)
  - Application logs (web servers, databases, business applications)
- **Retention:** 90 days hot/warm storage, 1 year cold storage
- **Query Access:**
  - Web interface for interactive querying
  - REST API available for programmatic access
  - CLI tools or SDK for automated hunts
- **Data Collections/Indexes:**
  - `security_events` - Primary security telemetry (12M+ events)
  - `windows_logs` - Windows Event Logs
  - `endpoint_data` - EDR/endpoint telemetry
  - `network_logs` - Network flow and firewall logs
  - `auth_logs` - Authentication events across all sources
- **Integration Guide:** Document platform-specific query syntax in `integrations/[platform]/AGENTS.md`
- **Common Fields:**
  - Windows: `EventCode`, `ComputerName`, `User`, `LogonType`, `SourceNetworkAddress`, `TargetUserName`
  - Network: `src_ip`, `dest_ip`, `src_port`, `dest_port`, `protocol`, `action`
  - Endpoint: `process_name`, `parent_process`, `command_line`, `user`, `dest`
- **Documentation:** [Link to internal docs, query examples in `queries/` directory]

### EDR / Endpoint Security

- **Product:** [To be configured - e.g., CrowdStrike Falcon, Microsoft Defender, Carbon Black]
- **Version:** [To be configured]
- **Deployment:** [To be configured - % of endpoints covered, OS types]
- **Telemetry:** Process execution, network connections, file events, registry modifications
- **API Access:** [To be configured]
- **Documentation:** [To be configured]

### Network Security

- **Firewalls:** [To be configured - vendor/model]
- **IDS/IPS:** [To be configured]
- **Flow Data:** NetFlow logs ingested into SIEM
- **Packet Capture:** [To be configured - limited PCAP availability]
- **Documentation:** [To be configured]

### Cloud Security

- **Cloud Providers:** [To be configured - AWS, Azure, GCP]
- **Security Services:** [To be configured - CloudTrail, Azure Monitor, etc.]
- **Documentation:** [To be configured]

### Identity & Access

- **Identity Provider:** Active Directory (on-premises)
- **Domain Controllers:** Multiple DCs logging authentication events to SIEM
- **MFA Solutions:** [To be configured]
- **PAM Tools:** [To be configured]
- **Authentication Logs:** Centralized in SIEM `windows_logs` and `auth_logs` collections
- **Key Event IDs:**
  - 4624 - Successful logon
  - 4625 - Failed logon
  - 4648 - Logon using explicit credentials
  - 4768 - Kerberos TGT requested
  - 4769 - Kerberos service ticket requested
  - 4771 - Kerberos pre-authentication failed
- **Documentation:** [To be configured]

### Other Security Tools

- **Vulnerability Scanners:** [To be configured]
- **Asset Management:** [To be configured]
- **Threat Intelligence:** [To be configured]
- **SOAR/Automation:** [To be configured]

---

## Technology Stack

### Operating Systems

- **Servers:**
  - Windows: Server 2016, Server 2019, Server 2022
  - Linux: [To be configured - distributions]

- **Workstations:**
  - Windows: Windows 10, Windows 11
  - macOS: [To be configured if applicable]
  - Linux: [To be configured if applicable]

- **Mobile:**
  - [To be configured]

### Development Stack

- **Languages:** [To be configured - Python, JavaScript, Java, etc.]
- **Web Frameworks:** [To be configured]
- **API Frameworks:** [To be configured]

### Databases & Data Stores

- **Relational:** [To be configured - SQL Server, PostgreSQL, etc.]
- **NoSQL:** [To be configured]
- **Caching:** [To be configured]
- **Data Warehouses:** [To be configured]

### Infrastructure & Platforms

- **Cloud Platforms:** [To be configured - AWS, Azure, GCP services]
- **Containers & Orchestration:** [To be configured]
- **CI/CD:** [To be configured]

### Networking

- **Network Architecture:** [To be configured - segmentation, VLANs, DMZ]
- **Load Balancers:** [To be configured]
- **DNS:** [To be configured]
- **VPN/Remote Access:** [To be configured]
- **Jump Boxes:** [To be configured - List known jump box hostnames/IPs for RDP hunting]

### Applications & Services

- **Productivity:**
  - Email: [To be configured]
  - Collaboration: [To be configured]
  - File Sharing: [To be configured]

- **Development:**
  - Version Control: [To be configured]
  - Project Management: [To be configured]
  - Documentation: [To be configured]

- **Business Applications:**
  - [To be configured]

---

## Internal Documentation & Resources

### Architecture Documentation

- **System Architecture:** [To be configured - link to diagrams]
- **Network Diagrams:** [To be configured]
- **Data Flow Diagrams:** [To be configured]
- **Security Architecture:** [To be configured]

### Operational Documentation

- **Runbooks:** [To be configured]
- **Incident Response Plans:** [To be configured]
- **DR/BCP Plans:** [To be configured]
- **Change Management:** [To be configured]

### Asset & Configuration Management

- **CMDB/Asset Inventory:** [To be configured]
- **Configuration Management:** [To be configured]
- **Service Catalog:** [To be configured]

---

## Access & Credentials

> **Do not store actual credentials here.** Document where to find them.

- **Secret Management:** [To be configured - Vault, AWS Secrets Manager, etc.]
- **Service Accounts:** [To be configured - location of hunt service account credentials]
- **API Keys:** [To be configured]
- **SIEM Access:** [To be configured - role-based access, API tokens]
- **Documentation:** [To be configured]

---

## Known Gaps & Blind Spots

Document areas where visibility is limited:

- **Unmonitored Systems:** [To be configured - legacy systems, contractor networks]
- **Data Source Gaps:** [To be configured - logs not collected]
- **Tool Limitations:** [To be configured - EDR coverage gaps]
- **Third-Party Services:** [To be configured - SaaS apps without logging]
- **RDP Visibility:** [To be configured - Are all RDP sessions logged? Any jump box exemptions?]

---

## Priority TTPs (Based on Threat Model)

**High Priority Tactics:**
- TA0006 - Credential Access (password spraying, credential dumping)
- TA0008 - Lateral Movement (RDP abuse, pass-the-hash, pass-the-ticket)
- TA0004 - Privilege Escalation (token manipulation, UAC bypass)
- TA0003 - Persistence (scheduled tasks, services, registry run keys)
- TA0010 - Exfiltration (data staging, exfil over C2 channel)

**Threat Model Focus:**
- Ransomware operators (initial access → lateral movement → encryption)
- Insider threats (data exfiltration, sabotage)
- External attackers (phishing → credential theft → lateral movement)

---

## Maintenance Notes

### Review Checklist (Quarterly)

- [ ] Verify SIEM data collections and data sources are current
- [ ] Add new log sources integrated into SIEM
- [ ] Remove decommissioned systems
- [ ] Update tool coverage percentages
- [ ] Refresh internal documentation links
- [ ] Validate SIEM API access still works
- [ ] Update jump box allowlist for RDP hunts
- [ ] Review priority TTPs based on recent incidents

### Change Log

- **2026-01-13:** Initial creation with SIEM configuration for RDP lateral movement hunting
