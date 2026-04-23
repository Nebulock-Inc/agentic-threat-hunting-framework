"""Tests for harness evaluator, dataset loader, and metrics."""

import json
import pytest
from pathlib import Path

from athf.harness.dataset import EvalCase, EvalDataset, load_dataset, list_bundled_datasets
from athf.harness.evaluator import CaseResult, HarnessEvaluator
from athf.harness.metrics import HarnessReport, build_report, render_report_json


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

class TestLoadDataset:
    def test_load_bundled_hypothesis_dataset(self):
        datasets = list_bundled_datasets()
        assert len(datasets) >= 1
        names = [p.name for p in datasets]
        assert any("hypothesis" in n for n in names)

    def test_bundled_dataset_valid(self):
        datasets = list_bundled_datasets()
        for path in datasets:
            ds = load_dataset(path)
            assert ds.version
            assert ds.agent
            assert ds.case_count > 0
            for case in ds.cases:
                assert case.id
                assert case.description

    def test_load_dataset_from_dict(self, tmp_path):
        import yaml

        data = {
            "version": "1.0",
            "agent": "hypothesis-generator",
            "description": "test dataset",
            "cases": [
                {
                    "id": "test-001",
                    "description": "Test case",
                    "input": {"threat_intel": "Test intel"},
                    "expected": {"observables_min_count": 1},
                }
            ],
        }
        path = tmp_path / "test.yaml"
        path.write_text(yaml.dump(data))
        ds = load_dataset(path)
        assert ds.case_count == 1
        assert ds.cases[0].id == "test-001"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dataset(tmp_path / "nonexistent.yaml")

    def test_missing_required_field_raises(self, tmp_path):
        import yaml

        bad = {"version": "1.0", "cases": []}  # missing 'agent'
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(bad))
        with pytest.raises(ValueError, match="missing required field 'agent'"):
            load_dataset(path)

    def test_get_bundled_dataset_for_agent(self):
        from athf.harness.dataset import get_bundled_dataset_for_agent

        path = get_bundled_dataset_for_agent("hypothesis-generator")
        assert path is not None
        assert path.exists()

    def test_get_bundled_dataset_unknown_agent(self):
        from athf.harness.dataset import get_bundled_dataset_for_agent

        path = get_bundled_dataset_for_agent("unknown-agent-xyz")
        assert path is None


# ---------------------------------------------------------------------------
# HarnessEvaluator — offline mode
# ---------------------------------------------------------------------------

class TestHarnessEvaluatorOffline:
    def setup_method(self):
        self.evaluator = HarnessEvaluator()

    def _make_dataset(self, cases):
        return EvalDataset(
            version="1.0",
            agent="hypothesis-generator",
            description="test",
            cases=cases,
        )

    def test_offline_well_formed_case_passes(self):
        case = EvalCase(
            id="t-001",
            description="Test",
            input={"threat_intel": "some intel"},
            expected={"observables_min_count": 1},
        )
        results = self.evaluator.run_offline(self._make_dataset([case]))
        assert len(results) == 1
        assert results[0].passed is True

    def test_offline_empty_input_fails(self):
        case = EvalCase(
            id="t-002",
            description="Missing input",
            input={},
            expected={"observables_min_count": 1},
        )
        results = self.evaluator.run_offline(self._make_dataset([case]))
        assert results[0].passed is False
        assert results[0].violations

    def test_offline_no_expectations_warns(self):
        case = EvalCase(
            id="t-003",
            description="No expectations",
            input={"threat_intel": "intel"},
            expected={},
        )
        results = self.evaluator.run_offline(self._make_dataset([case]))
        assert results[0].passed is True
        assert results[0].warnings

    def test_offline_returns_one_result_per_case(self):
        cases = [
            EvalCase(id="t-{}".format(i), description="case", input={"x": i}, expected={"a": 1})
            for i in range(5)
        ]
        results = self.evaluator.run_offline(self._make_dataset(cases))
        assert len(results) == 5

    def test_offline_bundled_dataset_all_pass(self):
        from athf.harness.dataset import get_bundled_dataset_for_agent, load_dataset

        path = get_bundled_dataset_for_agent("hypothesis-generator")
        assert path is not None
        ds = load_dataset(path)
        results = self.evaluator.run_offline(ds)
        for r in results:
            assert r.passed is True, "Case {} failed: {}".format(r.case_id, r.violations)


# ---------------------------------------------------------------------------
# HarnessEvaluator — score_dict_output
# ---------------------------------------------------------------------------

class TestHarnessEvaluatorScoring:
    def setup_method(self):
        self.evaluator = HarnessEvaluator()

    def _good_case(self):
        return EvalCase(
            id="s-001",
            description="LSASS dump",
            input={"threat_intel": "LSASS targeting"},
            expected={
                "mitre_techniques_contain": ["T1003.001"],
                "data_sources_any_of": ["EDR"],
                "observables_min_count": 1,
                "hypothesis_pattern_match": True,
            },
        )

    def _good_output(self):
        return {
            "hypothesis": "Adversaries use LSASS memory access to extract credentials on Windows",
            "justification": "NTLM hashes enable lateral movement",
            "mitre_techniques": ["T1003.001"],
            "data_sources": ["EDR", "Sysmon"],
            "expected_observables": ["lsass handle open", "suspicious memory read"],
            "known_false_positives": ["AV scanners"],
            "time_range_suggestion": "7 days",
        }

    def test_passing_output_scores_high(self):
        result = self.evaluator.score_dict_output(
            self._good_case(), self._good_output(), "hypothesis-generator"
        )
        assert result.passed is True
        assert result.score >= 0.8

    def test_missing_technique_causes_failure(self):
        output = self._good_output()
        output["mitre_techniques"] = ["T9999.001"]  # wrong technique
        result = self.evaluator.score_dict_output(
            self._good_case(), output, "hypothesis-generator"
        )
        assert result.passed is False
        assert result.score < 1.0

    def test_result_has_correct_case_id(self):
        result = self.evaluator.score_dict_output(
            self._good_case(), self._good_output(), "hypothesis-generator"
        )
        assert result.case_id == "s-001"


# ---------------------------------------------------------------------------
# HarnessReport and metrics
# ---------------------------------------------------------------------------

class TestHarnessReport:
    def _make_results(self, passed_count, failed_count):
        results = []
        for i in range(passed_count):
            results.append(CaseResult(
                case_id="p-{:03d}".format(i),
                description="pass",
                passed=True,
                score=0.9,
            ))
        for i in range(failed_count):
            results.append(CaseResult(
                case_id="f-{:03d}".format(i),
                description="fail",
                passed=False,
                score=0.3,
                violations=["something wrong"],
            ))
        return results

    def _dummy_dataset(self, n):
        return EvalDataset(
            version="1.0",
            agent="hypothesis-generator",
            description="test",
            cases=[
                EvalCase(id=str(i), description="", input={}, expected={})
                for i in range(n)
            ],
        )

    def test_pass_rate_calculation(self):
        results = self._make_results(3, 1)
        ds = self._dummy_dataset(4)
        report = build_report("hypothesis-generator", ds, results)
        assert report.passed == 3
        assert report.failed == 1
        assert report.pass_rate == pytest.approx(0.75)

    def test_perfect_pass_rate(self):
        results = self._make_results(5, 0)
        ds = self._dummy_dataset(5)
        report = build_report("hypothesis-generator", ds, results)
        assert report.pass_rate == 1.0

    def test_avg_score(self):
        results = self._make_results(2, 2)  # 0.9, 0.9, 0.3, 0.3
        ds = self._dummy_dataset(4)
        report = build_report("hypothesis-generator", ds, results)
        assert report.avg_score == pytest.approx((0.9 + 0.9 + 0.3 + 0.3) / 4, rel=1e-3)

    def test_all_violations_includes_case_id(self):
        results = self._make_results(0, 2)
        ds = self._dummy_dataset(2)
        report = build_report("hypothesis-generator", ds, results)
        violations = report.all_violations
        assert len(violations) == 2
        assert all("f-" in v for v in violations)

    def test_json_output_is_valid(self):
        results = self._make_results(1, 1)
        ds = self._dummy_dataset(2)
        report = build_report("hypothesis-generator", ds, results)
        json_str = render_report_json(report)
        parsed = json.loads(json_str)
        assert parsed["total_cases"] == 2
        assert parsed["passed"] == 1
        assert "cases" in parsed
        assert len(parsed["cases"]) == 2


# ---------------------------------------------------------------------------
# Agent base harness hooks
# ---------------------------------------------------------------------------

class TestAgentHarnessHooks:
    def test_sensor_attached_and_called(self):
        from athf.agents.base import Agent, AgentResult, Sensor

        observed = []

        class TrackingSensor(Sensor):
            def observe(self, result):
                observed.append(result)

        class NoOpAgent(Agent):
            def execute(self, input_data):
                return AgentResult(success=True, data="output")

        agent = NoOpAgent()
        agent.attach_sensor(TrackingSensor())
        agent("input")
        assert len(observed) == 1
        assert observed[0].data == "output"

    def test_sensor_not_called_on_failure(self):
        from athf.agents.base import Agent, AgentResult, Sensor

        observed = []

        class TrackingSensor(Sensor):
            def observe(self, result):
                observed.append(result)

        class FailingAgent(Agent):
            def execute(self, input_data):
                return AgentResult(success=False, data=None, error="fail")

        agent = FailingAgent()
        agent.attach_sensor(TrackingSensor())
        agent("input")
        assert len(observed) == 0

    def test_sensor_error_does_not_propagate(self):
        from athf.agents.base import Agent, AgentResult, Sensor

        class BrokenSensor(Sensor):
            def observe(self, result):
                raise RuntimeError("sensor broke")

        class SimpleAgent(Agent):
            def execute(self, input_data):
                return AgentResult(success=True, data="ok")

        agent = SimpleAgent()
        agent.attach_sensor(BrokenSensor())
        result = agent("input")  # Should not raise
        assert result.data == "ok"

    def test_pre_execute_hook_called(self):
        from athf.agents.base import Agent, AgentResult

        called_with = []

        class HookedAgent(Agent):
            def _pre_execute_hook(self, input_data):
                called_with.append(input_data)

            def execute(self, input_data):
                return AgentResult(success=True, data=input_data)

        agent = HookedAgent()
        agent("test_input")
        assert called_with == ["test_input"]

    def test_multiple_sensors(self):
        from athf.agents.base import Agent, AgentResult, Sensor

        counts = [0, 0]

        class S1(Sensor):
            def observe(self, result):
                counts[0] += 1

        class S2(Sensor):
            def observe(self, result):
                counts[1] += 1

        class SimpleAgent(Agent):
            def execute(self, input_data):
                return AgentResult(success=True, data="x")

        agent = SimpleAgent()
        agent.attach_sensor(S1())
        agent.attach_sensor(S2())
        agent("x")
        assert counts == [1, 1]
