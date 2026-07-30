"""Tests for `athf agent run --workshop` spend-guard behavior."""

import json

from click.testing import CliRunner

from athf.commands.agent import WORKSHOP_DEFAULT_TOKEN_CAP, _apply_workshop_mode, run


class FakeAgent:
    """Minimal stand-in exposing the `_call_llm(prompt, max_tokens)` contract."""

    def __init__(self):
        self.calls = []

    def _call_llm(self, prompt: str, max_tokens: int = 4096) -> str:
        self.calls.append(max_tokens)
        return "ok"


def test_clamps_max_tokens_to_cap(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    agent = FakeAgent()

    _apply_workshop_mode(agent, token_cap=256)
    agent._call_llm("hello", max_tokens=4096)

    assert agent.calls == [256]


def test_does_not_raise_cap_when_request_is_smaller(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    agent = FakeAgent()

    _apply_workshop_mode(agent, token_cap=WORKSHOP_DEFAULT_TOKEN_CAP)
    agent._call_llm("hello", max_tokens=128)

    assert agent.calls == [128]


def test_writes_audit_record_per_call(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)
    agent = FakeAgent()

    _apply_workshop_mode(agent, token_cap=256)
    agent._call_llm("a prompt", max_tokens=4096)

    log_path = temp_dir / ".athf" / "session.log"
    assert log_path.exists()

    record = json.loads(log_path.read_text().strip())
    assert record["requested_max_tokens"] == 4096
    assert record["effective_max_tokens"] == 256
    assert record["token_cap"] == 256
    assert record["prompt_chars"] == len("a prompt")
    assert record["error"] is None


def test_logs_and_reraises_on_error(temp_dir, monkeypatch):
    monkeypatch.chdir(temp_dir)

    class FailingAgent:
        def _call_llm(self, prompt: str, max_tokens: int = 4096) -> str:
            raise RuntimeError("boom")

    agent = FailingAgent()
    _apply_workshop_mode(agent, token_cap=256)

    raised = False
    try:
        agent._call_llm("x", max_tokens=512)
    except RuntimeError:
        raised = True
    assert raised

    record = json.loads((temp_dir / ".athf" / "session.log").read_text().strip())
    assert record["error"] == "boom"
    assert record["effective_max_tokens"] == 256


def test_setup_failure_does_not_block_call(temp_dir, monkeypatch):
    """An unwritable log dir must not abort the wrapped LLM call."""
    monkeypatch.chdir(temp_dir)
    # Make .athf a file so mkdir raises OSError — logging becomes unavailable.
    (temp_dir / ".athf").write_text("not a directory")

    agent = FakeAgent()
    _apply_workshop_mode(agent, token_cap=256)

    assert agent._call_llm("hello", max_tokens=4096) == "ok"
    assert agent.calls == [256]


def test_run_rejects_zero_token_cap(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        run,
        ["hypothesis-generator", "--threat-intel", "x", "--workshop", "--token-cap", "0"],
    )
    assert result.exit_code != 0
    assert "--token-cap must be >= 1" in result.output


def test_run_rejects_negative_token_cap(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(
        run,
        ["hunt-researcher", "--topic", "x", "--workshop", "--token-cap", "-5"],
    )
    assert result.exit_code != 0
    assert "--token-cap must be >= 1" in result.output
