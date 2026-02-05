"""Input validation utilities to prevent path traversal and injection attacks."""

import re
from pathlib import Path
from typing import Optional


def validate_hunt_id(hunt_id: str) -> bool:
    """Validate hunt ID format and prevent path traversal.

    Args:
        hunt_id: Hunt ID to validate (e.g., H-0001)

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_hunt_id("H-0001")
        True
        >>> validate_hunt_id("H-9999")
        True
        >>> validate_hunt_id("../../etc/passwd")
        False
        >>> validate_hunt_id("H-0001/../secrets.txt")
        False
    """
    if not hunt_id or not isinstance(hunt_id, str):
        return False

    # Check format: single letter(s) + dash + 4 digits
    if not re.match(r"^[A-Z]+-\d{4}$", hunt_id):
        return False

    # Prevent path traversal
    if ".." in hunt_id or "/" in hunt_id or "\\" in hunt_id:
        return False

    return True


def validate_investigation_id(investigation_id: str) -> bool:
    """Validate investigation ID format and prevent path traversal.

    Args:
        investigation_id: Investigation ID to validate (e.g., I-0001)

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_investigation_id("I-0001")
        True
        >>> validate_investigation_id("../../../secrets")
        False
    """
    if not investigation_id or not isinstance(investigation_id, str):
        return False

    # Check format: single letter + dash + 4 digits
    if not re.match(r"^[A-Z]+-\d{4}$", investigation_id):
        return False

    # Prevent path traversal
    if ".." in investigation_id or "/" in investigation_id or "\\" in investigation_id:
        return False

    return True


def validate_research_id(research_id: str) -> bool:
    """Validate research ID format and prevent path traversal.

    Args:
        research_id: Research ID to validate (e.g., R-0001)

    Returns:
        True if valid, False otherwise

    Examples:
        >>> validate_research_id("R-0001")
        True
        >>> validate_research_id("R-0001/../../secrets")
        False
    """
    if not research_id or not isinstance(research_id, str):
        return False

    # Check format: single letter + dash + 4 digits
    if not re.match(r"^[A-Z]+-\d{4}$", research_id):
        return False

    # Prevent path traversal
    if ".." in research_id or "/" in research_id or "\\" in research_id:
        return False

    return True


def validate_file_path(file_path: Path, base_dir: Path) -> bool:
    """Validate that resolved file path is within base directory.

    Args:
        file_path: File path to validate
        base_dir: Base directory that file must be within

    Returns:
        True if file is within base directory, False otherwise

    Examples:
        >>> base = Path("/app/hunts")
        >>> validate_file_path(Path("/app/hunts/H-0001.md"), base)
        True
        >>> validate_file_path(Path("/etc/passwd"), base)
        False
    """
    try:
        # Resolve to absolute paths
        resolved_file = file_path.resolve()
        resolved_base = base_dir.resolve()

        # Check if file is relative to base directory
        return resolved_file.is_relative_to(resolved_base)
    except (ValueError, OSError):
        return False


def safe_path_join(base_dir: Path, id_value: str, extension: str = ".md") -> Optional[Path]:
    """Safely join base directory with ID to create file path.

    Validates ID format and ensures resulting path is within base directory.

    Args:
        base_dir: Base directory (e.g., Path("hunts"))
        id_value: ID value (e.g., "H-0001")
        extension: File extension (default: .md)

    Returns:
        Validated Path object or None if validation fails

    Examples:
        >>> safe_path_join(Path("hunts"), "H-0001")
        Path('hunts/H-0001.md')
        >>> safe_path_join(Path("hunts"), "../../etc/passwd")
        None
    """
    # Validate ID format based on first letter
    if id_value.startswith("H-"):
        if not validate_hunt_id(id_value):
            return None
    elif id_value.startswith("I-"):
        if not validate_investigation_id(id_value):
            return None
    elif id_value.startswith("R-"):
        if not validate_research_id(id_value):
            return None
    else:
        # Unknown prefix - validate generic format
        if not re.match(r"^[A-Z]+-\d{4}$", id_value):
            return None
        if ".." in id_value or "/" in id_value or "\\" in id_value:
            return None

    # Construct path
    file_path = base_dir / f"{id_value}{extension}"

    # Validate path is within base directory
    if not validate_file_path(file_path, base_dir):
        return None

    return file_path
