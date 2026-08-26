"""Parse hunt files (YAML frontmatter + markdown)."""

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from athf.core.verdicts import (
    ATTEMPTED_NOT_VULNERABLE,
    CIRCULAR_CONFIRMATION,
    CONFIRMED,
    INVALID_VERDICT,
    LEGACY_VERDICT,
    MISROUTED,
    MISSING_VERDICT,
    UNNAMED_CONTROL,
    UNSUPPORTED_CONFIRMATION,
    VERDICTS,
    gate_failures,
)

LADDER_KEYS = ("findings", "ruled_out")


class HuntParser:
    """Parser for ATHF hunt files."""

    def __init__(self, file_path: Path):
        """Initialize parser with hunt file path."""
        self.file_path = Path(file_path)
        self.frontmatter: Dict = {}
        self.content = ""
        self.lock_sections: Dict = {}
        self.findings: List = []
        self.ruled_out: List = []

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

        # Verdict ladder. Malformed values surface as validation errors, so
        # parsing keeps them out of the exposed lists rather than raising here.
        self.findings = self._ladder_entries("findings")
        self.ruled_out = self._ladder_entries("ruled_out")

        return {
            "file_path": str(self.file_path),
            "hunt_id": self.frontmatter.get("hunt_id"),
            "frontmatter": self.frontmatter,
            "content": self.content,
            "lock_sections": self.lock_sections,
            "findings": self.findings,
            "ruled_out": self.ruled_out,
        }

    def _ladder_entries(self, key: str) -> List:
        """Return the well-formed entries under ``key``, tolerating junk."""
        raw = self.frontmatter.get(key)
        if not isinstance(raw, list):
            return []
        return [entry for entry in raw if isinstance(entry, dict)]

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

        errors.extend(self._validate_verdicts())

        return (len(errors) == 0, errors)

    def _validate_verdicts(self) -> List[str]:
        """Check the verdict ladder in ``findings`` and ``ruled_out``.

        Absent keys and empty lists are valid: hunts predating the ladder, and
        hunts that found nothing, must both validate clean.
        """
        errors: List[str] = []

        for key in LADDER_KEYS:
            raw = self.frontmatter.get(key)
            if raw is None:
                continue
            if not isinstance(raw, list):
                errors.append(f"{key} must be a list of verdict entries; got {type(raw).__name__}")
                continue

            for index, entry in enumerate(raw):
                if not isinstance(entry, dict):
                    errors.append(f"{key}[{index}] must be a mapping; got {type(entry).__name__}")
                    continue
                errors.extend(self._validate_entry(key, index, entry))

        return errors

    def _validate_entry(self, key: str, index: int, entry: Dict) -> List[str]:
        """Render :func:`gate_failures` as hunter-facing messages.

        The rules themselves live in ``athf.core.verdicts`` so that validation
        and aggregation cannot disagree about what earns a verdict.
        """
        subject = entry.get("subject") or f"{key}[{index}]"
        where = f"{key}[{index}] ({subject})"
        errors: List[str] = []

        for code, detail in gate_failures(key, entry):
            if code == MISSING_VERDICT:
                errors.append(f"{where} is missing required field: verdict")
            elif code == INVALID_VERDICT:
                errors.append(f"{where}: {detail}")
            elif code == LEGACY_VERDICT:
                errors.append(
                    f"{where} uses the legacy verdict '{detail}', which has no "
                    f"place on the ladder; assign one of {', '.join(VERDICTS)} or keep the count "
                    "in the legacy true_positives / false_positives keys"
                )
            elif code == MISROUTED:
                verdict, expected = detail
                errors.append(
                    f"{where} has verdict '{verdict}', which belongs in {expected}"
                )
            elif code == UNSUPPORTED_CONFIRMATION:
                errors.append(
                    f"{where} claims verdict '{CONFIRMED}' but has no usable "
                    f"{' or '.join(detail)}; confirmed requires telemetry evidence plus a "
                    "description of the independent confirmation performed outside the log "
                    "corpus (controlled reproduction, host forensics, or configuration review)"
                )
            elif code == CIRCULAR_CONFIRMATION:
                errors.append(
                    f"{where} confirms verdict '{CONFIRMED}' by pointing back "
                    "at the log corpus; the corpus cannot confirm itself. Describe what you did "
                    "outside it — reproduced the behavior, imaged the host, reviewed the config"
                )
            elif code == UNNAMED_CONTROL:
                errors.append(
                    f"{where} has verdict '{ATTEMPTED_NOT_VULNERABLE}' but does "
                    "not name the control that held; set 'control' to the specific control and how "
                    "you verified it held"
                )

        return errors


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
