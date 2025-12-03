#!/bin/bash
# ATHF Demo Recording Script
# This script demonstrates the ATHF CLI in action

# Configuration
DEMO_DIR="$HOME/athf-demo-recording"
ATHF_BIN="/Users/sydney/Library/Python/3.9/bin/athf"

# Function to pause between commands
pause() {
    sleep ${1:-2}
}

echo "Setting up demo environment..."
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

# Clear screen for clean recording
clear

# ====================
# DEMO SCRIPT START
# ====================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ATHF - Agentic Threat Hunting Framework"
echo "  Demo: From Zero to Hunting in 60 Seconds"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pause 2

# 1. Show version
echo "\$ athf --version"
$ATHF_BIN --version
pause 2

# 2. Initialize workspace
echo ""
echo "\$ athf init --non-interactive"
$ATHF_BIN init --non-interactive
pause 3

# 3. Show what was created
echo ""
echo "\$ ls -la"
ls -la
pause 2

# 4. Create first hunt
echo ""
echo "\$ athf hunt new --technique T1003.001 --title \"LSASS Dumping Detection\" --platform windows --non-interactive"
$ATHF_BIN hunt new --technique T1003.001 --title "LSASS Dumping Detection" --platform windows --non-interactive
pause 3

# 5. Create second hunt
echo ""
echo "\$ athf hunt new --technique T1558.003 --title \"Kerberoasting Detection\" --tactic credential-access --non-interactive"
$ATHF_BIN hunt new --technique T1558.003 --title "Kerberoasting Detection" --tactic credential-access --non-interactive
pause 3

# 6. List hunts
echo ""
echo "\$ athf hunt list"
$ATHF_BIN hunt list
pause 4

# 7. Validate hunts
echo ""
echo "\$ athf hunt validate"
$ATHF_BIN hunt validate
pause 3

# 8. Show stats
echo ""
echo "\$ athf hunt stats"
$ATHF_BIN hunt stats
pause 3

# Final message
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎯 Ready to hunt!"
echo "  github.com/Nebulock-Inc/agentic-threat-hunting-framework"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pause 2
