"""Tests that HuntResearcherAgent reports failure instead of a silent
$0.00 'success' when its LLM research skills error out.

Regression guard for the workshop-tester finding: `athf research new` ran with
Ollama, every section came back "Error during LLM analysis" (JSON parse
failures), yet the run reported "Research Complete, $0.00". A run that produced
no usable research must be loud, not look done.
"""

from unittest.mock import patch

import pytest

from athf.agents.llm.hunt_researcher import HuntResearcherAgent, ResearchInput
from athf.core.llm_provider import LLMProvider, LLMResponse


class ProseProvider(LLMProvider):
    """Provider that always returns prose the JSON parser cannot read,
    reproducing the Ollama-without-format:json failure mode."""

    def __init__(self):
        self.calls = 0

    @property
    def provider_name(self):
        return "prose-mock"

    def complete(self, messages, max_tokens=4096, temperature=0.7, response_format=None):
        self.calls += 1
        return LLMResponse(
            text="Sure! Here is a friendly prose answer with no JSON at all.",
            input_tokens=10,
            output_tokens=20,
            model="prose-model",
            duration_ms=5,
            cost_usd=0.0,
        )


def _input():
    return ResearchInput(
        topic="LSASS memory dumping",
        depth="basic",
        include_past_hunts=False,
        include_telemetry_mapping=True,
        web_search_enabled=False,
    )


@pytest.mark.unit
class TestHuntResearcherHonesty:
    def test_all_llm_skills_failing_warns_loudly(self):
        """When every LLM skill fails to parse, the doc is still written but the
        run carries a loud warning and a non-zero llm_failures count — never a
        silent clean success."""
        provider = ProseProvider()
        agent = HuntResearcherAgent(llm_enabled=True, provider=provider)

        # Isolate the LLM skills: no similarity search, no schema files.
        with patch(
            "athf.commands.similar._find_similar_hunts", return_value=[]
        ):
            result = agent.execute(_input())

        # Doc is still produced so the attendee keeps partial findings...
        assert result.data is not None
        # ...but the failure is surfaced loudly, not hidden.
        assert result.warnings
        assert any("LLM research skills failed" in w for w in result.warnings)
        assert result.metadata["llm_failures"] >= 4

    def test_llm_calls_counted_even_on_parse_failure(self):
        """The model WAS called; llm_calls must not report 0 on parse failure."""
        provider = ProseProvider()
        agent = HuntResearcherAgent(llm_enabled=True, provider=provider)

        with patch(
            "athf.commands.similar._find_similar_hunts", return_value=[]
        ):
            result = agent.execute(_input())

        assert result.metadata["llm_calls"] >= 4

    def test_json_format_requested_from_provider(self):
        """Research skills must request JSON output from the provider so a
        format-aware backend (Ollama) returns parseable JSON."""
        captured = []

        class CapturingProvider(LLMProvider):
            @property
            def provider_name(self):
                return "capture-mock"

            def complete(self, messages, max_tokens=4096, temperature=0.7, response_format=None):
                captured.append(response_format)
                return LLMResponse(
                    text='{"summary": "s", "key_findings": ["f"]}',
                    input_tokens=1,
                    output_tokens=1,
                    model="capture-model",
                    duration_ms=1,
                    cost_usd=0.0,
                )

        agent = HuntResearcherAgent(llm_enabled=True, provider=CapturingProvider())
        with patch(
            "athf.commands.similar._find_similar_hunts", return_value=[]
        ):
            result = agent.execute(_input())

        assert result.success is True
        assert captured  # at least one LLM call happened
        assert all(fmt == "json" for fmt in captured)
