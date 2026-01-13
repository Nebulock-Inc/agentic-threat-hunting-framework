"""LLM-powered agents for ATHF.

These agents use Claude API for creative and analytical tasks.
All LLM agents have fallback to deterministic methods when LLM is disabled.
"""

from athf.agents.llm.hunt_researcher import (
    HuntResearcherAgent,
    ResearchInput,
    ResearchOutput,
    ResearchSkillOutput,
)
from athf.agents.llm.hypothesis_generator import (
    HypothesisGenerationInput,
    HypothesisGenerationOutput,
    HypothesisGeneratorAgent,
)

__all__ = [
    "HypothesisGeneratorAgent",
    "HypothesisGenerationInput",
    "HypothesisGenerationOutput",
    "HuntResearcherAgent",
    "ResearchInput",
    "ResearchOutput",
    "ResearchSkillOutput",
]
