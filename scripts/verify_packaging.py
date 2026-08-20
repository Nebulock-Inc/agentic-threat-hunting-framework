#!/usr/bin/env python3
"""Verify that a built distribution actually ships and imports every source subpackage.

Runs three checks against the artifacts in a dist/ directory:

1. The wheel's subpackages match the source tree exactly -- nothing missing, and nothing
   shipped that the source tree no longer contains.
2. Every one of those subpackages imports from the *installed* wheel, asserted via
   ``__file__``, with the interpreter's working directory outside this checkout.
3. The sdist is held to the same parity requirement as the wheel.

Check 2 needs the ``__file__`` assertion and the foreign working directory together.
A bare ``import athf.metrics`` run from the repo root resolves against the source tree
because the working directory leads ``sys.path``, so it succeeds even when the wheel
ships nothing at all. That is how the original version of this check passed for four
releases while ``athf.metrics`` was missing from every published artifact.

Used by both .github/workflows/tests.yml and .github/workflows/publish.yml so the
artifact that ships to PyPI is held to the same bar as the artifact reviewed on a PR.
"""

import argparse
import glob
import os
import pathlib
import subprocess  # nosec B404
import sys
import tarfile
import tempfile
import zipfile

PACKAGE_ROOT = "athf"


def source_subpackages(repo_root):
    """Return dotted names of every package in the source tree, e.g. ``athf.metrics``."""
    root = repo_root / PACKAGE_ROOT
    if not root.is_dir():
        sys.exit(f"No {PACKAGE_ROOT}/ directory under {repo_root}; wrong working directory?")
    return {".".join(path.parent.relative_to(repo_root).parts) for path in root.rglob("__init__.py")}


def wheel_subpackages(wheel):
    return {".".join(name.split("/")[:-1]) for name in zipfile.ZipFile(wheel).namelist() if name.endswith("__init__.py")}


def sdist_subpackages(sdist):
    """Dotted names inside an sdist, whose members are prefixed with ``<name>-<version>/``."""
    names = set()
    with tarfile.open(sdist) as archive:
        for member in archive.getnames():
            if not member.endswith("__init__.py"):
                continue
            parts = member.split("/")[1:-1]
            if parts and parts[0] == PACKAGE_ROOT:
                names.add(".".join(parts))
    return names


def only(pattern, dist_dir, label):
    matches = sorted(glob.glob(str(dist_dir / pattern)))
    if not matches:
        sys.exit(f"No {label} found matching {dist_dir / pattern}")
    if len(matches) > 1:
        sys.exit(f"Expected exactly one {label} in {dist_dir}, found {len(matches)}: {matches}")
    return matches[0]


def report_parity(expected, actual, artifact, label):
    """Require the artifact's subpackages to match the source tree exactly, both directions.

    Checking only for absences would pass an artifact that still carries a package deleted
    from the source tree -- a stale build directory is enough to produce one, and the
    resulting archive ships code that no longer exists anywhere in the repo.
    """
    name = pathlib.Path(artifact).name
    ok = True
    for difference, phrasing in (
        (expected - actual, "in source but absent from"),
        (actual - expected, "shipped in but absent from the source tree of"),
    ):
        if difference:
            print(f"FAIL: subpackages {phrasing} {label} {name}:")
            for dotted in sorted(difference):
                print(f"  - {dotted}")
            ok = False
    if ok:
        print(f"OK: the {label} carries exactly the {len(expected)} subpackages in the source tree.")
    return ok


def check_imports_from_wheel(wheel, expected):
    """Install the wheel to a throwaway prefix and prove each module loads from it.

    ``pip install --target`` rather than a venv: venv creation runs ``ensurepip``, which
    is unavailable or broken on some managed interpreters, and the isolation a venv would
    add is unnecessary here because the ``__file__`` assertion is what proves provenance.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp).resolve()
        target = tmp / "installed"
        # A foreign working directory, so a source tree cannot satisfy the imports.
        run_dir = tmp / "elsewhere"
        run_dir.mkdir()

        # Fixed argv, no shell; every path is derived locally, none from user input.
        subprocess.run(  # nosec B603
            [sys.executable, "-m", "pip", "install", "--quiet", "--target", str(target), str(wheel)],
            check=True,
        )

        probe = """
import importlib, pathlib, sys

root = pathlib.Path(sys.argv[1]).resolve()
names = sys.argv[2:]
for name in names:
    module = importlib.import_module(name)
    location = pathlib.Path(module.__file__).resolve()
    if root not in location.parents:
        sys.exit("%s imported from %s, not the installed wheel" % (name, location))
print("OK: all %d subpackages import from the installed wheel." % len(names))
"""
        env = dict(os.environ, PYTHONPATH=str(target))
        # Keep the source tree out of reach even if the caller exported it.
        env.pop("PYTHONHOME", None)
        # Fixed argv, no shell; the module names come from the source tree, not user input.
        result = subprocess.run(  # nosec B603
            [sys.executable, "-c", probe, str(target), *sorted(expected)],
            cwd=str(run_dir),
            env=env,
        )
        return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", default="dist", help="directory holding the built artifacts")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="checkout whose source tree defines the expected set of subpackages",
    )
    parser.add_argument(
        "--skip-import-check",
        action="store_true",
        help="run only the archive-content checks (no venv creation)",
    )
    args = parser.parse_args()

    repo_root = pathlib.Path(args.repo_root).resolve()
    dist_dir = pathlib.Path(args.dist_dir).resolve()

    expected = source_subpackages(repo_root)
    print(f"Source tree declares {len(expected)} subpackages under {PACKAGE_ROOT}/.")

    wheel = only("*.whl", dist_dir, "wheel")
    sdist = only("*.tar.gz", dist_dir, "sdist")

    ok = report_parity(expected, wheel_subpackages(wheel), wheel, "wheel")
    ok = report_parity(expected, sdist_subpackages(sdist), sdist, "sdist") and ok

    if args.skip_import_check:
        print("Skipping clean-environment import check (--skip-import-check).")
    elif ok:
        ok = check_imports_from_wheel(wheel, expected)
    else:
        print("Skipping import check: the archive already failed, fix that first.")

    if not ok:
        sys.exit(1)
    print("Packaging verification passed.")


if __name__ == "__main__":
    main()
