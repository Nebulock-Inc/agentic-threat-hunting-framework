"""Tests for input validation and path traversal prevention."""

import pytest

from athf.utils.validation import (
    safe_path_join,
    validate_file_path,
    validate_hunt_id,
    validate_investigation_id,
    validate_research_id,
)


class TestHuntIDValidation:
    """Test hunt ID validation."""

    def test_valid_hunt_id(self):
        """Valid hunt IDs should pass."""
        assert validate_hunt_id("H-0001") is True
        assert validate_hunt_id("H-9999") is True
        assert validate_hunt_id("A-0001") is True

    def test_invalid_format(self):
        """Invalid formats should fail."""
        assert validate_hunt_id("H-1") is False  # Too few digits
        assert validate_hunt_id("H-00001") is False  # Too many digits
        assert validate_hunt_id("H0001") is False  # Missing dash
        assert validate_hunt_id("h-0001") is False  # Lowercase
        assert validate_hunt_id("") is False  # Empty string
        assert validate_hunt_id("H-") is False  # Missing number

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        assert validate_hunt_id("../../etc/passwd") is False
        assert validate_hunt_id("H-0001/../../secrets.txt") is False
        assert validate_hunt_id("../H-0001") is False
        assert validate_hunt_id("H-0001\\..\\..\\secrets") is False  # Windows paths
        assert validate_hunt_id("H-0001/.env") is False


class TestInvestigationIDValidation:
    """Test investigation ID validation."""

    def test_valid_investigation_id(self):
        """Valid investigation IDs should pass."""
        assert validate_investigation_id("I-0001") is True
        assert validate_investigation_id("I-9999") is True

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        assert validate_investigation_id("../../../secrets") is False
        assert validate_investigation_id("I-0001/../../../etc/passwd") is False


class TestResearchIDValidation:
    """Test research ID validation."""

    def test_valid_research_id(self):
        """Valid research IDs should pass."""
        assert validate_research_id("R-0001") is True
        assert validate_research_id("R-9999") is True

    def test_path_traversal_blocked(self):
        """Path traversal attempts should be blocked."""
        assert validate_research_id("R-0001/../../secrets") is False
        assert validate_research_id("../R-0001") is False


class TestFilePathValidation:
    """Test file path validation."""

    def test_valid_path_within_base(self, tmp_path):
        """Files within base directory should pass."""
        base = tmp_path / "hunts"
        base.mkdir()
        file_path = base / "H-0001.md"
        assert validate_file_path(file_path, base) is True

    def test_path_outside_base_rejected(self, tmp_path):
        """Files outside base directory should fail."""
        base = tmp_path / "hunts"
        base.mkdir()
        outside_file = tmp_path / "secrets.txt"
        assert validate_file_path(outside_file, base) is False

    def test_symbolic_link_traversal_blocked(self, tmp_path):
        """Symbolic links escaping base directory should be blocked."""
        base = tmp_path / "hunts"
        base.mkdir()

        # Create a directory outside base
        outside = tmp_path / "outside"
        outside.mkdir()
        secret_file = outside / "secret.txt"
        secret_file.write_text("secret data")

        # Try to create symlink inside base pointing outside
        link_path = base / "escape.md"
        try:
            link_path.symlink_to(secret_file)
            # If symlink created, verify it's blocked
            assert validate_file_path(link_path, base) is False
        except OSError:
            # On some systems, symlinks may not be allowed
            pytest.skip("Symbolic links not supported")


class TestSafePathJoin:
    """Test safe path joining utility."""

    def test_valid_hunt_id_join(self, tmp_path):
        """Valid hunt ID should create proper path."""
        base = tmp_path / "hunts"
        base.mkdir()
        result = safe_path_join(base, "H-0001")
        assert result == base / "H-0001.md"

    def test_invalid_id_returns_none(self, tmp_path):
        """Invalid IDs should return None."""
        base = tmp_path / "hunts"
        base.mkdir()
        assert safe_path_join(base, "../../etc/passwd") is None
        assert safe_path_join(base, "H-0001/../secrets") is None

    def test_path_traversal_returns_none(self, tmp_path):
        """Path traversal attempts should return None."""
        base = tmp_path / "hunts"
        base.mkdir()
        # Even if ID format looks valid, traversal should fail
        assert safe_path_join(base, "../etc/passwd") is None


class TestSecurityRegression:
    """Regression tests for CVE-like scenarios."""

    def test_directory_traversal_attack_blocked(self):
        """Verify the original vulnerability is fixed."""
        # Original vulnerability: user provides hunt_id like "../../etc/passwd"
        # which would construct: Path("hunts") / "../../etc/passwd"

        # This should be blocked by validation
        malicious_id = "../../etc/passwd"
        assert validate_hunt_id(malicious_id) is False

    def test_null_byte_injection_blocked(self):
        """Null byte injection should be blocked."""
        # Hunt IDs with null bytes
        assert validate_hunt_id("H-0001\x00.md") is False
        assert validate_hunt_id("H-0001\x00../../../etc/passwd") is False

    def test_windows_path_traversal_blocked(self):
        """Windows-style path traversal should be blocked."""
        assert validate_hunt_id("H-0001\\..\\..\\secrets") is False
        assert validate_hunt_id("..\\..\\etc\\passwd") is False
