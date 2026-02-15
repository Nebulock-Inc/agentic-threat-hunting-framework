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
@click.option("--sessions", is_flag=True, default=False, help="Include session logs as separate results")
def similar(
    query: Optional[str],
    hunt: Optional[str],
    limit: int,
    output_format: str,
    threshold: float,
    sessions: bool,
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
    results = _find_similar_hunts(query_text, limit=limit, threshold=threshold, exclude_hunt=hunt, include_sessions=sessions)

    # Format and display results
    if output_format == "json":
        output = json.dumps(results, indent=2)
        console.print(output)
    elif output_format == "yaml":
        output = yaml.dump(results, default_flow_style=False, sort_keys=False)
        console.print(output)
    else:  # table
        _display_results_table(results, query_text=query_text, reference_hunt=hunt, include_sessions=sessions)


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
    include_sessions: bool = False,
) -> List[Dict[str, Any]]:
    """Find similar hunts using TF-IDF similarity.

    Sessions are always folded into their parent hunt's searchable text
    at 0.75x weight. When include_sessions=True, sessions are also added
    as separate documents in the corpus.
    """
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
        return []

    sessions_dir = Path("sessions")

    # Extract hunt content and metadata, fold sessions in
    hunt_data = []
    session_data = []
    for hunt_file in hunt_files:
        hunt_id = hunt_file.stem

        if exclude_hunt and hunt_id == exclude_hunt:
            continue

        content = hunt_file.read_text(encoding="utf-8")
        metadata = _extract_hunt_metadata(content)
        searchable_text = _extract_searchable_text(content, metadata)

        # Load sessions for this hunt
        hunt_sessions = _load_session_data(sessions_dir, hunt_id)

        # Fold session text into hunt (0.75x weight)
        if hunt_sessions:
            session_texts = " ".join(s["searchable_text"] for s in hunt_sessions)
            # 0.75x weight: add 75% of the text
            truncated = session_texts[: int(len(session_texts) * 0.75)]
            searchable_text = f"{searchable_text} {truncated}"

        hunt_data.append({
            "hunt_id": hunt_id,
            "searchable_text": searchable_text,
            "metadata": metadata,
            "source": "hunt",
            "session_count": len(hunt_sessions),
        })

        # If --sessions, also add sessions as separate documents
        if include_sessions:
            for sess in hunt_sessions:
                session_data.append(sess)

    if not hunt_data:
        return []

    # Build document list: query + hunts + (optionally) sessions
    all_docs = hunt_data + session_data
    documents = [query_text] + [d["searchable_text"] for d in all_docs]

    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words="english",
        ngram_range=(1, 2),
    )

    tfidf_matrix = vectorizer.fit_transform(documents)

    query_vector = tfidf_matrix[0:1]
    doc_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(query_vector, doc_vectors)[0]

    # Build results
    results = []
    for i, doc_info in enumerate(all_docs):
        score = float(similarities[i])
        if score < threshold:
            continue

        if "session_id" not in doc_info:
            # Hunt result
            metadata = doc_info["metadata"]
            results.append({
                "source": "hunt",
                "hunt_id": doc_info["hunt_id"],
                "similarity_score": round(score, 4),
                "title": metadata.get("title", "Unknown"),
                "status": metadata.get("status", "unknown"),
                "tactics": metadata.get("tactics", []),
                "techniques": metadata.get("techniques", []),
                "platform": metadata.get("platform", []),
                "session_count": doc_info.get("session_count", 0),
            })
        else:
            # Session result
            sess_meta = doc_info.get("metadata", {})
            # Auto-generate title from first 60 chars of decision text
            title = doc_info["searchable_text"][:60]
            if len(doc_info["searchable_text"]) > 60:
                title = title.rsplit(" ", 1)[0] + "..."

            results.append({
                "source": "session",
                "session_id": doc_info["session_id"],
                "hunt_id": doc_info["hunt_id"],
                "similarity_score": round(score, 4),
                "title": title,
                "decision_count": len(sess_meta.get("decisions", [])) if isinstance(sess_meta.get("decisions"), list) else 0,
                "query_count": sess_meta.get("query_count", 0),
            })

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


def _extract_session_text(session_dir: Path) -> str:
    """Extract searchable text from a session's decisions and summary.

    Reads decisions.yaml (decision + rationale fields) and summary.md
    (Key Decisions + Lessons sections). Skips queries.yaml (SQL noise)
    and session.yaml (metadata only).
    """
    if not session_dir.exists():
        return ""

    parts = []

    # Extract from decisions.yaml
    decisions_file = session_dir / "decisions.yaml"
    if decisions_file.exists():
        try:
            data = yaml.safe_load(decisions_file.read_text(encoding="utf-8"))
            if data and isinstance(data.get("decisions"), list):
                for decision in data["decisions"]:
                    if isinstance(decision, dict):
                        text = decision.get("decision", "")
                        if text:
                            parts.append(str(text))
                        rationale = decision.get("rationale", "")
                        if rationale:
                            parts.append(str(rationale))
        except (yaml.YAMLError, OSError):
            pass

    # Extract from summary.md (Key Decisions + Lessons sections)
    summary_file = session_dir / "summary.md"
    if summary_file.exists():
        try:
            content = summary_file.read_text(encoding="utf-8")
            for heading in ["## Key Decisions", "## Lessons"]:
                section = _extract_section(content, heading)
                if section:
                    parts.append(section)
        except OSError:
            pass

    return " ".join(parts).strip()


def _load_session_data(sessions_dir: Path, hunt_id: str) -> List[Dict[str, Any]]:
    """Load session data for a given hunt ID.

    Returns list of dicts with session_id, hunt_id, searchable_text,
    and metadata from session.yaml.
    """
    if not sessions_dir.exists():
        return []

    sessions = []
    for session_dir in sorted(sessions_dir.glob(f"{hunt_id}-*")):
        if not session_dir.is_dir():
            continue

        session_id = session_dir.name
        searchable_text = _extract_session_text(session_dir)
        if not searchable_text:
            continue

        # Load session metadata
        metadata: Dict[str, Any] = {}
        session_yaml = session_dir / "session.yaml"
        if session_yaml.exists():
            try:
                metadata = yaml.safe_load(session_yaml.read_text(encoding="utf-8")) or {}
            except (yaml.YAMLError, OSError):
                pass

        sessions.append({
            "session_id": session_id,
            "hunt_id": hunt_id,
            "searchable_text": searchable_text,
            "metadata": metadata,
        })

    return sessions


def _display_results_table(
    results: List[Dict[str, Any]],
    query_text: str,
    reference_hunt: Optional[str] = None,
    include_sessions: bool = False,
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

    # Count sources
    hunt_count = sum(1 for r in results if r.get("source") == "hunt")
    session_count = sum(1 for r in results if r.get("source") == "session")
    if include_sessions and session_count > 0:
        console.print(f"[dim]Found {hunt_count} hunts and {session_count} sessions[/dim]\n")
    else:
        console.print(f"[dim]Found {len(results)} similar hunts[/dim]\n")

    # Table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Score", style="green", no_wrap=True, width=6)
    if include_sessions:
        table.add_column("Source", style="magenta", no_wrap=True, width=8)
    table.add_column("ID", style="cyan", no_wrap=True, width=22 if include_sessions else 10)
    table.add_column("Title", style="white")
    table.add_column("Status", style="yellow", no_wrap=True, width=12)
    table.add_column("Tactics", style="dim", width=20)

    for result in results:
        score = result["similarity_score"]
        source = result.get("source", "hunt")

        if source == "session":
            result_id = result.get("session_id", "")
            title = result.get("title", "")
            status_display = "[dim]\u2014[/dim]"
            tactics_str = "[dim]\u2014[/dim]"
        else:
            result_id = result.get("hunt_id", "")
            title = result.get("title", "Unknown")
            status = result.get("status", "unknown")
            status_map = {"completed": "\u2705", "in-progress": "\U0001f504", "planning": "\U0001f4cb"}
            status_emoji = status_map.get(status, "\u2753")
            status_display = f"{status_emoji} {status}"
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

        if include_sessions:
            source_str = f"[magenta]{source}[/magenta]" if source == "session" else source
            table.add_row(score_str, source_str, result_id, title, status_display, tactics_str)
        else:
            table.add_row(score_str, result_id, title, status_display, tactics_str)

    console.print(table)

    # Legend
    console.print("\n[dim]Similarity Score Legend:[/dim]")
    console.print(
        "[dim]  \u22650.50 = Very similar  |  0.30-0.49 = Similar  |  0.15-0.29 = Somewhat similar  |  <0.15 = Low similarity[/dim]\n"
    )
