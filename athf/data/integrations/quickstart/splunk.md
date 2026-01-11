# Quickstart: Splunk MCP Integration

This guide shows how to connect Claude Code to Splunk Enterprise or Splunk Cloud via the official Splunk MCP Server.

## What You Get

Once configured, Claude Code can:

- **Query Splunk:** Run SPL searches and get results
- **Generate SPL:** AI-assisted query generation
- **Analyze Data:** Get insights from Splunk logs
- **Browse Indexes:** List and explore available data sources

## Prerequisites

- Splunk Enterprise 8.0+ or Splunk Cloud with admin access
- Claude Code installed

## Setup Steps

### Step 1: Install Splunk MCP Server App

1. Download the official **Splunk MCP Server** app from [Splunkbase](https://splunkbase.splunk.com/app/7931)
2. Install it on your Splunk instance via **Settings → Apps → Install app from file**
3. Grant the `mcp_tool_execute` capability to your user role

**Documentation:** <https://help.splunk.com/en/splunk-cloud-platform/mcp-server-for-splunk-platform/>

### Step 2: Create API Token

1. Log into Splunk Web
2. Navigate to **Settings → Tokens**
3. Click **New Token**
4. **Set Audience to `mcp`** ⚠️ **CRITICAL** - Must be exactly `mcp`
5. Set expiration per your security policy
6. Copy the generated token

**Important:** If audience is not set to `mcp`, connection will fail with 403 error.

### Step 3: Configure Claude Code

Edit your `~/.claude.json` and add the Splunk MCP server configuration to the project section:

```json
{
  "projects": {
    "/path/to/your/project": {
      "mcpServers": {
        "splunk-mcp-server": {
          "command": "npx",
          "args": [
            "-y",
            "mcp-remote",
            "https://your-splunk-host.com:8089/services/mcp",
            "--header",
            "Authorization: Bearer YOUR_TOKEN_HERE"
          ],
          "env": {
            "NODE_TLS_REJECT_UNAUTHORIZED": "0"
          }
        }
      }
    }
  }
}
```

**Configuration:**

- Replace `your-splunk-host.com` with your Splunk server IP or hostname
- Replace `YOUR_TOKEN_HERE` with the token from Step 2
- Set `NODE_TLS_REJECT_UNAUTHORIZED: "0"` if using self-signed SSL certificates (testing only)
- For production with valid SSL certificates, remove the `env` section

**Security:** Store tokens in `.env` files, not directly in `.claude.json`.

### Step 4: Verify Connection

```bash
# Start Claude Code in your project directory
cd /path/to/your/project
claude

# Verify the connection
claude mcp list
# Expected: splunk-mcp-server ... ✓ Connected
```

**That's it!** The Splunk MCP tools are now available.

## Usage Examples

Simple prompts that work once Splunk MCP is configured:

```
"Show me all available Splunk indexes"

"Search Splunk for failed SSH attempts in the last 24 hours"

"Search for PowerShell executions in the last 4 hours"

"Generate a SPL query to find brute force authentication attempts"

"Run the query from hunt hypothesis H-0001"
```

Claude will automatically:

- Execute SPL queries
- Parse and format results
- Explain findings
- Suggest follow-up investigations

## Available Tools

The Splunk MCP provides these tools:

- **`run_splunk_query`** - Execute SPL searches
- **`get_indexes`** - List available indexes
- **`get_splunk_info`** - Get Splunk instance information
- **`generate_spl`** - AI-assisted query generation (requires Splunk AI Assistant)
- **`explain_spl`** - Explain what SPL queries do
- **`optimize_spl`** - Optimize existing queries
- **`get_knowledge_objects`** - Access saved searches and lookups

## Security Considerations

**Important:** Ensure you follow your organization's security policies and best practices when deploying this integration. Consider:

- Implementing least-privilege access controls for the MCP user
- Properly securing and rotating API tokens
- Monitoring and auditing MCP server usage
- Following your organization's SSL/TLS certificate policies
- Storing credentials securely (not in version control)

Consult the [official Splunk MCP documentation](https://help.splunk.com/en/splunk-cloud-platform/mcp-server-for-splunk-platform/) and your security team for specific requirements.

## Troubleshooting

**403 Error:**
Check token audience is set to `mcp` (not `search` or `claude-code-mcp`)

**Connection Failed:**

- Verify port 8089 is accessible
- For self-signed certs, add `NODE_TLS_REJECT_UNAUTHORIZED: "0"` to env

**Permission Denied:**
Grant user the `mcp_tool_execute` capability and index access

**Token Expired:**
Create a new token in Splunk Web → Settings → Tokens

## Resources

- **Splunk MCP Server App:** <https://splunkbase.splunk.com/app/7931>
- **Official Documentation:** <https://help.splunk.com/en/splunk-cloud-platform/mcp-server-for-splunk-platform/>
- **SPL Reference:** <https://docs.splunk.com/Documentation/Splunk/latest/SearchReference>

---

**Questions?** Open an issue in the ATHF repo or check the official Splunk MCP documentation.
