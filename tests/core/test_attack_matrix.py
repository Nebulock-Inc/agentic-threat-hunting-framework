"""Tests for athf.core.attack_matrix - ATT&CK data provider abstraction."""

import importlib
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# FallbackProvider tests (always pass, no optional deps needed)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFallbackProvider:
    """Test the hardcoded fallback provider."""

    def test_get_tactics_returns_14(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        tactics = provider.get_tactics()
        assert len(tactics) == 14

    def test_get_tactics_has_expected_keys(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        tactics = provider.get_tactics()
        assert "credential-access" in tactics
        assert "initial-access" in tactics
        assert "lateral-movement" in tactics

    def test_tactic_info_structure(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        tactics = provider.get_tactics()
        for key, info in tactics.items():
            assert "name" in info
            assert "technique_count" in info
            assert "order" in info
            assert isinstance(info["technique_count"], int)
            assert info["technique_count"] > 0

    def test_get_total_techniques(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        total = provider.get_total_techniques()
        assert total > 100  # Sanity check: ATT&CK has hundreds of techniques

    def test_get_sorted_tactic_keys(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        keys = provider.get_sorted_tactic_keys()
        assert len(keys) == 14
        assert keys[0] == "reconnaissance"
        assert keys[-1] == "impact"

    def test_technique_by_id_returns_none(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        assert provider.get_technique_by_id("T1003") is None

    def test_techniques_for_tactic_returns_empty(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        assert provider.get_techniques_for_tactic("credential-access") == []

    def test_sub_techniques_returns_empty(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        assert provider.get_sub_techniques("T1003") == []

    def test_version_string(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        assert "fallback" in provider.get_version().lower()

    def test_is_stix_false(self):
        from athf.core.attack_matrix import FallbackProvider

        provider = FallbackProvider()
        assert provider.is_stix() is False


# ---------------------------------------------------------------------------
# Module-level backward compatibility tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBackwardCompatibility:
    """Verify that existing imports and APIs still work."""

    def setup_method(self):
        """Reset the provider singleton before each test."""
        from athf.core import attack_matrix

        attack_matrix.reset_provider()

    def test_import_attack_tactics(self):
        """ATTACK_TACTICS can still be imported via __getattr__."""
        from athf.core.attack_matrix import ATTACK_TACTICS  # noqa: F811

        assert isinstance(ATTACK_TACTICS, dict)
        assert len(ATTACK_TACTICS) == 14
        assert "credential-access" in ATTACK_TACTICS

    def test_import_total_techniques(self):
        """TOTAL_TECHNIQUES can still be imported via __getattr__."""
        from athf.core.attack_matrix import TOTAL_TECHNIQUES  # noqa: F811

        assert isinstance(TOTAL_TECHNIQUES, int)
        assert TOTAL_TECHNIQUES > 100

    def test_get_tactic_display_name(self):
        from athf.core.attack_matrix import get_tactic_display_name

        assert get_tactic_display_name("credential-access") == "Credential Access"

    def test_get_tactic_display_name_unknown(self):
        from athf.core.attack_matrix import get_tactic_display_name

        # Unknown tactic should title-case the key
        assert get_tactic_display_name("unknown-tactic") == "Unknown Tactic"

    def test_get_tactic_technique_count(self):
        from athf.core.attack_matrix import get_tactic_technique_count

        count = get_tactic_technique_count("credential-access")
        assert count > 0

    def test_get_tactic_technique_count_unknown(self):
        from athf.core.attack_matrix import get_tactic_technique_count

        assert get_tactic_technique_count("nonexistent") == 0

    def test_get_sorted_tactics(self):
        from athf.core.attack_matrix import get_sorted_tactics

        tactics = get_sorted_tactics()
        assert len(tactics) == 14
        assert tactics[0] == "reconnaissance"

    def test_attack_tactics_tactic_info_shape(self):
        """Each tactic in ATTACK_TACTICS has the expected TacticInfo shape."""
        from athf.core.attack_matrix import ATTACK_TACTICS  # noqa: F811

        for key, info in ATTACK_TACTICS.items():
            assert isinstance(info["name"], str)
            assert isinstance(info["technique_count"], int)
            assert isinstance(info["order"], int)

    def test_getattr_raises_for_unknown(self):
        """Module __getattr__ raises AttributeError for unknown names."""
        with pytest.raises(AttributeError, match="no attribute"):
            from athf.core import attack_matrix

            attack_matrix.__getattr__("NONEXISTENT_THING")


# ---------------------------------------------------------------------------
# Provider selection tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProviderSelection:
    """Test automatic provider selection logic."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider()

    def test_fallback_when_no_mitreattack(self, monkeypatch):
        """Falls back when mitreattack-python is not importable."""
        from athf.core import attack_matrix

        attack_matrix.reset_provider()

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("mitreattack"):
                raise ImportError("mocked: no mitreattack")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Force re-selection
        attack_matrix.reset_provider()
        provider = attack_matrix._get_provider()
        assert isinstance(provider, attack_matrix.FallbackProvider)

    def test_reset_provider_with_explicit(self):
        """reset_provider(provider) sets a specific provider."""
        from athf.core.attack_matrix import FallbackProvider, reset_provider, _get_provider

        custom = FallbackProvider()
        reset_provider(custom)
        assert _get_provider() is custom

    def test_reset_provider_none_triggers_auto(self):
        """reset_provider(None) triggers auto-detection on next access."""
        from athf.core import attack_matrix

        attack_matrix.reset_provider(None)
        # _provider should be None, next _get_provider() auto-selects
        assert attack_matrix._provider is None
        provider = attack_matrix._get_provider()
        assert provider is not None


# ---------------------------------------------------------------------------
# New public API tests (fallback provider)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestNewPublicAPI:
    """Test new API functions with fallback provider."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_get_technique_returns_none(self):
        from athf.core.attack_matrix import get_technique

        assert get_technique("T1003") is None

    def test_get_techniques_for_tactic_returns_empty(self):
        from athf.core.attack_matrix import get_techniques_for_tactic

        assert get_techniques_for_tactic("credential-access") == []

    def test_get_sub_techniques_returns_empty(self):
        from athf.core.attack_matrix import get_sub_techniques

        assert get_sub_techniques("T1003") == []

    def test_get_attack_version(self):
        from athf.core.attack_matrix import get_attack_version

        version = get_attack_version()
        assert "fallback" in version.lower()

    def test_is_using_stix_false(self):
        from athf.core.attack_matrix import is_using_stix

        assert is_using_stix() is False


# ---------------------------------------------------------------------------
# Cache path tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCachePaths:
    """Test STIX cache path resolution."""

    def test_env_var_override(self, monkeypatch, tmp_path):
        from athf.core.attack_matrix import _get_stix_cache_dir

        monkeypatch.setenv("ATHF_STIX_CACHE", str(tmp_path / "custom"))
        assert _get_stix_cache_dir() == tmp_path / "custom"

    def test_global_default(self, monkeypatch):
        from athf.core.attack_matrix import _get_stix_cache_dir

        monkeypatch.delenv("ATHF_STIX_CACHE", raising=False)
        # Ensure no .athfconfig.yaml in cwd
        monkeypatch.chdir("/tmp")
        cache_dir = _get_stix_cache_dir()
        assert "stix-data" in str(cache_dir)
