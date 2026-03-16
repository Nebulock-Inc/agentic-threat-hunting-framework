"""ATT&CK data management commands."""

import time
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from athf.core.attack_matrix import TechniqueInfo

console = Console()


@click.group()
def attack() -> None:
    """Manage MITRE ATT&CK data.

    \b
    Commands for downloading, inspecting, and querying ATT&CK
    technique data via the STIX framework.

    \b
    Quick Start:
      athf attack update       Download/refresh STIX data
      athf attack status       Show provider info and cache age
      athf attack lookup T1003 Look up technique metadata
    """


@attack.command()
@click.option("--force", is_flag=True, help="Re-download even if cache exists")
def update(force: bool) -> None:
    """Download or refresh ATT&CK STIX data.

    Downloads the Enterprise ATT&CK STIX bundle from the official
    MITRE repository and caches it locally.

    \b
    Examples:
      athf attack update
      athf attack update --force
    """
    try:
        from mitreattack.stix20 import MitreAttackData
    except ImportError:
        console.print("[red]Error: mitreattack-python is not installed.[/red]")
        console.print("[dim]Install it with: pip install 'athf[attack]'[/dim]")
        raise click.Abort()

    from athf.core.attack_matrix import _get_stix_file_path, reset_provider

    stix_path = _get_stix_file_path()

    if stix_path.exists() and not force:
        age_days = int((time.time() - stix_path.stat().st_mtime) / 86400)
        console.print(f"[yellow]STIX data already exists (age: {age_days}d).[/yellow]")
        console.print("[dim]Use --force to re-download.[/dim]")
        return

    # Ensure cache directory exists
    stix_path.parent.mkdir(parents=True, exist_ok=True)

    console.print("[cyan]Downloading ATT&CK Enterprise STIX data...[/cyan]")
    console.print(f"[dim]Cache location: {stix_path}[/dim]")

    try:
        MitreAttackData.stix_store_to_file(
            "enterprise-attack",
            str(stix_path),
        )
        # Reset provider so it picks up the new data
        reset_provider()
        console.print("[green]ATT&CK STIX data downloaded successfully.[/green]")

        # Show summary
        from athf.core.attack_matrix import get_attack_version, is_using_stix

        if is_using_stix():
            console.print(f"[dim]Version: {get_attack_version()}[/dim]")
    except Exception as e:
        console.print(f"[red]Error downloading STIX data: {e}[/red]")
        raise click.Abort()


@attack.command()
def status() -> None:
    """Show ATT&CK data provider status.

    Displays the active provider type, ATT&CK version,
    technique counts, and cache file details.

    \b
    Example:
      athf attack status
    """
    from athf.core.attack_matrix import (
        _get_stix_file_path,
        get_attack_version,
        get_sorted_tactics,
        is_using_stix,
    )

    console.print("\n[bold]ATT&CK Data Status[/bold]\n")

    provider_type = "STIX (mitreattack-python)" if is_using_stix() else "Fallback (hardcoded v14)"
    console.print(f"  [cyan]Provider:[/cyan]  {provider_type}")
    console.print(f"  [cyan]Version:[/cyan]   {get_attack_version()}")
    console.print(f"  [cyan]Tactics:[/cyan]   {len(get_sorted_tactics())}")

    # Show cache info
    stix_path = _get_stix_file_path()
    if stix_path.exists():
        size_mb = stix_path.stat().st_size / (1024 * 1024)
        age_days = int((time.time() - stix_path.stat().st_mtime) / 86400)
        console.print(f"  [cyan]Cache:[/cyan]     {stix_path}")
        console.print(f"  [cyan]Size:[/cyan]      {size_mb:.1f} MB")
        console.print(f"  [cyan]Age:[/cyan]       {age_days} days")
    else:
        console.print(f"  [cyan]Cache:[/cyan]     Not found ({stix_path})")
        console.print("[dim]  Run 'athf attack update' to download STIX data.[/dim]")

    # Check if mitreattack-python is installed
    try:
        import mitreattack  # noqa: F401
        console.print("  [cyan]Library:[/cyan]   mitreattack-python installed")
    except ImportError:
        console.print("  [cyan]Library:[/cyan]   [yellow]mitreattack-python not installed[/yellow]")
        console.print("[dim]  Install with: pip install 'athf[attack]'[/dim]")

    console.print()


def _display_technique_fields(tech: "TechniqueInfo") -> None:
    """Print technique metadata fields to the console."""
    if tech.get("url"):
        console.print(f"  [cyan]URL:[/cyan]           {tech['url']}")
    if tech.get("platforms"):
        console.print(f"  [cyan]Platforms:[/cyan]     {', '.join(tech['platforms'])}")
    if tech.get("tactic_shortnames"):
        console.print(f"  [cyan]Tactics:[/cyan]       {', '.join(tech['tactic_shortnames'])}")
    if tech.get("data_sources"):
        console.print(f"  [cyan]Data Sources:[/cyan]  {', '.join(tech['data_sources'][:5])}")
        if len(tech.get("data_sources", [])) > 5:
            console.print(f"                 [dim]... and {len(tech['data_sources']) - 5} more[/dim]")
    is_sub = tech.get("is_subtechnique", False)
    console.print(f"  [cyan]Type:[/cyan]          {'Sub-technique' if is_sub else 'Technique'}")
    if is_sub and tech.get("parent_id"):
        console.print(f"  [cyan]Parent:[/cyan]        {tech['parent_id']}")
    if tech.get("description"):
        desc = tech["description"]
        if len(desc) > 300:
            desc = desc[:300] + "..."
        console.print(f"\n  [dim]{desc}[/dim]")


@attack.command()
@click.argument("technique_id")
def lookup(technique_id: str) -> None:
    """Look up an ATT&CK technique by ID.

    Shows technique metadata including name, platforms,
    data sources, tactics, and sub-techniques.

    \b
    Examples:
      athf attack lookup T1003
      athf attack lookup T1003.001
    """
    from athf.core.attack_matrix import get_sub_techniques, get_technique, is_using_stix

    if not is_using_stix():
        console.print("[yellow]STIX data not available. Technique lookup requires STIX.[/yellow]")
        console.print("[dim]Install and update: pip install 'athf[attack]' && athf attack update[/dim]")
        return

    tech = get_technique(technique_id)
    if tech is None:
        console.print(f"[yellow]Technique {technique_id} not found.[/yellow]")
        return

    console.print(f"\n[bold]{tech.get('id', '')} - {tech.get('name', '')}[/bold]\n")
    _display_technique_fields(tech)

    # Show sub-techniques if this is a parent
    if not tech.get("is_subtechnique", False):
        subs = get_sub_techniques(technique_id)
        if subs:
            console.print(f"\n  [bold]Sub-techniques ({len(subs)}):[/bold]")
            for sub in subs:
                console.print(f"    {sub.get('id', '')} - {sub.get('name', '')}")

    console.print()


@attack.command()
@click.argument("tactic_key")
def techniques(tactic_key: str) -> None:
    """List techniques for a tactic.

    Shows all techniques mapped to the specified tactic key
    (e.g., credential-access, lateral-movement).

    \b
    Examples:
      athf attack techniques credential-access
      athf attack techniques lateral-movement
    """
    from athf.core.attack_matrix import (
        get_tactic_display_name,
        get_techniques_for_tactic,
        is_using_stix,
    )

    if not is_using_stix():
        console.print("[yellow]STIX data not available. Technique listing requires STIX.[/yellow]")
        console.print("[dim]Install and update: pip install 'athf[attack]' && athf attack update[/dim]")
        return

    techs = get_techniques_for_tactic(tactic_key)
    if not techs:
        console.print(f"[yellow]No techniques found for tactic '{tactic_key}'.[/yellow]")
        console.print("[dim]Use a tactic shortname like: credential-access, lateral-movement[/dim]")
        return

    display_name = get_tactic_display_name(tactic_key)
    console.print(f"\n[bold]{display_name}[/bold] ({len(techs)} techniques)\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", style="white", width=12)
    table.add_column("Name", style="white")
    table.add_column("Sub?", style="dim", width=4)
    table.add_column("Platforms", style="dim")

    for tech in techs:
        is_sub = "Yes" if tech.get("is_subtechnique", False) else ""
        platforms = ", ".join(tech.get("platforms", [])[:3])
        if len(tech.get("platforms", [])) > 3:
            platforms += "..."
        table.add_row(
            tech.get("id", ""),
            tech.get("name", ""),
            is_sub,
            platforms,
        )

    console.print(table)
    console.print()
