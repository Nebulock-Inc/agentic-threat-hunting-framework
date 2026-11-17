"""MITRE ATLAS data management commands (attacks on AI systems)."""

import os
import re
import time
import urllib.request
from typing import Tuple

import click
import yaml
from rich.console import Console

from athf.core.atlas_matrix import (
    AtlasFormatError,
    check_format_version,
    get_atlas_file_path,
    reset_atlas_provider,
)

console = Console()

_ATLAS_DIST = "https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/"
_MANIFEST_URL = _ATLAS_DIST + "manifest.yaml"
# Only canonical release paths are fetched; a manifest can't redirect us elsewhere.
_RELEASE_PATH_RE = re.compile(r"^v6/ATLAS-\d{4}\.\d{2}\.yaml$")
_TIMEOUT_SECONDS = 60


@click.group()
def atlas() -> None:
    """Manage MITRE ATLAS data (adversarial threats to AI systems).

    \b
    ATLAS complements ATT&CK: tag AI-specific steps with atlas_techniques,
    keep conventional steps in techniques. Only tag hunts for attacks ON
    AI systems, not hunts that merely use AI.

    \b
    Quick Start:
      athf atlas update        Download/refresh ATLAS data
    """


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as resp:  # nosec B310 - fixed https host
        data: bytes = resp.read()
        return data


def _latest_release(manifest_bytes: bytes) -> Tuple[str, str]:
    """Return (release, path) for the newest v6 release in the manifest."""
    manifest = yaml.safe_load(manifest_bytes)
    if not isinstance(manifest, list):
        raise AtlasFormatError("ATLAS manifest is not a list of releases")
    candidates = []
    for entry in manifest:
        if not isinstance(entry, dict):
            continue
        for version in entry.get("versions") or []:
            if not isinstance(version, dict):
                continue
            path = str(version.get("path", ""))
            major = str(version.get("format-version", "")).split(".", 1)[0]
            if major == "6" and _RELEASE_PATH_RE.match(path):
                candidates.append((path, str(entry.get("release", ""))))
    if not candidates:
        raise AtlasFormatError("No v6 ATLAS release found in manifest")
    path, release = max(candidates)  # path embeds zero-padded YYYY.MM
    return release, path


@atlas.command()
@click.option("--force", is_flag=True, help="Re-download even if cache exists")
def update(force: bool) -> None:
    """Download or refresh MITRE ATLAS data.

    \b
    Fetches the newest v6 release listed in mitre-atlas/atlas-data's
    manifest and caches it for `athf hunt validate`.

    \b
    Examples:
      athf atlas update
      athf atlas update --force
    """
    path = get_atlas_file_path()
    if path.exists() and not force:
        age_days = int((time.time() - path.stat().st_mtime) / 86400)
        console.print(f"[yellow]ATLAS data already exists (age: {age_days}d).[/yellow]")
        console.print("[dim]Use --force to re-download.[/dim]")
        return

    console.print("[cyan]Downloading MITRE ATLAS data...[/cyan]")
    try:
        release, rel_path = _latest_release(_fetch(_MANIFEST_URL))
        body = _fetch(_ATLAS_DIST + rel_path)
        data = yaml.safe_load(body)
        check_format_version(data)
    except (OSError, yaml.YAMLError, AtlasFormatError) as exc:  # URLError and timeouts are OSError
        console.print(f"[red]Error downloading ATLAS data: {exc}[/red]")
        raise click.Abort()

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(body)
    os.replace(tmp, path)
    reset_atlas_provider()

    console.print(
        f"[green]ATLAS {release} downloaded[/green] "
        f"({len(data['techniques'])} techniques, {len(data['tactics'])} tactics)"
    )
    console.print(f"[dim]Cache location: {path}[/dim]")
