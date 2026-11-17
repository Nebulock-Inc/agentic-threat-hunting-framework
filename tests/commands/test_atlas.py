"""Tests for athf.commands.atlas - `athf atlas update`."""

import io
import sys
from urllib.error import URLError

import pytest
from click.testing import CliRunner

from athf.commands.atlas import atlas
from athf.core import atlas_matrix

# Get the module for monkeypatching
atlas_cmd = sys.modules['athf.commands.atlas']

MANIFEST = b"""- release: '2026.10'
  release-date: '2026-10-28'
  versions:
  - format-version: 6.1.0
    path: v6/ATLAS-2026.10.yaml
- release: '2026.09'
  versions:
  - format-version: 6.0.0
    path: v6/ATLAS-2026.09.yaml
- release: '9999.99'
  versions:
  - format-version: 6.0.0
    path: ../../evil.yaml
"""


@pytest.fixture
def fake_net(monkeypatch, atlas_fixture_path):
    """Serve MANIFEST and the fixture; record requested URLs."""
    requested = []
    body = atlas_fixture_path.read_bytes()

    def _urlopen(url, timeout=None):
        requested.append(url)
        if url.endswith("manifest.yaml"):
            return io.BytesIO(MANIFEST)
        if url.endswith("v6/ATLAS-2026.10.yaml"):
            return io.BytesIO(body)
        raise URLError(f"unexpected url {url}")

    monkeypatch.setattr(atlas_cmd.urllib.request, "urlopen", _urlopen)
    return requested


@pytest.mark.unit
class TestAtlasUpdate:
    def setup_method(self):
        atlas_matrix.reset_atlas_provider(None)

    def teardown_method(self):
        atlas_matrix.reset_atlas_provider(None)

    def test_downloads_newest_v6_and_caches(self, fake_net):
        result = CliRunner().invoke(atlas, ["update"])
        assert result.exit_code == 0, result.output
        assert fake_net[-1].endswith("dist/v6/ATLAS-2026.10.yaml")
        assert not any("evil" in u for u in fake_net)
        assert atlas_matrix.get_atlas_file_path().exists()
        assert atlas_matrix.get_atlas_provider().is_live()
        assert "2026.10" in result.output

    def test_existing_cache_skipped_without_force(self, fake_net):
        path = atlas_matrix.get_atlas_file_path()
        path.parent.mkdir(parents=True)
        path.write_text("sentinel", encoding="utf-8")
        result = CliRunner().invoke(atlas, ["update"])
        assert result.exit_code == 0
        assert fake_net == []
        assert path.read_text(encoding="utf-8") == "sentinel"

    def test_network_failure_keeps_old_cache(self, monkeypatch):
        path = atlas_matrix.get_atlas_file_path()
        path.parent.mkdir(parents=True)
        path.write_text("old", encoding="utf-8")

        def _boom(url, timeout=None):
            raise URLError("offline")

        monkeypatch.setattr(atlas_cmd.urllib.request, "urlopen", _boom)
        result = CliRunner().invoke(atlas, ["update", "--force"])
        assert result.exit_code != 0
        assert "offline" in result.output
        assert path.read_text(encoding="utf-8") == "old"

    def test_rejects_non_v6_payload(self, monkeypatch):
        def _urlopen(url, timeout=None):
            if url.endswith("manifest.yaml"):
                return io.BytesIO(MANIFEST)
            return io.BytesIO(b"id: ATLAS\nversion: 5.6.0\n")

        monkeypatch.setattr(atlas_cmd.urllib.request, "urlopen", _urlopen)
        result = CliRunner().invoke(atlas, ["update"])
        assert result.exit_code != 0
        assert not atlas_matrix.get_atlas_file_path().exists()

    def test_manifest_without_v6_fails(self, monkeypatch):
        monkeypatch.setattr(
            atlas_cmd.urllib.request, "urlopen",
            lambda url, timeout=None: io.BytesIO(b"- release: '2025.01'\n  versions: []\n"),
        )
        result = CliRunner().invoke(atlas, ["update"])
        assert result.exit_code != 0
        assert "No v6 ATLAS release" in result.output

    def test_registered_on_root_cli(self):
        from athf.cli import cli

        assert "atlas" in cli.commands
