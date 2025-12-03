# ATHF Installation Guide

This guide covers multiple installation methods for the Agentic Threat Hunting Framework (ATHF).

## Quick Start

The fastest way to get started:

```bash
pip install athf-framework
athf init
```

That's it! You're ready to start threat hunting.

---

## Installation Options

### Option 1: Install from PyPI (Recommended)

**Best for**: Most users who want a stable, production-ready installation.

```bash
# Install the latest stable release
pip install athf-framework

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
pip install athf-framework
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

**For development** (includes testing tools):

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=athf --cov-report=term-missing
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

## Platform-Specific Instructions

### macOS

```bash
# Python 3 usually comes pre-installed on modern macOS
python3 --version

# If not installed, get it from homebrew
brew install python3

# Install ATHF
pip3 install athf-framework

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
pip3 install athf-framework

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
pip install athf-framework

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

1. Find where pip installed athf:
   ```bash
   pip show athf-framework
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
pip install athf-framework

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
pip install --user athf-framework

# Option 2: Use a virtual environment (best practice)
python3 -m venv athf-env
source athf-env/bin/activate
pip install athf-framework

# Option 3: Install globally (not recommended)
sudo pip install athf-framework
```

### Import errors with dependencies

**Cause**: Dependency version conflicts.

**Solution**:

```bash
# Use a fresh virtual environment
python3 -m venv fresh-env
source fresh-env/bin/activate

# Install ATHF in the clean environment
pip install athf-framework

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
pip install --upgrade athf-framework

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
pip uninstall athf-framework

# Remove your workspace (optional - this deletes your hunts!)
# rm -rf /path/to/your/athf-workspace
```

Your hunt files are separate from the package installation, so uninstalling ATHF won't delete your hunts.

---

## Next Steps

After installation:

1. **Initialize your workspace**: `athf init`
2. **Read the getting started guide**: [docs/getting-started.md](docs/getting-started.md)
3. **Review the CLI reference**: [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)
4. **Create your first hunt**: `athf hunt new`
5. **Explore example hunts**: [hunts/H-0001.md](hunts/H-0001.md)

---

## Getting Help

- **CLI help**: `athf --help` or `athf <command> --help`
- **Documentation**: [docs/getting-started.md](docs/getting-started.md)
- **Issues**: [GitHub Issues](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)

---

## System Requirements

- **Python**: 3.8 or higher
- **OS**: macOS, Linux, or Windows
- **Disk Space**: ~5 MB for package, more for your hunt data
- **Memory**: Minimal (< 50 MB)
- **Dependencies**: 4 packages (click, pyyaml, rich, jinja2)
