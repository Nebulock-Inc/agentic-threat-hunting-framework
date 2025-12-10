<p align="center">
  <img src="assets/athf_logo.png" alt="ATHF Logo" width="400"/>
</p>

<h1 align="center">Agentic Threat Hunting Framework (ATHF)</h1>

[![PyPI version](https://badge.fury.io/py/athf-framework.svg)](https://badge.fury.io/py/athf-framework)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Nebulock-Inc/agentic-threat-hunting-framework?style=social)](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/stargazers)

**[Quick Start](#-quick-start)** • **[Installation](#installation)** • **[Documentation](#documentation)** • **[Examples](SHOWCASE.md)**

> Give your threat hunting program memory and agency.

The **Agentic Threat Hunting Framework (ATHF)** is the memory and automation layer for your threat hunting program. It gives your hunts structure, persistence, and context - making every past investigation accessible to both humans and AI.

ATHF works with any hunting methodology (PEAK, TaHiTI, or your own process). It's not a replacement; it's the layer that makes your existing process AI-ready.

## What is ATHF?

ATHF provides structure and persistence for threat hunting programs. It's a markdown-based framework that:

- Documents hunts using the LOCK pattern (Learn → Observe → Check → Keep)
- Maintains a searchable repository of past investigations
- Enables AI assistants to reference your environment and previous work
- Works with any SIEM/EDR platform

## The Problem

Most threat hunting programs lose valuable context once a hunt ends. Notes live in Slack or tickets, queries are written once and forgotten, and lessons learned exist only in analysts' heads.

Even AI tools start from zero every time without access to your environment, your data, or your past hunts.

ATHF changes that by giving your hunts structure, persistence, and context.

**Read more:** [docs/why-athf.md](docs/why-athf.md)

## The LOCK Pattern

Every threat hunt follows the same basic loop: **Learn → Observe → Check → Keep**.

![The LOCK Pattern](assets/athf_lock.png)

- **Learn:** Gather context from threat intel, alerts, or anomalies
- **Observe:** Form a hypothesis about adversary behavior
- **Check:** Test hypotheses with targeted queries
- **Keep:** Record findings and lessons learned

**Why LOCK?** It's small enough to use and strict enough for agents to interpret. By capturing every hunt in this format, ATHF makes it possible for AI assistants to recall prior work and suggest refined queries based on past results.

**Read more:** [docs/lock-pattern.md](docs/lock-pattern.md)

## The Five Levels of Agentic Hunting

ATHF defines a simple maturity model. Each level builds on the previous one.

**Most teams will live at Levels 1–2. Everything beyond that is optional maturity.**

![The Five Levels](assets/athf_fivelevels.png)

| Level | Capability | What You Get |
|-------|-----------|--------------|
| **0** | Ad-hoc | Hunts exist in Slack, tickets, or analyst notes |
| **1** | Documented | Persistent hunt records using LOCK |
| **2** | Searchable | AI reads and recalls your hunts |
| **3** | Generative | AI executes queries via MCP tools |
| **4** | Agentic | Autonomous agents monitor and act |

**Level 1:** Operational within a day
**Level 2:** Operational within a week
**Level 3:** 2-4 weeks (optional)
**Level 4:** 1-3 months (optional)

**Read more:** [docs/maturity-model.md](docs/maturity-model.md)

## 🚀 Quick Start

### Option 1: Python CLI (Recommended)

```bash
# Install via PyPI
pip install athf-framework

# Initialize your hunt program
athf init

# Create your first hunt
athf hunt new --technique T1003.001 --title "LSASS Credential Dumping"
```

**Or install from source:**

```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
pip install -e .
```

### Option 2: Pure Markdown (No Installation)

```bash
# Clone the repository
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework

# Copy a template and start documenting
cp templates/HUNT_LOCK.md hunts/H-0001.md

# Customize AGENTS.md with your environment
# Add your SIEM, EDR, and data sources
```

**Choose your AI assistant:** Claude Code, GitHub Copilot, or Cursor - any tool that can read your repository files.

**Full guide:** [docs/getting-started.md](docs/getting-started.md)

## 🔧 CLI Commands

ATHF includes a full-featured CLI for managing your hunts. Here's a quick reference:

### Initialize Workspace

```bash
athf init                           # Interactive setup
athf init --non-interactive         # Use defaults
```

### Create Hunts

```bash
athf hunt new                       # Interactive mode
athf hunt new \
  --technique T1003.001 \
  --title "LSASS Dumping Detection" \
  --platform windows
```

### List & Search

```bash
athf hunt list                      # Show all hunts
athf hunt list --status completed   # Filter by status
athf hunt list --output json        # JSON output
athf hunt search "kerberoasting"    # Full-text search
```

### Validate & Stats

```bash
athf hunt validate                  # Validate all hunts
athf hunt validate H-0001           # Validate specific hunt
athf hunt stats                     # Show statistics
athf hunt coverage                  # MITRE ATT&CK coverage
```

**Full documentation:** [CLI Reference](docs/CLI_REFERENCE.md)

> **Note:** The CLI is fully functional and ready to use. Install from source using `pip install -e .` in the repository directory. PyPI package publication coming soon.

## 📺 See It In Action

![ATHF Demo](assets/athf-cli-workflow.gif)

Watch ATHF in action: initialize a workspace, create hunts, and explore your threat hunting catalog in under 60 seconds.

**[View example hunts →](SHOWCASE.md)**

## Installation

### Prerequisites
- Python 3.8-3.13 (for CLI option)
- Git
- Your favorite AI code assistant

### CLI Installation

**Via PyPI (Recommended):**
```bash
pip install athf-framework
```

**From Source:**
```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
pip install -e .
```

### Markdown-Only Setup (No CLI)

```bash
git clone https://github.com/Nebulock-Inc/agentic-threat-hunting-framework
cd agentic-threat-hunting-framework
```

Start documenting hunts in the `hunts/` directory using the LOCK pattern.

## Documentation

### Core Concepts

- [Why ATHF Exists](docs/why-athf.md) - The problem and solution
- [The LOCK Pattern](docs/lock-pattern.md) - Structure for all hunts
- [Maturity Model](docs/maturity-model.md) - The five levels explained
- [Getting Started](docs/getting-started.md) - Step-by-step onboarding

### Level-Specific Guides

- [Level 1: Documented Hunts](docs/maturity-model.md#level-1-documented-hunts)
- [Level 2: Searchable Memory](docs/maturity-model.md#level-2-searchable-memory)
- [Level 3: Generative Capabilities](docs/level4-agentic-workflows.md)
- [Level 4: Agentic Workflows](docs/level4-agentic-workflows.md)

### Integration & Customization

- [Installation & Development](docs/INSTALL.md) - Setup, fork customization, testing
- [MCP Catalog](integrations/MCP_CATALOG.md) - Available tool integrations
- [Quickstart Guides](integrations/quickstart/) - Setup for specific tools
- [Using ATHF](USING_ATHF.md) - Adoption and customization

## 🎖️ Featured Hunts

### H-0001: macOS Information Stealer Detection

Detected Atomic Stealer collecting Safari cookies via AppleScript.
**Result:** 1 true positive, host isolated before exfiltration.

**Key Insight:** Behavior-based detection outperformed signature-based approaches. Process signature validation identified unsigned malware attempting data collection.

[View full hunt →](hunts/H-0001.md) | [See more examples →](SHOWCASE.md)

## Why This Matters

You might wonder how this interacts with frameworks like [PEAK](https://www.splunk.com/en_us/blog/security/peak-threat-hunting-framework.html). PEAK gives you a solid method for how to hunt. ATHF builds on that foundation by giving you structure, memory, and continuity. PEAK guides the work. ATHF ensures you capture the work, organize it, and reuse it across future hunts.

Agentic threat hunting is not about replacing analysts. It's about building systems that can:

- Remember what has been done before
- Learn from past successes and mistakes
- Support human judgment with contextual recall

When your framework has memory, you stop losing knowledge to turnover or forgotten notes. When your AI assistant can reference that memory, it becomes a force multiplier.

## 💬 Community & Support

- **GitHub Discussions:** [Ask questions, share hunts](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)
- **Issues:** [Report bugs or request features](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/issues)
- **Adoption Guide:** See [USING_ATHF.md](USING_ATHF.md) for how to use ATHF in your organization
- **LinkedIn:** [Nebulock Inc.](https://www.linkedin.com/company/nebulock-inc) - Follow for updates

## 📖 Using ATHF

ATHF is a framework to internalize, not a platform to extend. Fork it, customize it, make it yours.

**Repository:** [https://github.com/Nebulock-Inc/agentic-threat-hunting-framework](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework)

See [USING_ATHF.md](USING_ATHF.md) for adoption guidance. Your hunts stay yours—sharing back is optional but appreciated ([Discussions](https://github.com/Nebulock-Inc/agentic-threat-hunting-framework/discussions)).

The goal is to help every threat hunting team move from ad-hoc memory to structured, agentic capability.

---

## 🛠️ Development & Customization

ATHF is designed to be forked and customized for your organization.

**See [docs/INSTALL.md#development--customization](docs/INSTALL.md#development--customization) for:**
- Setting up your fork for development
- Pre-commit hooks for code quality
- Testing and type checking
- Customization examples
- CI/CD integration

Quick start:
```bash
pip install -e ".[dev]"       # Install dev dependencies
pre-commit install            # Set up quality checks
pytest tests/ -v              # Run tests
```

---

## 👤 Author

Created by **Sydney Marrone** © 2025

---

**Start small. Document one hunt. Add structure. Build memory.**

Memory is the multiplier. Agency is the force.
Once your program can remember, everything else becomes possible.

Happy hunting!
