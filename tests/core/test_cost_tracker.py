"""Tests for athf.core.cost_tracker - model-aware cost estimation."""

import pytest

from athf.core.cost_tracker import (
    MODEL_PRICING,
    _normalize_bedrock_model_id,
    _resolve_pricing,
    estimate_cost,
)


# ---------------------------------------------------------------------------
# _resolve_pricing tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestResolvePricing:
    """Test the fuzzy model-name matching logic."""

    def test_exact_match_pricing(self):
        """Exact model key returns the correct pricing dict."""
        pricing = _resolve_pricing("claude-sonnet-4")
        assert pricing is not None
        assert pricing == MODEL_PRICING["claude-sonnet-4"]

    def test_prefix_match(self):
        """A model string that starts with a known key matches via prefix."""
        pricing = _resolve_pricing("claude-sonnet-4-5-20250929")
        # Should match "claude-sonnet-4" (longest prefix key)
        assert pricing is not None
        assert pricing["input"] == MODEL_PRICING["claude-sonnet-4"]["input"]

    def test_substring_match(self):
        """A model string containing a known key matches via substring."""
        pricing = _resolve_pricing("us.openai.gpt-4o-2024")
        # "gpt-4o" is a substring; should match
        assert pricing is not None
        assert pricing["input"] == MODEL_PRICING["gpt-4o"]["input"]

    def test_bedrock_model_id(self):
        """Full Bedrock ARN-style IDs resolve after normalization."""
        pricing = _resolve_pricing(
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )
        assert pricing is not None
        # After stripping prefix and version suffix the normalized form
        # "claude-sonnet-4-5-20250929" should prefix-match "claude-sonnet-4".
        assert pricing["input"] == MODEL_PRICING["claude-sonnet-4"]["input"]

    def test_ollama_free(self):
        """Local/free models like llama resolve to zero-cost pricing."""
        pricing = _resolve_pricing("llama")
        assert pricing is not None
        assert pricing["input"] == 0.0
        assert pricing["output"] == 0.0

    def test_unknown_model(self):
        """A completely unknown model string returns None."""
        pricing = _resolve_pricing("some-random-model")
        assert pricing is None


# ---------------------------------------------------------------------------
# _normalize_bedrock_model_id tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestNormalizeBedrockModelId:
    """Test Bedrock model ID normalization."""

    def test_normalize_bedrock_strips_prefix(self):
        """Provider prefix like 'us.anthropic.' is removed."""
        result = _normalize_bedrock_model_id("us.anthropic.claude-sonnet-4-5")
        assert result == "claude-sonnet-4-5"

    def test_normalize_bedrock_strips_version(self):
        """Trailing version suffix like '-v1:0' is removed."""
        result = _normalize_bedrock_model_id("claude-sonnet-4-5-v1:0")
        assert result == "claude-sonnet-4-5"

    def test_normalize_bedrock_strips_both(self):
        """Both prefix and version suffix are removed together."""
        result = _normalize_bedrock_model_id(
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        )
        assert result == "claude-sonnet-4-5-20250929"

    def test_normalize_bedrock_noop(self):
        """A plain model name is returned unchanged."""
        result = _normalize_bedrock_model_id("claude-sonnet-4")
        assert result == "claude-sonnet-4"


# ---------------------------------------------------------------------------
# estimate_cost tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEstimateCost:
    """Test end-to-end cost estimation."""

    def test_zero_tokens(self):
        """Zero input and output tokens produce zero cost."""
        cost = estimate_cost("claude-sonnet-4", 0, 0)
        assert cost == 0.0

    def test_cost_calculation(self):
        """Verify arithmetic for a known pricing entry."""
        # claude-sonnet-4: input=0.003/1K, output=0.015/1K
        input_tokens = 1000
        output_tokens = 500
        expected = (1000 / 1000.0) * 0.003 + (500 / 1000.0) * 0.015
        expected = round(expected, 6)  # 0.003 + 0.0075 = 0.0105

        cost = estimate_cost("claude-sonnet-4", input_tokens, output_tokens)
        assert cost == expected

    def test_unknown_model_returns_zero(self):
        """An unrecognized model returns 0.0 cost."""
        cost = estimate_cost("some-random-model", 1000, 1000)
        assert cost == 0.0

    def test_bedrock_id_cost(self):
        """Full Bedrock model IDs still produce a non-zero cost."""
        cost = estimate_cost(
            "us.anthropic.claude-sonnet-4-5-20250929-v1:0", 1000, 500
        )
        assert cost > 0.0

    def test_ollama_free_cost(self):
        """Ollama/local models produce zero cost even with tokens."""
        cost = estimate_cost("llama", 5000, 3000)
        assert cost == 0.0
