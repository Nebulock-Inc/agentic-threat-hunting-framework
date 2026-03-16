"""Model-aware cost estimation for LLM API calls.

Provides fuzzy model name matching and per-token cost calculation
across Anthropic, OpenAI, Google, and local/free model providers.
"""

import re
from typing import Dict, Optional, Tuple

# Pricing per 1K tokens (as of early 2026)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # Anthropic
    "claude-opus-4": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4": {"input": 0.003, "output": 0.015},
    "claude-haiku-4": {"input": 0.0008, "output": 0.004},
    # OpenAI
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "o3": {"input": 0.01, "output": 0.04},
    "o3-mini": {"input": 0.0011, "output": 0.0044},
    # Google
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.0-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    # Local/Free
    "ollama": {"input": 0.0, "output": 0.0},
    "llama": {"input": 0.0, "output": 0.0},
    "mistral": {"input": 0.0, "output": 0.0},
    "qwen": {"input": 0.0, "output": 0.0},
}


def _normalize_bedrock_model_id(model: str) -> str:
    """Strip Bedrock provider prefixes and version suffixes.

    Converts IDs like 'us.anthropic.claude-sonnet-4-5-20250929-v1:0'
    into 'claude-sonnet-4-5-20250929' for further matching.

    Args:
        model: Raw model identifier string.

    Returns:
        Normalized model name with provider prefix and version suffix removed.
    """
    # Strip known cloud provider prefixes (e.g., "us.anthropic.", "us.openai.")
    normalized = re.sub(r"^[a-z]{2}\.[a-z]+\.", "", model)
    # Strip trailing version suffixes like "-v1:0", "-v2:0"
    normalized = re.sub(r"-v\d+:\d+$", "", normalized)
    return normalized


def _resolve_pricing(model: str) -> Optional[Dict[str, float]]:
    """Resolve a model string to its pricing entry using fuzzy matching.

    Matching priority:
        1. Exact match against MODEL_PRICING keys
        2. Prefix match (pricing key is a prefix of the model string)
        3. Substring match (pricing key appears anywhere in the model string)
        4. Bedrock ID parsing then repeat steps 1-3 on the normalized form

    Longer pricing key matches are preferred (most specific wins).

    Args:
        model: The model identifier to look up.

    Returns:
        The pricing dict if a match is found, otherwise None.
    """
    model_lower = model.lower()

    # 1. Exact match
    if model_lower in MODEL_PRICING:
        return MODEL_PRICING[model_lower]

    # Helper: find best match from candidates using a match function
    def _best_match(name: str) -> Optional[Dict[str, float]]:
        # Prefix match (longest key wins)
        prefix_matches = [
            (key, pricing)
            for key, pricing in MODEL_PRICING.items()
            if name.startswith(key)
        ]
        if prefix_matches:
            best = max(prefix_matches, key=lambda kv: len(kv[0]))
            return best[1]

        # Substring match (longest key wins)
        substr_matches = [
            (key, pricing)
            for key, pricing in MODEL_PRICING.items()
            if key in name
        ]
        if substr_matches:
            best = max(substr_matches, key=lambda kv: len(kv[0]))
            return best[1]

        return None

    # 2-3. Prefix and substring match on original
    result = _best_match(model_lower)
    if result is not None:
        return result

    # 4. Bedrock normalization then retry
    normalized = _normalize_bedrock_model_id(model_lower)
    if normalized != model_lower:
        if normalized in MODEL_PRICING:
            return MODEL_PRICING[normalized]
        result = _best_match(normalized)
        if result is not None:
            return result

    return None


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate the USD cost of an LLM API call.

    Uses fuzzy model name matching to find the correct pricing tier,
    then calculates cost based on token counts.

    Args:
        model: Model identifier (e.g., "claude-sonnet-4", "gpt-4o",
               or a full Bedrock ID like "us.anthropic.claude-sonnet-4-5-20250929-v1:0").
        input_tokens: Number of input (prompt) tokens.
        output_tokens: Number of output (completion) tokens.

    Returns:
        Estimated cost in USD, rounded to 6 decimal places.
        Returns 0.0 if the model is not recognized.
    """
    pricing = _resolve_pricing(model)
    if pricing is None:
        return 0.0

    input_cost = (input_tokens / 1000.0) * pricing["input"]
    output_cost = (output_tokens / 1000.0) * pricing["output"]

    return round(input_cost + output_cost, 6)
