"""LLM-powered agents for ATHF.

These agents use a model-agnostic provider abstraction supporting
Claude, GPT, Gemini, Ollama, and any OpenAI-compatible endpoint.
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
    ResearchContext,
)

__all__ = [
    "HypothesisGeneratorAgent",
    "HypothesisGenerationInput",
    "HypothesisGenerationOutput",
    "ResearchContext",
    "HuntResearcherAgent",
    "ResearchInput",
    "ResearchOutput",
    "ResearchSkillOutput",
]
