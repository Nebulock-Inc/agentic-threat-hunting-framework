# Changelog

All notable changes to the Agentic Threat Hunting Framework (ATHF) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 4: Community & Packaging infrastructure
  - GitHub issue templates (bug report, feature request, hunt contribution)
  - GitHub Actions workflows (tests.yml, publish.yml)
  - Complete testing suite with pytest fixtures
  - PyPI publication setup (pyproject.toml, MANIFEST.in, setup.py)
  - Code quality configurations (.flake8, .coveragerc, pytest.ini)

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.1.0] - TBD (Planned First Release)

### Added
- Initial ATHF framework documentation
  - LOCK pattern (Learn, Observe, Check, Keep)
  - 5-level maturity model
  - USING_ATHF.md adoption guide
  - INSTALL.md installation guide
- Example hunt implementations
  - H-0001: macOS Information Stealer Detection
  - H-0002: Linux Cron Persistence Detection
  - H-0015: Windows Credential Dumping Detection
- Templates
  - HUNT_LOCK.md template
  - Query templates for Splunk, KQL, Elastic
- Documentation
  - README.md with visual enhancements
  - SHOWCASE.md with real results
  - docs/CLI_REFERENCE.md (planned for CLI implementation)
- Knowledge base
  - hunting-knowledge.md expert hunting frameworks
  - AGENTS.md AI assistant instructions
  - environment.md template
- Integration guides
  - MCP_CATALOG.md for tool integrations
  - SIEM integration examples
  - EDR integration examples

### Philosophy
- Framework-first approach: "Structure over software, adapt to your environment"
- Document-first methodology: Works with markdown, git, and AI assistants
- Optional tooling: CLI enhances but doesn't replace core workflow
- Progression-minded: Start simple, scale when complexity demands it

---

## Version History

**Legend:**
- `[Unreleased]` - Changes in development
- `[X.Y.Z]` - Released versions

**Version Format:**
- `X` - Major version (breaking changes)
- `Y` - Minor version (new features, backward compatible)
- `Z` - Patch version (bug fixes, backward compatible)

**Change Categories:**
- `Added` - New features
- `Changed` - Changes to existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements

---

## Contribution Notes

ATHF is a framework to internalize, not a platform to extend. However, if you've adapted ATHF in interesting ways or have feedback, we'd love to hear about it in [GitHub Discussions](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions).

For more on the philosophy, see [USING_ATHF.md](USING_ATHF.md).
