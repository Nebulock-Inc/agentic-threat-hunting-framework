# Environment Profile

**Last Updated:** YYYY-MM-DD
**Review Cadence:** Quarterly
**Maintained By:** [Team/Individual Name]

> **⚠️ SENSITIVE DATA WARNING**
> This file contains technical details about your organization's infrastructure. Treat it with the same security posture as your hunt documentation. Consider what details should remain in private internal systems versus this repository.

---

## Purpose

This file captures the technical environment context that informs threat hunting decisions. It helps answer:

- What technologies are we running that might be vulnerable?
- Where should we focus hunting efforts based on our attack surface?
- What data sources and tools do we have available for hunts?

**How this file supports hunting:**

- **Level 0-1 (Manual):** Reference this when planning hunts to understand available data sources and potential targets
- **Level 2 (Memory):** Grep this file to remember what tech we have when reviewing past hunts or CVE alerts
- **Level 3+ (Automated):** Agents use this context to auto-generate hunt ideas, cross-reference CVEs, and prioritize targets

---

## Security & Monitoring Tools

### SIEM / Log Aggregation

- **Product:** [e.g., Splunk Enterprise, Elastic Security, Microsoft Sentinel]
- **Version:**
- **Coverage:** [What logs are ingested - endpoints, network, cloud, applications]
- **Retention:** [How long logs are kept]
- **Query Access:** [API available? Direct database access?]
- **Documentation:** [Link to internal wiki/runbooks]

### EDR / Endpoint Security

- **Product:** [e.g., CrowdStrike Falcon, Microsoft Defender, SentinelOne]
- **Version:**
- **Deployment:** [% of endpoints covered, OS types]
- **Telemetry:** [Process execution, network, file events]
- **API Access:** [Available for automated queries?]
- **Documentation:**

### Network Security

- **Firewalls:** [Vendor/model, management interfaces]
- **IDS/IPS:** [Snort, Suricata, commercial products]
- **Network TAPs/SPAN:** [Where traffic is monitored]
- **Flow Data:** [NetFlow, IPFIX, Zeek logs]
- **Packet Capture:** [Full PCAP availability, retention]
- **Documentation:**

### Cloud Security

- **Cloud Providers:** [AWS, Azure, GCP]
- **Security Services:** [CloudTrail, Azure Monitor, GCP Cloud Logging]
- **CSPM Tools:** [Wiz, Prisma Cloud, native tools]
- **Container Security:** [Falco, Aqua, Sysdig]
- **Documentation:**

### Identity & Access

- **Identity Provider:** [Active Directory, Okta, Azure AD]
- **MFA Solutions:** [Duo, Okta, hardware tokens]
- **PAM Tools:** [CyberArk, BeyondTrust]
- **Authentication Logs:** [Where are auth events logged?]
- **Documentation:**

### Other Security Tools

- **Vulnerability Scanners:** [Nessus, Qualys, Rapid7]
- **Asset Management:** [ServiceNow CMDB, custom inventory]
- **Threat Intelligence:** [Feeds, platforms, sharing communities]
- **SOAR/Automation:** [Automation platforms, orchestration tools]

---

## Technology Stack

### Operating Systems

- **Servers:**
  - Linux: [Distributions, versions - e.g., Ubuntu 22.04, RHEL 8]
  - Windows: [Server 2019, Server 2022]
  - Other: [BSD, proprietary systems]

- **Workstations:**
  - Windows: [10, 11]
  - macOS: [Versions]
  - Linux: [Desktop distributions]

- **Mobile:**
  - iOS: [MDM solution, version requirements]
  - Android: [MDM solution, BYOD policy]

### Development Stack

- **Languages:** [Python, JavaScript, Java, Go, C#, Ruby, PHP]
- **Web Frameworks:** [React, Angular, Django, Flask, Spring Boot, .NET]
- **API Frameworks:** [FastAPI, Express, REST, GraphQL]
- **Mobile Frameworks:** [React Native, Flutter, native iOS/Android]

### Databases & Data Stores

- **Relational:** [PostgreSQL, MySQL, SQL Server, Oracle]
- **NoSQL:** [MongoDB, Cassandra, DynamoDB]
- **Caching:** [Redis, Memcached]
- **Data Warehouses:** [Snowflake, Redshift, BigQuery]
- **Search:** [Elasticsearch, Solr]

### Infrastructure & Platforms

- **Cloud Platforms:**
  - AWS: [Services used - EC2, S3, Lambda, RDS, ECS, EKS]
  - Azure: [VMs, Blob Storage, Functions, SQL Database, AKS]
  - GCP: [Compute Engine, Cloud Storage, Cloud Functions, Cloud SQL, GKE]

- **Containers & Orchestration:**
  - Docker: [Version, registry location]
  - Kubernetes: [Distribution, version, cluster count]
  - OpenShift, Rancher, ECS, AKS, GKE

- **CI/CD:**
  - [Jenkins, GitLab CI, GitHub Actions, CircleCI, Azure DevOps]
  - [Artifact repositories - Artifactory, Nexus, container registries]

### Networking

- **Network Architecture:**
  - [Flat network, segmented, zero-trust zones]
  - [VLANs, subnets, DMZ configuration]
  - [Datacenter/office locations]

- **Load Balancers:** [F5, Nginx, HAProxy, cloud-native]
- **DNS:** [Providers, internal DNS servers]
- **VPN/Remote Access:** [Technologies, authentication methods]
- **SD-WAN:** [Vendor, deployment]

### Applications & Services

- **Productivity:**
  - Email: [Microsoft 365, Google Workspace, on-prem Exchange]
  - Collaboration: [Slack, Teams, Zoom]
  - File Sharing: [SharePoint, Google Drive, Box, Dropbox]

- **Development:**
  - Version Control: [GitHub, GitLab, Bitbucket, Azure Repos]
  - Project Management: [Jira, Azure DevOps, Linear]
  - Documentation: [Confluence, Notion, SharePoint, internal wikis]

- **Business Applications:**
  - CRM: [Salesforce, HubSpot, Dynamics 365]
  - ERP: [SAP, Oracle, NetSuite]
  - HR Systems: [Workday, ADP]
  - Finance: [QuickBooks, custom systems]

---

## Internal Documentation & Resources

### Architecture Documentation

- **System Architecture:** [Link to diagrams, wiki pages]
- **Network Diagrams:** [Link or file path - e.g., /docs/network-diagram.pdf]
- **Data Flow Diagrams:** [How data moves through systems]
- **Security Architecture:** [Security controls, trust boundaries]

### Operational Documentation

- **Runbooks:** [Location of operational procedures]
- **Incident Response Plans:** [IR playbooks, escalation paths]
- **DR/BCP Plans:** [Disaster recovery documentation]
- **Change Management:** [Where to find change records]

### Asset & Configuration Management

- **CMDB/Asset Inventory:** [ServiceNow, custom CMDB, spreadsheets]
  - Access: [API endpoint, web interface, query examples]
  - Update Frequency: [Real-time, daily, weekly]

- **Configuration Management:** [Ansible, Puppet, Chef, Terraform repos]
- **Service Catalog:** [What services exist, ownership]

### Integration Examples

#### Confluence Integration

```bash
# Example: Query Confluence for architecture docs
curl -u user:token https://confluence.company.com/rest/api/content/search?cql=type=page+and+space=SEC
```

#### ServiceNow CMDB Query

```bash
# Example: Pull asset inventory
curl "https://instance.service-now.com/api/now/table/cmdb_ci_server" \
  -H "Authorization: Bearer $TOKEN"
```

#### SharePoint Document Access

```bash
# Example: List security documentation
# Microsoft Graph API: GET /sites/{site-id}/drive/root/children
```

#### Jira Asset Tracking

- **Query:** [Link to Jira filter showing infrastructure assets]
- **Example:** `https://jira.company.com/issues/?jql=project=INFRA+AND+type=Asset`

---

## Access & Credentials

> **Do not store actual credentials here.** Document where to find them.

- **Secret Management:** [Vault, AWS Secrets Manager, Azure Key Vault, 1Password]
- **Service Accounts:** [Where to find hunt-related service account credentials]
- **API Keys:** [Where API keys for tools/platforms are stored]
- **Documentation:** [Links to access request procedures, onboarding docs]

---

## Known Gaps & Blind Spots

Document areas where visibility is limited:

- **Unmonitored Systems:** [Legacy systems, OT/ICS, contractor networks]
- **Data Source Gaps:** [Logs not collected, limited retention]
- **Tool Limitations:** [Known blind spots in EDR/SIEM coverage]
- **Third-Party Services:** [SaaS apps without logging integration]

---

## Maintenance Notes

### Review Checklist (Quarterly)

- [ ] Verify technology versions are current
- [ ] Add new services/applications deployed
- [ ] Remove decommissioned systems
- [ ] Update tool coverage percentages
- [ ] Refresh internal documentation links
- [ ] Validate API access and integrations still work

### Change Log

- **YYYY-MM-DD:** Initial creation
- **YYYY-MM-DD:** Added new EDR deployment details
- **YYYY-MM-DD:** Updated cloud services after migration
