"""Manage hunt files and operations."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from athf.core.attack_matrix import ATTACK_TACTICS, TOTAL_TECHNIQUES, get_sorted_tactics
from athf.core.hunt_parser import parse_hunt_file
from athf.core.verdicts import VERDICTS, precision_pair, tally_frontmatter_verdicts
from athf.utils.validation import validate_file_path, validate_hunt_id

# Documentation files to exclude when discovering hunt files at any directory level
EXCLUDED_DOC_FILES = {"README.md", "FORMAT_GUIDELINES.md", "INDEX.md", "AGENTS.md", "WEEKLY_SUMMARY_TEMPLATE.md"}


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

    def find_hunt_file(self, hunt_id: str) -> Optional[Path]:
        """Find a hunt file by ID, searching recursively.

        Args:
            hunt_id: Hunt ID (e.g., H-0001)

        Returns:
            Path to the hunt file, or None if not found
        """
        if not validate_hunt_id(hunt_id):
            return None
        # Try flat first for speed
        flat = self.hunts_dir / f"{hunt_id}.md"
        if flat.exists():
            return flat
        # Recursive fallback
        matches = list(self.hunts_dir.rglob(f"{hunt_id}.md"))
        if not matches:
            return None
        result = matches[0]
        if not validate_file_path(result, self.hunts_dir):
            return None
        return result

    def find_all_hunt_files(self) -> List[Path]:
        """Find all hunt files recursively, excluding documentation.

        Returns:
            Sorted list of hunt file Paths
        """
        return sorted(f for f in self.hunts_dir.rglob("*.md") if f.name not in EXCLUDED_DOC_FILES)

    def list_hunts(
        self,
        status: Optional[str] = None,
        tactic: Optional[str] = None,
        technique: Optional[str] = None,
        platform: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> List[Dict]:
        """List all hunts with optional filters.

        Args:
            status: Filter by status (planning, active, completed, etc.)
            tactic: Filter by MITRE tactic
            technique: Filter by MITRE technique (e.g., T1003.001)
            platform: Filter by platform (Windows, Linux, macOS, Cloud)
            directory: Filter by environment directory (test or production)

        Returns:
            List of hunt metadata dicts
        """
        hunts = []

        for hunt_file in self.find_all_hunt_files():
            try:
                hunt_data = parse_hunt_file(hunt_file)
                frontmatter = hunt_data.get("frontmatter", {})

                # Determine environment from file path
                hunt_file_parts = hunt_file.parts
                environment = None
                if "test" in hunt_file_parts:
                    environment = "test"
                elif "production" in hunt_file_parts:
                    environment = "production"

                # Apply filters
                if status and frontmatter.get("status") != status:
                    continue

                if tactic and tactic not in frontmatter.get("tactics", []):
                    continue

                if technique and technique not in frontmatter.get("techniques", []):
                    continue

                if platform and platform not in frontmatter.get("platform", []):
                    continue

                if directory and environment != directory:
                    continue

                # Extract summary info
                date_val = frontmatter.get("date")
                # Convert date objects to strings for JSON serialization
                if hasattr(date_val, "isoformat"):
                    date_str = date_val.isoformat()
                else:
                    date_str = str(date_val) if date_val else None

                tiers = tally_frontmatter_verdicts(frontmatter) or {v: 0 for v in VERDICTS}
                positives, negatives = precision_pair(tiers)

                summary = {
                    "hunt_id": frontmatter.get("hunt_id"),
                    "title": frontmatter.get("title"),
                    "status": frontmatter.get("status"),
                    "date": date_str,
                    "platform": frontmatter.get("platform", []),
                    "tactics": frontmatter.get("tactics", []),
                    "techniques": frontmatter.get("techniques", []),
                    "findings_count": frontmatter.get("findings_count", 0),
                    # A hand-typed legacy count always wins: it may record work
                    # done before the ladder existed, and nothing here should
                    # overwrite a number a hunter entered deliberately.
                    "true_positives": frontmatter.get("true_positives", positives),
                    "false_positives": frontmatter.get("false_positives", negatives),
                    "file_path": str(hunt_file),
                    "environment": environment,
                }
                summary.update(tiers)
                hunts.append(summary)

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
        hunt_file = self.find_hunt_file(hunt_id)
        if not hunt_file:
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

    def search_hunts(self, query: str, directory: Optional[str] = None) -> List[Dict]:
        """Full-text search across all hunt files.

        Args:
            query: Search query string
            directory: Filter by environment directory (test or production)

        Returns:
            List of matching hunts
        """
        results = []
        query_lower = query.lower()

        for hunt_file in self.find_all_hunt_files():
            # Determine environment from file path
            hunt_file_parts = hunt_file.parts
            environment = None
            if "test" in hunt_file_parts:
                environment = "test"
            elif "production" in hunt_file_parts:
                environment = "production"

            # Apply directory filter
            if directory and environment != directory:
                continue

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
                            "environment": environment,
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
            empty = {
                "total_hunts": 0,
                "completed_hunts": 0,
                "total_findings": 0,
                "true_positives": 0,
                "false_positives": 0,
                "success_rate": 0.0,
                "tp_fp_ratio": 0.0,
            }
            empty.update({verdict: 0 for verdict in VERDICTS})
            return empty

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

        stats = {
            "total_hunts": total_hunts,
            "completed_hunts": completed_hunts,
            "total_findings": total_findings,
            "true_positives": total_tp,
            "false_positives": total_fp,
            "success_rate": round(success_rate, 1),
            "tp_fp_ratio": round(tp_fp_ratio, 2) if tp_fp_ratio != float("inf") else "∞",
        }
        stats.update(
            {verdict: sum(h.get(verdict, 0) for h in hunts) for verdict in VERDICTS}
        )
        return stats

    def calculate_attack_coverage(self) -> Dict[str, Any]:
        """Calculate MITRE ATT&CK technique coverage with hunt references.

        Returns:
            Dict with structure:
            {
                "summary": {
                    "total_hunts": int,
                    "completed_hunts": int,
                    "unique_techniques": int,
                    "tactics_covered": int,
                    "total_techniques": int,
                    "overall_coverage_pct": float
                },
                "by_tactic": {
                    "tactic-name": {
                        "hunt_count": int,
                        "hunt_ids": List[str],
                        "techniques": {
                            "T1234.001": ["H-0001", "H-0003"]
                        },
                        "techniques_covered": int,
                        "total_techniques": int,
                        "coverage_pct": float
                    }
                }
            }
        """
        hunts = self.list_hunts()

        # Initialize coverage structure for ALL ATT&CK tactics (not just ones with hunts)
        coverage_by_tactic: Dict[str, Dict[str, Any]] = {}
        for tactic_key in get_sorted_tactics():
            coverage_by_tactic[tactic_key] = {
                "hunt_count": 0,
                "hunt_ids": set(),
                "techniques": {},
                "total_techniques": ATTACK_TACTICS[tactic_key]["technique_count"],
            }

        all_unique_techniques: Set[str] = set()

        for hunt in hunts:
            hunt_id = hunt.get("hunt_id", "UNKNOWN")
            tactics = hunt.get("tactics", [])
            techniques = hunt.get("techniques", [])

            # Track all unique techniques across all hunts
            all_unique_techniques.update(techniques)

            for tactic in tactics:
                # Skip if tactic not in ATT&CK matrix (might be custom tactic)
                if tactic not in coverage_by_tactic:
                    continue

                # Track hunt IDs for this tactic
                coverage_by_tactic[tactic]["hunt_ids"].add(hunt_id)

                # Track which hunts cover each technique under this tactic
                for technique in techniques:
                    if technique not in coverage_by_tactic[tactic]["techniques"]:
                        coverage_by_tactic[tactic]["techniques"][technique] = []
                    coverage_by_tactic[tactic]["techniques"][technique].append(hunt_id)

        # Calculate coverage percentages and convert sets to sorted lists
        for tactic in coverage_by_tactic:
            coverage_by_tactic[tactic]["hunt_count"] = len(coverage_by_tactic[tactic]["hunt_ids"])
            coverage_by_tactic[tactic]["hunt_ids"] = sorted(coverage_by_tactic[tactic]["hunt_ids"])
            coverage_by_tactic[tactic]["techniques_covered"] = len(coverage_by_tactic[tactic]["techniques"])

            # Calculate coverage percentage
            total = coverage_by_tactic[tactic]["total_techniques"]
            covered = coverage_by_tactic[tactic]["techniques_covered"]
            coverage_by_tactic[tactic]["coverage_pct"] = (covered / total * 100) if total > 0 else 0.0

        # Calculate overall coverage
        tactics_with_hunts = len([t for t in coverage_by_tactic.values() if t["hunt_count"] > 0])
        overall_coverage_pct = (len(all_unique_techniques) / TOTAL_TECHNIQUES * 100) if TOTAL_TECHNIQUES > 0 else 0.0

        # Build summary
        summary = {
            "total_hunts": len(hunts),
            "completed_hunts": len([h for h in hunts if h.get("status") == "completed"]),
            "unique_techniques": len(all_unique_techniques),
            "tactics_covered": tactics_with_hunts,
            "total_techniques": TOTAL_TECHNIQUES,
            "overall_coverage_pct": overall_coverage_pct,
        }

        return {"summary": summary, "by_tactic": coverage_by_tactic}
