# Changelog

All notable changes to the Agentic Threat Hunting Framework (ATHF) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- None

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

## [0.3.1] - 2026-01-13

### Fixed
- **Packaging Bug** - Fixed `ModuleNotFoundError: No module named 'athf.agents'` when installing via pip/pipx
  - Added missing packages to `pyproject.toml`: `athf.agents`, `athf.agents.llm`
  - Packages list now includes all subdirectories: athf, athf.agents, athf.agents.llm, athf.commands, athf.core, athf.data, athf.utils
  - Verified wheel build includes all agent module files

## [0.3.0] - 2026-01-11

### Added
- **Agent Framework** - Autonomous agents for threat hunting workflows
  - `athf.agents` - Base agent framework and orchestration
  - `athf.agents.llm` - LLM-powered agents (hypothesis generation, research, finding analysis)
  - Agent orchestration with task delegation and result aggregation
- **Research Workflow** - Pre-hunt research and investigation (`athf research`)
- **Drift Detection** - Behavioral anomaly detection infrastructure (`athf drift`)
- **Signal Investigation** - Low-fidelity pattern scoring and investigation (`athf signals`)

### Changed
- CLI refactored to support agent-based workflows
- Enhanced hunt creation with agent-generated hypotheses

## [0.2.2] - 2024-12-17

### Fixed
- Type errors in `athf/core/attack_matrix.py` (added TypedDict for proper mypy checking)
- Python 3.8 compatibility: `list[str]` → `List[str]` in `athf/core/attack_matrix.py`
- Python 3.8 compatibility: `tuple[...]` → `Tuple[...]` in `athf/core/investigation_parser.py`
- Python 3.8 compatibility: `tuple[...]`, `list[str]` → `Tuple[...]`, `List[str]` in `athf/commands/investigate.py`
- Python 3.8 compatibility: `set[str]` → `Set[str]` in `athf/core/hunt_manager.py`
- Python 3.8 compatibility: `int | str` → `Union[int, str]` in `athf/commands/env.py`
- Windows UTF-8 encoding errors in `athf/commands/context.py` (3 instances) and `athf/commands/similar.py` (2 instances)
- Test assertion errors in `tests/commands/test_env.py` for env info and activate commands
- Mypy unused-ignore errors in `athf/commands/similar.py` (sklearn imports handled by --ignore-missing-imports flag)
- CI/CD pipeline errors blocking builds on Python 3.8-3.12 across all platforms

## [0.2.1] - 2024-12-17

### Fixed
- Type errors in `athf/core/attack_matrix.py` (added TypedDict for proper mypy checking)
- Python 3.8 compatibility: `list[str]` → `List[str]` in `athf/core/attack_matrix.py`
- Python 3.8 compatibility: `tuple[...]` → `Tuple[...]` in `athf/core/investigation_parser.py`
- Python 3.8 compatibility: `tuple[...]`, `list[str]` → `Tuple[...]`, `List[str]` in `athf/commands/investigate.py`
- Python 3.8 compatibility: `set[str]` → `Set[str]` in `athf/core/hunt_manager.py`
- Python 3.8 compatibility: `int | str` → `Union[int, str]` in `athf/commands/env.py`
- Windows UTF-8 encoding errors in `athf/commands/context.py` (3 instances) and `athf/commands/similar.py` (2 instances)
- Test assertion errors in `tests/commands/test_env.py` for env info and activate commands
- Mypy unused-ignore errors in `athf/commands/similar.py` (sklearn imports handled by --ignore-missing-imports flag)
- CI/CD pipeline errors blocking builds on Python 3.8-3.12 across all platforms

## [0.2.0] - 2024-12-17

### Added
- **CLI Commands**
  - `athf context` - AI-optimized context loading (replaces ~5 Read operations, 75% token savings)
  - `athf env` - Environment setup and management (setup, info, activate, clean)
  - `athf investigate` - Investigation workflow for exploratory work (separate from hunt metrics)
  - `athf similar` - Semantic search for similar hunts using scikit-learn embeddings
- **Core Modules**
  - `athf/core/attack_matrix.py` - MITRE ATT&CK coverage tracking and analysis
  - `athf/core/investigation_parser.py` - Parser for I-XXXX investigation files
- **Testing Infrastructure**
  - Comprehensive test suite for all new commands (tests/commands/)
  - Command-specific test modules (test_context.py, test_env.py, test_similar.py)
  - Integration tests for multi-command workflows
- **Rich Content CLI Flags**
  - `--hypothesis`, `--threat-context`, `--actor`, `--behavior`, `--location`, `--evidence`
  - Enable fully-populated hunt files via single CLI command
  - AI-friendly one-liner hunt creation without manual editing

### Changed
- Enhanced `athf hunt` command with investigation integration
- Updated CLI help system with improved command descriptions
- Improved context bundling for AI workflows (structured JSON/YAML output)
- Updated documentation to reflect new commands and workflows

### Fixed
- Python 3.8 compatibility issues
- Testing framework stability improvements

## [0.1.0] - 2024-12-10

### Added
- Initial ATHF framework documentation
  - LOCK pattern (Learn, Observe, Check, Keep)
  - 5-level maturity model
  - USING_ATHF.md adoption guide
  - INSTALL.md installation guide
- Example hunt implementations
  - H-0001: macOS Data Collection via AppleScript Detection
  - H-0002: Linux Crontab Persistence Detection
  - H-0003: AWS Lambda Persistence Detection
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

For more on the philosophy, see [USING_ATHF.md](../../../USING_ATHF.md).
