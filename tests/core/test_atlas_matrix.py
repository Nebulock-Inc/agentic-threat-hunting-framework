"""Tests for athf.core.atlas_matrix - MITRE ATLAS data provider."""

import pytest

from athf.core.atlas_matrix import (
    ATLAS_TACTIC_RE,
    ATLAS_TECHNIQUE_RE,
    AtlasFallbackProvider,
    AtlasFormatError,
    AtlasYamlProvider,
    check_format_version,
    get_atlas_file_path,
    get_atlas_provider,
    reset_atlas_provider,
)


@pytest.mark.unit
class TestIdGrammar:
    @pytest.mark.parametrize("value", ["AML.T0051", "AML.T0051.000", "AML.T0002.001"])
    def test_valid_technique_ids(self, value):
        assert ATLAS_TECHNIQUE_RE.match(value)

    @pytest.mark.parametrize(
        "value", ["aml.t0051", "AML.T051", "AML.T0051.1", "AML.TA0005", "T1003", "AML.T0051 ", "", "AML.T0051\n"]
    )
    def test_invalid_technique_ids(self, value):
        assert not ATLAS_TECHNIQUE_RE.match(value)

    def test_tactic_ids(self):
        assert ATLAS_TACTIC_RE.match("AML.TA0005")
        assert not ATLAS_TACTIC_RE.match("AML.T0005")
        assert not ATLAS_TACTIC_RE.match("execution")
        assert not ATLAS_TACTIC_RE.match("AML.TA0005\n")


@pytest.mark.unit
class TestFormatCheck:
    def test_accepts_v6(self):
        check_format_version({"format-version": "6.1.0", "tactics": {}, "techniques": {}})

    @pytest.mark.parametrize("version", ["5.6.0", "7.0.0", "", None])
    def test_rejects_other_majors(self, version):
        with pytest.raises(AtlasFormatError, match="format-version"):
            check_format_version({"format-version": version, "tactics": {}, "techniques": {}})

    def test_rejects_missing_maps(self):
        with pytest.raises(AtlasFormatError, match="tactics/techniques"):
            check_format_version({"format-version": "6.1.0"})

    def test_rejects_non_mapping(self):
        with pytest.raises(AtlasFormatError):
            check_format_version(["not", "a", "mapping"])


@pytest.mark.unit
class TestFallbackProvider:
    def test_has_sixteen_tactics(self):
        tactics = AtlasFallbackProvider().get_tactics()
        assert len(tactics) == 16
        assert tactics["AML.TA0005"]["name"] == "Execution"

    def test_knows_no_techniques(self):
        p = AtlasFallbackProvider()
        assert p.get_technique_by_id("AML.T0051") is None
        assert p.get_techniques_for_tactic("AML.TA0005") == []
        assert p.is_live() is False


@pytest.mark.unit
class TestYamlProvider:
    def test_loads_tactics(self, atlas_fixture_path):
        tactics = AtlasYamlProvider(atlas_fixture_path).get_tactics()
        assert set(tactics) == {"AML.TA0002", "AML.TA0005", "AML.TA0010"}

    def test_technique_lookup_joins_tactics(self, atlas_fixture_path):
        tech = AtlasYamlProvider(atlas_fixture_path).get_technique_by_id("AML.T0051")
        assert tech["name"] == "LLM Prompt Injection"
        assert tech["tactics"] == ["AML.TA0005"]
        assert tech["platforms"] == ["Generative AI", "Agentic AI"]
        assert tech["is_subtechnique"] is False

    def test_dot_000_subtechnique(self, atlas_fixture_path):
        tech = AtlasYamlProvider(atlas_fixture_path).get_technique_by_id("AML.T0000.000")
        assert tech["is_subtechnique"] is True
        assert tech["parent_id"] == "AML.T0000"

    def test_lookup_is_exact_case(self, atlas_fixture_path):
        assert AtlasYamlProvider(atlas_fixture_path).get_technique_by_id("aml.t0051") is None

    def test_techniques_for_tactic_sorted(self, atlas_fixture_path):
        ids = [t["id"] for t in AtlasYamlProvider(atlas_fixture_path).get_techniques_for_tactic("AML.TA0005")]
        assert ids == ["AML.T0051", "AML.T0051.000"]

    def test_sub_techniques(self, atlas_fixture_path):
        ids = [t["id"] for t in AtlasYamlProvider(atlas_fixture_path).get_sub_techniques("AML.T0051")]
        assert ids == ["AML.T0051.000"]

    def test_version_and_live(self, atlas_fixture_path):
        p = AtlasYamlProvider(atlas_fixture_path)
        assert p.get_version() == "2099.01 (format 6.1.0)"
        assert p.is_live() is True

    def test_rejects_legacy_v5_file(self, tmp_path):
        legacy = tmp_path / "atlas.yaml"
        legacy.write_text("id: ATLAS\nversion: 5.6.0\nmatrices: []\n", encoding="utf-8")
        with pytest.raises(AtlasFormatError):
            AtlasYamlProvider(legacy).get_tactics()


@pytest.mark.unit
class TestCacheAndSingleton:
    def setup_method(self):
        reset_atlas_provider(None)

    def teardown_method(self):
        reset_atlas_provider(None)

    def test_env_var_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ATHF_ATLAS_CACHE", str(tmp_path / "x"))
        assert get_atlas_file_path() == tmp_path / "x" / "atlas.yaml"

    def test_workspace_local_cache(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ATHF_ATLAS_CACHE", raising=False)
        (tmp_path / ".athfconfig.yaml").write_text("hunt_prefix: H-\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        assert get_atlas_file_path() == tmp_path / ".athf" / "atlas-data" / "atlas.yaml"

    def test_no_cache_file_means_fallback(self):
        assert isinstance(get_atlas_provider(), AtlasFallbackProvider)

    def test_cached_file_means_yaml_provider(self, atlas_fixture_path):
        target = get_atlas_file_path()
        target.parent.mkdir(parents=True)
        target.write_bytes(atlas_fixture_path.read_bytes())
        assert get_atlas_provider().is_live() is True

    def test_corrupt_cache_degrades_to_fallback(self):
        target = get_atlas_file_path()
        target.parent.mkdir(parents=True)
        target.write_text("format-version: 5.0.0\n", encoding="utf-8")
        # Must not raise: a bad cache cannot be allowed to break `hunt validate`.
        assert isinstance(get_atlas_provider(), AtlasFallbackProvider)

    def test_singleton_is_cached(self):
        assert get_atlas_provider() is get_atlas_provider()

    def test_non_utf8_cache_degrades_to_fallback(self):
        """Corrupt cache with non-UTF-8 bytes must not raise (issue #75)."""
        target = get_atlas_file_path()
        target.parent.mkdir(parents=True)
        target.write_bytes(b"format-version: 6.0.0\ngarbage: \xff\xfe")
        # Must not raise UnicodeDecodeError: a bad cache cannot break `hunt validate`.
        assert isinstance(get_atlas_provider(), AtlasFallbackProvider)

    def test_malformed_relationships_tolerated_by_live_provider(self):
        """Cache with list-valued relationships entry must not raise (issue #75)."""
        target = get_atlas_file_path()
        target.parent.mkdir(parents=True)
        # Write a cache where relationships[AML.T0051] is a list, not a dict
        content = """format-version: 6.0.0
tactics:
  AML.TA0000:
    name: Initial Access
techniques:
  AML.T0051:
    name: Example
    description: Test
relationships:
  AML.T0051: [a]
collection:
  version: 6.1.0
"""
        target.write_text(content, encoding="utf-8")
        # Must not raise AttributeError: rels.get is not a method
        provider = get_atlas_provider()
        assert provider.is_live() is True
        # The technique should still exist, just with empty tactics list
        tech = provider.get_technique_by_id("AML.T0051")
        assert tech is not None
        assert tech["tactics"] == []

    def test_path_resolution_errors_degrade_to_fallback(self, monkeypatch):
        """Exceptions during path resolution or provider construction must not raise."""
        def raise_fnf():
            raise FileNotFoundError("cwd deleted")
        monkeypatch.setattr("athf.core.atlas_matrix.get_atlas_file_path", raise_fnf)
        # Must not raise: any exception in provider resolution should yield fallback
        provider = get_atlas_provider()
        assert isinstance(provider, AtlasFallbackProvider)
