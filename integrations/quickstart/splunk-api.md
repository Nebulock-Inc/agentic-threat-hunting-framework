# Splunk REST API Integration (Native Python)

This guide shows how to use ATHF's built-in Splunk REST API client for direct query execution.

## When to Use This vs MCP

**Use Native API Integration When:**
- Cannot install Splunk MCP Server app
- Need programmatic Python access to Splunk
- Building custom integrations or scripts
- Want simpler setup without MCP overhead

**Use MCP Integration When:**
- Want Claude Code to execute queries autonomously
- Need full AI-assisted query generation
- Prefer official Splunk-provided tooling
- See: [splunk.md](splunk.md) for MCP setup

## Prerequisites

- Splunk Enterprise 8.0+ or Splunk Cloud
- Python 3.8+
- ATHF installed with dependencies

## Setup

### Step 1: Create Splunk Authentication Token

1. Log into Splunk Web
2. Navigate to **Settings → Tokens**
3. Click **New Token**
4. Set audience (e.g., `api-access` or leave default)
5. Set expiration per your security policy
6. Copy the generated token

### Step 2: Configure Environment Variables

Add to your `.env` file or export in your shell:

```bash
export SPLUNK_HOST="splunk.example.com"
export SPLUNK_TOKEN="eyJraWQiOiJzcGx1bms..."
export SPLUNK_VERIFY_SSL="true"  # Optional: set to false for self-signed certs
```

**Important:** Never commit credentials to version control. Use `.env` files and add them to `.gitignore`.

### Step 3: Verify Connection

```bash
athf splunk test
```

Expected output:
```
✓ Connection successful!

Server: splunk-prod-01
Version: 9.0.3
Build: dd0128b1f8cd
```

## CLI Usage

**⚠️ IMPORTANT: For this deployment, always use `index=thrunt` for all hunt queries.**

The `thrunt` index contains 12M+ security events including:
- Network traffic (stream:ip, stream:dns, stream:tcp, stream:http)
- Windows events (XmlWinEventLog) - 513K events
- Firewall logs (juniper:junos:firewall) - 535K events
- Linux audit logs - 131K events
- Cloud logs (AWS, Azure, O365, Kubernetes)

### Test Connection

```bash
athf splunk test
```

### List Available Indexes

```bash
# Simple list
athf splunk indexes

# JSON output
athf splunk indexes --format json

# Table format
athf splunk indexes --format table
```

### Execute Queries

#### Basic Query

```bash
athf splunk search 'index=thrunt | head 10'
```

#### With Time Range

```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" | head 50' \
  --earliest "0" \
  --latest "now" \
  --count 50
```

#### Statistical Query

```bash
athf splunk search 'index=thrunt | stats count by sourcetype | sort -count' \
  --earliest "0" \
  --count 100 \
  --format table
```

#### Long-Running Query (Async)

For queries that may take more than 30 seconds:

```bash
athf splunk search 'index=thrunt sourcetype="stream:*" | stats count by sourcetype' \
  --async-search \
  --max-wait 600 \
  --count 1000
```

### Show Configuration

```bash
athf splunk config
```

## Command Reference

### `athf splunk test`

Test connection and authentication.

**Options:**
- `--host` - Override SPLUNK_HOST
- `--token` - Override SPLUNK_TOKEN
- `--verify-ssl / --no-verify-ssl` - SSL verification (default: true)

### `athf splunk indexes`

List available Splunk indexes.

**Options:**
- `--format` - Output format: `list`, `json`, or `table` (default: list)
- `--host`, `--token`, `--verify-ssl` - Connection options

### `athf splunk search QUERY`

Execute a Splunk search query.

**Arguments:**
- `QUERY` - SPL search query (auto-prepends "search" if needed)

**Options:**
- `--earliest` - Start time (default: `-24h`)
  - Examples: `-1h`, `-7d`, `2024-01-01T00:00:00`
- `--latest` - End time (default: `now`)
- `--count` - Max results to return (default: 100)
- `--format` - Output format: `json`, `table`, or `raw` (default: json)
- `--async-search` - Use async search for long queries
- `--max-wait` - Max wait time for async searches in seconds (default: 300)
- `--host`, `--token`, `--verify-ssl` - Connection options

### `athf splunk config`

Show current configuration and test connection.

## Programmatic Usage (Python)

### Basic Example

```python
from athf.core.splunk_client import SplunkClient

# Create client
client = SplunkClient(
    host="splunk.example.com",
    token="your-token-here",
    verify_ssl=True
)

# Test connection
info = client.test_connection()
print(f"Connected to Splunk version {info['version']}")

# Execute query on thrunt index
results = client.search(
    query='index=thrunt sourcetype="XmlWinEventLog" EventCode=4625',
    earliest_time="0",
    max_count=100
)

for event in results:
    print(event)
```

### From Environment Variables

```python
from athf.core.splunk_client import create_client_from_env

# Load from SPLUNK_HOST, SPLUNK_TOKEN, SPLUNK_VERIFY_SSL
client = create_client_from_env()

# Use client
indexes = client.get_indexes()
print(f"Available indexes: {indexes}")
```

### Async Search (Long Queries)

```python
# For queries that may take longer
results = client.search_async(
    query='index=thrunt | stats count by sourcetype | sort -count',
    earliest_time="0",
    max_results=1000,
    max_wait=600  # Wait up to 10 minutes
)
```

### Low-Level API Access

```python
# Create search job
sid = client.create_search_job(
    query='index=thrunt sourcetype="stream:*" | stats count by sourcetype',
    earliest_time="0"
)

# Check status
status = client.get_search_job_status(sid)
print(f"Job status: {status}")

# Wait for completion
if client.wait_for_search_job(sid, max_wait=300):
    # Get results
    results = client.get_search_results(sid, count=100)
    print(f"Got {len(results)} results")

# Cleanup
client.delete_search_job(sid)
```

## Integration with ATHF Workflow

### In Hunt Files

Document Splunk queries in your hunt files:

```markdown
## Check

### Query 1: Windows Authentication Failures

```spl
index=thrunt sourcetype="XmlWinEventLog" EventCode=4625
| stats count by Account_Name, src_ip
| where count > 10
| sort -count
```

**Execution:**
```bash
athf splunk search 'index=thrunt sourcetype="XmlWinEventLog" EventCode=4625 | stats count by Account_Name, src_ip | where count > 10 | sort -count' \
  --earliest "0" \
  --count 100 \
  --format json > results.json
```
```

### From Python Scripts

```python
#!/usr/bin/env python3
"""Execute hunt queries from Python."""

from athf.core.splunk_client import create_client_from_env

def run_hunt_query():
    client = create_client_from_env()

    # Query from hunt hypothesis
    query = '''
    index=thrunt sourcetype="XmlWinEventLog" EventCode=4625
    | stats count by Account_Name, src_ip
    | where count > 20
    '''

    results = client.search(query, earliest_time="0", max_count=50)

    # Analyze results
    if results:
        print(f"⚠️  Found {len(results)} suspicious accounts")
        for event in results:
            print(f"  - {event['Account_Name']}: {event['count']} failures")
    else:
        print("✓ No suspicious activity found")

if __name__ == "__main__":
    run_hunt_query()
```

## Query Guardrails

**Always follow these rules when executing queries:**

1. **Time Bounds** - Always specify time ranges
   ```bash
   --earliest "-7d" --latest "now"
   ```

2. **Result Limits** - Start small and increase as needed
   ```bash
   --count 100  # Start here, not 10000
   ```

3. **COUNT-FIRST Strategy** - Count before pulling results
   ```spl
   # First: count to gauge size
   index=main error | stats count

   # Then: pull results if count is reasonable
   index=main error | head 100
   ```

4. **Test Before Production** - Test on small time windows first
   ```bash
   # Test with 1 hour
   athf splunk search 'query' --earliest "-1h"

   # If fast, expand to 24 hours
   athf splunk search 'query' --earliest "-24h"
   ```

5. **Use Async for Heavy Queries** - If query takes >30s
   ```bash
   athf splunk search 'heavy query' --async-search --max-wait 600
   ```

## Security Best Practices

### Credential Management

**✅ DO:**
- Store credentials in `.env` files
- Use environment variables
- Rotate tokens regularly
- Use least-privilege access (read-only for hunting)
- Add `.env` to `.gitignore`

**❌ DON'T:**
- Commit credentials to git
- Share tokens in chat/email
- Use admin tokens for hunting
- Hardcode credentials in scripts

### Token Permissions

Create a dedicated Splunk role for hunting with:
- **Search permissions** on relevant indexes
- **NO delete/modify permissions**
- **NO admin capabilities**
- **Time-limited tokens** (e.g., 90 days)

### SSL Verification

**Production:**
```bash
export SPLUNK_VERIFY_SSL="true"  # Always verify in production
```

**Development/Testing only:**
```bash
export SPLUNK_VERIFY_SSL="false"  # Only for self-signed certs
```

## Troubleshooting

### Connection Failed

**Error:** `Connection refused` or `Timeout`

**Solution:**
- Verify port 8089 is accessible
- Check firewall rules
- Confirm host URL is correct

```bash
curl -k https://splunk.example.com:8089/services/server/info
```

### Authentication Failed

**Error:** `401 Unauthorized`

**Solution:**
- Verify token is valid and not expired
- Check token was copied completely (no truncation)
- Ensure token has search permissions

```bash
# Test with curl
curl -k https://splunk.example.com:8089/services/search/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "search=search index=main | head 1"
```

### SSL Certificate Error

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions:**
1. **Preferred:** Install valid SSL certificate on Splunk
2. **Dev/Test only:** Disable verification
   ```bash
   export SPLUNK_VERIFY_SSL="false"
   ```
3. Use `--no-verify-ssl` flag (not recommended for production)

### Query Timeout

**Error:** Query takes too long or times out

**Solutions:**
1. Reduce time range: `--earliest "-1h"` instead of `-7d`
2. Add more filters to query
3. Use `--async-search` for long queries
4. Increase `--max-wait` timeout
5. Simplify aggregations

### No Results

**Check:**
1. Time range includes data: `--earliest "-24h"`
2. Index exists: `athf splunk indexes`
3. Permissions: User can access specified indexes
4. Query syntax: Test in Splunk Web UI first

## API Reference

See [`athf/core/splunk_client.py`](../../athf/core/splunk_client.py) for full API documentation.

**Key Methods:**
- `test_connection()` - Verify connection
- `get_indexes()` - List indexes
- `search()` - Quick oneshot search
- `search_async()` - Long-running async search
- `create_search_job()` - Create search job
- `get_search_results()` - Get job results
- `delete_search_job()` - Clean up job

## Resources

- **Splunk REST API Docs:** https://docs.splunk.com/Documentation/Splunk/latest/RESTREF
- **SPL Reference:** https://docs.splunk.com/Documentation/Splunk/latest/SearchReference
- **ATHF Documentation:** https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
- **SPL Query Examples:** See `hunts/` directory for real-world queries

## Comparison: API vs MCP

| Feature | Native API (This Guide) | MCP Integration |
|---------|-------------------------|-----------------|
| **Setup** | Environment variables | MCP Server app + config |
| **Auth** | Token | Token (audience=mcp) |
| **Use Case** | CLI + scripts | AI-driven workflows |
| **Query Execution** | Manual via CLI | Autonomous via Claude |
| **AI Integration** | No | Yes |
| **Complexity** | Simple | Moderate |
| **Dependencies** | Python only | Node.js + Splunk app |

**Recommendation:** Use both!
- API for scripts and CLI workflows
- MCP for AI-assisted hunting with Claude Code

---

**Questions?** Open an issue in the ATHF repo.
