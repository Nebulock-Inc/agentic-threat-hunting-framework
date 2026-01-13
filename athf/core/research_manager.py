"""Manage research files and operations."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ResearchParser:
    """Parser for research files (YAML frontmatter + markdown)."""

    def __init__(self, file_path: Path) -> None:
        """Initialize parser with research file path."""
        self.file_path = Path(file_path)
        self.frontmatter: Dict[str, Any] = {}
        self.content = ""
        self.sections: Dict[str, str] = {}

    def parse(self) -> Dict[str, Any]:
        """Parse research file and return structured data.

        Returns:
            Dict containing frontmatter, content, and sections
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Research file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML frontmatter
        self.frontmatter = self._parse_frontmatter(content)

        # Extract main content (after frontmatter)
        self.content = self._extract_content(content)

        # Parse research sections
        self.sections = self._parse_sections(self.content)

        return {
            "file_path": str(self.file_path),
            "research_id": self.frontmatter.get("research_id"),
            "frontmatter": self.frontmatter,
            "content": self.content,
            "sections": self.sections,
        }

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Extract and parse YAML frontmatter."""
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            return {}

        frontmatter_text = match.group(1)

        try:
            return yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter: {e}")

    def _extract_content(self, content: str) -> str:
        """Extract content after frontmatter."""
        frontmatter_pattern = r"^---\s*\n.*?\n---\s*\n"
        content_without_fm = re.sub(frontmatter_pattern, "", content, count=1, flags=re.DOTALL)
        return content_without_fm.strip()

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse research sections from content.

        Returns:
            Dict with section names and content
        """
        sections = {}

        # Define section patterns for the 5 research skills
        section_patterns = {
            "system_research": r"##\s+1\.\s+System Research.*?(?=##\s+2\.|$)",
            "adversary_tradecraft": r"##\s+2\.\s+Adversary Tradecraft.*?(?=##\s+3\.|$)",
            "telemetry_mapping": r"##\s+3\.\s+Telemetry Mapping.*?(?=##\s+4\.|$)",
            "related_work": r"##\s+4\.\s+Related Work.*?(?=##\s+5\.|$)",
            "synthesis": r"##\s+5\.\s+Research Synthesis.*?(?=##\s+[A-Z]|$)",
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(0).strip()

        return sections


def parse_research_file(file_path: Path) -> Dict[str, Any]:
    """Convenience function to parse a research file."""
    parser = ResearchParser(file_path)
    return parser.parse()


class ResearchManager:
    """Manage research files and operations.

    Similar pattern to HuntManager but for research documents.
    Research files use R-XXXX IDs and are stored in research/ directory.
    """

    def __init__(self, research_dir: Optional[Path] = None) -> None:
        """Initialize research manager.

        Args:
            research_dir: Directory containing research files (default: ./research)
        """
        self.research_dir = Path(research_dir) if research_dir else Path.cwd() / "research"

        if not self.research_dir.exists():
            self.research_dir.mkdir(parents=True, exist_ok=True)

    def _find_all_research_files(self) -> List[Path]:
        """Find all research files (R-*.md).

        Returns:
            List of paths to research files
        """
        research_files: List[Path] = []

        # Find flat files (R-*.md)
        research_files.extend(self.research_dir.rglob("R-*.md"))

        return sorted(set(research_files))

    def get_next_research_id(self, prefix: str = "R-") -> str:
        """Calculate the next available research ID.

        Args:
            prefix: Research ID prefix (default: R-)

        Returns:
            Next research ID (e.g., R-0023)
        """
        research_files = self._find_all_research_files()

        if not research_files:
            return f"{prefix}0001"

        # Extract numbers from research IDs with matching prefix
        numbers = []
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")

        for research_file in research_files:
            try:
                research_data = parse_research_file(research_file)
                research_id = research_data.get("frontmatter", {}).get("research_id")

                if not research_id or not isinstance(research_id, str):
                    continue

                match = pattern.match(research_id)
                if match:
                    numbers.append(int(match.group(1)))
            except Exception:
                # Try to extract from filename if parsing fails
                match = pattern.match(research_file.stem)
                if match:
                    numbers.append(int(match.group(1)))

        if not numbers:
            return f"{prefix}0001"

        # Next number with zero-padding
        next_num = max(numbers) + 1
        return f"{prefix}{next_num:04d}"

    def list_research(
        self,
        status: Optional[str] = None,
        technique: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all research documents with optional filters.

        Args:
            status: Filter by status (draft, in_progress, completed)
            technique: Filter by MITRE technique
            topic: Filter by topic (substring match)

        Returns:
            List of research metadata dicts
        """
        research_list = []

        for research_file in self._find_all_research_files():
            try:
                research_data = parse_research_file(research_file)
                frontmatter = research_data.get("frontmatter", {})

                # Apply filters
                if status and frontmatter.get("status") != status:
                    continue

                if technique:
                    techniques = frontmatter.get("mitre_techniques", [])
                    if technique not in techniques:
                        continue

                if topic:
                    research_topic = frontmatter.get("topic", "").lower()
                    if topic.lower() not in research_topic:
                        continue

                # Extract summary info
                research_list.append(
                    {
                        "research_id": frontmatter.get("research_id"),
                        "topic": frontmatter.get("topic"),
                        "status": frontmatter.get("status"),
                        "created_date": frontmatter.get("created_date"),
                        "depth": frontmatter.get("depth"),
                        "mitre_techniques": frontmatter.get("mitre_techniques", []),
                        "linked_hunts": frontmatter.get("linked_hunts", []),
                        "duration_minutes": frontmatter.get("duration_minutes"),
                        "total_cost_usd": frontmatter.get("total_cost_usd"),
                        "file_path": str(research_file),
                    }
                )

            except Exception:
                # Skip files that can't be parsed
                continue

        return research_list

    def get_research(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific research document by ID.

        Args:
            research_id: Research ID (e.g., R-0001)

        Returns:
            Research data dict or None if not found
        """
        # Try direct file
        research_file = self.research_dir / f"{research_id}.md"
        if research_file.exists():
            return parse_research_file(research_file)

        # Try nested search
        research_files = list(self.research_dir.rglob(f"{research_id}.md"))
        if research_files:
            return parse_research_file(research_files[0])

        return None

    def search_research(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across research documents.

        Args:
            query: Search query string

        Returns:
            List of matching research documents
        """
        results = []
        query_lower = query.lower()

        for research_file in self._find_all_research_files():
            try:
                with open(research_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if query_lower in content.lower():
                    research_data = parse_research_file(research_file)
                    frontmatter = research_data.get("frontmatter", {})

                    results.append(
                        {
                            "research_id": frontmatter.get("research_id"),
                            "topic": frontmatter.get("topic"),
                            "status": frontmatter.get("status"),
                            "file_path": str(research_file),
                        }
                    )

            except Exception:
                continue

        return results

    def link_hunt_to_research(self, research_id: str, hunt_id: str) -> bool:
        """Link a hunt to its source research.

        Updates the research document's linked_hunts field.

        Args:
            research_id: Research ID (e.g., R-0001)
            hunt_id: Hunt ID to link (e.g., H-0001)

        Returns:
            True if successful, False otherwise
        """
        research_data = self.get_research(research_id)
        if not research_data:
            return False

        file_path = Path(research_data["file_path"])

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter
            frontmatter = research_data.get("frontmatter", {})
            linked_hunts = frontmatter.get("linked_hunts", [])

            # Add hunt if not already linked
            if hunt_id not in linked_hunts:
                linked_hunts.append(hunt_id)

                # Update the YAML frontmatter
                # Find and replace linked_hunts line
                if "linked_hunts:" in content:
                    # Replace existing linked_hunts
                    pattern = r"linked_hunts:.*?(?=\n[a-z_]+:|---)"
                    replacement = f"linked_hunts: {linked_hunts}\n"
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                else:
                    # Add linked_hunts before closing ---
                    pattern = r"\n---\s*\n"
                    replacement = f"\nlinked_hunts: {linked_hunts}\n---\n"
                    content = re.sub(pattern, replacement, content, count=1)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return True

        except Exception:
            return False

    def create_research_file(
        self,
        research_id: str,
        topic: str,
        content: str,
        frontmatter: Dict[str, Any],
    ) -> Path:
        """Create a new research file.

        Args:
            research_id: Research ID (e.g., R-0001)
            topic: Research topic
            content: Markdown content
            frontmatter: YAML frontmatter dict

        Returns:
            Path to created file
        """
        # Ensure research_id and topic are in frontmatter
        frontmatter["research_id"] = research_id
        frontmatter["topic"] = topic
        frontmatter.setdefault("created_date", datetime.now().strftime("%Y-%m-%d"))
        frontmatter.setdefault("status", "completed")

        # Build file content
        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        file_content = f"---\n{yaml_content}---\n\n{content}"

        # Write file
        file_path = self.research_dir / f"{research_id}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        return file_path

    def calculate_stats(self) -> Dict[str, Any]:
        """Calculate research program statistics.

        Returns:
            Dict with counts, costs, and other metrics
        """
        research_list = self.list_research()

        if not research_list:
            return {
                "total_research": 0,
                "completed_research": 0,
                "total_cost_usd": 0.0,
                "total_duration_minutes": 0,
                "avg_duration_minutes": 0.0,
                "by_status": {},
                "total_linked_hunts": 0,
            }

        total_research = len(research_list)
        completed_research = len([r for r in research_list if r.get("status") == "completed"])

        total_cost = sum(r.get("total_cost_usd", 0) or 0 for r in research_list)
        total_duration = sum(r.get("duration_minutes", 0) or 0 for r in research_list)
        avg_duration = total_duration / total_research if total_research > 0 else 0.0

        # Count by status
        by_status: Dict[str, int] = {}
        for research in research_list:
            status = research.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

        # Count linked hunts
        total_linked_hunts = sum(len(r.get("linked_hunts", [])) for r in research_list)

        return {
            "total_research": total_research,
            "completed_research": completed_research,
            "total_cost_usd": round(total_cost, 4),
            "total_duration_minutes": total_duration,
            "avg_duration_minutes": round(avg_duration, 1),
            "by_status": by_status,
            "total_linked_hunts": total_linked_hunts,
        }
