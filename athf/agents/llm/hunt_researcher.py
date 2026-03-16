"""Hunt researcher agent - LLM-powered thorough research before hunting.

Implements a structured 5-skill research methodology:
1. System Research - How does the technology/process normally work?
2. Adversary Tradecraft - How do adversaries abuse it? (web search)
3. Telemetry Mapping - What OCSF fields and data sources capture this?
4. Related Work - What past hunts/investigations are relevant?
5. Synthesis - Key findings, gaps, recommended focus areas
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from athf.agents.base import AgentResult, LLMAgent


@dataclass
class ResearchInput:
    """Input for hunt research."""

    topic: str  # Research topic (e.g., "LSASS memory dumping")
    mitre_technique: Optional[str] = None  # Optional T-code to focus research
    depth: str = "advanced"  # "basic" (5 min) or "advanced" (15-20 min)
    include_past_hunts: bool = True
    include_telemetry_mapping: bool = True
    web_search_enabled: bool = True  # Can be disabled for offline mode


@dataclass
class ResearchSkillOutput:
    """Output from a single research skill."""

    skill_name: str  # e.g., "system_research", "adversary_tradecraft"
    summary: str
    key_findings: List[str]
    sources: List[Dict[str, str]]  # {"title": "", "url": "", "snippet": ""}
    confidence: float  # 0-1 confidence in findings
    duration_ms: int = 0


@dataclass
class ResearchOutput:
    """Complete research output following OTR-inspired 5 skills."""

    research_id: str  # R-XXXX format
    topic: str
    mitre_techniques: List[str]

    # 5 OTR-inspired research skills
    system_research: ResearchSkillOutput
    adversary_tradecraft: ResearchSkillOutput
    telemetry_mapping: ResearchSkillOutput
    related_work: ResearchSkillOutput
    synthesis: ResearchSkillOutput

    # Synthesis outputs
    recommended_hypothesis: Optional[str] = None
    data_source_availability: Dict[str, bool] = field(default_factory=dict)
    estimated_hunt_complexity: str = "medium"  # low/medium/high
    gaps_identified: List[str] = field(default_factory=list)

    # Cost tracking
    total_duration_ms: int = 0
    web_searches_performed: int = 0
    llm_calls: int = 0
    total_cost_usd: float = 0.0


class HuntResearcherAgent(LLMAgent[ResearchInput, ResearchOutput]):
    """Performs thorough research before hunt creation.

    Implements a structured 5-skill research methodology:
    1. System Research - How does the technology/process normally work?
    2. Adversary Tradecraft - How do adversaries abuse it? (web search)
    3. Telemetry Mapping - What OCSF fields and data sources capture this?
    4. Related Work - What past hunts/investigations are relevant?
    5. Research Synthesis - Key findings, gaps, recommended focus areas

    Features:
    - Web search via Tavily API for external threat intel
    - OCSF schema awareness for telemetry mapping
    - Past hunt correlation via similarity search
    - Cost tracking across all operations
    - Fallback to limited research when APIs unavailable
    """

    def __init__(
        self,
        llm_enabled: bool = True,
        tavily_api_key: Optional[str] = None,
        provider: Optional[Any] = None,
    ) -> None:
        """Initialize researcher with optional API keys."""
        super().__init__(llm_enabled=llm_enabled, provider=provider)
        self.tavily_api_key = tavily_api_key or os.getenv("TAVILY_API_KEY")
        self._search_client: Optional[Any] = None
        self._total_cost = 0.0
        self._llm_calls = 0
        self._web_searches = 0

    def _log_llm_metrics(
        self,
        agent_name: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
    ) -> None:
        """Track LLM call metrics for cost reporting."""
        self._llm_calls += 1
        self._total_cost += cost_usd

    def _get_search_client(self) -> Optional[Any]:
        """Get or create Tavily search client."""
        if self._search_client is None and self.tavily_api_key:
            try:
                from athf.core.web_search import TavilySearchClient

                self._search_client = TavilySearchClient(
                    api_key=self.tavily_api_key,
                )
            except Exception:
                pass
        return self._search_client

    def execute(
        self, input_data: ResearchInput,
    ) -> AgentResult[ResearchOutput]:
        """Execute complete research workflow.

        Args:
            input_data: Research input with topic, technique, and depth

        Returns:
            AgentResult with complete research output or error
        """
        start_time = time.time()
        self._total_cost = 0.0
        self._llm_calls = 0
        self._web_searches = 0

        try:
            # Get next research ID
            from athf.core.research_manager import ResearchManager

            manager = ResearchManager()
            research_id = manager.get_next_research_id()

            # Determine search depth based on input
            search_depth = (
                "basic" if input_data.depth == "basic" else "advanced"
            )

            # Execute skills 1-4 in parallel (they are independent)
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=4) as executor:
                future_1 = executor.submit(
                    self._skill_1_system_research, input_data.topic, search_depth,
                )
                future_2 = executor.submit(
                    self._skill_2_adversary_tradecraft,
                    input_data.topic, input_data.mitre_technique,
                    search_depth, input_data.web_search_enabled,
                )
                future_3 = executor.submit(
                    self._skill_3_telemetry_mapping,
                    input_data.topic, input_data.mitre_technique,
                )
                future_4 = executor.submit(
                    self._skill_4_related_work, input_data.topic,
                )

                skill_1 = future_1.result()
                skill_2 = future_2.result()
                skill_3 = future_3.result()
                skill_4 = future_4.result()

            # Skill 5 (synthesis) depends on skills 1-4
            skill_5 = self._skill_5_synthesis(
                input_data.topic,
                input_data.mitre_technique,
                [skill_1, skill_2, skill_3, skill_4],
            )

            # Extract synthesis outputs
            mitre_techniques = (
                [input_data.mitre_technique]
                if input_data.mitre_technique
                else []
            )

            # Build output
            total_duration_ms = int((time.time() - start_time) * 1000)

            output = ResearchOutput(
                research_id=research_id,
                topic=input_data.topic,
                mitre_techniques=mitre_techniques,
                system_research=skill_1,
                adversary_tradecraft=skill_2,
                telemetry_mapping=skill_3,
                related_work=skill_4,
                synthesis=skill_5,
                recommended_hypothesis=self._extract_hypothesis(skill_5),
                data_source_availability=self._extract_data_sources(
                    skill_3,
                ),
                estimated_hunt_complexity=self._estimate_complexity(
                    skill_2, skill_3,
                ),
                gaps_identified=self._extract_gaps(skill_5),
                total_duration_ms=total_duration_ms,
                web_searches_performed=self._web_searches,
                llm_calls=self._llm_calls,
                total_cost_usd=round(self._total_cost, 4),
            )

            return AgentResult(
                success=True,
                data=output,
                error=None,
                warnings=[],
                metadata={
                    "research_id": research_id,
                    "duration_ms": total_duration_ms,
                    "web_searches": self._web_searches,
                    "llm_calls": self._llm_calls,
                    "cost_usd": round(self._total_cost, 4),
                },
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                warnings=[],
                metadata={},
            )

    def _skill_1_system_research(
        self,
        topic: str,
        search_depth: str,
    ) -> ResearchSkillOutput:
        """Skill 1: Research how the system/technology normally works.

        Args:
            topic: Research topic
            search_depth: "basic" or "advanced"

        Returns:
            ResearchSkillOutput with system research findings
        """
        start_time = time.time()
        sources: List[Dict[str, str]] = []
        search_results = None

        # Try web search for system internals
        search_client = self._get_search_client()
        if search_client:
            try:
                search_results = search_client.search_system_internals(
                    topic, search_depth,
                )
                self._web_searches += 1

                for result in search_results.results[:5]:
                    snippet = result.content
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    sources.append({
                        "title": result.title,
                        "url": result.url,
                        "snippet": snippet,
                    })
            except Exception:
                pass

        # Generate summary using LLM
        if self.llm_enabled:
            summary, key_findings = self._llm_summarize_system_research(
                topic, sources, search_results,
            )
        else:
            summary = (
                "System research for {} - requires LLM for detailed"
                " analysis".format(topic)
            )
            key_findings = ["LLM disabled - manual research required"]

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchSkillOutput(
            skill_name="system_research",
            summary=summary,
            key_findings=key_findings,
            sources=sources,
            confidence=0.8 if sources else 0.5,
            duration_ms=duration_ms,
        )

    def _skill_2_adversary_tradecraft(
        self,
        topic: str,
        technique: Optional[str],
        search_depth: str,
        web_search_enabled: bool,
    ) -> ResearchSkillOutput:
        """Skill 2: Research adversary tradecraft via web search.

        Args:
            topic: Research topic
            technique: Optional MITRE ATT&CK technique
            search_depth: "basic" or "advanced"
            web_search_enabled: Whether web search is enabled

        Returns:
            ResearchSkillOutput with adversary tradecraft findings
        """
        start_time = time.time()
        sources: List[Dict[str, str]] = []
        search_results = None

        # Try web search for adversary tradecraft
        search_client = self._get_search_client()
        if search_client and web_search_enabled:
            try:
                search_results = (
                    search_client.search_adversary_tradecraft(
                        topic, technique, search_depth,
                    )
                )
                self._web_searches += 1

                for result in search_results.results[:7]:
                    snippet = result.content
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    sources.append({
                        "title": result.title,
                        "url": result.url,
                        "snippet": snippet,
                    })
            except Exception:
                pass

        # Generate summary using LLM
        if self.llm_enabled:
            summary, key_findings = self._llm_summarize_tradecraft(
                topic, technique, sources, search_results,
            )
        else:
            summary = (
                "Adversary tradecraft for {} - requires LLM for"
                " detailed analysis".format(topic)
            )
            key_findings = ["LLM disabled - manual research required"]

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchSkillOutput(
            skill_name="adversary_tradecraft",
            summary=summary,
            key_findings=key_findings,
            sources=sources,
            confidence=0.85 if sources else 0.4,
            duration_ms=duration_ms,
        )

    def _skill_3_telemetry_mapping(
        self,
        topic: str,
        technique: Optional[str],
    ) -> ResearchSkillOutput:
        """Skill 3: Map to OCSF fields and available data sources.

        Args:
            topic: Research topic
            technique: Optional MITRE ATT&CK technique

        Returns:
            ResearchSkillOutput with telemetry mapping
        """
        start_time = time.time()
        sources: List[Dict[str, str]] = []

        # Load OCSF schema reference
        ocsf_schema = self._load_ocsf_schema()
        environment_data = self._load_environment()

        # Generate telemetry mapping using LLM
        if self.llm_enabled:
            summary, key_findings = self._llm_map_telemetry(
                topic, technique, ocsf_schema, environment_data,
            )
        else:
            summary = (
                "Telemetry mapping for {} - requires LLM for"
                " detailed analysis".format(topic)
            )
            key_findings = [
                "Common fields: process.name, process.command_line,"
                " actor.user.name",
                "Check OCSF_SCHEMA_REFERENCE.md for field population"
                " rates",
            ]

        # Add schema reference as source
        sources.append({
            "title": "OCSF Schema Reference",
            "url": "knowledge/OCSF_SCHEMA_REFERENCE.md",
            "snippet": (
                "Internal schema documentation with field population"
                " rates"
            ),
        })

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchSkillOutput(
            skill_name="telemetry_mapping",
            summary=summary,
            key_findings=key_findings,
            sources=sources,
            confidence=0.9,  # High confidence - based on internal schema
            duration_ms=duration_ms,
        )

    def _skill_4_related_work(
        self, topic: str,
    ) -> ResearchSkillOutput:
        """Skill 4: Find related past hunts and investigations.

        Args:
            topic: Research topic

        Returns:
            ResearchSkillOutput with related work
        """
        start_time = time.time()
        sources: List[Dict[str, str]] = []
        key_findings: List[str] = []

        # Use similarity search to find related hunts
        try:
            from athf.commands.similar import _find_similar_hunts

            similar_hunts = _find_similar_hunts(
                topic, limit=5, threshold=0.1,
            )

            for hunt in similar_hunts:
                sources.append({
                    "title": "{}: {}".format(
                        hunt["hunt_id"], hunt["title"],
                    ),
                    "url": "hunts/{}.md".format(hunt["hunt_id"]),
                    "snippet": "Status: {}, Score: {:.3f}".format(
                        hunt["status"], hunt["similarity_score"],
                    ),
                })
                key_findings.append(
                    "{}: {} (similarity: {:.2f})".format(
                        hunt["hunt_id"],
                        hunt["title"],
                        hunt["similarity_score"],
                    )
                )

        except Exception:
            key_findings.append(
                "No similar hunts found or similarity search unavailable"
            )

        summary = "Found {} related hunts for {}".format(
            len(sources), topic,
        )
        if not sources:
            summary = (
                "No related hunts found for {} - this may be a new"
                " research area".format(topic)
            )

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchSkillOutput(
            skill_name="related_work",
            summary=summary,
            key_findings=(
                key_findings
                if key_findings
                else ["No related past hunts found"]
            ),
            sources=sources,
            confidence=0.95,  # High confidence - based on internal search
            duration_ms=duration_ms,
        )

    def _skill_5_synthesis(
        self,
        topic: str,
        technique: Optional[str],
        skills: List[ResearchSkillOutput],
    ) -> ResearchSkillOutput:
        """Skill 5: Synthesize all research into actionable insights.

        Args:
            topic: Research topic
            technique: Optional MITRE ATT&CK technique
            skills: Outputs from skills 1-4

        Returns:
            ResearchSkillOutput with synthesis
        """
        start_time = time.time()

        # Generate synthesis using LLM
        if self.llm_enabled:
            summary, key_findings = self._llm_synthesize(
                topic, technique, skills,
            )
        else:
            summary = "Research synthesis for {}".format(topic)
            key_findings = [
                "LLM disabled - manual synthesis required",
                "Review individual skill outputs for findings",
            ]

        duration_ms = int((time.time() - start_time) * 1000)

        return ResearchSkillOutput(
            skill_name="synthesis",
            summary=summary,
            key_findings=key_findings,
            sources=[],  # Synthesis doesn't have external sources
            confidence=0.8,
            duration_ms=duration_ms,
        )

    def _llm_summarize_system_research(
        self,
        topic: str,
        sources: List[Dict[str, str]],
        search_results: Optional[Any],
    ) -> Tuple[str, List[str]]:
        """Use LLM to summarize system research findings."""
        try:
            # Build context from sources
            context = ""
            if (
                search_results
                and hasattr(search_results, "answer")
                and search_results.answer
            ):
                context = "Web search summary: {}\n\n".format(
                    search_results.answer,
                )

            for source in sources[:5]:
                context += "- {}: {}\n".format(
                    source["title"], source["snippet"],
                )

            prompt = (
                "You are a security researcher studying system"
                " internals.\n\n"
                "Topic: {topic}\n\n"
                "Research Context:\n{context}\n\n"
                "Based on this context, provide:\n"
                "1. A concise summary (2-3 sentences) of how this"
                " system/technology normally works\n"
                "2. 3-5 key findings about normal behavior\n\n"
                "Return JSON format:\n"
                '{{\n  "summary": "string",\n'
                '  "key_findings": ["finding1", "finding2",'
                ' "finding3"]\n}}'
            ).format(topic=topic, context=context)

            response = self._call_llm(prompt, max_tokens=2048)
            data = self._parse_json_response(response)
            return data["summary"], data["key_findings"]

        except Exception as e:
            return (
                "System research for {} (LLM error: {})".format(
                    topic, str(e)[:50],
                ),
                ["Error during LLM analysis"],
            )

    def _llm_summarize_tradecraft(
        self,
        topic: str,
        technique: Optional[str],
        sources: List[Dict[str, str]],
        search_results: Optional[Any],
    ) -> Tuple[str, List[str]]:
        """Use LLM to summarize adversary tradecraft findings."""
        try:
            # Build context from sources
            context = ""
            if (
                search_results
                and hasattr(search_results, "answer")
                and search_results.answer
            ):
                context = "Web search summary: {}\n\n".format(
                    search_results.answer,
                )

            for source in sources[:7]:
                context += "- {}: {}\n".format(
                    source["title"], source["snippet"],
                )

            technique_str = (
                " ({})".format(technique) if technique else ""
            )

            prompt = (
                "You are a threat intelligence analyst studying"
                " adversary techniques.\n\n"
                "Topic: {topic}{technique_str}\n\n"
                "Research Context:\n{context}\n\n"
                "Based on this context, provide:\n"
                "1. A concise summary (2-3 sentences) of how"
                " adversaries abuse this system/technique\n"
                "2. 4-6 key findings about attack methods, tools"
                " used, and indicators\n\n"
                "Return JSON format:\n"
                '{{\n  "summary": "string",\n'
                '  "key_findings": ["finding1", "finding2",'
                ' "finding3", "finding4"]\n}}'
            ).format(
                topic=topic,
                technique_str=technique_str,
                context=context,
            )

            response = self._call_llm(prompt, max_tokens=2048)
            data = self._parse_json_response(response)
            return data["summary"], data["key_findings"]

        except Exception as e:
            return (
                "Adversary tradecraft for {} (LLM error: {})".format(
                    topic, str(e)[:50],
                ),
                ["Error during LLM analysis"],
            )

    def _llm_map_telemetry(
        self,
        topic: str,
        technique: Optional[str],
        ocsf_schema: str,
        environment_data: str,
    ) -> Tuple[str, List[str]]:
        """Use LLM to map topic to OCSF telemetry fields."""
        try:
            technique_str = (
                " ({})".format(technique) if technique else ""
            )

            prompt = (
                "You are a detection engineer mapping attack"
                " behaviors to telemetry.\n\n"
                "Topic: {topic}{technique_str}\n\n"
                "OCSF Schema Reference (partial):\n"
                "{ocsf_schema}\n\n"
                "Environment:\n{environment_data}\n\n"
                "Based on this context, provide:\n"
                "1. A concise summary of what telemetry would"
                " capture this behavior\n"
                "2. 4-6 specific OCSF fields that are relevant,"
                " with population rates if known\n\n"
                "Return JSON format:\n"
                '{{\n  "summary": "string",\n'
                '  "key_findings": ["field1 (X% populated):'
                ' description", "field2: description"]\n}}'
            ).format(
                topic=topic,
                technique_str=technique_str,
                ocsf_schema=ocsf_schema[:3000],
                environment_data=environment_data[:1000],
            )

            response = self._call_llm(prompt, max_tokens=2048)
            data = self._parse_json_response(response)
            return data["summary"], data["key_findings"]

        except Exception as e:
            return (
                "Telemetry mapping for {} (LLM error: {})".format(
                    topic, str(e)[:50],
                ),
                ["Error during LLM analysis"],
            )

    def _llm_synthesize(
        self,
        topic: str,
        technique: Optional[str],
        skills: List[ResearchSkillOutput],
    ) -> Tuple[str, List[str]]:
        """Use LLM to synthesize all research findings."""
        try:
            # Build context from all skills
            context = ""
            for skill in skills:
                skill_title = skill.skill_name.replace("_", " ").title()
                context += "\n### {}\n".format(skill_title)
                context += "Summary: {}\n".format(skill.summary)
                context += "Key findings:\n"
                for finding in skill.key_findings[:4]:
                    context += "- {}\n".format(finding)

            technique_str = (
                " ({})".format(technique) if technique else ""
            )

            prompt = (
                "You are a senior threat hunter synthesizing"
                " research for a hunt.\n\n"
                "Topic: {topic}{technique_str}\n\n"
                "Research Findings:\n{context}\n\n"
                "Based on all research findings, provide:\n"
                "1. An executive summary (2-3 sentences)"
                " synthesizing all findings\n"
                '2. A recommended hypothesis statement in the'
                ' format: "Adversaries use [behavior] to [goal]'
                ' on [target]"\n'
                "3. 2-3 gaps identified in current coverage or"
                " knowledge\n"
                "4. 2-3 recommended focus areas for the hunt\n\n"
                "Return JSON format:\n"
                '{{\n  "summary": "string",\n'
                '  "key_findings": [\n'
                '    "Hypothesis: Adversaries use...",\n'
                '    "Gap: ...",\n'
                '    "Focus: ..."\n'
                "  ]\n}}"
            ).format(
                topic=topic,
                technique_str=technique_str,
                context=context,
            )

            response = self._call_llm(prompt, max_tokens=2048)
            data = self._parse_json_response(response)
            return data["summary"], data["key_findings"]

        except Exception as e:
            return (
                "Research synthesis for {} (LLM error: {})".format(
                    topic, str(e)[:50],
                ),
                ["Error during LLM analysis"],
            )

    def _load_ocsf_schema(self) -> str:
        """Load OCSF schema reference content."""
        schema_path = (
            Path.cwd() / "knowledge" / "OCSF_SCHEMA_REFERENCE.md"
        )
        if schema_path.exists():
            return schema_path.read_text()[:5000]  # Limit size
        return "OCSF schema reference not found"

    def _load_environment(self) -> str:
        """Load environment.md content."""
        env_path = Path.cwd() / "environment.md"
        if env_path.exists():
            return env_path.read_text()[:2000]  # Limit size
        return "Environment file not found"

    def _extract_hypothesis(
        self, synthesis: ResearchSkillOutput,
    ) -> Optional[str]:
        """Extract recommended hypothesis from synthesis."""
        for finding in synthesis.key_findings:
            if finding.lower().startswith("hypothesis:"):
                return (
                    finding
                    .replace("Hypothesis:", "")
                    .replace("hypothesis:", "")
                    .strip()
                )
        return None

    def _extract_data_sources(
        self, telemetry: ResearchSkillOutput,
    ) -> Dict[str, bool]:
        """Extract data source availability from telemetry mapping."""
        # Default data sources based on environment
        return {
            "process_execution": True,
            "file_operations": True,
            "network_connections": False,
            "registry_events": False,
        }

    def _estimate_complexity(
        self,
        tradecraft: ResearchSkillOutput,
        telemetry: ResearchSkillOutput,
    ) -> str:
        """Estimate hunt complexity based on research."""
        total_findings = (
            len(tradecraft.key_findings) + len(telemetry.key_findings)
        )

        if total_findings <= 4:
            return "low"
        elif total_findings <= 8:
            return "medium"
        else:
            return "high"

    def _extract_gaps(
        self, synthesis: ResearchSkillOutput,
    ) -> List[str]:
        """Extract identified gaps from synthesis."""
        gaps = []
        for finding in synthesis.key_findings:
            if finding.lower().startswith("gap:"):
                gaps.append(
                    finding
                    .replace("Gap:", "")
                    .replace("gap:", "")
                    .strip()
                )
        return gaps
