# Agentic Capabilities Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 6 agentic capabilities (reasoning loop, tool calling, session state, orchestration, checkpoints, event triggers) to the ATHF public framework.

**Architecture:** Layered Agent Runtime — new abstractions build on the existing `Agent` base class and `PluginRegistry`. Native Claude `tool_use` API behind an `LLMProvider` abstraction. All new features are optional — existing agents and CLI commands unchanged.

**Tech Stack:** Python 3.8+, click, pyyaml, rich, dataclasses, boto3 (optional), anthropic (optional)

**Design Doc:** `docs/plans/2026-02-15-agentic-capabilities-design.md`

---

## Phase 1: LLM Provider Abstraction

### Task 1.1: Tool Types (ToolResult, ToolCall)

**Files:**
- Create: `athf/agents/tools.py`
- Test: `tests/agents/test_tools.py`

**Step 1: Write failing tests**

```python
# tests/agents/test_tools.py
"""Tests for agent tool types."""
import pytest

from athf.agents.tools import ToolCall, ToolDefinition, ToolResult


class TestToolResult:
    def test_success_result(self):
        result = ToolResult(success=True, output={"count": 42})
        assert result.success is True
        assert result.output == {"count": 42}
        assert result.error is None
        assert result.metadata == {}

    def test_error_result(self):
        result = ToolResult(success=False, output=None, error="Query timeout")
        assert result.success is False
        assert result.error == "Query timeout"

    def test_result_with_metadata(self):
        result = ToolResult(success=True, output="ok", metadata={"duration_ms": 150})
        assert result.metadata["duration_ms"] == 150


class TestToolCall:
    def test_tool_call_fields(self):
        call = ToolCall(id="tc_001", name="search_hunts", input={"query": "kerberos"})
        assert call.id == "tc_001"
        assert call.name == "search_hunts"
        assert call.input == {"query": "kerberos"}


class TestToolDefinition:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ToolDefinition()

    def test_concrete_tool_definition(self):
        class EchoTool(ToolDefinition):
            name = "echo"
            description = "Echo input back"
            input_schema = {"type": "object", "properties": {"text": {"type": "string"}}}

            def execute(self, input_data):
                return ToolResult(success=True, output=input_data["text"])

        tool = EchoTool()
        assert tool.name == "echo"
        result = tool.execute({"text": "hello"})
        assert result.output == "hello"

    def test_tool_to_schema(self):
        class DummyTool(ToolDefinition):
            name = "dummy"
            description = "A dummy tool"
            input_schema = {"type": "object", "properties": {"x": {"type": "integer"}}}

            def execute(self, input_data):
                return ToolResult(success=True, output=None)

        schema = DummyTool().to_schema()
        assert schema["name"] == "dummy"
        assert schema["description"] == "A dummy tool"
        assert "input_schema" in schema
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_tools.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'athf.agents.tools'`

**Step 3: Implement**

```python
# athf/agents/tools.py
"""Tool definitions for ATHF agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """A request from the LLM to call a tool."""

    id: str
    name: str
    input: Dict[str, Any]


class ToolDefinition(ABC):
    """Base class for tools that agents can invoke."""

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """Execute the tool with given input.

        Args:
            input_data: Tool input matching input_schema

        Returns:
            ToolResult with output or error
        """
        ...

    def to_schema(self) -> Dict[str, Any]:
        """Convert to Claude tool_use schema format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_tools.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add athf/agents/tools.py tests/agents/test_tools.py
git commit -m "feat(agents): add tool types — ToolDefinition, ToolResult, ToolCall"
```

---

### Task 1.2: LLM Provider Abstraction

**Files:**
- Create: `athf/agents/providers.py`
- Test: `tests/agents/test_providers.py`

**Step 1: Write failing tests**

```python
# tests/agents/test_providers.py
"""Tests for LLM provider abstraction."""
import pytest

from athf.agents.providers import LLMProvider, LLMResponse, TokenUsage
from athf.agents.tools import ToolCall


class TestTokenUsage:
    def test_token_usage(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

    def test_cost_calculation(self):
        usage = TokenUsage(input_tokens=1000, output_tokens=500)
        # Default Claude Sonnet pricing
        cost = usage.cost_usd()
        assert cost > 0
        assert isinstance(cost, float)

    def test_custom_pricing(self):
        usage = TokenUsage(input_tokens=1000, output_tokens=1000)
        cost = usage.cost_usd(input_price_per_1k=0.01, output_price_per_1k=0.03)
        assert cost == pytest.approx(0.04)


class TestLLMResponse:
    def test_text_response(self):
        resp = LLMResponse(
            text="Analysis complete",
            tool_calls=[],
            stop_reason="end_turn",
            usage=TokenUsage(input_tokens=100, output_tokens=50),
            raw_content=[{"type": "text", "text": "Analysis complete"}],
        )
        assert resp.text == "Analysis complete"
        assert resp.stop_reason == "end_turn"
        assert len(resp.tool_calls) == 0

    def test_tool_use_response(self):
        tc = ToolCall(id="tc_1", name="search", input={"query": "test"})
        resp = LLMResponse(
            text=None,
            tool_calls=[tc],
            stop_reason="tool_use",
            usage=TokenUsage(input_tokens=200, output_tokens=100),
            raw_content=[],
        )
        assert resp.stop_reason == "tool_use"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "search"

    def test_has_tool_calls(self):
        resp = LLMResponse(
            text="hi", tool_calls=[], stop_reason="end_turn",
            usage=TokenUsage(input_tokens=10, output_tokens=5), raw_content=[],
        )
        assert resp.has_tool_calls is False


class TestLLMProviderABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_concrete_provider(self):
        class MockProvider(LLMProvider):
            def invoke(self, messages, system=None, tools=None, max_tokens=4096):
                return LLMResponse(
                    text="mock", tool_calls=[], stop_reason="end_turn",
                    usage=TokenUsage(input_tokens=10, output_tokens=5),
                    raw_content=[{"type": "text", "text": "mock"}],
                )

            def cost_per_1k_tokens(self):
                return (0.003, 0.015)

        provider = MockProvider()
        resp = provider.invoke([{"role": "user", "content": "test"}])
        assert resp.text == "mock"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_providers.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# athf/agents/providers.py
"""LLM provider abstraction for ATHF agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from athf.agents.tools import ToolCall, ToolDefinition


@dataclass
class TokenUsage:
    """Token usage from an LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0

    def cost_usd(
        self,
        input_price_per_1k: float = 0.003,
        output_price_per_1k: float = 0.015,
    ) -> float:
        """Calculate cost in USD.

        Args:
            input_price_per_1k: Price per 1000 input tokens
            output_price_per_1k: Price per 1000 output tokens

        Returns:
            Cost in USD
        """
        return (self.input_tokens / 1000 * input_price_per_1k) + (
            self.output_tokens / 1000 * output_price_per_1k
        )


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    text: Optional[str]
    tool_calls: List[ToolCall]
    stop_reason: str  # "end_turn", "tool_use", "max_tokens"
    usage: TokenUsage
    raw_content: List[Dict[str, Any]]  # Provider-specific content blocks

    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool call requests."""
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def invoke(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Invoke the LLM.

        Args:
            messages: Conversation messages
            system: System prompt
            tools: Tool definitions in provider format
            max_tokens: Maximum output tokens

        Returns:
            LLMResponse with text, tool calls, and usage
        """
        ...

    @abstractmethod
    def cost_per_1k_tokens(self) -> Tuple[float, float]:
        """Return (input_price_per_1k, output_price_per_1k)."""
        ...
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_providers.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add athf/agents/providers.py tests/agents/test_providers.py
git commit -m "feat(agents): add LLM provider abstraction — LLMProvider, LLMResponse, TokenUsage"
```

---

### Task 1.3: Bedrock Anthropic Provider

**Files:**
- Create: `athf/agents/providers_bedrock.py`
- Test: `tests/agents/test_providers_bedrock.py`

**Step 1: Write failing tests**

```python
# tests/agents/test_providers_bedrock.py
"""Tests for Bedrock Anthropic provider."""
import json
from unittest.mock import MagicMock, patch

import pytest

from athf.agents.providers import LLMResponse, TokenUsage
from athf.agents.providers_bedrock import BedrockAnthropicProvider
from athf.agents.tools import ToolCall


class TestBedrockAnthropicProvider:
    def test_init_default_model(self):
        with patch("athf.agents.providers_bedrock.boto3"):
            provider = BedrockAnthropicProvider()
            assert "claude" in provider.model_id.lower() or "anthropic" in provider.model_id.lower()

    def test_init_custom_model(self):
        with patch("athf.agents.providers_bedrock.boto3"):
            provider = BedrockAnthropicProvider(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")
            assert provider.model_id == "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_invoke_text_response(self):
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [{"type": "text", "text": "Hello"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }).encode())
        }

        with patch("athf.agents.providers_bedrock.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            provider = BedrockAnthropicProvider()
            resp = provider.invoke(
                messages=[{"role": "user", "content": "Hi"}],
                system="You are helpful",
            )

        assert isinstance(resp, LLMResponse)
        assert resp.text == "Hello"
        assert resp.stop_reason == "end_turn"
        assert resp.usage.input_tokens == 10
        assert len(resp.tool_calls) == 0

    def test_invoke_tool_use_response(self):
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {
            "body": MagicMock(read=lambda: json.dumps({
                "content": [
                    {"type": "tool_use", "id": "tc_1", "name": "search", "input": {"q": "test"}},
                ],
                "stop_reason": "tool_use",
                "usage": {"input_tokens": 50, "output_tokens": 30},
            }).encode())
        }

        with patch("athf.agents.providers_bedrock.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_client
            provider = BedrockAnthropicProvider()
            resp = provider.invoke(
                messages=[{"role": "user", "content": "Search"}],
                tools=[{"name": "search", "description": "Search", "input_schema": {}}],
            )

        assert resp.stop_reason == "tool_use"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].name == "search"
        assert resp.tool_calls[0].input == {"q": "test"}

    def test_cost_per_1k_tokens(self):
        with patch("athf.agents.providers_bedrock.boto3"):
            provider = BedrockAnthropicProvider()
            input_cost, output_cost = provider.cost_per_1k_tokens()
            assert input_cost > 0
            assert output_cost > 0
            assert output_cost > input_cost  # Output is always more expensive
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_providers_bedrock.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# athf/agents/providers_bedrock.py
"""AWS Bedrock Anthropic provider for ATHF agents."""

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from athf.agents.providers import LLMProvider, LLMResponse, TokenUsage
from athf.agents.tools import ToolCall

try:
    import boto3
except ImportError:
    boto3 = None  # type: ignore


class BedrockAnthropicProvider(LLMProvider):
    """LLM provider using AWS Bedrock with Claude models."""

    def __init__(
        self,
        model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region: Optional[str] = None,
        max_retries: int = 2,
    ):
        if boto3 is None:
            raise ImportError("boto3 is required for BedrockAnthropicProvider. Run: pip install boto3")

        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        self.max_retries = max_retries
        self._client = boto3.client(service_name="bedrock-runtime", region_name=self.region)

    def invoke(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Invoke Claude via Bedrock invoke_model API."""
        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }

        if system:
            body["system"] = system

        if tools:
            body["tools"] = tools

        response = self._client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        return self._parse_response(result)

    def _parse_response(self, result: Dict[str, Any]) -> LLMResponse:
        """Parse Bedrock response into LLMResponse."""
        content_blocks = result.get("content", [])
        usage_data = result.get("usage", {})

        text_parts = []
        tool_calls = []

        for block in content_blocks:
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block["id"],
                        name=block["name"],
                        input=block.get("input", {}),
                    )
                )

        return LLMResponse(
            text="\n".join(text_parts) if text_parts else None,
            tool_calls=tool_calls,
            stop_reason=result.get("stop_reason", "end_turn"),
            usage=TokenUsage(
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
            ),
            raw_content=content_blocks,
        )

    def cost_per_1k_tokens(self) -> Tuple[float, float]:
        """Return Claude Sonnet 4.5 Bedrock pricing."""
        # Claude Sonnet 4.5 via Bedrock
        return (0.003, 0.015)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_providers_bedrock.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add athf/agents/providers_bedrock.py tests/agents/test_providers_bedrock.py
git commit -m "feat(agents): add BedrockAnthropicProvider with tool_use support"
```

---

### Task 1.4: Extend PluginRegistry with tool/pipeline/trigger registries

**Files:**
- Modify: `athf/plugin_system.py`
- Test: `tests/test_plugin_system.py`

**Step 1: Write failing tests**

```python
# tests/test_plugin_system.py
"""Tests for extended plugin system."""
import pytest

from athf.plugin_system import PluginRegistry


class TestPluginRegistryTools:
    def setup_method(self):
        PluginRegistry._tools = {}
        PluginRegistry._pipelines = {}
        PluginRegistry._triggers = {}

    def test_register_and_get_tool(self):
        class FakeTool:
            name = "fake"

        PluginRegistry.register_tool("fake", FakeTool)
        assert PluginRegistry.get_tool("fake") is FakeTool

    def test_get_unknown_tool_returns_none(self):
        assert PluginRegistry.get_tool("nonexistent") is None


class TestPluginRegistryPipelines:
    def setup_method(self):
        PluginRegistry._pipelines = {}

    def test_register_and_get_pipeline(self):
        fake_pipeline = {"name": "test"}
        PluginRegistry.register_pipeline("test", fake_pipeline)
        assert PluginRegistry.get_pipeline("test") is fake_pipeline

    def test_get_unknown_pipeline_returns_none(self):
        assert PluginRegistry.get_pipeline("nonexistent") is None


class TestPluginRegistryTriggers:
    def setup_method(self):
        PluginRegistry._triggers = {}

    def test_register_and_get_trigger(self):
        fake_trigger = {"name": "hourly"}
        PluginRegistry.register_trigger("hourly", fake_trigger)
        assert PluginRegistry.get_trigger("hourly") is fake_trigger

    def test_get_unknown_trigger_returns_none(self):
        assert PluginRegistry.get_trigger("nonexistent") is None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_plugin_system.py -v`
Expected: FAIL — `AttributeError: type object 'PluginRegistry' has no attribute '_tools'`

**Step 3: Modify `athf/plugin_system.py`**

Add these class attributes and methods to `PluginRegistry` (after the existing `_commands` attribute at line 23):

```python
    _tools: Dict[str, Type[Any]] = {}
    _pipelines: Dict[str, Any] = {}
    _triggers: Dict[str, Any] = {}

    @classmethod
    def register_tool(cls, name: str, tool_class: Type[Any]) -> None:
        """Register a tool plugin."""
        cls._tools[name] = tool_class

    @classmethod
    def get_tool(cls, name: str) -> Optional[Type[Any]]:
        """Get registered tool by name."""
        return cls._tools.get(name)

    @classmethod
    def register_pipeline(cls, name: str, pipeline: Any) -> None:
        """Register a pipeline."""
        cls._pipelines[name] = pipeline

    @classmethod
    def get_pipeline(cls, name: str) -> Optional[Any]:
        """Get registered pipeline by name."""
        return cls._pipelines.get(name)

    @classmethod
    def register_trigger(cls, name: str, trigger: Any) -> None:
        """Register an event trigger."""
        cls._triggers[name] = trigger

    @classmethod
    def get_trigger(cls, name: str) -> Optional[Any]:
        """Get registered trigger by name."""
        return cls._triggers.get(name)
```

Also add entry point loading for `athf.tools`, `athf.pipelines`, `athf.triggers` inside `load_plugins()` following the existing pattern for `athf.commands` and `athf.agents`.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_plugin_system.py -v`
Expected: All 6 tests PASS

**Step 5: Verify existing tests still pass**

Run: `pytest tests/ -v`
Expected: All existing tests PASS (backward compatible)

**Step 6: Commit**

```bash
git add athf/plugin_system.py tests/test_plugin_system.py
git commit -m "feat(plugins): extend PluginRegistry with tool, pipeline, and trigger registries"
```

---

### Task 1.5: Update pyproject.toml and package exports

**Files:**
- Modify: `pyproject.toml`
- Modify: `athf/agents/__init__.py`

**Step 1: Update pyproject.toml**

Add to `[project.optional-dependencies]`:

```toml
reasoning = ["boto3>=1.26.0"]
anthropic = ["anthropic>=0.39.0"]
```

Add `"athf.tools"` to `[tool.setuptools] packages` list.

Add to `[[tool.mypy.overrides]]` module list: `"anthropic"`, `"anthropic.*"`.

**Step 2: Update athf/agents/__init__.py**

```python
from athf.agents.base import Agent, AgentResult, DeterministicAgent, LLMAgent
from athf.agents.providers import LLMProvider, LLMResponse, TokenUsage
from athf.agents.tools import ToolCall, ToolDefinition, ToolResult

__all__ = [
    "Agent",
    "AgentResult",
    "DeterministicAgent",
    "LLMAgent",
    "LLMProvider",
    "LLMResponse",
    "TokenUsage",
    "ToolCall",
    "ToolDefinition",
    "ToolResult",
]
```

**Step 3: Verify all tests pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add pyproject.toml athf/agents/__init__.py
git commit -m "chore: update package exports and optional dependencies for reasoning layer"
```

---

## Phase 2: Tool System (Built-in Tools)

### Task 2.1: SimilarHuntTool

**Files:**
- Create: `athf/tools/__init__.py`
- Create: `athf/tools/builtin.py`
- Test: `tests/tools/test_builtin.py`

**Step 1: Write failing tests**

```python
# tests/tools/__init__.py
# (empty)

# tests/tools/test_builtin.py
"""Tests for built-in ATHF tools."""
from unittest.mock import patch, MagicMock

import pytest

from athf.agents.tools import ToolResult
from athf.tools.builtin import SimilarHuntTool


class TestSimilarHuntTool:
    def test_tool_metadata(self):
        tool = SimilarHuntTool()
        assert tool.name == "similar_hunt_search"
        assert "similar" in tool.description.lower()
        assert tool.input_schema["type"] == "object"
        assert "query" in tool.input_schema["properties"]

    def test_to_schema_format(self):
        schema = SimilarHuntTool().to_schema()
        assert schema["name"] == "similar_hunt_search"
        assert "input_schema" in schema

    def test_execute_returns_tool_result(self):
        tool = SimilarHuntTool()
        # Mock the underlying athf.commands.similar module
        with patch("athf.tools.builtin._find_similar_hunts") as mock_find:
            mock_find.return_value = [
                {"hunt_id": "H-0001", "title": "Test Hunt", "similarity": 0.85}
            ]
            result = tool.execute({"query": "kerberoasting", "limit": 5})

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert len(result.output) == 1
        assert result.output[0]["hunt_id"] == "H-0001"

    def test_execute_handles_error(self):
        tool = SimilarHuntTool()
        with patch("athf.tools.builtin._find_similar_hunts", side_effect=Exception("no sklearn")):
            result = tool.execute({"query": "test"})

        assert result.success is False
        assert "no sklearn" in result.error
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/tools/test_builtin.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement**

```python
# athf/tools/__init__.py
"""ATHF tool definitions."""

# athf/tools/builtin.py
"""Built-in tools that wrap existing ATHF CLI functionality."""

from typing import Any, Dict, List

from athf.agents.tools import ToolDefinition, ToolResult


def _find_similar_hunts(query: str, limit: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
    """Wrapper around athf.commands.similar._find_similar_hunts."""
    try:
        from athf.commands.similar import _find_similar_hunts as find_fn

        return find_fn(query=query, limit=limit, threshold=threshold)
    except ImportError:
        return []


class SimilarHuntTool(ToolDefinition):
    """Search for similar past hunts using semantic similarity."""

    name = "similar_hunt_search"
    description = (
        "Search for similar past hunts using semantic similarity. "
        "Use this before creating new hunts to avoid duplicates. "
        "Returns hunt IDs, titles, and similarity scores."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language description of the hunt topic to search for",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """Execute semantic search across past hunts."""
        try:
            query = input_data["query"]
            limit = input_data.get("limit", 5)
            results = _find_similar_hunts(query=query, limit=limit)
            return ToolResult(success=True, output=results)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class HuntSearchTool(ToolDefinition):
    """Full-text search across hunt files."""

    name = "hunt_search"
    description = "Full-text keyword search across all hunt files. Returns matching hunts with context."
    input_schema = {
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Keyword or phrase to search for in hunt files",
            },
        },
        "required": ["keyword"],
    }

    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """Execute keyword search across hunts."""
        try:
            from athf.core.hunt_manager import HuntManager

            manager = HuntManager()
            results = manager.search_hunts(input_data["keyword"])
            return ToolResult(success=True, output=results)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class WebSearchTool(ToolDefinition):
    """Search the web for threat intelligence using Tavily."""

    name = "web_search"
    description = (
        "Search the web for threat intelligence, attack techniques, and security research. "
        "Uses Tavily API. Requires TAVILY_API_KEY environment variable."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for threat intelligence",
            },
            "search_depth": {
                "type": "string",
                "enum": ["basic", "advanced"],
                "description": "Search depth (default: basic)",
                "default": "basic",
            },
        },
        "required": ["query"],
    }

    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """Execute web search via Tavily."""
        try:
            from athf.core.web_search import TavilySearchClient

            client = TavilySearchClient()
            results = client.search_threat_intel(
                topic=input_data["query"],
                search_depth=input_data.get("search_depth", "basic"),
            )
            return ToolResult(success=True, output=results)
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/tools/test_builtin.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add athf/tools/__init__.py athf/tools/builtin.py tests/tools/__init__.py tests/tools/test_builtin.py
git commit -m "feat(tools): add built-in tools — SimilarHuntTool, HuntSearchTool, WebSearchTool"
```

---

## Phase 3: Reasoning Loop

### Task 3.1: RunState and StepRecord

**Files:**
- Create: `athf/agents/reasoning.py`
- Test: `tests/agents/test_reasoning.py`

**Step 1: Write failing tests**

```python
# tests/agents/test_reasoning.py
"""Tests for reasoning agent types."""
import pytest

from athf.agents.reasoning import RunState, StepRecord
from athf.agents.tools import ToolCall, ToolResult


class TestStepRecord:
    def test_step_record_fields(self):
        tc = ToolCall(id="tc_1", name="search", input={"q": "test"})
        tr = ToolResult(success=True, output="found")
        record = StepRecord(step=0, tool_call=tc, result=tr, duration_ms=150)
        assert record.step == 0
        assert record.tool_call.name == "search"
        assert record.result.output == "found"
        assert record.duration_ms == 150
        assert record.timestamp  # Auto-populated


class TestRunState:
    def test_default_state(self):
        state = RunState(input="test input")
        assert state.input == "test input"
        assert state.evidence == []
        assert state.messages == []
        assert state.step_count == 0
        assert state.total_cost_usd == 0.0
        assert state.store == {}

    def test_add_step(self):
        state = RunState(input="x")
        tc = ToolCall(id="tc_1", name="search", input={})
        tr = ToolResult(success=True, output="ok")
        state.add_step(tc, tr, duration_ms=100)
        assert len(state.evidence) == 1
        assert state.evidence[0].tool_call.name == "search"

    def test_store_for_domain_state(self):
        state = RunState(input="x")
        state.store["hostname"] = "endpoint-abc"
        state.store["zscore"] = 8.7
        assert state.store["hostname"] == "endpoint-abc"

    def test_accumulate_cost(self):
        state = RunState(input="x")
        state.total_cost_usd += 0.024
        state.total_cost_usd += 0.031
        assert state.total_cost_usd == pytest.approx(0.055)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_reasoning.py::TestStepRecord -v`
Expected: FAIL

**Step 3: Implement RunState and StepRecord**

```python
# athf/agents/reasoning.py
"""Reasoning agent with tool_use loop for ATHF."""

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional

from athf.agents.base import AgentResult, LLMAgent
from athf.agents.providers import LLMProvider, LLMResponse, TokenUsage
from athf.agents.tools import ToolCall, ToolDefinition, ToolResult

# Re-use the existing TypeVar
from athf.agents.base import InputT, OutputT


@dataclass
class StepRecord:
    """Record of a single tool call within a reasoning run."""

    step: int
    tool_call: ToolCall
    result: ToolResult
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RunState(Generic[InputT]):
    """State maintained during a single agent.run() execution."""

    input: InputT
    evidence: List[StepRecord] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    step_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    store: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, tool_call: ToolCall, result: ToolResult, duration_ms: int = 0) -> None:
        """Record a tool call step."""
        self.evidence.append(
            StepRecord(
                step=self.step_count,
                tool_call=tool_call,
                result=result,
                duration_ms=duration_ms,
            )
        )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_reasoning.py -v`
Expected: All 5 tests PASS

**Step 5: Commit**

```bash
git add athf/agents/reasoning.py tests/agents/test_reasoning.py
git commit -m "feat(agents): add RunState and StepRecord for reasoning loop state management"
```

---

### Task 3.2: ReasoningAgent base class

**Files:**
- Modify: `athf/agents/reasoning.py`
- Modify: `athf/agents/base.py` (add `run()` default to `Agent`)
- Test: `tests/agents/test_reasoning.py` (extend)

**Step 1: Write failing tests for ReasoningAgent**

Add to `tests/agents/test_reasoning.py`:

```python
from unittest.mock import MagicMock, patch

from athf.agents.base import AgentResult
from athf.agents.providers import LLMResponse, TokenUsage
from athf.agents.reasoning import ReasoningAgent, RunState


class TestReasoningAgent:
    def _make_provider(self, responses):
        """Create a mock provider that returns responses in sequence."""
        provider = MagicMock()
        provider.invoke = MagicMock(side_effect=responses)
        provider.cost_per_1k_tokens.return_value = (0.003, 0.015)
        return provider

    def test_single_turn_end_turn(self):
        """Agent gets end_turn on first call — no tool loop."""

        class SimpleAgent(ReasoningAgent[str, str]):
            tools = []

            def build_system_prompt(self, state):
                return "You are a test agent"

            def build_initial_prompt(self, state):
                return f"Process: {state.input}"

            def finalize(self, state, response=None, force=False):
                return AgentResult(success=True, data=response.text if response else "forced")

            def execute(self, input_data):
                return self.run(input_data)

        provider = self._make_provider([
            LLMResponse(
                text="Done!", tool_calls=[], stop_reason="end_turn",
                usage=TokenUsage(input_tokens=100, output_tokens=50),
                raw_content=[{"type": "text", "text": "Done!"}],
            )
        ])

        agent = SimpleAgent(llm_enabled=False)
        agent._get_provider = MagicMock(return_value=provider)
        result = agent.run("hello")

        assert result.is_success
        assert result.data == "Done!"
        assert provider.invoke.call_count == 1

    def test_tool_use_loop(self):
        """Agent calls a tool, then gets end_turn."""

        class EchoTool(ToolDefinition):
            name = "echo"
            description = "Echo"
            input_schema = {"type": "object", "properties": {"text": {"type": "string"}}}

            def execute(self, input_data):
                return ToolResult(success=True, output=f"echoed: {input_data['text']}")

        class ToolAgent(ReasoningAgent[str, str]):
            tools = [EchoTool()]

            def build_system_prompt(self, state):
                return "test"

            def build_initial_prompt(self, state):
                return state.input

            def finalize(self, state, response=None, force=False):
                return AgentResult(success=True, data=f"steps={state.step_count}")

            def execute(self, input_data):
                return self.run(input_data)

        responses = [
            # Turn 1: LLM requests tool call
            LLMResponse(
                text=None,
                tool_calls=[ToolCall(id="tc_1", name="echo", input={"text": "hi"})],
                stop_reason="tool_use",
                usage=TokenUsage(input_tokens=50, output_tokens=30),
                raw_content=[{"type": "tool_use", "id": "tc_1", "name": "echo", "input": {"text": "hi"}}],
            ),
            # Turn 2: LLM sees tool result, finishes
            LLMResponse(
                text="All done",
                tool_calls=[],
                stop_reason="end_turn",
                usage=TokenUsage(input_tokens=80, output_tokens=20),
                raw_content=[{"type": "text", "text": "All done"}],
            ),
        ]
        provider = self._make_provider(responses)

        agent = ToolAgent(llm_enabled=False)
        agent._get_provider = MagicMock(return_value=provider)
        result = agent.run("do something")

        assert result.is_success
        assert result.data == "steps=2"
        assert provider.invoke.call_count == 2

    def test_max_steps_forces_finalize(self):
        """Agent hits max_steps and force-finalizes."""

        class InfiniteToolAgent(ReasoningAgent[str, str]):
            max_steps = 2
            tools = []

            def build_system_prompt(self, state):
                return "test"

            def build_initial_prompt(self, state):
                return state.input

            def finalize(self, state, response=None, force=False):
                if force:
                    return AgentResult(success=True, data="forced", warnings=["Max steps reached"])
                return AgentResult(success=True, data="normal")

            def execute(self, input_data):
                return self.run(input_data)

        # Every response requests more tools — agent should stop at max_steps
        tool_response = LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="tc_x", name="missing", input={})],
            stop_reason="tool_use",
            usage=TokenUsage(input_tokens=10, output_tokens=5),
            raw_content=[],
        )
        provider = self._make_provider([tool_response, tool_response, tool_response])

        agent = InfiniteToolAgent(llm_enabled=False)
        agent._get_provider = MagicMock(return_value=provider)
        result = agent.run("loop forever")

        assert result.data == "forced"
        assert "Max steps" in result.warnings[0]

    def test_validate_tool_call_rejection(self):
        """Agent rejects unsafe tool call via validate_tool_call."""

        class SafeAgent(ReasoningAgent[str, str]):
            tools = []

            def build_system_prompt(self, state):
                return "test"

            def build_initial_prompt(self, state):
                return state.input

            def finalize(self, state, response=None, force=False):
                return AgentResult(success=True, data="ok")

            def validate_tool_call(self, state, tool_call):
                return tool_call.name != "dangerous"

            def execute(self, input_data):
                return self.run(input_data)

        responses = [
            LLMResponse(
                text=None,
                tool_calls=[ToolCall(id="tc_1", name="dangerous", input={})],
                stop_reason="tool_use",
                usage=TokenUsage(input_tokens=10, output_tokens=5),
                raw_content=[],
            ),
            LLMResponse(
                text="ok", tool_calls=[], stop_reason="end_turn",
                usage=TokenUsage(input_tokens=10, output_tokens=5),
                raw_content=[{"type": "text", "text": "ok"}],
            ),
        ]
        provider = self._make_provider(responses)

        agent = SafeAgent(llm_enabled=False)
        agent._get_provider = MagicMock(return_value=provider)
        result = agent.run("test")

        assert result.is_success
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/agents/test_reasoning.py::TestReasoningAgent -v`
Expected: FAIL — `ImportError: cannot import name 'ReasoningAgent'`

**Step 3: Implement ReasoningAgent**

Add to `athf/agents/reasoning.py` (after `RunState`):

```python
class ReasoningAgent(LLMAgent[InputT, OutputT]):
    """Agent with tool_use reasoning loop.

    Subclasses must implement:
    - build_system_prompt(state) -> str
    - build_initial_prompt(state) -> str
    - finalize(state, response, force) -> AgentResult[OutputT]
    - execute(input_data) -> AgentResult[OutputT]  (typically calls self.run())

    Optional overrides:
    - validate_tool_call(state, tool_call) -> bool
    - on_step_complete(state, step) -> None
    """

    max_steps: int = 10
    tools: List[ToolDefinition] = []

    def _get_provider(self) -> LLMProvider:
        """Get LLM provider. Override for custom providers."""
        from athf.agents.providers_bedrock import BedrockAnthropicProvider

        return BedrockAnthropicProvider()

    def run(self, input_data: InputT, max_steps: Optional[int] = None) -> AgentResult[OutputT]:
        """Execute agent with reasoning loop.

        Args:
            input_data: Agent input
            max_steps: Override default max_steps

        Returns:
            AgentResult from finalize()
        """
        state: RunState[InputT] = RunState(input=input_data)
        provider = self._get_provider()
        steps_limit = max_steps or self.max_steps

        # Build tool schemas
        tool_schemas = [t.to_schema() for t in self.tools]

        # Build initial conversation
        system = self.build_system_prompt(state)
        state.messages.append({"role": "user", "content": self.build_initial_prompt(state)})

        for step in range(steps_limit):
            state.step_count = step + 1

            # Invoke LLM
            response = provider.invoke(
                messages=state.messages,
                system=system,
                tools=tool_schemas if tool_schemas else None,
            )

            # Track cost
            input_cost, output_cost = provider.cost_per_1k_tokens()
            state.total_input_tokens += response.usage.input_tokens
            state.total_output_tokens += response.usage.output_tokens
            state.total_cost_usd += response.usage.cost_usd(input_cost, output_cost)

            # Append assistant response
            state.messages.append({"role": "assistant", "content": response.raw_content})

            if response.stop_reason == "end_turn" or not response.has_tool_calls:
                return self.finalize(state, response)

            # Execute tool calls
            tool_result_blocks = []
            for tool_call in response.tool_calls:
                if not self.validate_tool_call(state, tool_call):
                    tr = ToolResult(success=False, output=None, error="Rejected by safety check")
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str(tr.error),
                    })
                    state.add_step(tool_call, tr)
                    continue

                tool = self._get_tool(tool_call.name)
                if tool is None:
                    tr = ToolResult(success=False, output=None, error=f"Unknown tool: {tool_call.name}")
                    tool_result_blocks.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str(tr.error),
                    })
                    state.add_step(tool_call, tr)
                    continue

                import time

                start = time.monotonic()
                tr = tool.execute(tool_call.input)
                duration_ms = int((time.monotonic() - start) * 1000)

                output_str = str(tr.output) if tr.success else str(tr.error)
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": output_str,
                })
                state.add_step(tool_call, tr, duration_ms=duration_ms)

            # Send tool results back to LLM
            state.messages.append({"role": "user", "content": tool_result_blocks})

            # Step complete hook
            self.on_step_complete(state, step)

        # Max steps reached
        return self.finalize(state, force=True)

    def _get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Look up tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    @abstractmethod
    def build_system_prompt(self, state: RunState[InputT]) -> str:
        """Build the system prompt for this agent."""
        ...

    @abstractmethod
    def build_initial_prompt(self, state: RunState[InputT]) -> str:
        """Build the initial user message."""
        ...

    @abstractmethod
    def finalize(
        self, state: RunState[InputT], response: Optional[LLMResponse] = None, force: bool = False
    ) -> AgentResult[OutputT]:
        """Build final result from accumulated state."""
        ...

    def validate_tool_call(self, state: RunState[InputT], tool_call: ToolCall) -> bool:
        """Safety gate for tool calls. Override to add guardrails."""
        return True

    def on_step_complete(self, state: RunState[InputT], step: int) -> None:
        """Hook called after each reasoning step. Override for logging/checkpoints."""
        pass
```

Also add `run()` default method to `Agent` in `athf/agents/base.py` (after `__call__`):

```python
    def run(self, input_data: InputT, **kwargs: Any) -> AgentResult[OutputT]:
        """Run agent with reasoning loop. Default: calls execute() once."""
        return self.execute(input_data)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/agents/test_reasoning.py -v`
Expected: All 9 tests PASS (5 from Task 3.1 + 4 new)

**Step 5: Verify all existing tests still pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add athf/agents/reasoning.py athf/agents/base.py tests/agents/test_reasoning.py
git commit -m "feat(agents): add ReasoningAgent with tool_use reasoning loop"
```

---

## Phase 4: Session State (parallel with Phase 1-3)

### Task 4.1: SessionStore and YAMLSessionStore

**Files:**
- Create: `athf/core/session.py`
- Test: `tests/core/test_session.py`

**Step 1: Write failing tests**

```python
# tests/core/__init__.py
# (empty)

# tests/core/test_session.py
"""Tests for session state management."""
import pytest

from athf.core.session import SessionEvent, SessionManager, SessionStore, YAMLSessionStore


class TestSessionEvent:
    def test_event_fields(self):
        event = SessionEvent(event_type="query", data={"sql": "SELECT 1"})
        assert event.event_type == "query"
        assert event.data["sql"] == "SELECT 1"
        assert event.timestamp  # Auto-populated


class TestYAMLSessionStore:
    def test_save_and_load_metadata(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        store.save_metadata("H-0001-2026-02-15", {"hunt_id": "H-0001", "status": "active"})
        loaded = store.load_metadata("H-0001-2026-02-15")
        assert loaded["hunt_id"] == "H-0001"

    def test_save_and_load_events(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        sid = "H-0001-2026-02-15"
        store.save_event(sid, SessionEvent(event_type="query", data={"sql": "SELECT 1"}))
        store.save_event(sid, SessionEvent(event_type="decision", data={"phase": "analysis"}))
        store.save_event(sid, SessionEvent(event_type="query", data={"sql": "SELECT 2"}))

        all_events = store.load_events(sid)
        assert len(all_events) == 3

        query_events = store.load_events(sid, event_type="query")
        assert len(query_events) == 2

    def test_load_nonexistent_session(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        assert store.load_metadata("nonexistent") == {}
        assert store.load_events("nonexistent") == []


class TestSessionManager:
    def test_start_session(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        manager = SessionManager(store=store)
        session_id = manager.start_session("H-0001")
        assert session_id.startswith("H-0001")

    def test_log_query(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        manager = SessionManager(store=store)
        session_id = manager.start_session("H-0001")
        manager.log_query(session_id, sql="SELECT 1", result_count=42, duration_ms=100)
        events = store.load_events(session_id, event_type="query")
        assert len(events) == 1
        assert events[0].data["sql"] == "SELECT 1"

    def test_log_decision(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        manager = SessionManager(store=store)
        session_id = manager.start_session("H-0001")
        manager.log_decision(session_id, phase="analysis", decision="FP: scheduled task")
        events = store.load_events(session_id, event_type="decision")
        assert len(events) == 1

    def test_end_session(self, tmp_path):
        store = YAMLSessionStore(base_dir=tmp_path)
        manager = SessionManager(store=store)
        session_id = manager.start_session("H-0001")
        metadata = manager.end_session(session_id)
        assert metadata["end_time"] is not None
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_session.py -v`
Expected: FAIL

**Step 3: Implement**

```python
# athf/core/session.py
"""Session state management for ATHF."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class SessionEvent:
    """An event in a session log."""

    event_type: str  # "query", "decision", "finding", "tool_call", "agent_run"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))


class SessionStore(ABC):
    """Abstract persistence backend for session state."""

    @abstractmethod
    def save_event(self, session_id: str, event: SessionEvent) -> None:
        """Append an event to a session."""
        ...

    @abstractmethod
    def load_events(self, session_id: str, event_type: Optional[str] = None) -> List[SessionEvent]:
        """Load events from a session, optionally filtered by type."""
        ...

    @abstractmethod
    def save_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Save session metadata."""
        ...

    @abstractmethod
    def load_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata."""
        ...


class YAMLSessionStore(SessionStore):
    """File-based session persistence using YAML."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base_dir = base_dir or Path("sessions")

    def _session_dir(self, session_id: str) -> Path:
        d = self._base_dir / session_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_event(self, session_id: str, event: SessionEvent) -> None:
        """Append event to events.yaml."""
        session_dir = self._session_dir(session_id)
        events_file = session_dir / "events.yaml"

        existing: List[Dict[str, Any]] = []
        if events_file.exists():
            with open(events_file, "r") as f:
                data = yaml.safe_load(f)
                if data and "events" in data:
                    existing = data["events"]

        existing.append({
            "event_type": event.event_type,
            "timestamp": event.timestamp,
            "data": event.data,
        })

        with open(events_file, "w") as f:
            yaml.dump({"events": existing}, f, default_flow_style=False, sort_keys=False)

    def load_events(self, session_id: str, event_type: Optional[str] = None) -> List[SessionEvent]:
        """Load events from events.yaml."""
        events_file = self._base_dir / session_id / "events.yaml"
        if not events_file.exists():
            return []

        with open(events_file, "r") as f:
            data = yaml.safe_load(f)

        if not data or "events" not in data:
            return []

        events = [
            SessionEvent(
                event_type=e["event_type"],
                data=e.get("data", {}),
                timestamp=e.get("timestamp", ""),
            )
            for e in data["events"]
        ]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def save_metadata(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Save metadata to session.yaml."""
        session_dir = self._session_dir(session_id)
        with open(session_dir / "session.yaml", "w") as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

    def load_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load metadata from session.yaml."""
        meta_file = self._base_dir / session_id / "session.yaml"
        if not meta_file.exists():
            return {}
        with open(meta_file, "r") as f:
            return yaml.safe_load(f) or {}


class SessionManager:
    """Manages hunt session lifecycle."""

    def __init__(self, store: Optional[SessionStore] = None):
        self._store = store or YAMLSessionStore()

    def start_session(self, hunt_id: str) -> str:
        """Start a new session. Returns session_id."""
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        session_id = f"{hunt_id}-{date_str}"
        self._store.save_metadata(session_id, {
            "hunt_id": hunt_id,
            "session_id": session_id,
            "start_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": None,
        })
        return session_id

    def log_query(
        self, session_id: str, sql: str, result_count: int, duration_ms: int = 0, outcome: str = "success"
    ) -> None:
        """Log a query execution event."""
        self._store.save_event(session_id, SessionEvent(
            event_type="query",
            data={"sql": sql, "result_count": result_count, "duration_ms": duration_ms, "outcome": outcome},
        ))

    def log_decision(
        self, session_id: str, phase: str, decision: str, rationale: Optional[str] = None
    ) -> None:
        """Log a decision event."""
        self._store.save_event(session_id, SessionEvent(
            event_type="decision",
            data={"phase": phase, "decision": decision, "rationale": rationale},
        ))

    def log_finding(
        self, session_id: str, finding_type: str, description: str, count: int = 1
    ) -> None:
        """Log a finding event."""
        self._store.save_event(session_id, SessionEvent(
            event_type="finding",
            data={"type": finding_type, "description": description, "count": count},
        ))

    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End a session and return final metadata."""
        metadata = self._store.load_metadata(session_id)
        metadata["end_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._store.save_metadata(session_id, metadata)
        return metadata
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_session.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add athf/core/session.py tests/core/__init__.py tests/core/test_session.py
git commit -m "feat(core): add session state management — SessionStore, YAMLSessionStore, SessionManager"
```

---

## Phase 5: Pipeline Orchestration

### Task 5.1: Pipeline, PipelineStep, AgentStep, RouterStep

**Files:**
- Create: `athf/core/pipeline.py`
- Test: `tests/core/test_pipeline.py`

**Step 1: Write failing tests**

```python
# tests/core/test_pipeline.py
"""Tests for pipeline orchestration."""
import pytest

from athf.agents.base import Agent, AgentResult, DeterministicAgent
from athf.core.pipeline import AgentStep, Pipeline, PipelineContext, RouterStep


class AddOneAgent(DeterministicAgent[int, int]):
    def execute(self, input_data):
        return AgentResult(success=True, data=input_data + 1)


class DoubleAgent(DeterministicAgent[int, int]):
    def execute(self, input_data):
        return AgentResult(success=True, data=input_data * 2)


class FailAgent(DeterministicAgent[int, int]):
    def execute(self, input_data):
        return AgentResult(success=False, data=None, error="Intentional failure")


class TestPipelineContext:
    def test_initial_context(self):
        ctx = PipelineContext(initial_input=42)
        assert ctx.initial_input == 42
        assert ctx.results == {}

    def test_last_result(self):
        ctx = PipelineContext(initial_input=0)
        ctx.results["step1"] = AgentResult(success=True, data=10)
        assert ctx.last_result().data == 10

    def test_last_result_empty(self):
        ctx = PipelineContext(initial_input=0)
        assert ctx.last_result() is None


class TestAgentStep:
    def test_agent_step_runs_agent(self):
        step = AgentStep(
            name="add_one",
            agent=AddOneAgent(),
            input_mapper=lambda ctx: ctx.initial_input,
        )
        ctx = PipelineContext(initial_input=5)
        ctx = step.execute(ctx)
        assert ctx.results["add_one"].data == 6


class TestRouterStep:
    def test_routes_to_correct_branch(self):
        step = RouterStep(
            name="route",
            router=lambda ctx: "double" if ctx.initial_input > 10 else "add",
            branches={
                "double": AgentStep("double", DoubleAgent(), lambda ctx: ctx.initial_input),
                "add": AgentStep("add", AddOneAgent(), lambda ctx: ctx.initial_input),
            },
        )
        ctx = PipelineContext(initial_input=20)
        ctx = step.execute(ctx)
        assert "double" in ctx.results
        assert ctx.results["double"].data == 40

    def test_no_matching_branch_passes_through(self):
        step = RouterStep(name="route", router=lambda ctx: "unknown", branches={})
        ctx = PipelineContext(initial_input=1)
        ctx = step.execute(ctx)
        assert len(ctx.results) == 0  # No step ran


class TestPipeline:
    def test_sequential_pipeline(self):
        pipeline = Pipeline("test", [
            AgentStep("step1", AddOneAgent(), lambda ctx: ctx.initial_input),
            AgentStep("step2", DoubleAgent(), lambda ctx: ctx.results["step1"].data),
        ])
        ctx = pipeline.run(5)
        assert ctx.results["step1"].data == 6
        assert ctx.results["step2"].data == 12

    def test_pipeline_stops_on_failure(self):
        pipeline = Pipeline("test", [
            AgentStep("step1", FailAgent(), lambda ctx: ctx.initial_input),
            AgentStep("step2", AddOneAgent(), lambda ctx: 0),  # Should not run
        ])
        ctx = pipeline.run(1)
        assert "step1" in ctx.results
        assert "step2" not in ctx.results

    def test_pipeline_with_router(self):
        pipeline = Pipeline("test", [
            RouterStep(
                name="route",
                router=lambda ctx: "a" if ctx.initial_input > 0 else "b",
                branches={
                    "a": AgentStep("branch_a", DoubleAgent(), lambda ctx: ctx.initial_input),
                    "b": AgentStep("branch_b", AddOneAgent(), lambda ctx: ctx.initial_input),
                },
            ),
        ])
        ctx = pipeline.run(5)
        assert ctx.results["branch_a"].data == 10
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_pipeline.py -v`
Expected: FAIL

**Step 3: Implement**

```python
# athf/core/pipeline.py
"""Pipeline orchestration for multi-agent workflows."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from athf.agents.base import Agent, AgentResult


@dataclass
class PipelineContext:
    """Shared context flowing through a pipeline."""

    initial_input: Any
    results: Dict[str, AgentResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def last_result(self) -> Optional[AgentResult]:
        """Get the most recent agent result."""
        if self.results:
            return list(self.results.values())[-1]
        return None


class PipelineStep(ABC):
    """A step in an agent pipeline."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute this step and return updated context."""
        ...


class AgentStep(PipelineStep):
    """Run an agent as a pipeline step."""

    def __init__(self, name: str, agent: Agent, input_mapper: Callable[[PipelineContext], Any]):
        super().__init__(name)
        self.agent = agent
        self.input_mapper = input_mapper

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute agent with mapped input."""
        agent_input = self.input_mapper(context)
        result = self.agent.run(agent_input)
        context.results[self.name] = result
        return context


class RouterStep(PipelineStep):
    """Conditional routing between branches."""

    def __init__(
        self,
        name: str,
        router: Callable[[PipelineContext], str],
        branches: Dict[str, PipelineStep],
    ):
        super().__init__(name)
        self.router = router
        self.branches = branches

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Route to a branch based on context."""
        branch_key = self.router(context)
        branch = self.branches.get(branch_key)
        if branch:
            return branch.execute(context)
        return context


class Pipeline:
    """Ordered sequence of agent steps with routing."""

    def __init__(self, name: str, steps: List[PipelineStep]):
        self.name = name
        self.steps = steps

    def run(self, initial_input: Any) -> PipelineContext:
        """Run the pipeline and return final context."""
        context = PipelineContext(initial_input=initial_input)

        for step in self.steps:
            context = step.execute(context)

            # Stop on failure
            last = context.results.get(step.name)
            if last and not last.is_success:
                break

        return context
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_pipeline.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add athf/core/pipeline.py tests/core/test_pipeline.py
git commit -m "feat(core): add Pipeline orchestration — Pipeline, AgentStep, RouterStep"
```

---

## Phase 6: Checkpoint System

### Task 6.1: Checkpoint types and AutoApproveHandler

**Files:**
- Create: `athf/core/checkpoints.py`
- Test: `tests/core/test_checkpoints.py`

**Step 1: Write failing tests**

```python
# tests/core/test_checkpoints.py
"""Tests for checkpoint system."""
import pytest

from athf.core.checkpoints import (
    AutoApproveHandler,
    Checkpoint,
    CheckpointPolicy,
    CheckpointRequest,
    CheckpointResponse,
)


class TestCheckpointPolicy:
    def test_policies_exist(self):
        assert CheckpointPolicy.ALWAYS_PAUSE
        assert CheckpointPolicy.AUTO_APPROVE
        assert CheckpointPolicy.PAUSE_ON_LOW_CONFIDENCE
        assert CheckpointPolicy.POLICY_BASED


class TestCheckpoint:
    def test_checkpoint_defaults(self):
        cp = Checkpoint(name="review", description="Review results")
        assert cp.policy == CheckpointPolicy.ALWAYS_PAUSE
        assert cp.confidence_threshold == 0.8

    def test_checkpoint_with_policy(self):
        cp = Checkpoint(
            name="auto",
            description="Auto-approve",
            policy=CheckpointPolicy.AUTO_APPROVE,
        )
        assert cp.policy == CheckpointPolicy.AUTO_APPROVE


class TestCheckpointRequest:
    def test_request_fields(self):
        req = CheckpointRequest(
            checkpoint=Checkpoint(name="test", description="test"),
            summary="Agent wants to run a query",
            details={"sql": "SELECT 1"},
        )
        assert req.summary == "Agent wants to run a query"
        assert req.precedents == []


class TestAutoApproveHandler:
    def test_always_approves(self):
        handler = AutoApproveHandler()
        req = CheckpointRequest(
            checkpoint=Checkpoint(name="test", description="test"),
            summary="anything",
            details={},
        )
        resp = handler.request_approval(req)
        assert resp.approved is True
        assert resp.action == "auto_approve"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_checkpoints.py -v`
Expected: FAIL

**Step 3: Implement**

```python
# athf/core/checkpoints.py
"""Human-in-the-loop checkpoint system for ATHF."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class CheckpointPolicy(Enum):
    """Policy for when a checkpoint should pause."""

    ALWAYS_PAUSE = "always_pause"
    PAUSE_ON_LOW_CONFIDENCE = "low_confidence"
    AUTO_APPROVE = "auto_approve"
    POLICY_BASED = "policy_based"


@dataclass
class Checkpoint:
    """Definition of a checkpoint where human review may be required."""

    name: str
    description: str
    policy: CheckpointPolicy = CheckpointPolicy.ALWAYS_PAUSE
    confidence_threshold: float = 0.8
    policy_fn: Optional[Callable] = None


@dataclass
class CheckpointRequest:
    """Request presented to a human for review."""

    checkpoint: Checkpoint
    summary: str
    details: Dict[str, Any]
    suggested_action: Optional[str] = None
    precedents: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CheckpointResponse:
    """Human response to a checkpoint request."""

    approved: bool
    action: str  # "approve", "reject", "modify", "defer", "auto_approve"
    feedback: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None


class CheckpointHandler(ABC):
    """How checkpoint requests reach humans and responses come back."""

    @abstractmethod
    def request_approval(self, request: CheckpointRequest) -> CheckpointResponse:
        """Request human approval for a checkpoint."""
        ...


class AutoApproveHandler(CheckpointHandler):
    """Auto-approve all checkpoints. For autonomous mode and testing."""

    def request_approval(self, request: CheckpointRequest) -> CheckpointResponse:
        """Always approve."""
        return CheckpointResponse(approved=True, action="auto_approve")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_checkpoints.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add athf/core/checkpoints.py tests/core/test_checkpoints.py
git commit -m "feat(core): add checkpoint system — Checkpoint, CheckpointPolicy, AutoApproveHandler"
```

---

### Task 6.2: CheckpointStep for pipelines

**Files:**
- Modify: `athf/core/pipeline.py` (add `CheckpointStep`)
- Test: `tests/core/test_pipeline.py` (extend)

**Step 1: Write failing test**

Add to `tests/core/test_pipeline.py`:

```python
from athf.core.checkpoints import AutoApproveHandler, Checkpoint, CheckpointPolicy
from athf.core.pipeline import CheckpointStep


class TestCheckpointStep:
    def test_auto_approve_continues_pipeline(self):
        pipeline = Pipeline("test", [
            AgentStep("step1", AddOneAgent(), lambda ctx: ctx.initial_input),
            CheckpointStep(
                name="review",
                checkpoint=Checkpoint(name="review", description="Review step1"),
                handler=AutoApproveHandler(),
                summary_fn=lambda ctx: f"Step1 result: {ctx.results['step1'].data}",
            ),
            AgentStep("step2", DoubleAgent(), lambda ctx: ctx.results["step1"].data),
        ])
        ctx = pipeline.run(5)
        assert ctx.results["step1"].data == 6
        assert ctx.results["step2"].data == 12

    def test_rejection_stops_pipeline(self):
        from athf.core.checkpoints import CheckpointHandler, CheckpointResponse

        class RejectHandler(CheckpointHandler):
            def request_approval(self, request):
                return CheckpointResponse(approved=False, action="reject", feedback="Not ready")

        pipeline = Pipeline("test", [
            AgentStep("step1", AddOneAgent(), lambda ctx: ctx.initial_input),
            CheckpointStep(
                name="gate",
                checkpoint=Checkpoint(name="gate", description="Gate"),
                handler=RejectHandler(),
                summary_fn=lambda ctx: "review",
            ),
            AgentStep("step2", DoubleAgent(), lambda ctx: 0),  # Should not run
        ])
        ctx = pipeline.run(5)
        assert "step1" in ctx.results
        assert "step2" not in ctx.results
        assert ctx.results["gate"].success is False
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_pipeline.py::TestCheckpointStep -v`
Expected: FAIL

**Step 3: Add CheckpointStep to `athf/core/pipeline.py`**

```python
from athf.core.checkpoints import Checkpoint, CheckpointHandler, CheckpointRequest


class CheckpointStep(PipelineStep):
    """Human review gate in a pipeline."""

    def __init__(
        self,
        name: str,
        checkpoint: Checkpoint,
        handler: CheckpointHandler,
        summary_fn: Callable[[PipelineContext], str],
    ):
        super().__init__(name)
        self.checkpoint = checkpoint
        self.handler = handler
        self.summary_fn = summary_fn

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Request human approval."""
        request = CheckpointRequest(
            checkpoint=self.checkpoint,
            summary=self.summary_fn(context),
            details={"results": {k: v.data for k, v in context.results.items()}},
        )
        response = self.handler.request_approval(request)
        context.metadata["checkpoint_response"] = response

        if not response.approved:
            context.results[self.name] = AgentResult(
                success=False,
                data=None,
                error=f"Rejected at checkpoint '{self.checkpoint.name}': {response.feedback}",
            )
        else:
            context.results[self.name] = AgentResult(success=True, data="approved")

        return context
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_pipeline.py -v`
Expected: All 11 tests PASS

**Step 5: Commit**

```bash
git add athf/core/pipeline.py tests/core/test_pipeline.py
git commit -m "feat(core): add CheckpointStep to pipeline for human-in-the-loop gates"
```

---

## Phase 7: Event System

### Task 7.1: Event, Trigger, EventDispatcher

**Files:**
- Create: `athf/core/events.py`
- Test: `tests/core/test_events.py`

**Step 1: Write failing tests**

```python
# tests/core/test_events.py
"""Tests for event-driven trigger system."""
import pytest

from athf.agents.base import AgentResult, DeterministicAgent
from athf.core.events import Event, EventDispatcher, Trigger
from athf.core.pipeline import AgentStep, Pipeline, PipelineContext


class IncrementAgent(DeterministicAgent[int, int]):
    def execute(self, input_data):
        return AgentResult(success=True, data=input_data + 1)


class TestEvent:
    def test_event_fields(self):
        e = Event(event_type="baseline.detect", payload={"metric": "process_count"})
        assert e.event_type == "baseline.detect"
        assert e.source == "cli"
        assert e.event_id  # Auto-generated

    def test_event_custom_source(self):
        e = Event(event_type="cti.new", payload={}, source="webhook")
        assert e.source == "webhook"


class TestTrigger:
    def test_exact_match(self):
        t = Trigger(name="t1", event_pattern="baseline.detect", pipeline_name="p1")
        assert t.matches(Event(event_type="baseline.detect", payload={}))
        assert not t.matches(Event(event_type="baseline.calculate", payload={}))

    def test_glob_match(self):
        t = Trigger(name="t1", event_pattern="baseline.*", pipeline_name="p1")
        assert t.matches(Event(event_type="baseline.detect", payload={}))
        assert t.matches(Event(event_type="baseline.calculate", payload={}))
        assert not t.matches(Event(event_type="cti.new", payload={}))

    def test_disabled_trigger(self):
        t = Trigger(name="t1", event_pattern="*", pipeline_name="p1", enabled=False)
        assert not t.matches(Event(event_type="anything", payload={}))

    def test_condition_filter(self):
        t = Trigger(
            name="t1",
            event_pattern="baseline.*",
            pipeline_name="p1",
            condition=lambda e: e.payload.get("zscore", 0) >= 5.0,
        )
        assert t.matches(Event(event_type="baseline.detect", payload={"zscore": 8.0}))
        assert not t.matches(Event(event_type="baseline.detect", payload={"zscore": 2.0}))


class TestEventDispatcher:
    def test_dispatch_triggers_pipeline(self):
        pipeline = Pipeline("test", [
            AgentStep("inc", IncrementAgent(), lambda ctx: ctx.initial_input),
        ])

        dispatcher = EventDispatcher()
        dispatcher.register_trigger(Trigger(
            name="t1",
            event_pattern="test.run",
            pipeline_name="test",
            input_mapper=lambda e: e.payload.get("value", 0),
        ))
        dispatcher.register_pipeline("test", pipeline)

        results = dispatcher.dispatch(Event(event_type="test.run", payload={"value": 10}))
        assert len(results) == 1
        assert results[0].results["inc"].data == 11

    def test_dispatch_no_match(self):
        dispatcher = EventDispatcher()
        results = dispatcher.dispatch(Event(event_type="unknown", payload={}))
        assert results == []

    def test_rate_limiting(self):
        pipeline = Pipeline("test", [
            AgentStep("inc", IncrementAgent(), lambda ctx: ctx.initial_input),
        ])

        dispatcher = EventDispatcher()
        dispatcher.register_trigger(Trigger(
            name="limited",
            event_pattern="test.*",
            pipeline_name="test",
            max_runs_per_hour=2,
            input_mapper=lambda e: 0,
        ))
        dispatcher.register_pipeline("test", pipeline)

        event = Event(event_type="test.run", payload={})
        dispatcher.dispatch(event)  # Run 1
        dispatcher.dispatch(event)  # Run 2
        results = dispatcher.dispatch(event)  # Run 3 — should be rate-limited
        assert results == []
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_events.py -v`
Expected: FAIL

**Step 3: Implement**

```python
# athf/core/events.py
"""Event-driven trigger system for ATHF."""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from typing import Any, Callable, Dict, List, Optional

from athf.core.pipeline import Pipeline, PipelineContext


@dataclass
class Event:
    """Something that happened that may trigger a pipeline."""

    event_type: str
    payload: Dict[str, Any]
    source: str = "cli"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class Trigger:
    """Rule that maps events to pipeline execution."""

    name: str
    event_pattern: str
    pipeline_name: str
    enabled: bool = True
    condition: Optional[Callable[[Event], bool]] = None
    input_mapper: Optional[Callable[[Event], Any]] = None
    max_runs_per_hour: Optional[int] = None
    max_runs_per_day: Optional[int] = None

    def matches(self, event: Event) -> bool:
        """Check if this trigger matches an event."""
        if not self.enabled:
            return False
        if not fnmatch(event.event_type, self.event_pattern):
            return False
        if self.condition and not self.condition(event):
            return False
        return True


class EventDispatcher:
    """Routes events to pipelines via triggers."""

    def __init__(self) -> None:
        self._triggers: List[Trigger] = []
        self._pipelines: Dict[str, Pipeline] = {}
        self._run_history: Dict[str, List[datetime]] = {}

    def register_trigger(self, trigger: Trigger) -> None:
        """Register an event trigger."""
        self._triggers.append(trigger)

    def register_pipeline(self, name: str, pipeline: Pipeline) -> None:
        """Register a pipeline by name."""
        self._pipelines[name] = pipeline

    def dispatch(self, event: Event) -> List[PipelineContext]:
        """Find matching triggers and run their pipelines."""
        results = []

        for trigger in self._triggers:
            if not trigger.matches(event):
                continue

            if not self._check_rate_limit(trigger):
                continue

            pipeline = self._pipelines.get(trigger.pipeline_name)
            if not pipeline:
                continue

            pipeline_input = event.payload
            if trigger.input_mapper:
                pipeline_input = trigger.input_mapper(event)

            context = pipeline.run(pipeline_input)
            results.append(context)
            self._record_run(trigger)

        return results

    def _check_rate_limit(self, trigger: Trigger) -> bool:
        """Check if trigger is within rate limits."""
        if not trigger.max_runs_per_hour and not trigger.max_runs_per_day:
            return True

        now = datetime.utcnow()
        runs = self._run_history.get(trigger.name, [])

        if trigger.max_runs_per_hour:
            recent = [r for r in runs if (now - r).total_seconds() < 3600]
            if len(recent) >= trigger.max_runs_per_hour:
                return False

        if trigger.max_runs_per_day:
            today = [r for r in runs if (now - r).total_seconds() < 86400]
            if len(today) >= trigger.max_runs_per_day:
                return False

        return True

    def _record_run(self, trigger: Trigger) -> None:
        """Record a trigger execution for rate limiting."""
        if trigger.name not in self._run_history:
            self._run_history[trigger.name] = []
        self._run_history[trigger.name].append(datetime.utcnow())


class EventSource(ABC):
    """Abstract source of events for the dispatcher."""

    @abstractmethod
    def listen(self, callback: Callable[[Event], None]) -> None:
        """Start listening for events and dispatch via callback."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop listening."""
        ...
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_events.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add athf/core/events.py tests/core/test_events.py
git commit -m "feat(core): add event-driven trigger system — Event, Trigger, EventDispatcher"
```

---

## Phase 8: CLI Commands and Integration

### Task 8.1: Pipeline CLI commands

**Files:**
- Create: `athf/commands/pipeline.py`
- Modify: `athf/cli.py` (register command)
- Test: `tests/commands/test_pipeline.py`

**Step 1: Write failing test**

```python
# tests/commands/test_pipeline.py
"""Tests for pipeline CLI commands."""
from click.testing import CliRunner

from athf.cli import cli


class TestPipelineList:
    def test_pipeline_list_no_pipelines(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["pipeline", "list"])
        assert result.exit_code == 0
        assert "No pipelines registered" in result.output or "pipeline" in result.output.lower()
```

**Step 2: Run to verify failure**

Run: `pytest tests/commands/test_pipeline.py -v`
Expected: FAIL — `Usage: cli [OPTIONS] COMMAND` (no pipeline subcommand)

**Step 3: Implement CLI**

```python
# athf/commands/pipeline.py
"""Pipeline management CLI commands."""

import json

import click
from rich.console import Console
from rich.table import Table

from athf.plugin_system import PluginRegistry

console = Console()


@click.group()
def pipeline() -> None:
    """Manage agent pipelines."""
    pass


@pipeline.command("list")
def list_pipelines() -> None:
    """List registered pipelines."""
    pipelines = PluginRegistry._pipelines
    if not pipelines:
        console.print("[dim]No pipelines registered.[/dim]")
        console.print("[dim]Plugins can register pipelines via athf.pipelines entry points.[/dim]")
        return

    table = Table(title="Registered Pipelines")
    table.add_column("Name", style="cyan")
    table.add_column("Steps", style="green")

    for name, pipe in pipelines.items():
        step_count = len(pipe.steps) if hasattr(pipe, "steps") else "?"
        table.add_row(name, str(step_count))

    console.print(table)


@pipeline.command("run")
@click.argument("pipeline_name")
@click.option("--input", "input_json", default="{}", help="JSON input for the pipeline")
def run_pipeline(pipeline_name: str, input_json: str) -> None:
    """Run a registered pipeline."""
    pipe = PluginRegistry.get_pipeline(pipeline_name)
    if not pipe:
        console.print(f"[red]Pipeline not found: {pipeline_name}[/red]")
        raise SystemExit(1)

    try:
        input_data = json.loads(input_json)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON input: {e}[/red]")
        raise SystemExit(1)

    console.print(f"Running pipeline: [cyan]{pipeline_name}[/cyan]")
    context = pipe.run(input_data)

    # Display results
    for step_name, result in context.results.items():
        status = "[green]OK[/green]" if result.is_success else "[red]FAIL[/red]"
        console.print(f"  {step_name}: {status}")
        if result.error:
            console.print(f"    Error: {result.error}")
```

Add to `athf/cli.py` after the agent import:

```python
from athf.commands.pipeline import pipeline  # noqa: E402
```

And register it after the agent command:

```python
cli.add_command(pipeline)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/commands/test_pipeline.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add athf/commands/pipeline.py athf/cli.py tests/commands/test_pipeline.py
git commit -m "feat(cli): add athf pipeline list/run CLI commands"
```

---

### Task 8.2: Trigger CLI commands

**Files:**
- Create: `athf/commands/trigger.py`
- Modify: `athf/cli.py` (register command)
- Test: `tests/commands/test_trigger.py`

**Step 1: Write failing test**

```python
# tests/commands/test_trigger.py
"""Tests for trigger CLI commands."""
from click.testing import CliRunner

from athf.cli import cli


class TestTriggerList:
    def test_trigger_list_no_triggers(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["trigger", "list"])
        assert result.exit_code == 0

class TestTriggerEmit:
    def test_trigger_emit_no_match(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["trigger", "emit", "test.event"])
        assert result.exit_code == 0
        assert "0 pipelines triggered" in result.output or "No matching triggers" in result.output
```

**Step 2: Run to verify failure**

Run: `pytest tests/commands/test_trigger.py -v`
Expected: FAIL

**Step 3: Implement**

```python
# athf/commands/trigger.py
"""Event trigger CLI commands."""

import json

import click
from rich.console import Console
from rich.table import Table

from athf.core.events import Event, EventDispatcher
from athf.plugin_system import PluginRegistry

console = Console()


@click.group()
def trigger() -> None:
    """Manage event triggers."""
    pass


@trigger.command("list")
def list_triggers() -> None:
    """List registered triggers."""
    triggers = PluginRegistry._triggers
    if not triggers:
        console.print("[dim]No triggers registered.[/dim]")
        return

    table = Table(title="Registered Triggers")
    table.add_column("Name", style="cyan")
    table.add_column("Pattern", style="green")
    table.add_column("Pipeline", style="yellow")
    table.add_column("Enabled", style="dim")

    for name, t in triggers.items():
        enabled = "Yes" if getattr(t, "enabled", True) else "No"
        pattern = getattr(t, "event_pattern", "?")
        pipeline_name = getattr(t, "pipeline_name", "?")
        table.add_row(name, pattern, pipeline_name, enabled)

    console.print(table)


@trigger.command("emit")
@click.argument("event_type")
@click.option("--payload", default="{}", help="JSON payload for the event")
@click.option("--source", default="cli", help="Event source identifier")
def emit_event(event_type: str, payload: str, source: str) -> None:
    """Emit an event and trigger matching pipelines."""
    try:
        payload_data = json.loads(payload)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON payload: {e}[/red]")
        raise SystemExit(1)

    event = Event(event_type=event_type, payload=payload_data, source=source)

    # Build dispatcher from registered triggers and pipelines
    dispatcher = EventDispatcher()
    for name, t in PluginRegistry._triggers.items():
        dispatcher.register_trigger(t)
    for name, p in PluginRegistry._pipelines.items():
        dispatcher.register_pipeline(name, p)

    results = dispatcher.dispatch(event)

    if not results:
        console.print(f"[dim]No matching triggers for event: {event_type}[/dim]")
    else:
        console.print(f"[green]{len(results)} pipelines triggered[/green]")
        for ctx in results:
            for step_name, result in ctx.results.items():
                status = "[green]OK[/green]" if result.is_success else "[red]FAIL[/red]"
                console.print(f"  {step_name}: {status}")
```

Register in `athf/cli.py`:

```python
from athf.commands.trigger import trigger  # noqa: E402
cli.add_command(trigger)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/commands/test_trigger.py -v`
Expected: PASS

**Step 5: Verify ALL tests pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add athf/commands/trigger.py athf/cli.py tests/commands/test_trigger.py
git commit -m "feat(cli): add athf trigger list/emit CLI commands"
```

---

### Task 8.3: Update package configuration

**Files:**
- Modify: `pyproject.toml`
- Modify: `athf/agents/__init__.py`

**Step 1: Add new packages to setuptools**

In `pyproject.toml` `[tool.setuptools]` packages list, add:
- `"athf.tools"`

**Step 2: Update agent exports**

Add `ReasoningAgent`, `RunState`, `StepRecord` to `athf/agents/__init__.py`.

**Step 3: Verify all tests pass**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add pyproject.toml athf/agents/__init__.py
git commit -m "chore: update package config with new modules and exports"
```

---

## Phase 9: Hunt-Vault Migration (Separate Repo)

> **Note:** This phase is executed in the `/home/projects/hunt-vault/` repository, not ATHF. It depends on all ATHF phases being complete and the updated ATHF package being installed.

### Task 9.1: Create ClickHouseQueryTool

**Files:**
- Create: `nebulock_hunt_vault/tools/__init__.py`
- Create: `nebulock_hunt_vault/tools/clickhouse.py`
- Test: `tests/tools/test_clickhouse_tool.py`

Implementation: Wrap existing `_safe_query()` and `_is_safe_query()` from `DeepBaselineInvestigator` into a `ClickHouseQueryTool(ToolDefinition)` that validates SQL safety and executes via `ClickHouseConnection`.

### Task 9.2: Refactor DeepBaselineInvestigator to extend ReasoningAgent

**Files:**
- Modify: `nebulock_hunt_vault/agents/deep_baseline_investigator.py`
- Test: `tests/agents/test_deep_baseline_investigator.py`

Implementation: Change base class from `LLMAgent` to `ReasoningAgent`. Remove `_iterative_analysis()` loop — replaced by `ReasoningAgent.run()`. Keep `_build_system_prompt()`, `_gather_initial_context()`, `_is_safe_query()` as `build_system_prompt()`, `build_initial_prompt()`, and `validate_tool_call()`.

### Task 9.3: Define pipeline configurations

**Files:**
- Create: `nebulock_hunt_vault/pipelines/__init__.py`
- Create: `nebulock_hunt_vault/pipelines/baseline.py`

Implementation: Define `baseline_pipeline = Pipeline("baseline-investigation", [...])` with DetectorAgent → RouterStep → InvestigatorAgent → NotifierAgent.

### Task 9.4: Register entry points

**Files:**
- Modify: `pyproject.toml`

Add entry points for `athf.tools`, `athf.pipelines`, `athf.triggers`.

### Task 9.5: Refactor lambda_handler.py

**Files:**
- Modify: `infra/lambda_handler.py`

Replace 886-line handler with ~30-line adapter using `LambdaEventSource` → `EventDispatcher`.

---

## Verification Checklist

After all phases are complete, verify:

1. **Backward compatibility:** `pytest tests/ -v` — all existing ATHF tests pass
2. **New tests:** `pytest tests/ -v --tb=short` — all new tests pass
3. **Type checking:** `mypy athf/ --ignore-missing-imports` — no new errors
4. **Import check:** `python -c "from athf.agents import ReasoningAgent, ToolDefinition, LLMProvider"` — succeeds
5. **CLI check:** `athf pipeline list` and `athf trigger list` — work without errors
6. **Plugin check:** `athf agent list` — still shows existing agents
