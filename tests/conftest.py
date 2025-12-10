"""
Pytest configuration and shared fixtures for ATHF tests.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


@pytest.fixture
def sample_hunt_content():
    """Provide sample hunt content for testing."""
    return """---
hunt_id: H-0001
title: Test Hunt
status: completed
date: 2025-12-02
hunter: Test Hunter
techniques: [T1003.001]
tactics: [credential-access]
platforms: [windows]
data_sources: [windows-event-logs]
tags: [lsass, credential-dumping]
true_positives: 1
false_positives: 0
---

# H-0001: Test Hunt

## LEARN: Prepare the Hunt

### Hypothesis Statement

Test hypothesis for credential dumping detection.

### Threat Context

LSASS memory access is a common technique used by adversaries.

## OBSERVE: Expected Behaviors

### What Normal Looks Like

Legitimate LSASS access by system processes.

### What Suspicious Looks Like

Unsigned processes accessing LSASS memory.

## CHECK: Execute & Analyze

### Data Source Information

- **Index/Data Source:** windows-event-logs
- **Time Range:** Last 7 days

### Hunting Queries

```spl
index=windows EventCode=10 TargetImage="*lsass.exe"
| stats count by SourceImage
```

## KEEP: Findings & Response

### Executive Summary

Found 1 true positive of credential dumping activity.

### Findings

- True Positive: Mimikatz detected on DESKTOP-001
"""


@pytest.fixture
def sample_config_content():
    """Provide sample config file content for testing."""
    return """siem: splunk
edr: crowdstrike
hunt_prefix: H
retention_days: 90
initialized: 2025-12-02T14:30:00
version: 0.1.0
"""


@pytest.fixture
def athf_workspace(temp_dir, sample_config_content):
    """Create a complete ATHF workspace structure for testing."""
    # Create directories
    (temp_dir / "hunts").mkdir()
    (temp_dir / "queries").mkdir()
    (temp_dir / "runs").mkdir()
    (temp_dir / "templates").mkdir()

    # Create config file
    config_path = temp_dir / ".athfconfig.yaml"
    config_path.write_text(sample_config_content)

    # Create AGENTS.md
    agents_path = temp_dir / "AGENTS.md"
    agents_path.write_text("# ATHF AI Assistant Instructions\n\nTest content.")

    yield temp_dir


@pytest.fixture
def sample_hunt_file(athf_workspace, sample_hunt_content):
    """Create a sample hunt file in the workspace."""
    hunt_path = athf_workspace / "hunts" / "H-0001.md"
    hunt_path.write_text(sample_hunt_content)
    return hunt_path


@pytest.fixture
def athf_workspace_with_hunts(athf_workspace, sample_hunt_content):
    """Create an ATHF workspace with sample hunt files."""
    # Create first hunt
    hunt1_path = athf_workspace / "hunts" / "H-0001.md"
    hunt1_path.write_text(sample_hunt_content)

    # Create second hunt with different content
    hunt2_content = sample_hunt_content.replace("H-0001", "H-0002").replace("Test Hunt", "Second Hunt")
    hunt2_path = athf_workspace / "hunts" / "H-0002.md"
    hunt2_path.write_text(hunt2_content)

    return athf_workspace


# Custom markers for categorizing tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (fast, isolated)")
    config.addinivalue_line("markers", "integration: mark test as an integration test (slower, multiple components)")
    config.addinivalue_line("markers", "slow: mark test as slow (skipped in quick test runs)")
