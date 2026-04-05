#!/usr/bin/env bash
# install.sh — Bootstrap the Claude Skills library on macOS / Linux
# Run: bash install.sh

set -euo pipefail

REPO_URL="https://VitaliiRibii@dev.azure.com/VitaliiRibii/claude-skills/_git/claude-skills"
INSTALL_DIR="$HOME/claude-skills"

# Detect OS
OS="$(uname -s)"

step()  { echo -e "\n  \033[36m▸ $*\033[0m"; }
ok()    { echo -e "  \033[32m✓\033[0m $*"; }
fail()  { echo -e "  \033[31m✗\033[0m $*"; exit 1; }
warn()  { echo -e "  \033[33m⚠\033[0m $*"; }

echo -e "\n\033[36m==================================================\033[0m"
echo -e "\033[36m  Claude Skills — Bootstrap (${OS})\033[0m"
echo -e "\033[36m==================================================\033[0m"

# ── 1. Check Python 3 ─────────────────────────────────────────────────────────
step "Checking Python 3..."
if ! command -v python3 &>/dev/null; then
    if [[ "$OS" == "Darwin" ]]; then
        fail "Python 3 not found.\n  Install with: brew install python3\n  Or: https://www.python.org/downloads/"
    else
        fail "Python 3 not found.\n  Install with: sudo apt install python3 python3-pip"
    fi
fi
PY_VERSION="$(python3 --version)"
ok "$PY_VERSION"

# ── 2. Check Git ──────────────────────────────────────────────────────────────
step "Checking Git..."
if ! command -v git &>/dev/null; then
    if [[ "$OS" == "Darwin" ]]; then
        fail "Git not found.\n  Install with: brew install git"
    else
        fail "Git not found.\n  Install with: sudo apt install git"
    fi
fi
GIT_VERSION="$(git --version)"
ok "$GIT_VERSION"

# ── 3. Clone or update the repo ───────────────────────────────────────────────
step "Setting up repository at $INSTALL_DIR..."

if [[ -d "$INSTALL_DIR/.git" ]]; then
    warn "Repository exists — pulling latest..."
    git -C "$INSTALL_DIR" pull --quiet
    ok "Repository updated"
elif [[ -d "$INSTALL_DIR" ]]; then
    fail "Directory exists but is not a git repo: $INSTALL_DIR\n  Remove it and retry."
else
    warn "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR" --quiet
    ok "Repository cloned to $INSTALL_DIR"
fi

# ── 4. Install Python dependencies ────────────────────────────────────────────
step "Installing Python dependencies..."
python3 -m pip install packaging pyyaml --quiet
ok "packaging, pyyaml installed"

# ── 5. Install agent-orchestrator ─────────────────────────────────────────────
step "Installing agent-orchestrator skill (and all dependencies)..."
cd "$INSTALL_DIR"
python3 skillman.py install agent-orchestrator

# ── Done ──────────────────────────────────────────────────────────────────────
echo -e "\n\033[32m==================================================\033[0m"
echo -e "\033[32m  Installation complete!\033[0m"
echo -e "\033[32m==================================================\033[0m"
echo ""
echo -e "  Location:  \033[1m$INSTALL_DIR\033[0m"
echo ""
echo -e "  To use the skill, open Claude Code and say:"
echo -e "    \033[33m'Avengers assemble'\033[0m"
echo ""
echo -e "  To update later:"
echo -e "    \033[33mcd $INSTALL_DIR && python3 skillman.py update\033[0m"
echo ""
