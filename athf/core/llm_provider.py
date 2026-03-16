"""Model-agnostic LLM provider abstraction for ATHF.

Supports multiple LLM backends (LiteLLM, AWS Bedrock, Ollama, OpenAI-compatible)
with lazy imports so no single provider's dependencies are required at install time.

Usage:
    from athf.core.llm_provider import create_provider

    provider = create_provider()  # auto-detect from env/config
    response = provider.complete(
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=1024,
    )
    print(response.text, response.cost_usd)
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

# Per-1K-token pricing (input, output) for common models.
# Used as a best-effort fallback when the provider does not report cost.
_MODEL_PRICING = {
    # Anthropic Claude via Bedrock / direct
    "claude-sonnet-4-5": (0.003, 0.015),
    "claude-sonnet-4-5-20250929": (0.003, 0.015),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "claude-3-opus": (0.015, 0.075),
    "claude-3-5-haiku": (0.0008, 0.004),
    # OpenAI
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-4": (0.03, 0.06),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    # Default fallback
    "_default": (0.003, 0.015),
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate LLM call cost in USD based on token counts.

    Attempts to import the canonical cost_tracker first; falls back to a
    built-in pricing table when the module is not available.

    Args:
        model: Model identifier string.
        input_tokens: Number of input/prompt tokens.
        output_tokens: Number of output/completion tokens.

    Returns:
        Estimated cost in USD, rounded to 6 decimal places.
    """
    try:
        from athf.core.cost_tracker import estimate_cost

        return estimate_cost(model, input_tokens, output_tokens)
    except (ImportError, AttributeError):
        pass

    # Local fallback: match the longest key that appears in the model string.
    model_lower = model.lower()
    best_key = "_default"
    best_len = 0
    for key in _MODEL_PRICING:
        if key != "_default" and key in model_lower and len(key) > best_len:
            best_key = key
            best_len = len(key)

    input_rate, output_rate = _MODEL_PRICING[best_key]
    cost = (input_tokens / 1000.0) * input_rate + (output_tokens / 1000.0) * output_rate
    return round(cost, 6)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class LLMResponse:
    """Response from an LLM provider call.

    Attributes:
        text: The generated text content.
        input_tokens: Number of prompt/input tokens consumed.
        output_tokens: Number of completion/output tokens generated.
        model: Model identifier used for the request.
        duration_ms: Wall-clock time of the LLM call in milliseconds.
        cost_usd: Estimated cost of the call in USD.
    """

    text: str
    input_tokens: int
    output_tokens: int
    model: str
    duration_ms: int
    cost_usd: float


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Subclasses must implement ``complete`` and ``provider_name``.
    """

    @abstractmethod
    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a chat-completion request to the LLM.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (0.0 - 1.0).

        Returns:
            An LLMResponse with the generated text and metadata.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable name for this provider (e.g. ``'bedrock'``)."""
        ...


# ---------------------------------------------------------------------------
# LiteLLM provider (100+ models)
# ---------------------------------------------------------------------------


class LiteLLMProvider(LLMProvider):
    """Provider backed by the ``litellm`` library.

    Supports 100+ models via a unified interface. The ``litellm`` package is
    imported lazily so it is only required when this provider is actually used.

    Args:
        model: A litellm-compatible model string (e.g. ``"anthropic/claude-sonnet-4-5-20250514"``).
    """

    def __init__(self, model: str = "anthropic/claude-sonnet-4-5-20250514"):
        self.model = model

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "litellm"

    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Complete a chat request via litellm.

        Args:
            messages: Chat messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with results and metrics.

        Raises:
            ImportError: If litellm is not installed.
        """
        try:
            import litellm  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "litellm package is not installed. Install it with: pip install litellm"
            )

        start = time.monotonic()
        response = litellm.completion(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        text = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0

        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            duration_ms=duration_ms,
            cost_usd=_estimate_cost(self.model, input_tokens, output_tokens),
        )


# ---------------------------------------------------------------------------
# AWS Bedrock provider (backward-compatible)
# ---------------------------------------------------------------------------


class BedrockProvider(LLMProvider):
    """Provider for AWS Bedrock with the Anthropic Messages API.

    Preserves the exact request/response pattern used by the existing ATHF
    codebase for backward compatibility.

    Args:
        model_id: Bedrock model identifier.
        region: AWS region. Defaults to ``AWS_REGION`` / ``AWS_DEFAULT_REGION``
            env vars, then ``us-east-1``.
    """

    def __init__(
        self,
        model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region: Optional[str] = None,
    ):
        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        self._client = None  # type: Any

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "bedrock"

    def _get_client(self) -> Any:
        """Lazily create and cache the Bedrock runtime client.

        Returns:
            A boto3 Bedrock runtime client.

        Raises:
            ImportError: If boto3 is not installed.
            ValueError: If client creation fails (e.g. bad credentials).
        """
        if self._client is not None:
            return self._client

        try:
            import boto3  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError("boto3 package is not installed. Install it with: pip install boto3")

        try:
            self._client = boto3.client(service_name="bedrock-runtime", region_name=self.region)
        except Exception as exc:
            raise ValueError("Failed to create Bedrock client: {}".format(exc))

        return self._client

    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a chat-completion request to AWS Bedrock.

        Args:
            messages: Chat messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with results and metrics.

        Raises:
            ImportError: If boto3 is not installed.
            ValueError: If Bedrock client creation or invocation fails.
        """
        client = self._get_client()

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }

        start = time.monotonic()
        response = client.invoke_model(modelId=self.model_id, body=json.dumps(request_body))
        duration_ms = int((time.monotonic() - start) * 1000)

        response_body = json.loads(response["body"].read())
        text = response_body["content"][0]["text"]

        usage = response_body.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model_id,
            duration_ms=duration_ms,
            cost_usd=_estimate_cost(self.model_id, input_tokens, output_tokens),
        )


# ---------------------------------------------------------------------------
# Ollama provider (local models, stdlib only)
# ---------------------------------------------------------------------------


class OllamaProvider(LLMProvider):
    """Provider for locally-running Ollama models.

    Uses only ``urllib.request`` from the standard library so there are zero
    external dependencies.

    Args:
        model: Ollama model name (e.g. ``"llama3"``).
        base_url: Ollama HTTP API base URL.
    """

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "ollama"

    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a chat request to the local Ollama API.

        Args:
            messages: Chat messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with results and metrics.

        Raises:
            ConnectionError: If Ollama is not reachable.
        """
        import urllib.request
        import urllib.error

        url = "{}/api/chat".format(self.base_url)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        start = time.monotonic()
        try:
            resp = urllib.request.urlopen(req)
        except urllib.error.URLError as exc:
            raise ConnectionError(
                "Cannot reach Ollama at {}. Is it running? Error: {}".format(self.base_url, exc)
            )
        duration_ms = int((time.monotonic() - start) * 1000)

        body = json.loads(resp.read().decode("utf-8"))
        text = body.get("message", {}).get("content", "")

        # Ollama may report token counts in eval_count / prompt_eval_count
        input_tokens = body.get("prompt_eval_count", 0) or 0
        output_tokens = body.get("eval_count", 0) or 0

        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            duration_ms=duration_ms,
            cost_usd=0.0,  # Local models are free
        )


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------


class OpenAICompatibleProvider(LLMProvider):
    """Provider for any OpenAI-compatible API endpoint.

    Works with OpenAI, Azure OpenAI, vLLM, text-generation-inference, and
    other servers that expose the ``/v1/chat/completions`` interface.

    The ``openai`` package is imported lazily.

    Args:
        model: Model name to request (e.g. ``"gpt-4o"``).
        api_key: API key. Falls back to ``OPENAI_API_KEY`` env var.
        base_url: Optional base URL override for non-OpenAI endpoints.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url
        self._client = None  # type: Any

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    def _get_client(self) -> Any:
        """Lazily create and cache the OpenAI client.

        Returns:
            An ``openai.OpenAI`` client instance.

        Raises:
            ImportError: If the openai package is not installed.
        """
        if self._client is not None:
            return self._client

        try:
            import openai  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "openai package is not installed. Install it with: pip install openai"
            )

        kwargs = {}  # type: Dict[str, Any]
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url

        self._client = openai.OpenAI(**kwargs)
        return self._client

    def complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a chat-completion request to an OpenAI-compatible API.

        Args:
            messages: Chat messages.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.

        Returns:
            LLMResponse with results and metrics.

        Raises:
            ImportError: If the openai package is not installed.
        """
        client = self._get_client()

        start = time.monotonic()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        duration_ms = int((time.monotonic() - start) * 1000)

        text = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0

        return LLMResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            duration_ms=duration_ms,
            cost_usd=_estimate_cost(self.model, input_tokens, output_tokens),
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

# Canonical mapping from config/env strings to provider classes.
_PROVIDER_MAP = {
    "litellm": "LiteLLMProvider",
    "bedrock": "BedrockProvider",
    "ollama": "OllamaProvider",
    "openai": "OpenAICompatibleProvider",
}


def _load_config_file() -> Dict[str, Any]:
    """Load LLM settings from .athfconfig.yaml if present.

    Searches two conventional locations relative to the current working directory:
    ``./config/.athfconfig.yaml`` and ``./.athfconfig.yaml``.

    Returns:
        The ``llm`` section of the config as a dict, or an empty dict.
    """
    from pathlib import Path

    candidates = [
        Path.cwd() / "config" / ".athfconfig.yaml",
        Path.cwd() / ".athfconfig.yaml",
    ]

    for path in candidates:
        if path.is_file():
            try:
                import yaml  # type: ignore[import-untyped]

                with open(str(path), "r") as fh:
                    data = yaml.safe_load(fh) or {}
                return data.get("llm", {})
            except ImportError:
                # PyYAML not installed; try stdlib JSON fallback (unlikely to work, but safe)
                logger.debug("PyYAML not installed; skipping config file %s", path)
            except Exception as exc:
                logger.debug("Failed to read config %s: %s", path, exc)

    return {}


def _ollama_is_running(base_url: str = "http://localhost:11434") -> bool:
    """Check whether an Ollama instance is reachable.

    Args:
        base_url: Ollama HTTP API base URL.

    Returns:
        True if Ollama responds to a version request.
    """
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request("{}/api/version".format(base_url))
        resp = urllib.request.urlopen(req, timeout=2)
        return resp.status == 200
    except Exception:
        return False


def create_provider(config: Optional[Dict[str, Any]] = None) -> LLMProvider:
    """Create an LLM provider using a layered configuration strategy.

    Resolution order:

    1. Explicit ``config`` dict (``provider``, ``model``, plus provider-specific keys).
    2. Environment variables: ``ATHF_LLM_PROVIDER``, ``ATHF_LLM_MODEL``.
    3. ``.athfconfig.yaml`` ``llm`` section.
    4. Auto-detection based on available API keys / running services.

    Auto-detection order:
        ``ANTHROPIC_API_KEY`` -> LiteLLM (Anthropic)
        ``OPENAI_API_KEY`` -> OpenAI-compatible
        ``AWS_PROFILE`` or ``AWS_ACCESS_KEY_ID`` -> Bedrock
        Ollama running locally -> Ollama
        Otherwise -> raises RuntimeError

    Args:
        config: Optional configuration dictionary with keys such as
            ``provider``, ``model``, ``api_key``, ``base_url``, ``region``.

    Returns:
        A configured LLMProvider instance.

    Raises:
        RuntimeError: If no provider can be determined.
        ValueError: If an unknown provider name is given.
    """
    effective = {}  # type: Dict[str, Any]

    # Layer 1: config file
    file_config = _load_config_file()
    if file_config:
        effective.update(file_config)

    # Layer 2: environment variables
    env_provider = os.getenv("ATHF_LLM_PROVIDER")
    env_model = os.getenv("ATHF_LLM_MODEL")
    if env_provider:
        effective["provider"] = env_provider
    if env_model:
        effective["model"] = env_model

    # Layer 3: explicit config dict (highest priority)
    if config:
        effective.update(config)

    provider_name = effective.get("provider", "").lower()
    model = effective.get("model")

    # --- Explicit provider requested ---
    if provider_name:
        return _build_provider(provider_name, model, effective)

    # --- Auto-detection ---
    logger.debug("No explicit LLM provider configured; auto-detecting...")

    # Anthropic API key -> LiteLLM with anthropic prefix
    if os.getenv("ANTHROPIC_API_KEY"):
        detected_model = model or "anthropic/claude-sonnet-4-5-20250514"
        logger.info("Auto-detected ANTHROPIC_API_KEY -> using LiteLLM provider with model %s", detected_model)
        return LiteLLMProvider(model=detected_model)

    # OpenAI API key -> OpenAI-compatible provider
    if os.getenv("OPENAI_API_KEY"):
        detected_model = model or "gpt-4o"
        logger.info("Auto-detected OPENAI_API_KEY -> using OpenAI provider with model %s", detected_model)
        return OpenAICompatibleProvider(
            model=detected_model,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=effective.get("base_url"),
        )

    # AWS credentials -> Bedrock
    if os.getenv("AWS_PROFILE") or os.getenv("AWS_ACCESS_KEY_ID"):
        detected_model = model or "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
        logger.info("Auto-detected AWS credentials -> using Bedrock provider with model %s", detected_model)
        return BedrockProvider(
            model_id=detected_model,
            region=effective.get("region"),
        )

    # Ollama running locally
    ollama_url = effective.get("base_url", "http://localhost:11434")
    if _ollama_is_running(ollama_url):
        detected_model = model or "llama3"
        logger.info("Auto-detected local Ollama -> using Ollama provider with model %s", detected_model)
        return OllamaProvider(model=detected_model, base_url=ollama_url)

    raise RuntimeError(
        "No LLM provider could be determined. Set one of: "
        "ATHF_LLM_PROVIDER env var, ANTHROPIC_API_KEY, OPENAI_API_KEY, "
        "AWS_PROFILE/AWS_ACCESS_KEY_ID, or start a local Ollama instance. "
        "Alternatively, add an 'llm' section to .athfconfig.yaml."
    )


def _build_provider(name: str, model: Optional[str], config: Dict[str, Any]) -> LLMProvider:
    """Instantiate a specific provider by name.

    Args:
        name: Provider name (e.g. ``"bedrock"``, ``"litellm"``).
        model: Optional model override.
        config: Full effective config dict for provider-specific keys.

    Returns:
        A configured LLMProvider instance.

    Raises:
        ValueError: If the provider name is not recognized.
    """
    if name not in _PROVIDER_MAP:
        raise ValueError(
            "Unknown LLM provider '{}'. Supported providers: {}".format(
                name, ", ".join(sorted(_PROVIDER_MAP.keys()))
            )
        )

    if name == "litellm":
        return LiteLLMProvider(model=model or "anthropic/claude-sonnet-4-5-20250514")

    if name == "bedrock":
        return BedrockProvider(
            model_id=model or "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region=config.get("region"),
        )

    if name == "ollama":
        return OllamaProvider(
            model=model or "llama3",
            base_url=config.get("base_url", "http://localhost:11434"),
        )

    if name == "openai":
        return OpenAICompatibleProvider(
            model=model or "gpt-4o",
            api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY", ""),
            base_url=config.get("base_url"),
        )

    # Unreachable given the _PROVIDER_MAP check, but satisfies type checkers.
    raise ValueError("Unknown provider: {}".format(name))
