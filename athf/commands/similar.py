"""Semantic similarity search for past hunts."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

SIMILAR_EPILOG = """
\b
Examples:
  # Find hunts similar to a text query
  athf similar "password spraying via RDP"

  # Find hunts similar to specific hunt
  athf similar --hunt H-0013

  # Limit results to top 5
  athf similar "kerberos" --limit 5

  # Export as JSON
  athf similar "credential theft" --format json

\b
Why This Helps AI:
  • Semantic search (not just keyword matching)
  • Find related hunts with different terminology
  • Discover patterns across hunt history
  • Better than grep for conceptual matches
  • Identify similar hunts to avoid duplication
"""


@click.command(epilog=SIMILAR_EPILOG)
@click.argument("query", required=False)
@click.option("--hunt", help="Hunt ID to find similar hunts for (e.g., H-0013)")
@click.option("--limit", default=10, type=int, help="Maximum number of results (default: 10)")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
@click.option("--threshold", default=0.1, type=float, help="Minimum similarity score (0-1, default: 0.1)")
def similar(
    query: Optional[str],
    hunt: Optional[str],
    limit: int,
    output_format: str,
    threshold: float,
) -> None:
    """Find hunts similar to a query or hunt ID.

    Uses semantic similarity to find related hunts even when
    terminology differs. Better than keyword search for discovering
    patterns and avoiding duplicate hunts.

    \b
    Use Cases:
    • Check if similar hunt already exists
    • Find related hunts for context
    • Discover patterns across hunt history
    • Identify hunt clusters by topic

    \b
    Examples:
      # Text query
      athf similar "password spraying"

      # Similar to existing hunt
      athf similar --hunt H-0013

      # Top 5 results
      athf similar "lateral movement" --limit 5
    """
    # Validate inputs
    if not query and not hunt:
        console.print("[red]Error: Must provide either QUERY or --hunt option[/red]")
        console.print("\n[dim]Examples:[/dim]")
        console.print('  athf similar "password spraying"')
        console.print("  athf similar --hunt H-0013")
        raise click.Abort()

    if query and hunt:
        console.print("[red]Error: Cannot specify both QUERY and --hunt[/red]")
        raise click.Abort()

    # Get query text
    query_text: str
    if hunt:
        hunt_text = _get_hunt_text(hunt)
        if not hunt_text:
            console.print(f"[red]Error: Hunt {hunt} not found[/red]")
            raise click.Abort()
        query_text = hunt_text
    else:
        query_text = query or ""  # Should never be None due to validation above

    # Find similar hunts
    results = _find_similar_hunts(query_text, limit=limit, threshold=threshold, exclude_hunt=hunt)

    # Format and display results
    if output_format == "json":
        output = json.dumps(results, indent=2)
        console.print(output)
    elif output_format == "yaml":
        output = yaml.dump(results, default_flow_style=False, sort_keys=False)
        console.print(output)
    else:  # table
        _display_results_table(results, query_text=query_text, reference_hunt=hunt)


def _get_hunt_text(hunt_id: str) -> Optional[str]:
    """Get full text content of a hunt."""
    hunt_file = Path(f"hunts/{hunt_id}.md")
    if not hunt_file.exists():
        return None
    return hunt_file.read_text(encoding="utf-8")


def _find_similar_hunts(
    query_text: str,
    limit: int = 10,
    threshold: float = 0.1,
    exclude_hunt: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find similar hunts using TF-IDF similarity."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        console.print("[red]Error: scikit-learn not installed[/red]")
        console.print("[dim]Install with: pip install scikit-learn[/dim]")
        raise click.Abort()

    # Load all hunts
    hunts_dir = Path("hunts")
    hunt_files = list(hunts_dir.glob("H-*.md"))

    if not hunt_files:
        # Don't print warning - let the output format handle empty results
        return []

    # Extract hunt content and metadata
    hunt_data = []
    for hunt_file in hunt_files:
        hunt_id = hunt_file.stem

        # Skip excluded hunt
        if exclude_hunt and hunt_id == exclude_hunt:
            continue

        content = hunt_file.read_text(encoding="utf-8")
        metadata = _extract_hunt_metadata(content)

        # Extract searchable text (weighted semantic sections)
        searchable_text = _extract_searchable_text(content, metadata)

        hunt_data.append(
            {
                "hunt_id": hunt_id,
                "content": content,
                "searchable_text": searchable_text,
                "metadata": metadata,
            }
        )

    if not hunt_data:
        # Don't print warning - let the output format handle empty results
        return []

    # Build TF-IDF vectors using searchable text (weighted semantic sections)
    documents = [query_text] + [h["searchable_text"] for h in hunt_data]

    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words="english",
        ngram_range=(1, 2),  # Unigrams and bigrams
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    # Calculate similarity scores
    query_vector = tfidf_matrix[0:1]
    hunt_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(query_vector, hunt_vectors)[0]

    # Combine results with metadata
    results = []
    for i, hunt_info in enumerate(hunt_data):
        score = float(similarities[i])

        if score >= threshold:
            metadata = hunt_info["metadata"]  # type: ignore[assignment]
            results.append(
                {
                    "hunt_id": hunt_info["hunt_id"],
                    "similarity_score": round(score, 4),
                    "title": metadata.get("title", "Unknown"),
                    "status": metadata.get("status", "unknown"),
                    "tactics": metadata.get("tactics", []),
                    "techniques": metadata.get("techniques", []),
                    "platform": metadata.get("platform", []),
                }
            )

    # Sort by similarity score (descending)
    results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return results[:limit]


def _extract_hunt_metadata(content: str) -> Dict[str, Any]:
    """Extract YAML frontmatter metadata from hunt file."""
    if not content.startswith("---"):
        return {}

    try:
        yaml_end = content.find("---", 3)
        if yaml_end > 0:
            frontmatter = content[3:yaml_end]
            return yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError:
        return {}

    return {}


def _extract_searchable_text(content: str, metadata: Dict[str, Any]) -> str:  # noqa: C901
    """Extract semantically important text for similarity matching.

    Focuses on key sections and applies weighting to improve match accuracy:
    - Title (3x weight)
    - Hypothesis (2x weight)
    - ABLE framework sections (1.5x weight)
    - Tactics/Techniques (1x weight)

    Ignores: SQL queries, results, timestamps, org IDs, lessons learned
    """
    parts = []

    # Title (3x weight - most important)
    title = metadata.get("title", "")
    if title:
        parts.extend([title] * 3)

    # Tactics and techniques (1x weight)
    tactics = metadata.get("tactics", [])
    if isinstance(tactics, list):
        parts.extend(tactics)
    elif tactics:
        parts.append(str(tactics))

    techniques = metadata.get("techniques", [])
    if isinstance(techniques, list):
        parts.extend(techniques)
    elif techniques:
        parts.append(str(techniques))

    platform = metadata.get("platform", [])
    if isinstance(platform, list):
        parts.extend(platform)
    elif platform:
        parts.append(str(platform))

    # Extract hypothesis section (2x weight)
    hypothesis = _extract_section(content, "## Hypothesis")
    if hypothesis:
        parts.extend([hypothesis] * 2)

    # Extract ABLE framework sections (1.5x weight each)
    able_sections = ["Actor", "Behavior", "Location", "Evidence"]
    for section in able_sections:
        text = _extract_section(content, f"### {section}")
        if text:
            # Weight 1.5x = add once + half again
            parts.append(text)
            parts.append(text[: len(text) // 2])  # Add first half again for 1.5x weight

    return " ".join(parts)


def _extract_section(content: str, heading: str) -> str:
    """Extract text from a markdown section until the next heading."""
    lines = content.split("\n")
    section_lines = []
    in_section = False

    for line in lines:
        if line.startswith(heading):
            in_section = True
            continue

        if in_section:
            # Stop at next heading of same or higher level
            if line.startswith("#"):
                break
            section_lines.append(line)

    return " ".join(section_lines).strip()


def _display_results_table(
    results: List[Dict[str, Any]],
    query_text: str,
    reference_hunt: Optional[str] = None,
) -> None:
    """Display results in rich table format."""
    # Header (always show, even if no results)
    if reference_hunt:
        console.print(f"\n[bold]Similar to {reference_hunt}:[/bold]")
    else:
        query_preview = query_text[:60] + "..." if len(query_text) > 60 else query_text
        console.print(f"\n[bold]Similar to:[/bold] [dim]{query_preview}[/dim]")

    if not results:
        console.print("[yellow]No similar hunts found[/yellow]")
        return

    console.print(f"[dim]Found {len(results)} similar hunts[/dim]\n")

    # Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Score", style="green", no_wrap=True, width=6)
    table.add_column("Hunt ID", style="cyan", no_wrap=True, width=10)
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow", no_wrap=True, width=12)
    table.add_column("Tactics", style="dim", width=20)

    for result in results:
        score = result["similarity_score"]
        hunt_id = result["hunt_id"]
        title = result["title"]
        status = result["status"]

        # Format tactics (abbreviate if too long)
        tactics = result.get("tactics", [])
        tactics_str = ", ".join(tactics[:2])
        if len(tactics) > 2:
            tactics_str += f" +{len(tactics) - 2}"

        # Color-code score
        if score >= 0.5:
            score_str = f"[bold green]{score:.3f}[/bold green]"
        elif score >= 0.3:
            score_str = f"[green]{score:.3f}[/green]"
        elif score >= 0.15:
            score_str = f"[yellow]{score:.3f}[/yellow]"
        else:
            score_str = f"[dim]{score:.3f}[/dim]"

        # Status emoji
        status_map = {
            "completed": "✅",
            "in-progress": "🔄",
            "planning": "📋",
        }
        status_emoji = status_map.get(status, "❓")
        status_display = f"{status_emoji} {status}"

        table.add_row(score_str, hunt_id, title, status_display, tactics_str)

    console.print(table)

    # Legend
    console.print("\n[dim]Similarity Score Legend:[/dim]")
    console.print(
        "[dim]  ≥0.50 = Very similar  |  0.30-0.49 = Similar  |  0.15-0.29 = Somewhat similar  |  <0.15 = Low similarity[/dim]\n"
    )
