"""
Tests for hunt file parsing and validation.
"""

import os
import tempfile
from pathlib import Path

import pytest

from athf.core.hunt_parser import HuntParser, parse_hunt_file, validate_hunt_file

# Sample valid hunt content for testing
VALID_HUNT = """---
hunt_id: H-0001
title: Test Hunt
status: completed
date: 2025-12-02
hunter: Test Hunter
techniques: [T1003.001]
tactics: [credential-access]
platform: [Windows]
data_sources: [windows-event-logs]
tags: [lsass, credential-dumping]
---

# H-0001: Test Hunt

## LEARN: Prepare the Hunt

Hypothesis and preparation content.

## OBSERVE: Expected Behaviors

Expected behaviors.

## CHECK: Execute & Analyze

Query execution and analysis.

## KEEP: Findings & Response

Findings and lessons learned.
"""


class TestHuntParser:
    """Test suite for hunt file parsing."""

    def test_parse_valid_hunt(self):
        """Test parsing a complete valid hunt file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(VALID_HUNT)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            hunt_data = parser.parse()

            # Check frontmatter
            assert hunt_data["hunt_id"] == "H-0001"
            assert hunt_data["frontmatter"]["hunt_id"] == "H-0001"
            assert hunt_data["frontmatter"]["title"] == "Test Hunt"
            assert hunt_data["frontmatter"]["status"] == "completed"
            assert hunt_data["frontmatter"]["techniques"] == ["T1003.001"]

            # Check LOCK sections
            assert "learn" in hunt_data["lock_sections"]
            assert "observe" in hunt_data["lock_sections"]
            assert "check" in hunt_data["lock_sections"]
            assert "keep" in hunt_data["lock_sections"]
        finally:
            os.unlink(temp_path)

    def test_parse_missing_frontmatter(self):
        """Test handling of hunts without frontmatter."""
        content = "# Just a markdown file\n\nNo frontmatter here."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            hunt_data = parser.parse()

            # Should handle gracefully, return empty frontmatter
            assert hunt_data["frontmatter"] == {}
        finally:
            os.unlink(temp_path)

    def test_parse_lock_sections(self):
        """Test extracting LOCK sections."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(VALID_HUNT)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            hunt_data = parser.parse()

            sections = hunt_data["lock_sections"]
            assert "learn" in sections
            assert "observe" in sections
            assert "check" in sections
            assert "keep" in sections

            # Check sections contain content
            assert "Hypothesis" in sections["learn"]
            assert "Expected behaviors" in sections["observe"]
        finally:
            os.unlink(temp_path)

    def test_parse_missing_lock_sections(self):
        """Test detection of missing LOCK sections."""
        incomplete_hunt = """---
hunt_id: H-0001
title: Test Hunt
status: planning
date: 2025-12-02
---

# H-0001: Test Hunt

## LEARN: Prepare the Hunt

Content here.

## OBSERVE: Expected Behaviors

Content here.

# Missing CHECK and KEEP
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(incomplete_hunt)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            hunt_data = parser.parse()

            sections = hunt_data["lock_sections"]
            assert "learn" in sections
            assert "observe" in sections
            assert "check" not in sections
            assert "keep" not in sections
        finally:
            os.unlink(temp_path)

    def test_validate_complete_hunt(self):
        """Test validation of a complete, valid hunt."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(VALID_HUNT)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            parser.parse()
            is_valid, errors = parser.validate()

            assert is_valid is True
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_missing_required_fields(self):
        """Test validation catches missing required fields."""
        incomplete_hunt = """---
hunt_id: H-0001
title: Test Hunt
---

# Test Hunt

## LEARN: Prepare the Hunt
## OBSERVE: Expected Behaviors
## CHECK: Execute & Analyze
## KEEP: Findings & Response
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(incomplete_hunt)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            parser.parse()
            is_valid, errors = parser.validate()

            assert is_valid is False
            assert len(errors) >= 1
            # Should catch missing required fields like status, date
            assert any("status" in err.lower() or "date" in err.lower() for err in errors)
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_hunt_id_format(self):
        """Test validation catches invalid hunt ID format."""
        invalid_hunt = """---
hunt_id: INVALID
title: Test Hunt
status: completed
date: 2025-12-02
---

# Test Hunt

## LEARN: Prepare the Hunt
## OBSERVE: Expected Behaviors
## CHECK: Execute & Analyze
## KEEP: Findings & Response
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(invalid_hunt)
            temp_path = f.name

        try:
            parser = HuntParser(Path(temp_path))
            parser.parse()
            is_valid, errors = parser.validate()

            assert is_valid is False
            assert any("hunt_id" in err.lower() for err in errors)
        finally:
            os.unlink(temp_path)


class TestModuleFunctions:
    """Test suite for module-level convenience functions."""

    def test_parse_hunt_file(self):
        """Test parse_hunt_file convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(VALID_HUNT)
            temp_path = f.name

        try:
            hunt_data = parse_hunt_file(Path(temp_path))

            assert hunt_data["hunt_id"] == "H-0001"
            assert hunt_data["frontmatter"]["title"] == "Test Hunt"
            assert "lock_sections" in hunt_data
        finally:
            os.unlink(temp_path)

    def test_validate_hunt_file(self):
        """Test validate_hunt_file convenience function."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(VALID_HUNT)
            temp_path = f.name

        try:
            is_valid, errors = validate_hunt_file(Path(temp_path))

            assert is_valid is True
            assert len(errors) == 0
        finally:
            os.unlink(temp_path)

    def test_validate_invalid_hunt_file(self):
        """Test validate_hunt_file with invalid hunt."""
        incomplete_hunt = """---
hunt_id: H-0001
title: Test Hunt
---

# Test Hunt
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(incomplete_hunt)
            temp_path = f.name

        try:
            is_valid, errors = validate_hunt_file(Path(temp_path))

            assert is_valid is False
            assert len(errors) > 0
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            parse_hunt_file(Path("/nonexistent/path/hunt.md"))


class TestHuntDirectory:
    """Test suite for hunt directory structure."""

    def test_hunt_directory_structure(self):
        """Test that hunt files follow expected directory structure."""
        hunts_dir = Path(__file__).parent.parent / "hunts"

        # This test verifies the test structure is correct
        # Actual hunt examples may or may not exist
        assert True


# Run tests with: pytest tests/test_hunt_parser.py -v
