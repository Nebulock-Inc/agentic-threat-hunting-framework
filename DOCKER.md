# Docker Testing Environment

This document describes how to use Docker to test ATHF CLI in a clean, isolated environment.

## Quick Start

### Option 1: Using docker-compose (Recommended)

```bash
# Build and start container
docker-compose up -d

# Enter container shell
docker-compose exec athf-test bash

# Inside container: verify ATHF is installed
athf --version

# Initialize a test workspace
athf init

# Test CLI commands
athf hunt list
athf similar "test"
```

### Option 2: Using docker directly

```bash
# Build image
docker build -t athf:test .

# Run container interactively
docker run -it --rm athf:test

# Inside container: test CLI
athf --version
athf init
```

## What's Included

The container includes:
- Python 3.11 (slim)
- ATHF CLI installed in editable mode
- All optional dependencies:
  - scikit-learn (for similarity search)
  - requests (for Splunk integration)
- Git (for version control)
- GitHub CLI (`gh`) - for repository operations
- AWS CLI v2 - for AWS Bedrock access (optional LLM provider)
- Clean `/workspace` directory for testing
- **Optional:** Claude Code CLI can be installed manually (see below)

## Workspace Persistence

When using docker-compose, the `/workspace` directory is persisted in a named volume (`athf-workspace`). This means:
- Hunt files, investigations, and config survive container restarts
- You can safely stop/start the container without losing work

To reset workspace:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Start fresh
```

## Live Code Changes

The docker-compose.yml mounts the current directory into `/app`, so changes to ATHF source code on your host are reflected in the container. However, you'll need to reinstall for changes to take effect:

```bash
# Inside container
pip install -e ".[similarity,splunk]"
```

## LLM Provider Configuration (For ATHF Agents)

ATHF agents auto-detect your LLM provider from environment variables. You can use **any** supported provider — no single provider is required.

### Supported Providers

| Provider | Required Env Var | Install Extra |
|----------|-----------------|---------------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | `pip install 'athf[anthropic]'` |
| OpenAI (GPT) | `OPENAI_API_KEY` | `pip install 'athf[openai]'` |
| AWS Bedrock | `AWS_PROFILE` or `AWS_ACCESS_KEY_ID` | `pip install 'athf[bedrock]'` |
| Ollama (local) | `OLLAMA_HOST` (default: localhost:11434) | `pip install 'athf[ollama]'` |
| Any via LiteLLM | varies | `pip install 'athf[litellm]'` |

### Quick Setup

Export your provider's API key in the shell (avoid placing secrets directly on the command line — they leak into shell history and `ps` output) before starting the container. Prefer a gitignored `.env` file or `read -s`:

```bash
# Option A: Anthropic
read -rs ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
docker-compose up -d

# Option B: OpenAI
read -rs OPENAI_API_KEY && export OPENAI_API_KEY
docker-compose up -d

# Option C: AWS Bedrock (mount AWS credentials, no secret on the command line)
AWS_PROFILE=my-sso-profile docker-compose up -d

# Option D: Local Ollama (connect to host)
OLLAMA_HOST=http://host.docker.internal:11434 docker-compose up -d
```

### Using ATHF Agents

Once a provider is configured, ATHF agents auto-detect it:

```bash
# Inside container:
athf agent run hypothesis-generator --threat-intel "APT29 credential theft"
athf agent run hunt-researcher --topic "Kerberoasting"
athf research new --topic "LSASS dumping"
```

### Override Provider

To explicitly set a provider instead of auto-detection:

```bash
# In docker-compose.yml environment or shell:
ATHF_LLM_PROVIDER=openai
ATHF_LLM_MODEL=gpt-4o
```

### AWS SSO Configuration (For Bedrock Provider)

If using AWS Bedrock as your LLM provider, the container mounts your `~/.aws` directory for SSO authentication.

**Security Note:** The mount is read-write (not read-only) because AWS CLI needs to write cache files to `~/.aws/cli/cache/`.

**Setup:**
```bash
# 1. Authenticate on your host
aws sso login --profile <your-profile>

# 2. Start container with your AWS profile
AWS_PROFILE=my-sso-profile docker-compose up -d

# 3. Verify credentials inside container
docker-compose exec athf-test bash -c 'aws sts get-caller-identity'
```

**Credential Refresh:** AWS SSO sessions expire (typically after 1-12 hours). Re-authenticate on the host with `aws sso login` — no container restart needed.

### Troubleshooting

**"Unable to locate credentials" (Bedrock):**
```bash
# On host: verify SSO session is active
aws sts get-caller-identity --profile <your-profile>

# If expired, re-authenticate
aws sso login --profile <your-profile>
```

**"No LLM provider detected":**
- Ensure at least one provider API key is set in environment
- Check with: `docker-compose exec athf-test env | grep -E 'ANTHROPIC|OPENAI|AWS_PROFILE|OLLAMA'`
- Without an LLM provider, the provider factory raises a `RuntimeError` at agent init — agents do not fall back to template output. Set one of: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `AWS_PROFILE`/`AWS_ACCESS_KEY_ID`, or set `ATHF_LLM_PROVIDER` explicitly.

## Claude Code CLI with AWS Bedrock (Optional - Manual Install)

Claude Code CLI is NOT pre-installed in the container to keep builds fast. You can install it manually inside the container when needed.

**Official Documentation:** https://code.claude.com/docs/en/amazon-bedrock

**Why manual install?**
- Faster container builds (avoids Node.js installation during build)
- Installs only when needed
- Configuration is already set up for Bedrock

### Prerequisites

Before installing Claude Code:

**1. Ensure AWS SSO is authenticated (on your host):**
```bash
aws sso login --profile your-profile
```

**2. Start container with your AWS profile:**
```bash
AWS_PROFILE=your-profile docker-compose up -d
docker-compose exec athf-test bash
```

### Installation Steps

The runtime user (`athf`) is non-root, so Node.js must be installed as root via a separate exec, then Claude Code is installed globally from the normal non-root shell:

```bash
# 1. Install Node.js 20.x as root from the host:
docker-compose exec --user root athf-test bash -lc \
  'curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs'

# 2. Drop into the normal non-root shell:
docker-compose exec athf-test bash

# 3. Install Claude Code CLI globally (npm uses the user prefix):
npm install -g @anthropic-ai/claude-code

# 4. Verify installation
claude --version

# 5. Test with Bedrock (should work immediately - no login needed)
claude chat "Hello, can you access Bedrock?"
```

### How It Works

The container is pre-configured for Bedrock authentication:

**Environment Variables (already set in docker-compose.yml):**
- `CLAUDE_CODE_USE_BEDROCK=1` - Enables Bedrock integration
- `AWS_REGION=us-east-1` - Required region setting
- `AWS_PROFILE` - Your SSO profile (set when starting container)

**Volume Mounts (already configured):**
- `~/.aws:/home/athf/.aws` - AWS credentials (SSO)
- `claude-config:/home/athf/.claude` - Claude settings **isolated from your macOS Claude**

**Your macOS Claude settings are NOT shared with the container.** The container uses its own isolated config volume.

### Using Claude Code

Once installed, Claude Code works with Bedrock authentication:

```bash
# Interactive session
claude

# Chat mode
claude chat "Help me write a threat hunting hypothesis"

# Code mode
claude code "Review this Python function"
```

**Note:** `/login` and `/logout` commands are disabled when using Bedrock - authentication is handled through AWS credentials.

### Default Models

Claude Code uses these Bedrock models by default:
- **Primary:** `global.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Small/Fast:** `us.anthropic.claude-haiku-4-5-20251001-v1:0`

To customize models, add to docker-compose.yml environment section:
```yaml
- ANTHROPIC_MODEL=global.anthropic.claude-sonnet-4-5-20250929-v1:0
- ANTHROPIC_SMALL_FAST_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0
```

### Alternative Access Methods (No Installation Needed)

If you don't want to install Claude Code, you can use:

**1. ATHF Agents (auto-detects your LLM provider, already installed):**
```bash
athf agent run hypothesis-generator --threat-intel "APT29"
athf research new --topic "Kerberoasting"
```

**2. AWS CLI (direct Bedrock API, already installed):**
```bash
aws bedrock-runtime invoke-model \
    --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
    --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}' \
    --region us-east-1 output.json
```

### Persistence

Claude Code installation and settings persist between container restarts via:
- Node.js packages: Stored in container filesystem (survives normal restarts)
- Claude settings: Stored in `claude-config` Docker volume (survives restarts)

**To reset Claude settings:**
```bash
# On host:
docker-compose down
docker volume rm agentic-threat-hunting-framework_claude-config
docker-compose up -d
```

**To reinstall Claude after container rebuild:**
```bash
# Rebuild loses Node.js/Claude Code - just reinstall:
docker-compose exec athf-test bash
# Run installation steps again (see above)
```

### Troubleshooting

**Claude asks for login despite Bedrock config:**
- Verify environment: `docker-compose exec athf-test env | grep CLAUDE`
- Should see: `CLAUDE_CODE_USE_BEDROCK=1`
- Verify AWS credentials: `aws sts get-caller-identity`

**"Unable to authenticate" or "Access denied":**
```bash
# On host: verify AWS SSO session is active
aws sts get-caller-identity --profile your-profile

# If expired, re-authenticate
aws sso login --profile your-profile

# Restart container (no rebuild needed)
docker-compose down
AWS_PROFILE=your-profile docker-compose up -d
```

**"Bedrock access denied":**
- Verify IAM permissions: `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`
- Check Claude model availability in your region: `aws bedrock list-inference-profiles --region us-east-1`
- Try different region: `AWS_REGION=us-west-2 docker-compose up -d`

**"claude: command not found" after installation:**
```bash
# Verify Node.js installed:
node --version

# Verify npm installed:
npm --version

# Reinstall Claude Code:
npm install -g @anthropic-ai/claude-code

# Check PATH:
echo $PATH
```

## Common Use Cases

### Test CLI Installation
```bash
docker-compose run athf-test athf --version
```

### Test Hunt Workflow
```bash
docker-compose exec athf-test bash
# Inside container:
athf init
athf hunt new --title "Test Hunt" --technique T1003 --non-interactive
athf hunt list
```

### Test Similarity Search
```bash
docker-compose exec athf-test bash
# Inside container:
athf init
# Create a few hunts
athf similar "credential access"
```

### Clone External Hunt Repositories
```bash
docker-compose exec athf-test bash
# Inside container:
# Using GitHub CLI (gh)
gh repo clone <org>/<your-hunt-repo>

# Or using git directly
git clone https://github.com/<org>/<your-hunt-repo>.git
```

### Clean Rebuild
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

**Container won't start:**
- Ensure Docker daemon is running
- Check logs: `docker-compose logs athf-test`

**CLI commands not found:**
- Verify installation: `pip list | grep agentic`
- Reinstall: `pip install -e ".[similarity,splunk]"`

**Permission errors:**
- The container runs as the unprivileged `athf` user
- Workspace is isolated in container filesystem

## Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove container and volumes (full cleanup)
docker-compose down -v

# Remove image
docker rmi athf:test
```
