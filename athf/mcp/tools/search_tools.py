"""Search and context MCP tools (similar, context)."""

import logging
from typing import Any, Dict, Optional

from athf.mcp.server import get_workspace, _json_result

logger = logging.getLogger(__name__)


def register_search_tools(mcp: "FastMCP") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Register search-related MCP tools."""

    @mcp.tool(
        name="athf_similar",
        description=(
            "Find hunts semantically similar to a query or to an existing hunt. "
            "Uses TF-IDF + cosine similarity. Scores: >=0.50 very similar, "
            "0.30-0.49 related, <0.30 weak match. "
            "IMPORTANT: Use this before creating new hunts to avoid duplicates."
        ),
    )
    def similar(
        query: Optional[str] = None,
        hunt_id: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.1,
    ) -> str:
        if not query and not hunt_id:
            return _json_result({"error": "Provide either 'query' text or 'hunt_id' to search."})

        workspace = get_workspace()
        from athf.core.hunt_manager import HuntManager

        manager = HuntManager(hunts_dir=workspace / "hunts")
        hunt_files = manager.find_all_hunt_files()

        if not hunt_files:
            return _json_result({"count": 0, "results": [], "message": "No hunts found in workspace."})

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            return _json_result({"error": "scikit-learn is required for similarity search. Install with: pip install 'athf[similarity]'"})

        # Build corpus
        from athf.core.hunt_parser import parse_hunt_file

        corpus_texts = []
        corpus_hunts = []
        for f in hunt_files:
            try:
                parsed = parse_hunt_file(f)
                fm = parsed.get("frontmatter", {})
                text_parts = [
                    fm.get("title", ""),
                    fm.get("technique", ""),
                    " ".join(fm.get("tactics", []) if isinstance(fm.get("tactics"), list) else [str(fm.get("tactics", ""))]),
                    parsed.get("content", ""),
                ]
                corpus_texts.append(" ".join(str(p) for p in text_parts))
                corpus_hunts.append({
                    "hunt_id": fm.get("hunt_id", f.stem),
                    "title": fm.get("title", ""),
                    "technique": fm.get("technique", ""),
                    "status": fm.get("status", ""),
                })
            except Exception as e:
                logger.debug("Skipping %s: %s", f.name, e)
                continue

        if not corpus_texts:
            return _json_result({"count": 0, "results": []})

        # Build query text
        if hunt_id:
            hunt = manager.get_hunt(hunt_id)
            if hunt is None:
                return _json_result({"error": f"Hunt not found: {hunt_id}"})
            fm = hunt.get("frontmatter", {})
            query_text = " ".join([fm.get("title", ""), fm.get("technique", ""), hunt.get("content", "")])
        else:
            query_text = query or ""

        # TF-IDF similarity
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(corpus_texts + [query_text])
        query_vec = tfidf_matrix[-1]
        corpus_matrix = tfidf_matrix[:-1]
        similarities = cosine_similarity(query_vec, corpus_matrix).flatten()

        # Rank and filter
        results = []
        for idx, score in enumerate(similarities):
            if score >= threshold:
                entry = corpus_hunts[idx].copy()
                entry["similarity_score"] = round(float(score), 4)
                results.append(entry)

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        results = results[:limit]

        return _json_result({"count": len(results), "results": results})

    @mcp.tool(
        name="athf_context",
        description=(
            "Load AI-optimized context bundle for a hunt, tactic, or platform. "
            "Combines environment.md, past hunts, and domain knowledge into one structured output. "
            "Use this before generating queries or hypotheses to reduce context-loading overhead."
        ),
    )
    def context(
        hunt_id: Optional[str] = None,
        tactic: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> str:
        if not hunt_id and not tactic and not platform:
            return _json_result({"error": "Provide at least one filter: hunt_id, tactic, or platform."})

        workspace = get_workspace()
        result: Dict[str, Any] = {}

        # Load environment.md
        env_file = workspace / "environment.md"
        if env_file.exists():
            result["environment"] = env_file.read_text(encoding="utf-8")

        # Load hunts matching filters
        from athf.core.hunt_manager import HuntManager

        manager = HuntManager(hunts_dir=workspace / "hunts")

        if hunt_id:
            hunt = manager.get_hunt(hunt_id)
            if hunt:
                result["hunt"] = hunt
            else:
                result["hunt_error"] = f"Hunt not found: {hunt_id}"
        else:
            hunts = manager.list_hunts(tactic=tactic, platform=platform)
            result["hunts"] = hunts
            result["hunt_count"] = len(hunts)

        # Load domain knowledge if tactic specified
        if tactic:
            knowledge_dir = workspace / "knowledge" / "domains"
            if knowledge_dir.is_dir():
                for f in knowledge_dir.glob("*.md"):
                    if tactic.replace("-", " ") in f.stem.replace("-", " "):
                        result.setdefault("domain_knowledge", {})[f.stem] = f.read_text(encoding="utf-8")

        return _json_result(result)
