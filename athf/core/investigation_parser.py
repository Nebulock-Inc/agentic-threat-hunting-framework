"""Parse investigation files (YAML frontmatter + markdown).

Investigation parser is simpler than hunt parser:
- Minimal validation (only ID, title, date required)
- No LOCK section validation (optional/flexible content)
- No findings count validation (investigations not tracked in metrics)
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


class InvestigationParser:
    """Parser for ATHF investigation files."""

    def __init__(self, file_path: Path):
        """Initialize parser with investigation file path."""
        self.file_path = Path(file_path)
        self.frontmatter: Dict[str, Any] = {}
        self.content = ""

    def parse(self) -> Dict[str, Any]:
        """Parse investigation file and return structured data.

        Returns:
            Dict containing frontmatter and content
        """
        if not self.file_path.exists():
            raise FileNotFoundError(f"Investigation file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse YAML frontmatter
        self.frontmatter = self._parse_frontmatter(content)

        # Extract main content (after frontmatter)
        self.content = self._extract_content(content)

        return {
            "file_path": str(self.file_path),
            "investigation_id": self.frontmatter.get("investigation_id"),
            "frontmatter": self.frontmatter,
            "content": self.content,
        }

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
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

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate investigation structure.

        Lightweight validation - only checks minimal required fields.
        Does NOT validate LOCK sections or findings counts.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check frontmatter exists
        if not self.frontmatter:
            errors.append("Missing YAML frontmatter")
            return (False, errors)

        # Check required frontmatter fields (minimal)
        required_fields = ["investigation_id", "title", "date"]
        for field in required_fields:
            if field not in self.frontmatter:
                errors.append(f"Missing required frontmatter field: {field}")

        # Validate investigation_id format (e.g., I-0001)
        investigation_id = self.frontmatter.get("investigation_id", "")
        if investigation_id and not re.match(r"^I-\d{4}$", investigation_id):
            errors.append(f"Invalid investigation_id format: {investigation_id} (expected format: I-0001)")

        # Validate file name matches investigation_id
        if investigation_id:
            expected_filename = f"{investigation_id}.md"
            if self.file_path.name != expected_filename:
                errors.append(f"File name mismatch: {self.file_path.name} (expected: {expected_filename})")

        # Validate type field if present
        investigation_type = self.frontmatter.get("type")
        valid_types = ["finding", "baseline", "exploratory", "other"]
        if investigation_type and investigation_type not in valid_types:
            errors.append(f"Invalid investigation type: {investigation_type} (expected one of: {', '.join(valid_types)})")

        return (len(errors) == 0, errors)


def parse_investigation_file(file_path: Path) -> Dict[str, Any]:
    """Convenience function to parse an investigation file.

    Args:
        file_path: Path to investigation file

    Returns:
        Parsed investigation data
    """
    parser = InvestigationParser(file_path)
    return parser.parse()


def validate_investigation_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Convenience function to validate an investigation file.

    Args:
        file_path: Path to investigation file

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    parser = InvestigationParser(file_path)
    parser.parse()
    return parser.validate()


def get_all_investigations(investigations_dir: Path) -> List[Dict[str, Any]]:
    """Get all investigation files from the investigations directory.

    Args:
        investigations_dir: Path to investigations directory

    Returns:
        List of parsed investigation data (sorted by investigation_id)
    """
    investigations_dir = Path(investigations_dir)

    if not investigations_dir.exists():
        return []

    # Find all I-*.md files
    investigation_files = sorted(investigations_dir.glob("I-*.md"))

    investigations = []
    for file_path in investigation_files:
        try:
            investigation = parse_investigation_file(file_path)
            investigations.append(investigation)
        except Exception as e:
            # Skip invalid files but log the error
            print(f"Warning: Failed to parse {file_path}: {e}")
            continue

    return investigations


def get_next_investigation_id(investigations_dir: Path) -> str:
    """Get the next available investigation ID.

    Args:
        investigations_dir: Path to investigations directory

    Returns:
        Next investigation ID (e.g., "I-0001", "I-0042")
    """
    investigations = get_all_investigations(investigations_dir)

    if not investigations:
        return "I-0001"

    # Extract numeric IDs and find max
    max_id = 0
    for investigation in investigations:
        investigation_id = investigation.get("investigation_id", "")
        match = re.match(r"^I-(\d{4})$", investigation_id)
        if match:
            id_num = int(match.group(1))
            max_id = max(max_id, id_num)

    # Return next ID with zero-padding
    return f"I-{max_id + 1:04d}"
