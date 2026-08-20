"""MITRE ATT&CK MCP tools."""

from athf.mcp.server import _json_result


def register_attack_tools(mcp: "FastMCP") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Register ATT&CK-related MCP tools."""

    @mcp.tool(
        name="athf_attack_lookup",
        description=(
            "Look up a MITRE ATT&CK technique by ID (e.g., T1003, T1003.001). "
            "Returns technique name, description, tactics, platforms, and data sources."
        ),
    )
    def attack_lookup(technique_id: str) -> str:
        from athf.core.attack_matrix import get_technique

        tech = get_technique(technique_id.upper())
        if tech is None:
            return _json_result({"error": f"Technique not found: {technique_id}"})

        return _json_result({
            "technique_id": tech.get("id", technique_id),
            "name": tech.get("name", ""),
            "description": tech.get("description", ""),
            "tactics": tech.get("tactic_shortnames", []),
            "platforms": tech.get("platforms", []),
            "data_sources": tech.get("data_sources", []),
            "is_subtechnique": tech.get("is_subtechnique", False),
            "url": tech.get("url", ""),
        })

    @mcp.tool(
        name="athf_attack_techniques",
        description=(
            "List ATT&CK techniques for a given tactic "
            "(e.g., credential-access, lateral-movement, execution). "
            "Returns technique IDs, names, and platforms."
        ),
    )
    def attack_techniques(tactic: str) -> str:
        from athf.core.attack_matrix import get_techniques_for_tactic

        techniques = get_techniques_for_tactic(tactic)
        if not techniques:
            return _json_result({"error": f"No techniques found for tactic: {tactic}"})

        result = []
        for tech in techniques:
            result.append({
                "technique_id": tech.get("id", ""),
                "name": tech.get("name", ""),
                "platforms": tech.get("platforms", []),
                "is_subtechnique": tech.get("is_subtechnique", False),
            })

        return _json_result({"tactic": tactic, "count": len(result), "techniques": result})
