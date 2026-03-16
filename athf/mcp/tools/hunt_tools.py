"""Hunt management MCP tools."""

from typing import Optional

from athf.mcp.server import get_workspace, _json_result


def register_hunt_tools(mcp: "FastMCP") -> None:  # type: ignore[name-defined]  # noqa: F821
    """Register all hunt-related MCP tools."""

    @mcp.tool(
        name="athf_hunt_list",
        description=(
            "List threat hunts with optional filters. "
            "Returns hunt metadata including ID, title, status, technique, tactic, and platform."
        ),
    )
    def hunt_list(
        status: Optional[str] = None,
        tactic: Optional[str] = None,
        technique: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> str:
        from athf.core.hunt_manager import HuntManager

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        hunts = manager.list_hunts(status=status, tactic=tactic, technique=technique, platform=platform)
        return _json_result({"count": len(hunts), "hunts": hunts})

    @mcp.tool(
        name="athf_hunt_search",
        description="Full-text search across all hunt files. Returns matching hunts with relevance context.",
    )
    def hunt_search(query: str) -> str:
        from athf.core.hunt_manager import HuntManager

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        results = manager.search_hunts(query)
        return _json_result({"count": len(results), "results": results})

    @mcp.tool(
        name="athf_hunt_get",
        description="Get full details of a specific hunt by ID (e.g., H-0001). Returns frontmatter, content, and LOCK sections.",
    )
    def hunt_get(hunt_id: str) -> str:
        from athf.core.hunt_manager import HuntManager

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        hunt = manager.get_hunt(hunt_id)
        if hunt is None:
            return _json_result({"error": f"Hunt not found: {hunt_id}"})
        return _json_result(hunt)

    @mcp.tool(
        name="athf_hunt_stats",
        description="Get hunt statistics: total hunts, status breakdown, true/false positive counts, and success rate.",
    )
    def hunt_stats() -> str:
        from athf.core.hunt_manager import HuntManager

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        stats = manager.calculate_stats()
        return _json_result(stats)

    @mcp.tool(
        name="athf_hunt_coverage",
        description=(
            "Analyze MITRE ATT&CK coverage across all hunts. "
            "Optionally filter by tactic (e.g., 'credential-access'). "
            "Returns covered techniques, gaps, and coverage percentage."
        ),
    )
    def hunt_coverage(tactic: Optional[str] = None) -> str:
        from athf.core.hunt_manager import HuntManager

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        coverage = manager.calculate_attack_coverage()

        if tactic:
            tactic_lower = tactic.lower().replace(" ", "-")
            tactic_data = coverage.get("by_tactic", {}).get(tactic_lower)
            if tactic_data is None:
                return _json_result({"error": f"Unknown tactic: {tactic}"})
            return _json_result({"tactic": tactic_lower, **tactic_data})

        return _json_result(coverage)

    @mcp.tool(
        name="athf_hunt_validate",
        description="Validate a hunt file's structure and YAML frontmatter. Returns validation errors if any.",
    )
    def hunt_validate(hunt_id: str) -> str:
        from athf.core.hunt_parser import validate_hunt_file

        workspace = get_workspace()
        from athf.core.hunt_manager import HuntManager

        manager = HuntManager(hunts_dir=workspace / "hunts")
        hunt_file = manager.find_hunt_file(hunt_id)
        if hunt_file is None:
            return _json_result({"valid": False, "error": f"Hunt not found: {hunt_id}"})

        is_valid, errors = validate_hunt_file(hunt_file)
        return _json_result({"valid": is_valid, "hunt_id": hunt_id, "errors": errors})

    @mcp.tool(
        name="athf_hunt_new",
        description=(
            "Create a new hunt file with LOCK structure. "
            "Requires at minimum a title and MITRE technique ID (e.g., T1003.001). "
            "Returns the created hunt ID and file path."
        ),
    )
    def hunt_new(
        title: str,
        technique: str,
        tactic: Optional[str] = None,
        platform: Optional[str] = None,
        data_source: Optional[str] = None,
        hypothesis: Optional[str] = None,
        threat_context: Optional[str] = None,
        actor: Optional[str] = None,
        behavior: Optional[str] = None,
        location: Optional[str] = None,
        evidence: Optional[str] = None,
        hunter: str = "AI Assistant",
        research_id: Optional[str] = None,
    ) -> str:
        from athf.core.hunt_manager import HuntManager
        from athf.core.template_engine import render_hunt_template

        workspace = get_workspace()
        manager = HuntManager(hunts_dir=workspace / "hunts")
        hunt_id = manager.get_next_hunt_id()

        tactics_list = [tactic] if tactic else None
        platform_list = [platform] if platform else None
        data_source_list = [data_source] if data_source else None

        content = render_hunt_template(
            hunt_id=hunt_id,
            title=title,
            technique=technique,
            tactics=tactics_list,
            platform=platform_list,
            data_sources=data_source_list,
            hypothesis=hypothesis,
            threat_context=threat_context,
            actor=actor,
            behavior=behavior,
            location=location,
            evidence=evidence,
            hunter=hunter,
            spawned_from=research_id,
        )

        from datetime import datetime

        now = datetime.now()
        quarter = f"Q{(now.month - 1) // 3 + 1}"
        hunt_dir = workspace / "hunts" / "production" / str(now.year) / quarter
        hunt_dir.mkdir(parents=True, exist_ok=True)
        hunt_file = hunt_dir / f"{hunt_id}.md"

        # Atomic exclusive create to prevent TOCTOU race
        try:
            with open(str(hunt_file), "x", encoding="utf-8") as fh:
                fh.write(content)
        except FileExistsError:
            return _json_result({"error": f"Hunt file already exists: {hunt_file}"})

        return _json_result({
            "hunt_id": hunt_id,
            "file_path": str(hunt_file),
            "title": title,
            "technique": technique,
        })
