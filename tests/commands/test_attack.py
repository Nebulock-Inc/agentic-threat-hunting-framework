"""Tests for athf.commands.attack - ATT&CK CLI commands."""

import json

import pytest
from click.testing import CliRunner

from athf.commands.attack import _sanitize_stix_bundle, attack


@pytest.mark.unit
class TestAttackStatus:
    """Test 'athf attack status' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_status_shows_provider(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Provider" in result.output
        assert "Fallback" in result.output or "STIX" in result.output

    def test_status_shows_version(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Version" in result.output

    def test_status_shows_tactic_count(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["status"])
        assert result.exit_code == 0
        assert "Tactics" in result.output


@pytest.mark.unit
class TestAttackLookup:
    """Test 'athf attack lookup' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_lookup_without_stix_shows_message(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["lookup", "T1003"])
        assert result.exit_code == 0
        assert "not available" in result.output.lower() or "requires" in result.output.lower()


@pytest.mark.unit
class TestAttackTechniques:
    """Test 'athf attack techniques' command."""

    def setup_method(self):
        from athf.core import attack_matrix

        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

    def test_techniques_without_stix_shows_message(self):
        runner = CliRunner()
        result = runner.invoke(attack, ["techniques", "credential-access"])
        assert result.exit_code == 0
        assert "not available" in result.output.lower() or "requires" in result.output.lower()


@pytest.mark.unit
class TestAttackUpdate:
    """Test 'athf attack update' command."""

    def test_update_without_mitreattack_installed(self, monkeypatch):
        """update should error gracefully when mitreattack-python is not installed."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name.startswith("mitreattack"):
                raise ImportError("mocked: no mitreattack")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        runner = CliRunner()
        result = runner.invoke(attack, ["update"])
        # Should abort (exit code 1) with helpful message
        assert result.exit_code != 0 or "not installed" in result.output.lower()

    def test_update_downloads_via_urllib(self, monkeypatch, tmp_path):
        """update should use urllib.request.urlretrieve, not MitreAttackData.stix_store_to_file."""
        import builtins
        import types
        import urllib.request

        # Ensure the mitreattack import inside update() succeeds even when
        # the package is not installed, by providing a stub module.
        original_import = builtins.__import__
        fake_mitreattack = types.ModuleType("mitreattack")
        fake_stix20 = types.ModuleType("mitreattack.stix20")
        fake_stix20.MitreAttackData = type("MitreAttackData", (), {})
        fake_mitreattack.stix20 = fake_stix20

        def mock_import(name, *args, **kwargs):
            if name == "mitreattack.stix20":
                return fake_stix20
            if name == "mitreattack":
                return fake_mitreattack
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        downloaded = {}

        def mock_urlretrieve(url, dest):
            downloaded["url"] = url
            downloaded["dest"] = dest
            import json
            with open(dest, "w") as f:
                json.dump({"type": "bundle", "objects": []}, f)

        monkeypatch.setattr(urllib.request, "urlretrieve", mock_urlretrieve)

        # Point STIX cache to tmp_path so no real file exists
        monkeypatch.setenv("ATHF_STIX_CACHE", str(tmp_path / "stix-data"))

        from athf.core import attack_matrix
        attack_matrix.reset_provider(attack_matrix.FallbackProvider())

        runner = CliRunner()
        result = runner.invoke(attack, ["update"])

        assert "url" in downloaded, "urlretrieve was not called"
        assert "enterprise-attack" in downloaded["url"]
        assert result.exit_code == 0 or "successfully" in result.output.lower()


@pytest.mark.unit
class TestSanitizeStixBundle:
    """Test _sanitize_stix_bundle strips invalid x_mitre_data_source_ref."""

    def test_removes_empty_refs(self, tmp_path):
        bundle = {
            "type": "bundle",
            "objects": [
                {"type": "x-mitre-data-component", "x_mitre_data_source_ref": ""},
                {"type": "x-mitre-data-component", "x_mitre_data_source_ref": "bad-value"},
                {
                    "type": "x-mitre-data-component",
                    "x_mitre_data_source_ref": "x-mitre-data-source--abcd1234-abcd-abcd-abcd-abcdef123456",
                },
                {"type": "attack-pattern", "name": "no ref field"},
            ],
        }
        path = tmp_path / "enterprise-attack.json"
        with open(path, "w") as f:
            json.dump(bundle, f)

        _sanitize_stix_bundle(path)

        with open(path, "r") as f:
            result = json.load(f)

        objects = result["objects"]
        assert "x_mitre_data_source_ref" not in objects[0]
        assert "x_mitre_data_source_ref" not in objects[1]
        assert objects[2]["x_mitre_data_source_ref"] == "x-mitre-data-source--abcd1234-abcd-abcd-abcd-abcdef123456"
        assert objects[3] == {"type": "attack-pattern", "name": "no ref field"}

    def test_noop_when_all_refs_valid(self, tmp_path):
        bundle = {
            "type": "bundle",
            "objects": [
                {
                    "type": "x-mitre-data-component",
                    "x_mitre_data_source_ref": "x-mitre-data-source--abcd1234-abcd-abcd-abcd-abcdef123456",
                },
            ],
        }
        path = tmp_path / "enterprise-attack.json"
        with open(path, "w") as f:
            json.dump(bundle, f)

        mtime_before = path.stat().st_mtime
        _sanitize_stix_bundle(path)
        mtime_after = path.stat().st_mtime

        assert mtime_before == mtime_after
