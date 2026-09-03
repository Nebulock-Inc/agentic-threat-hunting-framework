"""Tests for packaging declarations that CI alone would not catch until release time."""

import pathlib
import re

import athf

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _minor(version):
    """Return the 3.x minor number from a '3.x' string, or None if it isn't one."""
    match = re.fullmatch(r"3\.(\d+)", version.strip())
    return int(match.group(1)) if match else None


def _project_table():
    """Return the text of pyproject.toml's [project] table.

    A regex slice rather than tomllib: these callers assert against the literal
    text so a change in quote style or key placement stays visible, and a targeted
    text check is simpler than parsing the file to inspect a handful of lines.
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
        # Both quote styles: TOML accepts 'x' as readily as "x", and a single-quoted
        # literal would reintroduce the second version source this test exists to prevent.
        assert not re.search(r"^version\s*=\s*['\"]", _project_table(), re.MULTILINE), (
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


class TestPythonSupportFloorIsConsistent:
    """The declared Python floor must agree across metadata, classifiers, and CI.

    #47 shipped because requires-python claimed >=3.8 while the classifiers, the
    attack extra's transitive floor, and the test-extras matrix had already moved
    on. Each surface was internally valid, so nothing failed until an install on a
    real old interpreter. These assertions pin every surface to one floor offline.
    """

    def test_requires_python_declares_a_lower_bound(self):
        match = re.search(r'^requires-python\s*=\s*"([^"]+)"', _project_table(), re.MULTILINE)
        assert match, "pyproject.toml [project] must declare requires-python"
        floor = re.search(r">=\s*3\.(\d+)", match.group(1))
        assert floor, f"requires-python must set a >=3.x lower bound, got {match.group(1)!r}"

    def _requires_python_floor(self):
        match = re.search(r">=\s*3\.(\d+)", _project_table())
        return int(match.group(1))

    def _classifier_minors(self):
        return sorted(int(m) for m in re.findall(r'"Programming Language :: Python :: 3\.(\d+)"', _project_table()))

    def test_floor_matches_lowest_classifier(self):
        classifiers = self._classifier_minors()
        assert classifiers, "pyproject.toml must list Programming Language :: Python :: 3.x classifiers"
        assert self._requires_python_floor() == classifiers[0], (
            f"requires-python floor 3.{self._requires_python_floor()} must equal the lowest "
            f"Python classifier 3.{classifiers[0]}; a mismatch is exactly the #47 bug"
        )

    def _matrix_minors(self, workflow):
        text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
        found = set()
        for block in re.findall(r"python-version:\s*\[([^\]]+)\]", text):
            found.update(m for m in (_minor(v.strip(" '\"")) for v in block.split(",")) if m is not None)
        for single in re.findall(r"python-version:\s*['\"]?(3\.\d+)['\"]?\s*$", text, re.MULTILINE):
            m = _minor(single)
            if m is not None:
                found.add(m)
        return sorted(found)

    def test_floor_matches_ci_matrix_minimums(self):
        floor = self._requires_python_floor()
        for workflow in ("tests.yml", "publish.yml"):
            minors = self._matrix_minors(workflow)
            assert minors, f"{workflow} must pin at least one python-version"
            assert min(minors) == floor, (
                f"{workflow} tests 3.{min(minors)} as its lowest Python but requires-python "
                f"floor is 3.{floor}; CI must exercise the declared floor"
            )
