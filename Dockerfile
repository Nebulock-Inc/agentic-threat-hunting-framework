# Agentic Threat Hunting Framework - Test Container
# Purpose: Clean isolated environment for testing ATHF CLI

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including GitHub CLI and AWS CLI
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    unzip \
    groff \
    less \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 with GPG signature verification.
# AWS CLI signing key fingerprint (per https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html#getting-started-install-verify):
#   FB5D B77F D5C1 18B8 0511  ADA8 A631 0ACC 4672 475C
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        AWSCLI_URL="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        AWSCLI_URL="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -fsSL "$AWSCLI_URL" -o awscliv2.zip && \
    curl -fsSL "$AWSCLI_URL.sig" -o awscliv2.sig && \
    gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys A6310ACC4672475C && \
    gpg --fingerprint --with-colons A6310ACC4672475C \
        | grep -q "fpr:::::::::FB5DB77FD5C118B80511ADA8A6310ACC4672475C:" && \
    gpg --verify awscliv2.sig awscliv2.zip && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip awscliv2.sig

# Note: Claude Code CLI can be installed manually inside container
# See DOCKER.md for instructions

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Copy source code
COPY athf/ ./athf/

# Install ATHF in editable mode with all optional dependencies
# This includes:
# - Core dependencies (click, pyyaml, rich, jinja2)
# - Similarity search (scikit-learn)
# - Splunk integration (requests)
RUN pip install --no-cache-dir -e ".[similarity,splunk]"

# Create non-root container user
RUN useradd -m -s /bin/bash athf

# Create a workspace directory for testing
RUN mkdir -p /workspace && chown athf:athf /workspace

# Set workspace as default directory
WORKDIR /workspace

# Drop privileges for runtime
USER athf:athf

# Default command: drop into bash shell
CMD ["/bin/bash"]
