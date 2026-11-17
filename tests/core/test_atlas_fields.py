"""Tests for athf.core.atlas_fields - ATLAS front-matter rules."""

import pytest

from athf.core import atlas_matrix
from athf.core.atlas_fields import atlas_field_errors, atlas_field_warnings


@pytest.mark.unit
class TestAtlasFieldErrors:
    def test_absent_fields_are_clean(self):
        assert atlas_field_errors({"techniques": ["T1003"]}) == []

    def test_null_and_empty_are_clean(self):
        assert atlas_field_errors({"atlas_techniques": None, "atlas_tactics": []}) == []

    def test_valid_ids_are_clean(self):
        fm = {"atlas_techniques": ["AML.T0051", "AML.T0002.000"], "atlas_tactics": ["AML.TA0005"]}
        assert atlas_field_errors(fm) == []

    def test_scalar_instead_of_list(self):
        errors = atlas_field_errors({"atlas_techniques": "AML.T0051"})
        assert errors == ["atlas_techniques must be a list; got str"]

    def test_non_string_element(self):
        errors = atlas_field_errors({"atlas_techniques": [51]})
        assert errors == ["atlas_techniques[0] must be a string; got int"]

    def test_attack_id_in_atlas_field(self):
        errors = atlas_field_errors({"atlas_techniques": ["T1567"]})
        assert len(errors) == 1
        assert "ATT&CK ID" in errors[0] and "techniques" in errors[0]

    @pytest.mark.parametrize("bad", ["aml.t0051", "AML.T51", "AML.TA0005", "AML.T0051.1"])
    def test_malformed_technique(self, bad):
        errors = atlas_field_errors({"atlas_techniques": [bad]})
        assert len(errors) == 1
        assert "AML.T0000" in errors[0]

    @pytest.mark.parametrize("bad", ["execution", "AML.T0005", "TA0002"])
    def test_malformed_tactic(self, bad):
        errors = atlas_field_errors({"atlas_tactics": [bad]})
        assert len(errors) == 1
        assert "AML.TA0000" in errors[0]

    def test_non_mapping_frontmatter(self):
        assert atlas_field_errors(None) == []  # type: ignore[arg-type]


@pytest.mark.unit
class TestAtlasFieldWarnings:
    def setup_method(self):
        atlas_matrix.reset_atlas_provider(None)

    def teardown_method(self):
        atlas_matrix.reset_atlas_provider(None)

    def test_no_atlas_fields_never_loads_data(self):
        assert atlas_field_warnings({"techniques": ["T1003"]}) == []
        assert atlas_matrix._provider is None

    def test_atlas_id_in_attack_field(self):
        warnings = atlas_field_warnings({"techniques": ["T1003", "AML.T0051"]})
        assert len(warnings) == 1
        assert "atlas_techniques" in warnings[0]

    def test_unknown_ids_warn_with_live_data(self, atlas_provider):
        fm = {"atlas_techniques": ["AML.T0051", "AML.T9999"], "atlas_tactics": ["AML.TA0099"]}
        warnings = atlas_field_warnings(fm)
        assert len(warnings) == 2
        assert any("AML.T9999" in w for w in warnings)
        assert any("AML.TA0099" in w for w in warnings)
        assert all("2099.01" in w for w in warnings)

    def test_known_ids_are_quiet(self, atlas_provider):
        assert atlas_field_warnings({"atlas_techniques": ["AML.T0051.000"], "atlas_tactics": ["AML.TA0005"]}) == []

    def test_fallback_cannot_judge_so_stays_quiet(self):
        atlas_matrix.reset_atlas_provider(atlas_matrix.AtlasFallbackProvider())
        assert atlas_field_warnings({"atlas_techniques": ["AML.T9999"]}) == []

    def test_malformed_ids_are_not_double_reported(self, atlas_provider):
        # Malformed IDs are errors; warnings must not repeat them as "unknown".
        assert atlas_field_warnings({"atlas_techniques": ["bogus"]}) == []
