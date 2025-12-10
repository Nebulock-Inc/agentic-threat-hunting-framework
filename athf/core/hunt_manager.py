"""Manage hunt files and operations."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from athf.core.hunt_parser import parse_hunt_file


class HuntManager:
    """Manage hunt files and operations."""

    def __init__(self, hunts_dir: Optional[Path] = None):
        """Initialize hunt manager.

        Args:
            hunts_dir: Directory containing hunt files (default: ./hunts)
        """
        self.hunts_dir = Path(hunts_dir) if hunts_dir else Path.cwd() / "hunts"

        if not self.hunts_dir.exists():
            self.hunts_dir.mkdir(parents=True, exist_ok=True)

    def list_hunts(
        self,
        status: Optional[str] = None,
        tactic: Optional[str] = None,
        technique: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[Dict]:
        """List all hunts with optional filters.

        Args:
            status: Filter by status (planning, active, completed, etc.)
            tactic: Filter by MITRE tactic
            technique: Filter by MITRE technique (e.g., T1003.001)
            platform: Filter by platform (Windows, Linux, macOS, Cloud)

        Returns:
            List of hunt metadata dicts
        """
        hunts = []

        # Find all hunt files
        hunt_files = sorted(self.hunts_dir.glob("*.md"))

        for hunt_file in hunt_files:
            try:
                hunt_data = parse_hunt_file(hunt_file)
                frontmatter = hunt_data.get("frontmatter", {})

                # Apply filters
                if status and frontmatter.get("status") != status:
                    continue

                if tactic and tactic not in frontmatter.get("tactics", []):
                    continue

                if technique and technique not in frontmatter.get("techniques", []):
                    continue

                if platform and platform not in frontmatter.get("platform", []):
                    continue

                # Extract summary info
                date_val = frontmatter.get("date")
                # Convert date objects to strings for JSON serialization
                if hasattr(date_val, "isoformat"):
                    date_str = date_val.isoformat()
                else:
                    date_str = str(date_val) if date_val else None

                hunts.append(
                    {
                        "hunt_id": frontmatter.get("hunt_id"),
                        "title": frontmatter.get("title"),
                        "status": frontmatter.get("status"),
                        "date": date_str,
                        "platform": frontmatter.get("platform", []),
                        "tactics": frontmatter.get("tactics", []),
                        "techniques": frontmatter.get("techniques", []),
                        "findings_count": frontmatter.get("findings_count", 0),
                        "true_positives": frontmatter.get("true_positives", 0),
                        "false_positives": frontmatter.get("false_positives", 0),
                        "file_path": str(hunt_file),
                    }
                )

            except Exception:
                # Skip files that can't be parsed
                continue

        return hunts

    def get_hunt(self, hunt_id: str) -> Optional[Dict]:
        """Get a specific hunt by ID.

        Args:
            hunt_id: Hunt ID (e.g., H-0001)

        Returns:
            Hunt data dict or None if not found
        """
        hunt_file = self.hunts_dir / f"{hunt_id}.md"

        if not hunt_file.exists():
            return None

        return parse_hunt_file(hunt_file)

    def get_next_hunt_id(self, prefix: str = "H-") -> str:
        """Calculate the next available hunt ID.

        Args:
            prefix: Hunt ID prefix (default: H-)

        Returns:
            Next hunt ID (e.g., H-0023)
        """
        hunts = self.list_hunts()

        if not hunts:
            return f"{prefix}0001"

        # Extract numbers from hunt IDs with matching prefix
        numbers = []
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")

        for hunt in hunts:
            hunt_id = hunt.get("hunt_id")
            if not hunt_id or not isinstance(hunt_id, str):
                continue
            match = pattern.match(hunt_id)
            if match:
                numbers.append(int(match.group(1)))

        if not numbers:
            return f"{prefix}0001"

        # Next number with zero-padding
        next_num = max(numbers) + 1
        return f"{prefix}{next_num:04d}"

    def search_hunts(self, query: str) -> List[Dict]:
        """Full-text search across all hunt files.

        Args:
            query: Search query string

        Returns:
            List of matching hunts
        """
        results = []
        query_lower = query.lower()

        for hunt_file in self.hunts_dir.glob("*.md"):
            try:
                with open(hunt_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check if query appears in file
                if query_lower in content.lower():
                    hunt_data = parse_hunt_file(hunt_file)
                    frontmatter = hunt_data.get("frontmatter", {})

                    results.append(
                        {
                            "hunt_id": frontmatter.get("hunt_id"),
                            "title": frontmatter.get("title"),
                            "status": frontmatter.get("status"),
                            "file_path": str(hunt_file),
                        }
                    )

            except Exception:
                continue

        return results

    def calculate_stats(self) -> Dict:
        """Calculate hunt program statistics.

        Returns:
            Dict with success rates, TP/FP ratios, coverage metrics
        """
        hunts = self.list_hunts()

        if not hunts:
            return {
                "total_hunts": 0,
                "completed_hunts": 0,
                "total_findings": 0,
                "true_positives": 0,
                "false_positives": 0,
                "success_rate": 0.0,
                "tp_fp_ratio": 0.0,
            }

        total_hunts = len(hunts)
        completed_hunts = len([h for h in hunts if h.get("status") == "completed"])

        total_findings = sum(h.get("findings_count", 0) for h in hunts)
        total_tp = sum(h.get("true_positives", 0) for h in hunts)
        total_fp = sum(h.get("false_positives", 0) for h in hunts)

        # Calculate success rate (hunts with TP / completed hunts)
        hunts_with_tp = len([h for h in hunts if h.get("true_positives", 0) > 0])
        success_rate = (hunts_with_tp / completed_hunts * 100) if completed_hunts > 0 else 0.0

        # Calculate TP/FP ratio
        tp_fp_ratio = (total_tp / total_fp) if total_fp > 0 else float("inf")

        return {
            "total_hunts": total_hunts,
            "completed_hunts": completed_hunts,
            "total_findings": total_findings,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "success_rate": round(success_rate, 1),
            "tp_fp_ratio": round(tp_fp_ratio, 2) if tp_fp_ratio != float("inf") else "∞",
        }

    def calculate_attack_coverage(self) -> Dict[str, List[str]]:
        """Calculate MITRE ATT&CK technique coverage.

        Returns:
            Dict mapping tactics to lists of covered techniques
        """
        hunts = self.list_hunts()

        coverage: Dict = {}

        for hunt in hunts:
            tactics = hunt.get("tactics", [])
            techniques = hunt.get("techniques", [])

            for tactic in tactics:
                if tactic not in coverage:
                    coverage[tactic] = set()

                for technique in techniques:
                    coverage[tactic].add(technique)

        # Convert sets to sorted lists
        return {tactic: sorted(list(techniques)) for tactic, techniques in coverage.items()}
