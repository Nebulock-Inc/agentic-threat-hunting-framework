# MCP Catalog for Threat Hunting

You'll need to **do your own research** to find MCP servers for your organization's security tools. This catalog walks through **Splunk as an example** to demonstrate the process of integrating an MCP server with Claude Code for threat hunting workflows.

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
