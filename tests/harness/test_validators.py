"""Tests for harness computational validators (sensors)."""

import pytest

from athf.harness.validators import (
    HypothesisValidator,
    ResearchOutputValidator,
    ValidationResult,
    validate_hypothesis_against_expectations,
)


# ---------------------------------------------------------------------------
# HypothesisValidator
# ---------------------------------------------------------------------------

class TestHypothesisValidator:
    def setup_method(self):
        self.validator = HypothesisValidator()

    def _good_output(self, **overrides):
        data = {
            "hypothesis": "Adversaries use LSASS memory access to dump credentials on Windows endpoints",
            "justification": "LSASS contains NTLM hashes used for lateral movement",
            "mitre_techniques": ["T1003.001"],
            "data_sources": ["EDR", "Sysmon"],
            "expected_observables": ["lsass.exe opened by non-system process", "ReadProcessMemory calls"],
            "known_false_positives": ["AV products", "backup agents"],
            "time_range_suggestion": "7 days (standard baseline window)",
        }
        data.update(overrides)
        return data

    def test_valid_output_passes(self):
        result = self.validator.validate(self._good_output())
        assert result.passed is True
        assert result.score > 0.8
        assert result.violations == []

    def test_empty_hypothesis_is_violation(self):
        result = self.validator.validate(self._good_output(hypothesis=""))
        assert result.passed is False
        assert any("hypothesis" in v for v in result.violations)

    def test_invalid_technique_format_is_violation(self):
        result = self.validator.validate(self._good_output(mitre_techniques=["T1558"]))
        # T1558 without sub-technique is valid (4-digit base code)
        assert result.passed is True

        result2 = self.validator.validate(self._good_output(mitre_techniques=["T155"]))
        assert result2.passed is False
        assert any("mitre_techniques" in v for v in result2.violations)

    def test_subtechnique_format_passes(self):
        result = self.validator.validate(self._good_output(mitre_techniques=["T1003.001"]))
        assert result.passed is True
        assert result.violations == []

    def test_empty_data_sources_is_violation(self):
        result = self.validator.validate(self._good_output(data_sources=[]))
        assert result.passed is False
        assert any("data_sources" in v for v in result.violations)

    def test_no_observables_is_violation(self):
        result = self.validator.validate(self._good_output(expected_observables=[]))
        assert result.passed is False
        assert any("expected_observables" in v for v in result.violations)

    def test_missing_time_range_is_warning_not_violation(self):
        result = self.validator.validate(self._good_output(time_range_suggestion=""))
        assert result.passed is True  # warning, not violation
        assert any("time_range" in w for w in result.warnings)

    def test_hypothesis_without_adversary_pattern_is_warning(self):
        result = self.validator.validate(
            self._good_output(hypothesis="Investigate suspicious LSASS memory reads")
        )
        assert result.passed is True  # warning only
        assert any("adversary" in w.lower() or "pattern" in w.lower() for w in result.warnings)

    def test_accepts_dataclass_like_object(self):
        class FakeOutput:
            hypothesis = "Adversaries use LSASS to dump creds on Windows"
            justification = "NTLM hashes"
            mitre_techniques = ["T1003.001"]
            data_sources = ["EDR"]
            expected_observables = ["process open"]
            known_false_positives = []
            time_range_suggestion = "7 days"

        result = self.validator.validate(FakeOutput())
        assert result.passed is True

    def test_score_is_between_0_and_1(self):
        result = self.validator.validate(self._good_output(hypothesis="", data_sources=[]))
        assert 0.0 <= result.score <= 1.0


# ---------------------------------------------------------------------------
# ResearchOutputValidator
# ---------------------------------------------------------------------------

class TestResearchOutputValidator:
    def setup_method(self):
        self.validator = ResearchOutputValidator()

    def _make_skill(self, name, summary="Content here", findings=None):
        class Skill:
            skill_name = name
            key_findings = findings or ["finding 1"]

        s = Skill()
        s.summary = summary
        return s

    def _good_output(self, **overrides):
        data = {
            "research_id": "R-0001",
            "topic": "LSASS credential dumping",
            "mitre_techniques": ["T1003.001"],
            "system_research": self._make_skill("system_research"),
            "adversary_tradecraft": self._make_skill("adversary_tradecraft"),
            "telemetry_mapping": self._make_skill("telemetry_mapping"),
            "related_work": self._make_skill("related_work"),
            "synthesis": self._make_skill("synthesis"),
            "recommended_hypothesis": "Adversaries dump LSASS to extract credentials",
            "data_source_availability": {"EDR": True, "Sysmon": True},
        }
        data.update(overrides)
        return data

    def test_valid_output_passes(self):
        result = self.validator.validate(self._good_output())
        assert result.passed is True
        assert result.score > 0.8

    def test_invalid_research_id_is_violation(self):
        result = self.validator.validate(self._good_output(research_id="INVALID"))
        assert result.passed is False
        assert any("research_id" in v for v in result.violations)

    def test_empty_topic_is_violation(self):
        result = self.validator.validate(self._good_output(topic=""))
        assert result.passed is False
        assert any("topic" in v for v in result.violations)

    def test_missing_skill_is_violation(self):
        data = self._good_output()
        del data["system_research"]
        result = self.validator.validate(data)
        assert result.passed is False
        assert any("system_research" in v for v in result.violations)

    def test_empty_skill_summary_is_violation(self):
        data = self._good_output()
        data["adversary_tradecraft"] = self._make_skill("adversary_tradecraft", summary="")
        result = self.validator.validate(data)
        assert result.passed is False
        assert any("adversary_tradecraft" in v for v in result.violations)

    def test_missing_hypothesis_is_warning(self):
        result = self.validator.validate(self._good_output(recommended_hypothesis=None))
        assert result.passed is True  # warning only
        assert any("recommended_hypothesis" in w for w in result.warnings)

    def test_research_id_formats(self):
        valid_ids = ["R-0001", "R-9999", "R-0042"]
        for rid in valid_ids:
            result = self.validator.validate(self._good_output(research_id=rid))
            assert result.passed is True, "Should pass for research_id={}".format(rid)

        invalid_ids = ["R-001", "H-0001", "r-0001", "R0001"]
        for rid in invalid_ids:
            result = self.validator.validate(self._good_output(research_id=rid))
            assert result.passed is False, "Should fail for research_id={}".format(rid)


# ---------------------------------------------------------------------------
# validate_hypothesis_against_expectations
# ---------------------------------------------------------------------------

class TestExpectationValidation:
    def _good_output(self):
        return {
            "hypothesis": "Adversaries use LSASS memory access to dump credentials",
            "mitre_techniques": ["T1003.001"],
            "data_sources": ["EDR", "Sysmon"],
            "expected_observables": ["lsass memory read", "suspicious process handle"],
            "time_range_suggestion": "7 days",
        }

    def test_all_expectations_met(self):
        expected = {
            "mitre_techniques_contain": ["T1003.001"],
            "data_sources_any_of": ["EDR"],
            "observables_min_count": 2,
            "hypothesis_pattern_match": True,
        }
        result = validate_hypothesis_against_expectations(self._good_output(), expected)
        assert result.passed is True
        assert result.score == 1.0

    def test_missing_required_technique(self):
        expected = {"mitre_techniques_contain": ["T1558.003"]}
        result = validate_hypothesis_against_expectations(self._good_output(), expected)
        assert result.passed is False
        assert any("T1558.003" in v for v in result.violations)

    def test_data_source_any_of_partial_match(self):
        expected = {"data_sources_any_of": ["Sysmon", "WinEventLog"]}
        result = validate_hypothesis_against_expectations(self._good_output(), expected)
        assert result.passed is True

    def test_insufficient_observables(self):
        expected = {"observables_min_count": 5}
        result = validate_hypothesis_against_expectations(self._good_output(), expected)
        assert result.passed is False
        assert any("observables" in v.lower() for v in result.violations)

    def test_empty_expectations_always_passes(self):
        result = validate_hypothesis_against_expectations(self._good_output(), {})
        assert result.passed is True
        assert result.score == 1.0
