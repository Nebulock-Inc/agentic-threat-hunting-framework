"""AI agent MCP tools (hypothesis generation, research)."""

import logging
from typing import Optional

from athf.mcp.server import get_workspace, _json_result

logger = logging.getLogger(__name__)


def register_agent_tools(mcp: "FastMCP") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Register AI agent MCP tools."""

    @mcp.tool(
        name="athf_agent_run_hypothesis",
        description=(
            "Generate a threat hunting hypothesis from threat intelligence. "
            "Uses an LLM to produce a structured hypothesis with MITRE techniques, "
            "data sources, and ABLE framework scoping. "
            "Requires an LLM provider to be configured (falls back to template-based output without one)."
        ),
    )
    def agent_run_hypothesis(
        threat_intel: str,
        research_id: Optional[str] = None,
        use_llm: bool = True,
    ) -> str:
        from athf.agents.llm.hypothesis_generator import (
            HypothesisGeneratorAgent,
            HypothesisGenerationInput,
        )

        workspace = get_workspace()

        # Load research context if provided
        research = None
        if research_id:
            from athf.core.research_manager import ResearchManager

            rm = ResearchManager(research_dir=workspace / "research")
            doc = rm.get_research(research_id)
            if doc:
                research = rm.extract_research_context(doc)

        # Load past hunts and environment context from workspace
        from athf.core.hunt_manager import HuntManager

        manager = HuntManager(hunts_dir=workspace / "hunts")
        past_hunts = manager.list_hunts()

        env_file = workspace / "environment.md"
        environment = {"environment_md": env_file.read_text(encoding="utf-8")} if env_file.exists() else {}

        agent = HypothesisGeneratorAgent(llm_enabled=use_llm)
        input_data = HypothesisGenerationInput(
            threat_intel=threat_intel,
            past_hunts=past_hunts,
            environment=environment,
            research=research,
        )

        result = agent.execute(input_data)
        if not result.success:
            return _json_result({"error": result.error or "Hypothesis generation failed"})

        output = result.data
        if output is None:
            return _json_result({"error": "No output from hypothesis generator"})

        return _json_result({
            "hypothesis": output.hypothesis,
            "mitre_techniques": output.mitre_techniques,
            "data_sources": output.data_sources,
            "justification": output.justification,
            "metadata": result.metadata,
        })

    @mcp.tool(
        name="athf_agent_run_researcher",
        description=(
            "Conduct deep pre-hunt research on a topic using the 5-skill methodology: "
            "System Internals, Adversary Tradecraft, Telemetry Mapping, Historical Analysis, "
            "and Synthesis. Uses web search (Tavily) and LLM analysis. "
            "Creates a research document (R-XXXX.md) in the workspace."
        ),
    )
    def agent_run_researcher(
        topic: str,
        technique: Optional[str] = None,
        depth: str = "advanced",
        use_web_search: bool = True,
        use_llm: bool = True,
    ) -> str:
        import os

        from athf.agents.llm.hunt_researcher import HuntResearcherAgent, ResearchInput

        workspace = get_workspace()

        tavily_key = os.environ.get("TAVILY_API_KEY") if use_web_search else None

        agent = HuntResearcherAgent(llm_enabled=use_llm, tavily_api_key=tavily_key)
        input_data = ResearchInput(
            topic=topic,
            mitre_technique=technique,
            depth=depth,
            web_search_enabled=use_web_search,
        )

        result = agent.execute(input_data)
        if not result.success:
            return _json_result({"error": result.error or "Research failed"})

        output = result.data
        if output is None:
            return _json_result({"error": "No output from researcher"})

        # Build a report from the skill outputs
        report_parts = [
            f"# {topic} Research\n",
            f"## System Research\n{output.system_research.summary}\n",
            f"## Adversary Tradecraft\n{output.adversary_tradecraft.summary}\n",
            f"## Telemetry Mapping\n{output.telemetry_mapping.summary}\n",
            f"## Related Work\n{output.related_work.summary}\n",
            f"## Synthesis\n{output.synthesis.summary}\n",
        ]
        if output.recommended_hypothesis:
            report_parts.append(f"## Recommended Hypothesis\n{output.recommended_hypothesis}\n")

        full_report = "\n".join(report_parts)

        # Save research file — use agent's research_id if available, else generate
        from athf.core.research_manager import ResearchManager

        rm = ResearchManager(research_dir=workspace / "research")
        rid = getattr(output, "research_id", None) or rm.get_next_research_id()

        frontmatter = {
            "research_id": rid,
            "title": f"{topic} Research",
            "topic": topic,
            "technique": technique or "",
            "depth": depth,
            "status": "completed",
        }

        file_path = rm.create_research_file(
            research_id=rid,
            topic=topic,
            content=full_report,
            frontmatter=frontmatter,
        )

        return _json_result({
            "research_id": rid,
            "file_path": str(file_path),
            "topic": topic,
            "depth": depth,
            "recommended_hypothesis": output.recommended_hypothesis,
            "gaps_identified": output.gaps_identified,
            "metadata": result.metadata,
        })
