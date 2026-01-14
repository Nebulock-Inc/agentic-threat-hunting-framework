# AGENTS.md - Splunk Integration Context for AI Assistants

**Purpose:** This file provides AI assistant context for executing threat hunting queries against Splunk using ATHF's native API integration.

---

## Query Execution Method

**PRIMARY METHOD: Use `athf splunk search` CLI command**

AI assistants MUST use the `athf splunk search` command for all Splunk query execution. This provides:
- Automatic authentication via environment variables
- Result limits and timeouts
- Structured output (JSON, table, raw)
- Error handling and retry logic

**✅ CORRECT - Use CLI:**
```bash
athf splunk search 'index=windows EventCode=4624 | stats count by ComputerName' \
  --earliest "-7d" \
  --count 100 \
  --format json
```

**❌ WRONG - Don't use raw HTTP requests or manual API calls**

---

## Default Index

**⚠️ CRITICAL: For this deployment, always use `index=thrunt` for all hunt queries.**

The `thrunt` index contains 12M+ security events including:
- **Windows events** (XmlWinEventLog) - 513K events
- **Network traffic** (stream:ip, stream:dns, stream:tcp, stream:http)
- **Firewall logs** (juniper:junos:firewall) - 535K events
- **Linux audit logs** - 131K events
- **Cloud logs** (AWS, Azure, O365, Kubernetes)

**Always start queries with:** `index=thrunt`

---

## SPL Query Syntax Guidelines

### Time Bounds (Mandatory)

**ALWAYS specify time range** using `--earliest` and `--latest` flags:

```bash
# Last 7 days (default for exploratory hunts)
--earliest "-7d" --latest "now"

# Last 24 hours (for initial testing)
--earliest "-24h" --latest "now"

# Last hour (for quick tests)
--earliest "-1h" --latest "now"

# All available data in thrunt index (use sparingly)
--earliest "0" --latest "now"
```

**Note:** The `thrunt` index contains historical data. Use `--earliest "0"` to search all data, but be mindful of query performance.

### Result Limits (Mandatory)

**ALWAYS use `--count` flag** to limit results:

```bash
# Start with 100 for exploratory queries
--count 100

# Increase if needed based on COUNT-FIRST results
--count 1000

# For COUNT queries only
--count 0  # (only when using | stats count)
```

### COUNT-FIRST Strategy (Required)

**ALWAYS count before pulling results.** Execute queries in this sequence:

#### Step 1: Baseline Count
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 | stats count' \
  --earliest "0" \
  --count 1 \
  --format json
```

**Decision tree:**
- **count = 0** → No data, stop
- **count < 100** → Proceed with `--count 100`
- **count 100-1000** → Proceed with `--count 1000`
- **count > 1000** → Add filters, then recount

#### Step 2: Filtered Count (Add Constraints)
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10 | stats count' \
  --earliest "0" \
  --count 1 \
  --format json
```

#### Step 3: Pull Results (Only if Justified)
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10' \
  --earliest "0" \
  --count 100 \
  --format json
```

**STOP after each query** - Wait for user feedback before proceeding.

### Query Performance Best Practices

1. **Index + Sourcetype First** - Most efficient filters
   ```spl
   index=thrunt sourcetype="XmlWinEventLog" EventCode=4624
   ```

2. **Avoid Wildcards in Index** - Use specific index names
   ```spl
   ✅ index=thrunt
   ❌ index=*
   ```

3. **Use stats Instead of Head** - More efficient for large datasets
   ```spl
   ✅ | stats count by field
   ❌ | head 1000 | dedup field
   ```

4. **Field Extraction Efficiency** - Reference fields that exist in sourcetype
   ```spl
   ✅ EventCode=4624  (indexed field)
   ❌ custom_field=*  (may require extraction)
   ```

5. **Use Async for Long Queries** - If query may take >30 seconds
   ```bash
   athf splunk search 'complex query' \
     --async-search \
     --max-wait 600
   ```

---

## Common Field Names

### Windows Event Logs (sourcetype="XmlWinEventLog")

| Field | Description | Example Values |
|-------|-------------|----------------|
| `EventCode` | Windows Event ID | 4624, 4625, 4648, 4768 |
| `ComputerName` | Hostname | WIN-SERVER01 |
| `Account_Name` | Username | jdoe, administrator |
| `LogonType` | Windows logon type | 2 (interactive), 3 (network), 10 (RDP) |
| `SourceNetworkAddress` | Source IP address | 10.0.1.50 |
| `TargetUserName` | Target account | domain\user |
| `WorkstationName` | Source workstation | CLIENT01 |

**Common EventCodes:**
- **4624** - Successful logon
- **4625** - Failed logon
- **4648** - Logon using explicit credentials
- **4768** - Kerberos TGT requested
- **4769** - Kerberos service ticket requested
- **4771** - Kerberos pre-authentication failed

### Network Logs (sourcetype="stream:*")

| Field | Description |
|-------|-------------|
| `src_ip` | Source IP address |
| `dest_ip` | Destination IP address |
| `src_port` | Source port |
| `dest_port` | Destination port |
| `protocol` | Network protocol (TCP, UDP) |
| `bytes_in` | Bytes received |
| `bytes_out` | Bytes sent |

### Firewall Logs (sourcetype="juniper:junos:firewall")

| Field | Description |
|-------|-------------|
| `action` | Permit/Deny |
| `src_ip` | Source IP |
| `dest_ip` | Destination IP |
| `src_zone` | Source zone |
| `dest_zone` | Destination zone |

---

## RDP Lateral Movement Hunt Example

**Hypothesis:** Detect RDP (EventCode 4624, LogonType 10) from unusual sources or at unusual times.

### Query Sequence

**Query 1: Baseline Count (All RDP Logons)**
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10 | stats count' \
  --earliest "0" \
  --count 1 \
  --format json
```

**Query 2: Aggregated by Source IP**
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10 | stats count by SourceNetworkAddress, ComputerName | sort -count' \
  --earliest "0" \
  --count 100 \
  --format table
```

**Query 3: Anomaly Detection (Multiple Destinations from Single Source)**
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10 | stats dc(ComputerName) as dest_count by SourceNetworkAddress | where dest_count > 5 | sort -dest_count' \
  --earliest "0" \
  --count 50 \
  --format json
```

**Query 4: Pull Full Events (Only if Query 3 Shows Anomalies)**
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4624 LogonType=10 SourceNetworkAddress="10.0.1.50"' \
  --earliest "0" \
  --count 100 \
  --format json
```

---

## Output Formats

### JSON (Default - Best for Programmatic Use)
```bash
--format json
```
Returns structured JSON array of events, ideal for parsing and analysis.

### Table (Best for Human Review)
```bash
--format table
```
Returns Rich table output in terminal, ideal for quick triage.

### Raw (Full Event Details)
```bash
--format raw
```
Returns full event details with all fields, ideal for deep investigation.

---

## Query Workflow for Hunts

When AI assistant is executing hunt queries:

1. **Activate virtual environment first:**
   ```bash
   source .venv/bin/activate
   which athf  # Verify correct athf
   ```

2. **Test connection:**
   ```bash
   athf splunk test
   ```

3. **Execute COUNT-FIRST queries:**
   - Baseline count → Filtered count → Analyze → Pull results

4. **STOP after each query:**
   - Present results to user
   - Wait for feedback before next query
   - Ask if user wants to proceed

5. **Document queries in hunt file:**
   - Add SPL queries to Hunt Check section
   - Record results and findings
   - Include command used for reproducibility

---

## Common Mistakes to Avoid

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `index=*` | `index=thrunt` |
| No time bounds | `--earliest "-7d"` |
| No result limit | `--count 100` |
| Pull results first | Count first, then pull |
| Multiple queries in parallel | One query at a time, wait for feedback |
| Omit `athf splunk search` | Always use CLI command |

---

## Authentication

Splunk API authentication uses environment variables:

```bash
export SPLUNK_HOST="splunk.example.com"
export SPLUNK_TOKEN="your-token-here"
export SPLUNK_VERIFY_SSL="true"
```

**AI assistants should:**
- Assume credentials are already configured
- Use `athf splunk test` to verify connection before queries
- Report authentication errors to user if credentials missing

**AI assistants should NOT:**
- Ask user for credentials (assume already set)
- Attempt to set environment variables
- Hard-code credentials in queries

---

## Error Handling

### Query Timeout
**Error:** Query takes too long or times out

**Solution:**
1. Reduce time range: `--earliest "-1h"` instead of "0"
2. Add more filters to query
3. Use `--async-search` for long queries
4. Simplify aggregations

### No Results
**Check:**
1. Time range includes data: Use `--earliest "0"` for all thrunt data
2. EventCode exists: Verify EventCode is valid for sourcetype
3. Typos in field names: Use exact field names from table above

### Connection Failed
**Solutions:**
1. Run `athf splunk test` to verify connection
2. Check environment variables are set
3. Verify network access to Splunk host

---

## Integration with Hunt Workflow

### Before Generating Queries

1. **Load context:**
   ```bash
   athf context --hunt H-XXXX --format json
   ```

2. **Check past hunts for similar queries:**
   ```bash
   athf similar "RDP lateral movement"
   ```

3. **Verify connection:**
   ```bash
   athf splunk test
   ```

### During Query Execution

- **One query at a time** - Execute sequentially
- **Wait for user feedback** - Don't auto-proceed
- **Present results clearly** - Use structured output (JSON or table)
- **Stop if anomalies found** - Ask user if they want to pivot

### After Query Execution

- **Document in hunt file** - Add queries to Check section
- **Record results** - Summarize findings
- **Update lessons learned** - Capture what worked/didn't work

---

## Resources

- **CLI Reference:** [integrations/quickstart/splunk-api.md](../quickstart/splunk-api.md)
- **SPL Documentation:** https://docs.splunk.com/Documentation/Splunk/latest/SearchReference
- **Field Reference:** See environment.md for deployment-specific fields
- **Example Queries:** See `hunts/` directory for past hunt queries

---

**Last Updated:** 2026-01-13
**Maintained By:** ATHF Framework Team
