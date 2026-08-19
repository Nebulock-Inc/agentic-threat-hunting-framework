"""Tests for packaging declarations that CI alone would not catch until release time."""

import pathlib
import re

import athf

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _project_table():
    """Return the text of pyproject.toml's [project] table.

    Parsed with a regex rather than tomllib because the test suite runs on Python 3.8,
    where tomllib does not exist and no TOML library is a declared dependency.
    """
    text = PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r"^\[project\]\s*$(.*?)^\[", text, re.MULTILINE | re.DOTALL)
    assert match, "could not locate the [project] table in pyproject.toml"
    return match.group(1)


class TestVersionSingleSource:
    """athf/__version__.py must be the only place the version is written."""

    def test_pyproject_declares_version_dynamic(self):
        assert re.search(r'^dynamic\s*=\s*\[[^\]]*"version"', _project_table(), re.MULTILINE), (
            'pyproject.toml [project] must declare dynamic = ["version"] so the version ' "is read from athf/__version__.py"
        )

    def test_pyproject_has_no_literal_version(self):
        assert not re.search(r'^version\s*=\s*"', _project_table(), re.MULTILINE), (
            "pyproject.toml [project] must not pin a literal version; a second literal can "
            "disagree with athf/__version__.py and the release pipeline only checks one"
        )

    def test_dynamic_version_points_at_the_version_module(self):
        text = PYPROJECT.read_text(encoding="utf-8")
        assert (
            'version = {attr = "athf.__version__.__version__"}' in text
        ), "[tool.setuptools.dynamic] must source the version from athf.__version__"

    def test_version_is_pep440_release(self):
        assert re.fullmatch(r"\d+\.\d+\.\d+", athf.__version__), f"unexpected version shape: {athf.__version__!r}"
