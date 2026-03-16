"""Base classes for ATHF agents."""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

# Type variables for input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

logger = logging.getLogger(__name__)


@dataclass
class AgentResult(Generic[OutputT]):
    """Standard result format for all agents."""

    success: bool
    data: Optional[OutputT]
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if the agent execution was successful."""
        return self.success and self.error is None


class Agent(ABC, Generic[InputT, OutputT]):
    """Base class for all agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agent with optional configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._setup()

    def _setup(self) -> None:
        """Optional setup method for subclasses."""
        pass

    @abstractmethod
    def execute(self, input_data: InputT) -> AgentResult[OutputT]:
        """Execute agent logic.

        Args:
            input_data: Input for the agent

        Returns:
            AgentResult with output data or error
        """
        pass

    def __call__(self, input_data: InputT) -> AgentResult[OutputT]:
        """Allow calling agent as a function."""
        return self.execute(input_data)


class DeterministicAgent(Agent[InputT, OutputT]):
    """Base class for deterministic Python agents (no LLM)."""

    pass


class LLMAgent(Agent[InputT, OutputT]):
    """Base class for LLM-powered agents.

    Uses the model-agnostic provider abstraction from athf.core.llm_provider.
    Supports Claude, GPT, Gemini, Ollama, and any OpenAI-compatible endpoint.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        llm_enabled: bool = True,
        provider: Optional[Any] = None,
    ):
        """Initialize LLM agent.

        Args:
            config: Optional configuration dictionary
            llm_enabled: Whether to enable LLM functionality
            provider: Optional pre-configured LLMProvider instance. If None,
                auto-detects from environment/config when first needed.
        """
        self.llm_enabled = llm_enabled
        self._provider = provider
        super().__init__(config)

    def _get_provider(self) -> Any:
        """Get or create an LLM provider.

        Uses the provider abstraction layer which auto-detects the available
        LLM backend from environment variables and configuration.

        Returns:
            LLMProvider instance

        Raises:
            RuntimeError: If no provider can be determined
        """
        if self._provider is not None:
            return self._provider

        from athf.core.llm_provider import create_provider

        llm_config = self.config.get("llm", {})
        self._provider = create_provider(llm_config if llm_config else None)
        return self._provider

    def _call_llm(self, prompt: str, max_tokens: int = 4096) -> str:
        """Call the LLM and return response text.

        Provider-agnostic: works with any configured LLM backend.

        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum tokens to generate.

        Returns:
            The generated text content.
        """
        provider = self._get_provider()
        response = provider.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

        self._log_llm_metrics(
            agent_name=self.__class__.__name__,
            model_id=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
            duration_ms=response.duration_ms,
        )

        result: str = response.text
        return result

    def _call_llm_with_retry(
        self,
        prompt: str,
        validate_fn: Callable[[str], Optional[str]],
        max_retries: int = 2,
        max_tokens: int = 4096,
    ) -> str:
        """Call LLM with a validation-retry loop.

        If the response fails validation, appends the error feedback to the
        prompt and retries up to ``max_retries`` times.

        Args:
            prompt: The prompt to send to the LLM.
            validate_fn: A function that takes the response text and returns
                None if valid, or an error string if invalid.
            max_retries: Maximum number of retry attempts.
            max_tokens: Maximum tokens to generate.

        Returns:
            The generated text (last attempt, even if imperfect).
        """
        current_prompt = prompt
        result = ""

        for attempt in range(1 + max_retries):
            result = self._call_llm(current_prompt, max_tokens=max_tokens)
            error = validate_fn(result)
            if error is None:
                return result
            if attempt < max_retries:
                logger.debug("LLM response validation failed (attempt %d): %s", attempt + 1, error)
                current_prompt = (
                    "{}\n\nYour previous response had an error: {}\n"
                    "Please fix the issue and try again. Return valid JSON only.".format(prompt, error)
                )

        return result

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from an LLM response.

        Handles responses wrapped in markdown code blocks.

        Args:
            text: Raw LLM response text.

        Returns:
            Parsed JSON as a dictionary.

        Raises:
            ValueError: If JSON cannot be extracted or parsed.
        """
        cleaned = text.strip()

        # Try to extract JSON from markdown code blocks
        if "```json" in cleaned:
            json_start = cleaned.find("```json") + 7
            json_end = cleaned.find("```", json_start)
            if json_end > json_start:
                cleaned = cleaned[json_start:json_end].strip()
        elif "```" in cleaned:
            json_start = cleaned.find("```") + 3
            json_end = cleaned.find("```", json_start)
            if json_end > json_start:
                cleaned = cleaned[json_start:json_end].strip()

        try:
            parsed: Dict[str, Any] = json.loads(cleaned)
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(
                "Failed to parse JSON from LLM response. Error: {}. "
                "Response text (first 500 chars): {}".format(e, cleaned[:500])
            )

    def _log_llm_metrics(
        self,
        agent_name: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
    ) -> None:
        """Log LLM call metrics to centralized tracker.

        Override this method in subclasses or plugins to implement custom metrics tracking.

        Args:
            agent_name: Name of the agent (e.g., "hypothesis-generator")
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Estimated cost in USD
            duration_ms: Call duration in milliseconds
        """
        # No-op by default. Override in plugins for custom metrics tracking.
        pass
