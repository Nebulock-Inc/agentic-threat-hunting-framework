"""Tests for athf.core.llm_provider - model-agnostic LLM provider layer."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from athf.core.llm_provider import (
    BedrockProvider,
    LiteLLMProvider,
    LLMProvider,
    LLMResponse,
    OllamaProvider,
    OpenAICompatibleProvider,
    _load_config_file,
    _ollama_is_running,
    create_provider,
)


# ---------------------------------------------------------------------------
# LiteLLM provider
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLiteLLMProvider:
    """Test LiteLLMProvider with mocked litellm."""

    def test_litellm_provider_complete(self):
        """Mocked litellm.completion returns a properly parsed LLMResponse."""
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 80
        mock_usage.completion_tokens = 40

        mock_message = MagicMock()
        mock_message.content = "LiteLLM response"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_litellm = MagicMock()
        mock_litellm.completion.return_value = mock_response

        with patch.dict(sys.modules, {"litellm": mock_litellm}):
            provider = LiteLLMProvider(model="anthropic/claude-sonnet-4-5-20250514")
            result = provider.complete(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result.text == "LiteLLM response"
        assert result.input_tokens == 80
        assert result.output_tokens == 40
        assert result.model == "anthropic/claude-sonnet-4-5-20250514"
        assert provider.provider_name == "litellm"

        # Verify the request was built correctly
        mock_litellm.completion.assert_called_once_with(
            model="anthropic/claude-sonnet-4-5-20250514",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=4096,
            temperature=0.7,
        )

    def test_litellm_provider_import_error(self):
        """ImportError is raised when litellm is not installed."""
        # Remove litellm from sys.modules so the lazy import fails
        with patch.dict(sys.modules, {"litellm": None}):
            provider = LiteLLMProvider()
            with pytest.raises(ImportError, match="litellm"):
                provider.complete(
                    messages=[{"role": "user", "content": "Hi"}]
                )


# ---------------------------------------------------------------------------
# Bedrock provider
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBedrockProvider:
    """Test BedrockProvider with mocked boto3."""

    def _make_mock_client(self, text="Hello from Bedrock", input_tok=100, output_tok=50):
        """Build a mock boto3 bedrock-runtime client."""
        mock_body = MagicMock()
        mock_body.read.return_value = json.dumps(
            {
                "content": [{"text": text}],
                "usage": {
                    "input_tokens": input_tok,
                    "output_tokens": output_tok,
                },
            }
        ).encode()
        mock_client = MagicMock()
        mock_client.invoke_model.return_value = {"body": mock_body}
        return mock_client

    def test_bedrock_provider_complete(self):
        """Mocked Bedrock invoke_model returns a properly parsed LLMResponse."""
        mock_client = self._make_mock_client()

        provider = BedrockProvider(model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0")
        provider._client = mock_client  # inject mock, bypass boto3 import

        result = provider.complete(
            messages=[{"role": "user", "content": "Hi"}]
        )

        assert result.text == "Hello from Bedrock"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert provider.provider_name == "bedrock"

        # Verify the Bedrock request body format is preserved
        call_kwargs = mock_client.invoke_model.call_args
        sent_body = json.loads(call_kwargs.kwargs.get("body", call_kwargs[1].get("body", "")))
        assert sent_body["anthropic_version"] == "bedrock-2023-05-31"
        assert sent_body["messages"] == [{"role": "user", "content": "Hi"}]

    def test_bedrock_provider_import_error(self):
        """ImportError is raised when boto3 is not installed."""
        with patch.dict(sys.modules, {"boto3": None}):
            provider = BedrockProvider()
            provider._client = None  # ensure lazy init triggers
            with pytest.raises(ImportError, match="boto3"):
                provider.complete(
                    messages=[{"role": "user", "content": "Hi"}]
                )


# ---------------------------------------------------------------------------
# Ollama provider
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestOllamaProvider:
    """Test OllamaProvider with mocked urllib."""

    def test_ollama_provider_complete(self):
        """Mocked urlopen returns a properly parsed LLMResponse."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "message": {"content": "Hello from Ollama"},
                "prompt_eval_count": 10,
                "eval_count": 5,
            }
        ).encode("utf-8")
        mock_resp.status = 200

        with patch("urllib.request.urlopen", return_value=mock_resp):
            provider = OllamaProvider(model="llama3")
            result = provider.complete(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result.text == "Hello from Ollama"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        assert result.cost_usd == 0.0
        assert provider.provider_name == "ollama"

    def test_ollama_provider_sends_correct_payload(self):
        """Verify the JSON payload sent to Ollama's /api/chat endpoint."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "message": {"content": "ok"},
                "prompt_eval_count": 1,
                "eval_count": 1,
            }
        ).encode("utf-8")
        mock_resp.status = 200

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            provider = OllamaProvider(model="llama3")
            provider.complete(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=512,
                temperature=0.3,
            )

        sent_request = mock_urlopen.call_args[0][0]
        sent_body = json.loads(sent_request.data.decode("utf-8"))
        assert sent_body["model"] == "llama3"
        assert sent_body["messages"] == [{"role": "user", "content": "test"}]
        assert sent_body["stream"] is False
        assert sent_body["options"]["num_predict"] == 512
        assert sent_body["options"]["temperature"] == 0.3
        assert "api/chat" in sent_request.full_url

    def test_ollama_provider_connection_error(self):
        """ConnectionError is raised when Ollama is unreachable."""
        from urllib.error import URLError

        with patch(
            "urllib.request.urlopen",
            side_effect=URLError("Connection refused"),
        ):
            provider = OllamaProvider()
            with pytest.raises(ConnectionError, match="Cannot reach Ollama"):
                provider.complete(
                    messages=[{"role": "user", "content": "Hi"}]
                )


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestOpenAICompatibleProvider:
    """Test OpenAICompatibleProvider with mocked openai."""

    def test_openai_provider_complete(self):
        """Mocked openai client returns a properly parsed LLMResponse."""
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 60
        mock_usage.completion_tokens = 30

        mock_message = MagicMock()
        mock_message.content = "Hello from OpenAI"

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAICompatibleProvider(model="gpt-4o", api_key="test-key")
        provider._client = mock_client  # inject mock, bypass openai import

        result = provider.complete(
            messages=[{"role": "user", "content": "Hi"}]
        )

        assert result.text == "Hello from OpenAI"
        assert result.input_tokens == 60
        assert result.output_tokens == 30
        assert provider.provider_name == "openai"

        # Verify the request was built correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=4096,
            temperature=0.7,
        )


# ---------------------------------------------------------------------------
# create_provider factory
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCreateProvider:
    """Test the create_provider factory with various configurations."""

    def _clean_env(self):
        """Return a dict for patch.dict that clears all auto-detect keys."""
        return {
            "ATHF_LLM_PROVIDER": "",
            "ATHF_LLM_MODEL": "",
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
            "AWS_PROFILE": "",
            "AWS_ACCESS_KEY_ID": "",
        }

    def test_create_provider_explicit_config(self):
        """Explicit config dict selects the correct provider class."""
        with patch.object(
            BedrockProvider, "_get_client", return_value=MagicMock()
        ), patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict(
            "os.environ", self._clean_env(), clear=False
        ):
            provider = create_provider(
                {"provider": "bedrock", "model": "us.anthropic.claude-sonnet-4-5-v1:0"}
            )
            assert isinstance(provider, BedrockProvider)

    def test_create_provider_env_vars(self):
        """ATHF_LLM_PROVIDER env var selects the correct provider."""
        env = self._clean_env()
        env["ATHF_LLM_PROVIDER"] = "ollama"

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict("os.environ", env, clear=False):
            provider = create_provider()
            assert isinstance(provider, OllamaProvider)

    def test_create_provider_auto_detect_anthropic(self):
        """ANTHROPIC_API_KEY triggers LiteLLM provider."""
        env = self._clean_env()
        env["ANTHROPIC_API_KEY"] = "sk-ant-test"

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict("os.environ", env, clear=False):
            provider = create_provider()
            assert isinstance(provider, LiteLLMProvider)

    def test_create_provider_auto_detect_openai(self):
        """OPENAI_API_KEY triggers OpenAICompatibleProvider."""
        env = self._clean_env()
        env["OPENAI_API_KEY"] = "sk-test"

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict("os.environ", env, clear=False):
            provider = create_provider()
            assert isinstance(provider, OpenAICompatibleProvider)

    def test_create_provider_auto_detect_aws(self):
        """AWS_PROFILE triggers BedrockProvider."""
        env = self._clean_env()
        env["AWS_PROFILE"] = "default"

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict("os.environ", env, clear=False):
            provider = create_provider()
            assert isinstance(provider, BedrockProvider)

    def test_create_provider_auto_detect_ollama(self):
        """Running Ollama triggers OllamaProvider when no API keys set."""
        env = self._clean_env()

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict(
            "os.environ", env, clear=False
        ), patch(
            "athf.core.llm_provider._ollama_is_running", return_value=True
        ):
            provider = create_provider()
            assert isinstance(provider, OllamaProvider)

    def test_create_provider_no_provider_error(self):
        """RuntimeError when no provider can be determined."""
        env = self._clean_env()

        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict(
            "os.environ", env, clear=False
        ), patch(
            "athf.core.llm_provider._ollama_is_running", return_value=False
        ):
            with pytest.raises(RuntimeError, match="No LLM provider"):
                create_provider()

    def test_create_provider_unknown_provider(self):
        """ValueError for an unrecognized provider name."""
        with patch(
            "athf.core.llm_provider._load_config_file", return_value={}
        ), patch.dict("os.environ", self._clean_env(), clear=False):
            with pytest.raises(ValueError, match="Unknown LLM provider"):
                create_provider({"provider": "unknown"})
