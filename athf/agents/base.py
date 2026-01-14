"""Base classes for hunt-vault agents."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Type variables for input/output
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


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
    """Base class for LLM-powered agents."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, llm_enabled: bool = True):
        """Initialize LLM agent.

        Args:
            config: Optional configuration dictionary
            llm_enabled: Whether to enable LLM functionality
        """
        self.llm_enabled = llm_enabled
        super().__init__(config)

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

        Args:
            agent_name: Name of the agent (e.g., "hypothesis-generator")
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost_usd: Estimated cost in USD
            duration_ms: Call duration in milliseconds
        """
        try:
            from athf.core.metrics_tracker import MetricsTracker

            MetricsTracker.get_instance().log_bedrock_call(
                agent=agent_name,
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                duration_ms=duration_ms,
            )
        except Exception:
            pass  # Never fail agent execution due to metrics logging

    def _get_llm_client(self) -> Any:
        """Get AWS Bedrock runtime client for Claude models.

        Returns:
            Bedrock runtime client instance or None if LLM is disabled

        Raises:
            ValueError: If AWS credentials are not configured
            ImportError: If boto3 package is not installed
        """
        if not self.llm_enabled:
            return None

        try:
            import boto3

            # Get AWS region from environment or use default
            region = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

            # Create Bedrock runtime client
            # Uses AWS credentials from environment, ~/.aws/credentials, or IAM role
            client = boto3.client(service_name="bedrock-runtime", region_name=region)

            return client
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")
        except Exception as e:
            raise ValueError(f"Failed to create Bedrock client: {e}")
