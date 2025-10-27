# Query Builder Prompt

Use this prompt to help draft hunting queries from your hypothesis (Level 1: Assisted).

## Prompt

```
You are a threat hunting query expert. Help me write a safe, bounded query to test a hunt hypothesis.

HYPOTHESIS:
[Your hypothesis here]

PLATFORM: [Splunk / KQL (Sentinel/Defender) / Elastic]

DATA AVAILABLE:
- Index/Table: [name]
- Sourcetype/DataSource: [name]
- Key fields: [list]

CONSTRAINTS:
1. Time range: earliest=-24h latest=now (adjust as needed)
2. Result cap: head 1000 (or | take 1000 for KQL)
3. Use tstats (Splunk) or summarize (KQL) when possible for performance
4. Include metadata comments with hunt ID and ATT&CK technique
5. Return only essential fields
6. Add eval/extend to tag results with hunt_id and attack_technique

OUTPUT FORMAT:
Provide:
1. The complete query
2. Brief explanation of what it does
3. Expected runtime estimate
4. Suggestions for tuning if results are too noisy

Generate query now:
```

## Query Templates

### Splunk SPL Template

```spl
/* H-#### | ATT&CK: T#### | Purpose: [description]
   Earliest: -24h | Latest: now | Cap: 1000 | Owner: [name] */

| tstats count from datamodel=YourDataModel where
  [your conditions]
  by _time, host, [key_fields] span=5m
| head 1000
| eval hunt_id="H-####", attack_technique="T####"
| fields _time, host, [relevant_fields], hunt_id, attack_technique
```

### KQL Template

```kql
// H-#### | ATT&CK: T#### | Purpose: [description]
// TimeRange: ago(24h) | Cap: 1000 | Owner: [name]

YourTable
| where TimeGenerated >= ago(24h)
| where [your conditions]
| summarize Count=count() by bin(TimeGenerated, 5m), Computer, [key_fields]
| take 1000
| extend HuntId="H-####", AttackTechnique="T####"
```

## Tips for Good Queries

### Performance
- **Use data models** (Splunk) or summarize (KQL) when possible
- **Filter early** - Most restrictive conditions first
- **Limit fields** - Only return what you need
- **Set sensible time ranges** - Start with 24h, expand if needed

### Safety
- **Always bound time** - Never open-ended searches
- **Always cap results** - Protect your SIEM
- **Test on small timeframes first** - 1 hour before 24 hours
- **Use lookups for enrichment** - Don't join large datasets inline

### Signal Quality
- **Filter known good** - Baseline automation, admin tools
- **Add context** - Enrich with asset inventory, user roles
- **Look for anomalies** - Rare processes, unusual times, unexpected hosts
- **Use stats wisely** - Count, distinct count, rare events

## Common Patterns

### Process Execution Hunt
```spl
| tstats count from datamodel=Endpoint.Processes where
  Processes.process_name IN ("suspicious.exe", "bad.exe")
  by _time, host, Processes.process, Processes.user span=5m
```

### Authentication Hunt
```kql
SecurityEvent
| where EventID == 4625  // Failed logon
| where TimeGenerated >= ago(24h)
| summarize FailedAttempts=count() by bin(TimeGenerated, 10m), Account, Computer
```

### Network Connection Hunt
```spl
| tstats count from datamodel=Network_Traffic where
  All_Traffic.dest_port IN (443, 8080)
  NOT All_Traffic.dest IN (known_good_ips)
  by _time, All_Traffic.src, All_Traffic.dest, All_Traffic.dest_port
```

## Troubleshooting

**Too many results?**
- Add more specific filters
- Shorten time range
- Filter out known benign activity
- Use rare() or unusual patterns

**Too few results?**
- Broaden conditions
- Check field names and values
- Verify data is actually indexed
- Expand time range

**Query too slow?**
- Use data models/accelerated searches
- Reduce time range
- Remove expensive operations (regex, complex joins)
- Add index= constraints

## Next Steps

After drafting your query:
1. Test on a short timeframe first (1 hour)
2. Review sample results
3. Refine filters based on false positives
4. Document any allowlists needed
5. Add to `queries/H-####.spl` or `.kql`
