"""Parse hunt files (YAML frontmatter + markdown)."""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class HuntParser:
    """Parser for ATHF hunt files."""

    def __init__(self, file_path: Path):
        """Initialize parser with hunt file path."""
        self.file_path = Path(file_path)
        self.frontmatter: Dict = {}
        self.content = ""
        self.lock_sections: Dict = {}

    def parse(self) -> Dict:
        """Parse hunt file and return structured data.

        Returns:
            Dict containing frontmatter, content, and LOCK sections
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Hunt file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML frontmatter
        self.frontmatter = self._parse_frontmatter(content)

        # Extract main content (after frontmatter)
        self.content = self._extract_content(content)

        # Parse LOCK sections
        self.lock_sections = self._parse_lock_sections(self.content)

        return {
            "file_path": str(self.file_path),
            "hunt_id": self.frontmatter.get("hunt_id"),
            "frontmatter": self.frontmatter,
            "content": self.content,
            "lock_sections": self.lock_sections,
        }

    def _parse_frontmatter(self, content: str) -> Dict:
        """Extract and parse YAML frontmatter.

        Args:
            content: Full file content

        Returns:
            Dict of frontmatter fields
        """
        # Match YAML frontmatter between --- delimiters
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
        """Extract content after frontmatter.

        Args:
            content: Full file content

        Returns:
            Content after frontmatter
        """
        # Remove frontmatter
        frontmatter_pattern = r"^---\s*\n.*?\n---\s*\n"
        content_without_fm = re.sub(frontmatter_pattern, "", content, count=1, flags=re.DOTALL)

        return content_without_fm.strip()

    def _parse_lock_sections(self, content: str) -> Dict[str, str]:
        """Parse LOCK pattern sections from content.

        Args:
            content: Hunt content (without frontmatter)

        Returns:
            Dict with keys: learn, observe, check, keep
        """
        sections = {}

        # Define section patterns (case-insensitive)
        section_patterns = {
            "learn": r"##\s+LEARN[:\s].*?(?=##\s+OBSERVE|$)",
            "observe": r"##\s+OBSERVE[:\s].*?(?=##\s+CHECK|$)",
            "check": r"##\s+CHECK[:\s].*?(?=##\s+KEEP|$)",
            "keep": r"##\s+KEEP[:\s].*?(?=##\s+[A-Z]|$)",
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[section_name] = match.group(0).strip()

        return sections

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate hunt structure.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check frontmatter exists
        if not self.frontmatter:
            errors.append("Missing YAML frontmatter")

        # Check required frontmatter fields
        required_fields = ["hunt_id", "title", "status", "date"]
        for field in required_fields:
            if field not in self.frontmatter:
                errors.append(f"Missing required frontmatter field: {field}")

        # Validate hunt_id format (e.g., H-0001)
        hunt_id = self.frontmatter.get("hunt_id", "")
        if hunt_id and not re.match(r"^[A-Z]+-\d+$", hunt_id):
            errors.append(f"Invalid hunt_id format: {hunt_id} (expected format: H-0001)")

        # Check LOCK sections present
        lock_sections = ["learn", "observe", "check", "keep"]
        for section in lock_sections:
            if section not in self.lock_sections:
                errors.append(f"Missing LOCK section: {section.upper()}")

        return (len(errors) == 0, errors)


def parse_hunt_file(file_path: Path) -> Dict:
    """Convenience function to parse a hunt file.

    Args:
        file_path: Path to hunt file

    Returns:
        Parsed hunt data
    """
    parser = HuntParser(file_path)
    return parser.parse()


def validate_hunt_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Convenience function to validate a hunt file.

    Args:
        file_path: Path to hunt file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    parser = HuntParser(file_path)
    parser.parse()
    return parser.validate()
