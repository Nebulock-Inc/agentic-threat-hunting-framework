# Level 3: Generative - Bring Your Own MCP

At Level 3, you extend Claude Code's capabilities by connecting MCP (Model Context Protocol) servers for the security tools you already use. This transforms the LOCK workflow from manual investigation to tool-integrated analysis.

## What Is Level 3?

**Level 1 (Documented):** You manually document hunts in markdown files
**Level 2 (Searchable):** Claude reads past hunts, applies expert hunting frameworks from knowledge/hunting-knowledge.md, and uses AGENTS.md for environmental context
**Level 3 (Generative):** Claude executes queries, enriches data, and creates tickets through MCPs

At Level 3, Claude doesn't just read about your tools - it **uses** them.

## What Does Integration Mean?

Instead of copying queries and results back and forth between Claude and your tools, **MCPs let Claude directly interact with your security stack**.

**The transformation:**

- **Before:** You describe your tools to Claude, manually run queries, paste results back
- **After:** Claude executes queries, analyzes data, and takes actions through tool APIs

**We demonstrate this with Splunk**, but the same principles apply to any tool with an MCP server.

## How MCPs Enhance the LOCK Workflow

### Learn Phase

**Without MCP:** Copy-paste threat intel into Claude
**With MCP:** Claude queries threat intel platforms directly for TTP context

### Observe Phase

**Without MCP:** Manually list expected behaviors
**With MCP:** Claude queries asset inventory to understand your environment

### Check Phase

**Without MCP:** Copy queries into Splunk manually
**With MCP:** Claude executes queries and analyzes results

### Keep Phase

**Without MCP:** Manually create Jira tickets
**With MCP:** Claude auto-creates tickets with findings

## Getting Started

Ready to try Level 3? We provide a complete Splunk MCP integration walkthrough:

**[Start the Splunk walkthrough →](MCP_CATALOG.md)**

Once you complete it, you'll understand how to integrate MCPs for any security tool.

## Quick Example

### Without MCP Integration (Level 2)

```
You: "Search for SSH brute force attempts in Splunk"
Claude: "Here's a Splunk query you can run:
index=linux_secure action=failure | stats count by src_ip"
You: [Copies query to Splunk, runs it, pastes results back]
Claude: "Based on those results, I see 3 high-volume IPs..."
```

### With MCP Integration (Level 3)

```
You: "Search for SSH brute force attempts"
Claude: [Executes Splunk query via MCP]
"I found 3 source IPs with high failure rates:
- 203.0.113.45 (127 attempts)
- 198.51.100.22 (89 attempts)
- 192.0.2.15 (67 attempts)

203.0.113.45 shows sustained activity over 2 hours. Should I pivot
to see what accounts were targeted?"
```

The difference: **Claude executes queries and analyzes results directly, no copy-paste.**

## Security Considerations

### Permissions

MCPs run with the credentials you provide. Follow the principle of least privilege:

- **Read-only access** for SIEMs and asset inventory
- **Create-only access** for ticketing systems
- **No destructive permissions** (delete, modify critical data)

### Guardrails

Always maintain human oversight:

- **Queries should be bounded** (time range, result limits)
- **No automatic remediation** without approval
- **Audit all MCP actions** in logs
- **Review generated queries** before execution

### Credential Management

- **Never commit credentials** to your ATHF repository
- **Use environment variables** for API keys
- **Rotate keys regularly** per your security policy
- **Use Claude Code's built-in permission system** to approve/deny MCP usage

## What's Next?

**[Start the Splunk MCP walkthrough →](MCP_CATALOG.md)**

## Level 4 Preview

Once you have MCP integrations working, Level 4 (Agentic) becomes possible. Instead of you asking Claude to run hunts, **autonomous agents** can:

- Monitor CTI feeds and generate draft hunts
- Execute scheduled hunts automatically
- Enrich findings with threat intel
- Create tickets for analyst review

Level 3 gives Claude the **tools**. Level 4 gives it **agency**.

## Support

- **MCP Documentation:** <https://modelcontextprotocol.io>
- **Claude Code MCP Guide:** <https://docs.claude.com/claude-code/mcp>
- **ATHF Issues:** <https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues>

Happy hunting!
