"""Context export command for AI-optimized context loading."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console

console = Console()

CONTEXT_EPILOG = """
\b
Examples:
  # Export context for specific hunt
  athf context --hunt H-0013

  # Export context for all credential access hunts
  athf context --tactic credential-access

  # Export context for macOS platform hunts
  athf context --platform macos

  # Combine filters: persistence hunts on Linux
  athf context --tactic persistence --platform linux

  # Export full repository context (large output)
  athf context --full

  # Export as JSON (default)
  athf context --hunt H-0013 --format json

  # Export as markdown
  athf context --hunt H-0013 --format markdown

\b
Why This Helps AI:
  • Single tool call instead of 5+ Read operations
  • Pre-filtered, relevant content only
  • Structured format (easier to parse)
  • Token optimization (strips unnecessary formatting)
  • Saves ~2,000 tokens per hunt
"""


@click.command(epilog=CONTEXT_EPILOG)
@click.option("--hunt", help="Hunt ID to export context for (e.g., H-0013)")
@click.option(
    "--tactic",
    help="MITRE tactic to filter hunts (e.g., credential-access)",
)
@click.option("--platform", help="Platform to filter hunts (e.g., macos, windows, linux)")
@click.option("--full", is_flag=True, help="Export full repository context (use sparingly)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "markdown", "yaml"]),
    default="json",
    help="Output format (default: json)",
)
@click.option("--output", type=click.Path(), help="Output file path (default: stdout)")
def context(
    hunt: Optional[str],
    tactic: Optional[str],
    platform: Optional[str],
    full: bool,
    output_format: str,
    output: Optional[str],
) -> None:
    """Export AI-optimized context bundle.

    Combines relevant files into single structured output:
    - environment.md (tech stack, data sources)
    - hunts/INDEX.md (hunt metadata index)
    - Hunt files (filtered by hunt ID, tactic, or platform)
    - Domain knowledge (if relevant)

    \b
    Use Cases:
    • AI assistants: Reduce context-loading from ~5 tool calls to 1
    • Token optimization: Pre-filtered, structured content only
    • Hunt planning: Get all relevant context in one shot
    • Query generation: Include past hunt lessons and data sources

    \b
    Token Savings:
    • Without context: ~5 Read operations, ~3,000 tokens
    • With context: 1 command, ~1,000 tokens
    • Savings: ~2,000 tokens per hunt (~$0.03 per hunt)
    """
    # Validate that at least one filter is provided
    has_filter = any([hunt, tactic, platform, full])
    if not has_filter:
        console.print("[red]Error: Must specify at least one of: --hunt, --tactic, --platform, or --full[/red]")
        console.print("\n[dim]Examples:[/dim]")
        console.print("  athf context --hunt H-0013")
        console.print("  athf context --tactic credential-access")
        console.print("  athf context --platform macos")
        console.print("  athf context --tactic persistence --platform linux")
        raise click.Abort()

    # --full flag is mutually exclusive with other filters
    if full and (hunt or tactic or platform):
        console.print("[red]Error: --full cannot be combined with other filters[/red]")
        raise click.Abort()

    # Build context bundle
    context_data = _build_context(hunt=hunt, tactic=tactic, platform=platform, full=full)

    # Format output
    if output_format == "json":
        # Use ensure_ascii=True to force proper escaping of all special characters
        # This fixes issues with unescaped control characters and newlines
        formatted_output = json.dumps(context_data, indent=2, ensure_ascii=True)
    elif output_format == "yaml":
        formatted_output = yaml.dump(context_data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:  # markdown
        formatted_output = _format_as_markdown(context_data)

    # Write to file or stdout
    if output:
        Path(output).write_text(formatted_output, encoding="utf-8")
        console.print(f"[green]✅ Context exported to: {output}[/green]")
    else:
        # Use plain print() for JSON/YAML to avoid Rich formatting issues
        if output_format in ("json", "yaml"):
            print(formatted_output)
        else:
            console.print(formatted_output)


def _build_context(  # noqa: C901
    hunt: Optional[str] = None,
    tactic: Optional[str] = None,
    platform: Optional[str] = None,
    full: bool = False,
) -> Dict[str, Any]:
    """Build context bundle based on filters."""
    context: Dict[str, Any] = {
        "metadata": {
            "generated_by": "athf context",
            "filters": {
                "hunt": hunt,
                "tactic": tactic,
                "platform": platform,
                "full": full,
            },
        },
        "environment": None,
        "hunt_index": None,
        "hunts": [],
        "domain_knowledge": [],
    }

    # Always include environment.md
    env_path = Path("environment.md")
    if env_path.exists():
        context["environment"] = _read_and_optimize(env_path)

    # Always include hunts/INDEX.md
    index_path = Path("hunts/INDEX.md")
    if index_path.exists():
        context["hunt_index"] = _read_and_optimize(index_path)

    # Load hunts based on filters (can be combined)
    if full:
        # Full export: include all hunts
        hunt_files = list(Path("hunts").glob("H-*.md"))
    elif hunt:
        # Specific hunt: only load that one
        hunt_files = [Path(f"hunts/{hunt}.md")]
    else:
        # Combine tactic and platform filters
        if tactic and platform:
            # Both filters: find hunts matching both criteria
            tactic_hunts = set(_find_hunts_by_tactic(tactic))
            platform_hunts = set(_find_hunts_by_platform(platform))
            hunt_files = list(tactic_hunts & platform_hunts)  # Intersection
        elif tactic:
            hunt_files = _find_hunts_by_tactic(tactic)
        elif platform:
            hunt_files = _find_hunts_by_platform(platform)
        else:
            hunt_files = []

    # Load hunt content
    for hunt_file in hunt_files:
        if hunt_file.exists():
            context["hunts"].append(
                {
                    "hunt_id": hunt_file.stem,
                    "content": _read_and_optimize(hunt_file),
                }
            )

    # Load relevant domain knowledge
    if tactic or full:
        domain_files = _get_relevant_domain_files(tactic)
        for domain_file in domain_files:
            if domain_file.exists():
                context["domain_knowledge"].append(
                    {
                        "file": str(domain_file),
                        "content": _read_and_optimize(domain_file),
                    }
                )

    return context


def _read_and_optimize(file_path: Path) -> str:
    """Read file and optimize for token efficiency."""
    content = file_path.read_text(encoding="utf-8")

    # First pass: Remove all control characters except tabs and newlines
    # Control characters are U+0000 through U+001F (0-31), except tab (9), LF (10), CR (13)
    cleaned_content = "".join(char for char in content if ord(char) >= 32 or char in "\t\n\r")

    # Token optimization:
    # 1. Strip excessive whitespace (but preserve single newlines)
    lines = cleaned_content.split("\n")
    optimized_lines = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_empty:
                optimized_lines.append("")
                prev_empty = True
        else:
            optimized_lines.append(line.rstrip())
            prev_empty = False

    return "\n".join(optimized_lines)


def _find_hunts_by_tactic(tactic: str) -> List[Path]:
    """Find hunt files matching MITRE tactic."""
    hunts_dir = Path("hunts")
    matching_hunts = []

    # Normalize tactic name (e.g., "credential-access" -> "credential access")
    normalized_tactic = tactic.replace("-", " ").lower()

    for hunt_file in hunts_dir.glob("H-*.md"):
        content = hunt_file.read_text(encoding="utf-8")

        # Check YAML frontmatter for tactics field
        if content.startswith("---"):
            try:
                # Extract YAML frontmatter
                yaml_end = content.find("---", 3)
                if yaml_end > 0:
                    frontmatter = content[3:yaml_end]
                    metadata = yaml.safe_load(frontmatter)

                    if metadata and "tactics" in metadata:
                        hunt_tactics = [t.lower().replace("-", " ") for t in metadata["tactics"]]
                        if normalized_tactic in hunt_tactics:
                            matching_hunts.append(hunt_file)
            except yaml.YAMLError:
                continue

    return matching_hunts


def _find_hunts_by_platform(platform: str) -> List[Path]:
    """Find hunt files matching platform."""
    hunts_dir = Path("hunts")
    matching_hunts = []

    normalized_platform = platform.lower()

    for hunt_file in hunts_dir.glob("H-*.md"):
        content = hunt_file.read_text(encoding="utf-8")

        # Check YAML frontmatter for platform field
        if content.startswith("---"):
            try:
                yaml_end = content.find("---", 3)
                if yaml_end > 0:
                    frontmatter = content[3:yaml_end]
                    metadata = yaml.safe_load(frontmatter)

                    if metadata and "platform" in metadata:
                        hunt_platforms = [p.lower() for p in metadata["platform"]]
                        if normalized_platform in hunt_platforms:
                            matching_hunts.append(hunt_file)
            except yaml.YAMLError:
                continue

    return matching_hunts


def _get_relevant_domain_files(tactic: Optional[str] = None) -> List[Path]:
    """Get relevant domain knowledge files based on tactic."""
    domain_files = []

    # Always include core hunting knowledge
    domain_files.append(Path("knowledge/hunting-knowledge.md"))

    # Add tactic-specific domain files
    if tactic:
        tactic_lower = tactic.lower().replace("-", " ")

        # Map tactics to domain files
        tactic_domain_map = {
            "credential access": [Path("knowledge/domains/iam-security.md")],
            "persistence": [Path("knowledge/domains/endpoint-security.md")],
            "privilege escalation": [Path("knowledge/domains/endpoint-security.md")],
            "defense evasion": [Path("knowledge/domains/endpoint-security.md")],
            "execution": [Path("knowledge/domains/endpoint-security.md")],
            "initial access": [
                Path("knowledge/domains/endpoint-security.md"),
                Path("knowledge/domains/iam-security.md"),
            ],
            "collection": [Path("knowledge/domains/insider-threat.md")],
            "exfiltration": [Path("knowledge/domains/insider-threat.md")],
            "impact": [Path("knowledge/domains/insider-threat.md")],
        }

        if tactic_lower in tactic_domain_map:
            domain_files.extend(tactic_domain_map[tactic_lower])

    return list(set(domain_files))  # Remove duplicates


def _format_as_markdown(context_data: Dict[str, Any]) -> str:
    """Format context data as markdown."""
    md = "# ATHF Context Export\n\n"

    # Metadata
    filters = context_data["metadata"]["filters"]
    active_filters = [f"{k}={v}" for k, v in filters.items() if v]
    md += f"**Filters:** {', '.join(active_filters)}\n\n"

    md += "---\n\n"

    # Environment
    if context_data.get("environment"):
        md += "## Environment\n\n"
        md += context_data["environment"]
        md += "\n\n---\n\n"

    # Hunt Index
    if context_data.get("hunt_index"):
        md += "## Hunt Index\n\n"
        md += context_data["hunt_index"]
        md += "\n\n---\n\n"

    # Hunts
    if context_data.get("hunts"):
        md += "## Hunts\n\n"
        for hunt in context_data["hunts"]:
            md += f"### {hunt['hunt_id']}\n\n"
            md += hunt["content"]
            md += "\n\n---\n\n"

    # Domain Knowledge
    if context_data.get("domain_knowledge"):
        md += "## Domain Knowledge\n\n"
        for domain in context_data["domain_knowledge"]:
            md += f"### {domain['file']}\n\n"
            md += domain["content"]
            md += "\n\n---\n\n"

    return md
