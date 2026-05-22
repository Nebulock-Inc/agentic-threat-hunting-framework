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

    @mcp.tool(
        name="athf_research_new",
        description=(
            "Run deep research on a security topic using Tavily web search "
            "and the ATHF 5-skill methodology (system internals, adversary tradecraft, "
            "telemetry mapping, related work, synthesis). Returns a structured report "
            "with sourced findings, recommended hypothesis, and identified gaps. "
            "Also saves an R-XXXX document to the research directory."
        ),
    )
    def research_new(
        topic: str,
        technique: Optional[str] = None,
        depth: Optional[str] = "advanced",
    ) -> str:
        from athf.agents.llm.hunt_researcher import HuntResearcherAgent, ResearchInput
        from athf.core.research_manager import ResearchManager

        if not topic or not topic.strip():
            return _json_result({"error": "topic is required and must be a non-empty string"})

        if isinstance(depth, str):
            depth = depth.strip()
        depth = depth or "advanced"
        if depth not in {"basic", "advanced"}:
            return _json_result({"error": f"depth must be 'basic' or 'advanced' (got {depth!r})"})

        workspace = get_workspace()
        manager = ResearchManager(research_dir=workspace / "research")

        agent = HuntResearcherAgent(llm_enabled=True)
        result = agent.execute(
            ResearchInput(
                topic=topic,
                mitre_technique=technique,
                depth=depth,
                include_past_hunts=True,
                include_telemetry_mapping=True,
                web_search_enabled=True,
            )
        )

        if not result.success or result.data is None:
            return _json_result({"error": result.error or "Research failed"})

        output = result.data

        # Generate and save the research document
        from athf.commands.research import _generate_research_markdown
        markdown_content = _generate_research_markdown(output)
        frontmatter = {
            "research_id": output.research_id,
            "topic": output.topic,
            "mitre_techniques": output.mitre_techniques,
            "status": "completed",
            "depth": depth,
            "duration_minutes": round(output.total_duration_ms / 60000, 1),
            "linked_hunts": [],
            "web_searches": output.web_searches_performed,
            "llm_calls": output.llm_calls,
            "total_cost_usd": output.total_cost_usd,
        }
        file_path = manager.create_research_file(
            research_id=output.research_id,
            topic=output.topic,
            content=markdown_content,
            frontmatter=frontmatter,
        )

        return _json_result({
            "research_id": output.research_id,
            "topic": output.topic,
            "file_path": str(file_path),
            "duration_seconds": round(output.total_duration_ms / 1000, 1),
            "cost_usd": output.total_cost_usd,
            "system_research": {
                "summary": output.system_research.summary,
                "key_findings": output.system_research.key_findings,
                "sources": output.system_research.sources,
            },
            "adversary_tradecraft": {
                "summary": output.adversary_tradecraft.summary,
                "key_findings": output.adversary_tradecraft.key_findings,
                "sources": output.adversary_tradecraft.sources,
            },
            "telemetry_mapping": {
                "summary": output.telemetry_mapping.summary,
                "key_findings": output.telemetry_mapping.key_findings,
            },
            "related_work": {
                "summary": output.related_work.summary,
                "key_findings": output.related_work.key_findings,
            },
            "synthesis": {
                "summary": output.synthesis.summary,
                "key_findings": output.synthesis.key_findings,
            },
            "recommended_hypothesis": output.recommended_hypothesis,
            "gaps_identified": output.gaps_identified,
            "estimated_hunt_complexity": output.estimated_hunt_complexity,
            "next_steps": [
                f"Review full research: athf research view {output.research_id}",
                f"Create hunt: athf hunt new --research {output.research_id}",
                "Generate hypothesis: athf agent run hypothesis-generator",
            ],
        })
