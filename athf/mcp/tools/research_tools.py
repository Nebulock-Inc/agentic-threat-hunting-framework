"""Research management MCP tools."""

from typing import Optional

from athf.mcp.server import get_workspace, _json_result


def register_research_tools(mcp: "FastMCP") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Register all research-related MCP tools."""

    @mcp.tool(
        name="athf_research_list",
        description="List research documents with optional filters by status or technique.",
    )
    def research_list(
        status: Optional[str] = None,
        technique: Optional[str] = None,
    ) -> str:
        from athf.core.research_manager import ResearchManager

        workspace = get_workspace()
        manager = ResearchManager(research_dir=workspace / "research")
        results = manager.list_research(status=status, technique=technique)
        return _json_result({"count": len(results), "research": results})

    @mcp.tool(
        name="athf_research_view",
        description="View a specific research document by ID (e.g., R-0001). Returns full content and metadata.",
    )
    def research_view(research_id: str) -> str:
        from athf.core.research_manager import ResearchManager

        workspace = get_workspace()
        manager = ResearchManager(research_dir=workspace / "research")
        doc = manager.get_research(research_id)
        if doc is None:
            return _json_result({"error": f"Research not found: {research_id}"})
        return _json_result(doc)

    @mcp.tool(
        name="athf_research_search",
        description="Full-text search across research documents.",
    )
    def research_search(query: str) -> str:
        from athf.core.research_manager import ResearchManager

        workspace = get_workspace()
        manager = ResearchManager(research_dir=workspace / "research")
        results = manager.search_research(query)
        return _json_result({"count": len(results), "results": results})

    @mcp.tool(
        name="athf_research_stats",
        description="Get research metrics: total documents, completion rate, cost, and duration stats.",
    )
    def research_stats() -> str:
        from athf.core.research_manager import ResearchManager

        workspace = get_workspace()
        manager = ResearchManager(research_dir=workspace / "research")
        stats = manager.calculate_stats()
        return _json_result(stats)
