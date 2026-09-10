"""`athf hunt validate` must fail the process when the evidence gate refuses.

AGENTS.md tells hunters to run this before closeout and CI runs it as a check,
but the command printed refusals and exited 0 — so a hunt claiming ``confirmed``
by a means its producer cannot perform merged green. The gate has to be
observable to a shell, not only to a human reading scrollback.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from athf.commands.hunt import hunt
from athf.commands.init import init

CONFIRMED_FINDING = {
    "subject": "web-prod-04",
    "verdict": "confirmed",
    "evidence": "OCSF process_activity shows sh writing /var/spool/cron/crontabs/svc_deploy",
    "confirmation": {
        "method": "host_forensics",
        "produced_by": "ir-team",
        "attested_by": "J. Halloran",
        "detail": "Recovered the crontab entry and the dropper binary from the imaged disk",
    },
}


def _write_config(producers: dict[str, object]) -> None:
    """Declare a producer registry at the workspace root."""
    Path(".athfconfig.yaml").write_text(
        yaml.safe_dump({"provenance": {"producers": producers}}, sort_keys=False),
        encoding="utf-8",
    )


def _write_hunt(hunt_id: str, **extra: object) -> None:
    """Overwrite a hunt file's frontmatter, keeping the LOCK body intact."""
    hunt_file = next(Path("hunts").rglob(f"{hunt_id}.md"))
    body = hunt_file.read_text(encoding="utf-8").split("---", 2)[2]
    frontmatter = {
        "hunt_id": hunt_id,
        "title": "Gate probe",
        "status": "completed",
        "date": "2026-09-02",
        "hunter": "Sydney Marrone",
        "platform": ["Linux"],
        "tactics": ["persistence"],
        "techniques": ["T1053.003"],
        "customer_deliverables": [],
        **extra,
    }
    hunt_file.write_text(
        f"---\n{yaml.safe_dump(frontmatter, sort_keys=False)}---{body}",
        encoding="utf-8",
    )


@pytest.fixture
def workspace(tmp_path):
    """An initialized workspace containing one hunt, as the CLI would create it."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(init, ["--non-interactive"])
        runner.invoke(hunt, ["new", "--title", "Gate probe", "--non-interactive"])
        yield runner


class TestValidateSignalsRefusalToTheShell:
    """A refused hunt must exit nonzero so CI and `&&` chains observe it."""

    def test_single_hunt_refusal_exits_nonzero(self, workspace):
        _write_config({"query-agent": {"capabilities": ["clickhouse_query"]}})
        _write_hunt("H-0001", findings=[CONFIRMED_FINDING], ruled_out=[])

        result = workspace.invoke(hunt, ["validate", "H-0001"])

        assert result.exit_code != 0, result.output

    def test_valid_hunt_still_exits_zero(self, workspace):
        _write_config({"ir-team": {"capabilities": ["host_forensics"]}})
        _write_hunt("H-0001", findings=[CONFIRMED_FINDING], ruled_out=[])

        result = workspace.invoke(hunt, ["validate", "H-0001"])

        assert result.exit_code == 0, result.output

    def test_validate_all_exits_nonzero_when_any_hunt_is_refused(self, workspace):
        _write_config({"query-agent": {"capabilities": ["clickhouse_query"]}})
        _write_hunt("H-0001", findings=[CONFIRMED_FINDING], ruled_out=[])

        result = workspace.invoke(hunt, ["validate"])

        assert result.exit_code != 0, result.output

    def test_missing_hunt_exits_nonzero(self, workspace):
        result = workspace.invoke(hunt, ["validate", "H-9999"])

        assert result.exit_code != 0, result.output
        assert "not found" in result.output.lower()

    def test_malformed_hunt_id_exits_nonzero(self, workspace):
        result = workspace.invoke(hunt, ["validate", "not-a-hunt-id"])

        assert result.exit_code != 0, result.output


class TestRootConfigIsNotShadowedByInitConfig:
    """The root ``.athfconfig.yaml`` is the documented place to declare producers.

    ``athf init`` writes ``config/.athfconfig.yaml``, so a workspace routinely has
    both. Reading the init copy first meant a hunter who followed AGENTS.md and
    edited the root file had their declaration silently ignored, and every
    ``confirmed`` was refused as an undeclared producer with no hint why.
    """

    def test_root_declaration_wins_over_init_config(self, workspace):
        Path("config").mkdir(exist_ok=True)
        Path("config/.athfconfig.yaml").write_text(
            yaml.safe_dump({"hunt_prefix": "H-"}, sort_keys=False), encoding="utf-8"
        )
        _write_config({"ir-team": {"capabilities": ["host_forensics"]}})
        _write_hunt("H-0001", findings=[CONFIRMED_FINDING], ruled_out=[])

        result = workspace.invoke(hunt, ["validate", "H-0001"])

        assert result.exit_code == 0, result.output

    def test_init_config_still_read_when_root_absent(self, workspace):
        Path("config").mkdir(exist_ok=True)
        Path("config/.athfconfig.yaml").write_text(
            yaml.safe_dump(
                {"provenance": {"producers": {"ir-team": {"capabilities": ["host_forensics"]}}}},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        Path(".athfconfig.yaml").unlink(missing_ok=True)
        _write_hunt("H-0001", findings=[CONFIRMED_FINDING], ruled_out=[])

        result = workspace.invoke(hunt, ["validate", "H-0001"])

        assert result.exit_code == 0, result.output
