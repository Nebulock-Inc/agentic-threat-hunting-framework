# MCP Catalog for Threat Hunting

## ATHF MCP Server (Built-in)

ATHF includes its own MCP server that exposes hunting operations as tools for any AI assistant.

**Install:**
```bash
pip install 'athf[mcp]'
```

**Configure for Claude Code** (`~/.claude/mcp-servers.json`):
```json
{
  "athf": {
    "command": "athf-mcp",
    "args": ["--workspace", "/path/to/your/hunts"]
  }
}
```

**Available tools (14):**

| Tool | Description |
|------|-------------|
| `athf_hunt_list` | List/filter hunts by status, tactic, technique, platform |
| `athf_hunt_search` | Full-text search across hunt files |
| `athf_hunt_get` | Get full details of a specific hunt |
| `athf_hunt_stats` | Hunt metrics (total, TP/FP, success rate) |
| `athf_hunt_coverage` | MITRE ATT&CK coverage analysis |
| `athf_hunt_validate` | Validate hunt file structure |
| `athf_hunt_new` | Create a new hunt with LOCK structure |
| `athf_similar` | Semantic similarity search (TF-IDF) |
| `athf_context` | AI-optimized context bundle (environment + hunts + knowledge) |
| `athf_research_list` | List research documents |
| `athf_research_view` | View specific research document |
| `athf_research_search` | Search research documents |
| `athf_research_stats` | Research metrics |
| `athf_investigate_list` | List investigations |
| `athf_investigate_search` | Search investigations |
| `athf_agent_run_hypothesis` | Generate hypothesis from threat intel (LLM-powered) |
| `athf_agent_run_researcher` | Deep 5-skill pre-hunt research (LLM-powered) |

**Works with:** Claude Code, GitHub Copilot, Cursor, Windsurf, or any MCP-compatible client.

---

## External MCP Servers

You'll need to **do your own research** to find MCP servers for your organization's security tools. The section below walks through **Splunk as an example** to demonstrate the process of integrating an external MCP server with Claude Code for threat hunting workflows.

## Splunk Integration Walkthrough

**Transform your workflow:** Claude executes Splunk queries directly and analyzes results - no more copy-paste between tools.

**Official MCP:** [Splunkbase app 7931](https://splunkbase.splunk.com/app/7931)

**Complete setup guide:** [quickstart/splunk.md](quickstart/splunk.md) - 4 steps to get Splunk MCP working, includes troubleshooting and usage examples

---

## After You Complete the Splunk Example

Once you understand how MCP integration works through the Splunk walkthrough, you can find MCPs for your other security tools:

**Where to look:**

- Check vendor GitHub repositories (e.g., <https://github.com/elastic>, <https://github.com/microsoft>)
- Search the official MCP servers collection: <https://github.com/modelcontextprotocol/servers>
- Look for vendor-published MCPs on their documentation sites
- Search GitHub for "[tool-name] mcp server"

**Verify before use:**

- Is it from the official vendor or a trusted source?
- Does it have active maintenance and community support?
- Does it fit your security and compliance requirements?

---

## MCP Development Resources

Want to build an MCP for your security tool?

- **MCP Documentation:** <https://modelcontextprotocol.io/docs>
- **Python Quickstart:** <https://modelcontextprotocol.io/quickstart/server>
- **Example MCPs:** <https://github.com/modelcontextprotocol/servers>
- **Claude Code Integration:** <https://docs.claude.com/claude-code/mcp>

---

**Last Updated:** 2025-01-11
