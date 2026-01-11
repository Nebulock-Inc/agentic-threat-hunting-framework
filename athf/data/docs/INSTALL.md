# ATHF Installation & Development Guide

This guide covers installation methods and development setup for the Agentic Threat Hunting Framework (ATHF).

## Quick Start

The fastest way to get started:

```bash
pip install agentic-threat-hunting-framework
athf init
```

That's it! You're ready to start threat hunting.

---

## Installation Options

### Option 1: Install from PyPI (Recommended)

**Best for**: Most users who want a stable, production-ready installation.

```bash
# Install the latest stable release
pip install agentic-threat-hunting-framework

# Verify installation
athf --version

# Initialize your workspace
athf init
```

**Requirements**:
- Python 3.8 or higher
- pip (comes with Python)

**Virtual Environment (Recommended)**:

```bash
# Create a virtual environment
python3 -m venv athf-env

# Activate it
source athf-env/bin/activate  # On macOS/Linux
athf-env\Scripts\activate     # On Windows

# Install ATHF
pip install agentic-threat-hunting-framework
```

---

### Option 2: Install from Source

**Best for**: Contributors, developers, or users who want the latest features.

```bash
# Clone the repository
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework.git
cd agentic-threat-hunting-framework

# Install in editable mode (changes take effect immediately)
pip install -e .

# Or install normally
pip install .

# Verify installation
athf --version
```

---

### Option 3: No Installation (Pure Markdown)

**Best for**: Users who prefer a documentation-only approach or don't want to install Python packages.

```bash
# Clone the repository
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework.git
cd agentic-threat-hunting-framework

# Copy the template structure
mkdir -p my-hunts/hunts my-hunts/queries my-hunts/runs
cp templates/HUNT_LOCK.md my-hunts/templates/
cp docs/AGENTS.md my-hunts/

# Start creating hunts by copying the template
cp templates/HUNT_LOCK.md my-hunts/hunts/H-0001.md
```

**Pros**:
- No installation required
- Works with any text editor
- Complete control over file structure
- AI assistants can edit markdown directly

**Cons**:
- No validation or automation
- Manual hunt ID tracking
- No built-in search or statistics
- No standardized workflow

---

## Development & Customization

ATHF is designed to be forked and customized for your organization. This section covers setting up your development environment and maintaining code quality in your fork.

### Setting Up Your Fork for Development

```bash
# Fork and clone your repository
git clone https://github.com/YOUR-ORG/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Install with development dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (recommended)
pre-commit install

# Run tests
pytest tests/ -v

# Run type checking
mypy athf --ignore-missing-imports

# Run linting
flake8 athf
black athf --check
isort athf --check-only
```

### Pre-commit Hooks (Optional)

Pre-commit hooks help maintain code quality as you customize ATHF for your organization. Once installed, they run automatically on every commit and check:

- **Code formatting** (black, isort)
- **Linting** (flake8)
- **Security** (bandit)
- **Type checking** (mypy)
- **File hygiene** (trailing whitespace, end-of-file fixes, etc.)

**Installing Pre-commit Hooks**:

```bash
# Install pre-commit (included in dev dependencies)
pip install -e ".[dev]"

# Set up the git hook
pre-commit install

# Run manually on all files (optional)
pre-commit run --all-files
```

**Running Individual Tools**:

```bash
# Format code
black athf
isort athf

# Check formatting without changes
black athf --check
isort athf --check-only

# Lint code
flake8 athf

# Check security issues
bandit -r athf -c pyproject.toml

# Type check
mypy athf --ignore-missing-imports
```

### Code Quality Standards

When customizing ATHF for your team:

**Type Hints**: Maintain type annotations for better IDE support and catch errors early:

```python
def get_config_path() -> Path:
    """Get config file path."""
    return Path("config/.athfconfig.yaml")

def search_hunts(query: str) -> list[dict]:
    """Search hunts by query string."""
    results = []
    return results
```

The mypy configuration in `pyproject.toml` enforces:
- `disallow_untyped_defs = true` - All functions need type annotations
- `disallow_incomplete_defs = true` - Function signatures must be complete

**Testing**: Add tests for custom features you build. ATHF uses pytest:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_commands.py -v

# Run with coverage
pytest tests/ -v --cov=athf --cov-report=term-missing

# Run specific test
pytest tests/test_commands.py::TestInitCommand::test_init_creates_structure_non_interactive -v
```

Tests use Click's `CliRunner` to test actual CLI commands rather than mocks. See [tests/test_commands.py](../../../tests/test_commands.py) for examples.

**Documentation**: Keep your fork's documentation current:
- **AGENTS.md** - Update with your environment details, data sources, team context
- **environment.md** - Document your tech stack, tools, known gaps
- **Hunt files** - Use LOCK pattern consistently across all hunts
- **Custom features** - Document any custom commands or extensions you build

**Security**: Run bandit to check for security issues in custom code:

```bash
# Check all Python files
bandit -r athf -c pyproject.toml

# Check specific file
bandit athf/commands/hunt.py
```

### Testing Your Changes

Before committing significant customizations:

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Check types
mypy athf --ignore-missing-imports

# 3. Format code
black athf
isort athf

# 4. Check security
bandit -r athf -c pyproject.toml

# 5. Or run pre-commit on everything
pre-commit run --all-files
```

### Customization Examples

**Adding a Custom Command**:

```python
# athf/commands/custom.py
import click
from rich.console import Console

console = Console()

@click.command()
def mycustom() -> None:
    """My custom command."""
    console.print("[cyan]Running custom command![/cyan]")

# Register in athf/cli.py
from athf.commands import custom
cli.add_command(custom.mycustom)
```

**Extending Hunt Metadata**: Modify the hunt template in `athf/core/template_engine.py` to add custom fields:

```python
HUNT_TEMPLATE = """---
hunt_id: {{ hunt_id }}
title: {{ title }}
# Your custom fields
priority: {{ priority | default('medium') }}
owner_team: {{ owner_team | default('SOC') }}
---
```

**Custom Workflows**: ATHF's structure makes it easy to build custom workflows:

```bash
#!/bin/bash
# weekly-hunt-report.sh

# Get all completed hunts from last week
athf hunt list --status completed --output json | \
  jq '[.[] | select(.date >= "2025-11-29")]' | \
  athf stats
```

### CI/CD Integration

ATHF includes a GitHub Actions workflow ([.github/workflows/tests.yml](../../../.github/workflows/tests.yml)) that runs:

- Tests across Python 3.8-3.12 on Ubuntu, macOS, Windows
- Linting with flake8
- Type checking with mypy
- Hunt validation
- Package building

Customize the workflow for your organization's needs.

### Tools Configuration

All tools are configured in `pyproject.toml`:

- **Black**: Line length 127, targets Python 3.8-3.12
- **isort**: Black-compatible profile
- **mypy**: Strict type checking enabled
- **pytest**: Test discovery, coverage reporting
- **bandit**: Security checks with test exclusions

See [pyproject.toml](../../../pyproject.toml) for full configuration.

---

## Platform-Specific Instructions

### macOS

```bash
# Python 3 usually comes pre-installed on modern macOS
python3 --version

# If not installed, get it from homebrew
brew install python3

# Install ATHF
pip3 install agentic-threat-hunting-framework

# Add to PATH if needed (check installation output)
export PATH="$HOME/Library/Python/3.x/bin:$PATH"
```

Add the PATH export to your `~/.zshrc` or `~/.bash_profile` to make it permanent.

### Linux (Ubuntu/Debian)

```bash
# Install Python 3 and pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Install ATHF
pip3 install agentic-threat-hunting-framework

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"
```

Add the PATH export to your `~/.bashrc` to make it permanent.

### Windows

```powershell
# Download Python from python.org (ensure "Add to PATH" is checked)

# Verify installation
python --version

# Install ATHF
pip install agentic-threat-hunting-framework

# Verify
athf --version
```

If `athf` is not recognized, add Python Scripts to your PATH:
- `C:\Users\<YourUser>\AppData\Local\Programs\Python\Python3x\Scripts`

---

## Verifying Installation

After installation, verify everything works:

```bash
# Check version
athf --version

# Get help
athf --help

# List available commands
athf hunt --help

# Initialize a test workspace
mkdir athf-test
cd athf-test
athf init --non-interactive

# Create a test hunt
athf hunt new --technique T1003.001 --title "Test Hunt" --non-interactive

# List hunts
athf hunt list

# View statistics
athf hunt stats
```

If all commands work, you're ready to go!

---

## Troubleshooting

### "athf: command not found"

**Cause**: The Python scripts directory is not in your PATH.

**Solution**:

1. Find where pip installed the package:
   ```bash
   pip show agentic-threat-hunting-framework
   ```

2. The scripts are typically in:
   - **macOS**: `~/Library/Python/3.x/bin`
   - **Linux**: `~/.local/bin`
   - **Windows**: `%APPDATA%\Python\Python3x\Scripts`

3. Add to PATH:
   ```bash
   # macOS/Linux (add to ~/.zshrc or ~/.bashrc)
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"

   # Windows (use System Properties > Environment Variables)
   ```

4. Reload your shell or open a new terminal.

### "No module named 'athf'"

**Cause**: Package not installed or wrong Python environment.

**Solution**:

```bash
# Check if installed
pip list | grep athf

# If not listed, install it
pip install agentic-threat-hunting-framework

# Check which Python pip is using
pip --version

# Make sure it matches your Python
python --version
```

### "ERROR: Could not find a version that satisfies the requirement"

**Cause**: Python version too old (< 3.8).

**Solution**:

```bash
# Check Python version
python --version

# Upgrade Python to 3.8 or higher
# - macOS: brew install python3
# - Linux: sudo apt install python3.11
# - Windows: Download from python.org
```

### "Permission denied" errors

**Cause**: Installing globally without sudo (Linux/macOS).

**Solution** (choose one):

```bash
# Option 1: Install for current user only (recommended)
pip install --user agentic-threat-hunting-framework

# Option 2: Use a virtual environment (best practice)
python3 -m venv athf-env
source athf-env/bin/activate
pip install agentic-threat-hunting-framework

# Option 3: Install globally (not recommended)
sudo pip install agentic-threat-hunting-framework
```

### Import errors with dependencies

**Cause**: Dependency version conflicts.

**Solution**:

```bash
# Use a fresh virtual environment
python3 -m venv fresh-env
source fresh-env/bin/activate

# Install ATHF in the clean environment
pip install agentic-threat-hunting-framework

# Verify dependencies
pip list
```

### Windows: "python is not recognized"

**Cause**: Python not installed or not in PATH.

**Solution**:

1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation, **check "Add Python to PATH"**
3. Restart your terminal
4. Verify: `python --version`

---

## Upgrading ATHF

To upgrade to the latest version:

```bash
# Upgrade from PyPI
pip install --upgrade agentic-threat-hunting-framework

# Or from source
cd agentic-threat-hunting-framework
git pull
pip install --upgrade .

# Verify new version
athf --version
```

---

## Uninstalling ATHF

To remove ATHF:

```bash
# Uninstall the package
pip uninstall agentic-threat-hunting-framework

# Remove your workspace (optional - this deletes your hunts!)
# rm -rf /path/to/your/athf-workspace
```

Your hunt files are separate from the package installation, so uninstalling ATHF won't delete your hunts.

---

## Next Steps

After installation:

1. **Initialize your workspace**: `athf init`
2. **Read the getting started guide**: [getting-started.md](getting-started.md)
3. **Review the CLI reference**: [CLI_REFERENCE.md](CLI_REFERENCE.md)
4. **Create your first hunt**: `athf hunt new`
5. **Explore example hunts**: [../hunts/H-0001.md](../hunts/H-0001.md)

---

## Getting Help

- **CLI help**: `athf --help` or `athf <command> --help`
- **Documentation**: [getting-started.md](getting-started.md)
- **Issues**: [GitHub Issues](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)

---

## System Requirements

- **Python**: 3.8 or higher
- **OS**: macOS, Linux, or Windows
- **Disk Space**: ~5 MB for package, more for your hunt data
- **Memory**: Minimal (< 50 MB)
- **Dependencies**: 4 packages (click, pyyaml, rich, jinja2)
