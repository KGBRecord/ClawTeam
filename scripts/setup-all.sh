#!/usr/bin/env bash
set -euo pipefail

# ─── Colors ──────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { printf "${GREEN}[OK]${NC}    %s\n" "$*"; }
warn() { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
info() { printf "${CYAN}[INFO]${NC}  %s\n" "$*"; }
fail() { printf "${RED}[FAIL]${NC}  %s\n" "$*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

printf "${CYAN}
  ╔══════════════════════════════════════════╗
  ║  ClawTeam-OpenClaw — Quick Setup         ║
  ╚══════════════════════════════════════════╝
${NC}\n"

# ─── 1. Check Python ────────────────────────────────────────────────────
info "Checking Python..."
if ! command -v python3 &>/dev/null; then
    fail "python3 not found. Install: brew install python@3.12"
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [[ "$PY_MAJOR" -lt 3 ]] || { [[ "$PY_MAJOR" -eq 3 ]] && [[ "$PY_MINOR" -lt 10 ]]; }; then
    fail "Python 3.10+ required (found $PY_VER)"
fi
ok "Python $PY_VER"

# ─── 2. Check tmux ──────────────────────────────────────────────────────
info "Checking tmux..."
if ! command -v tmux &>/dev/null; then
    fail "tmux not found. Install: brew install tmux"
fi
ok "tmux $(tmux -V | awk '{print $2}')"

# ─── 2b. Check Node.js & npx ────────────────────────────────────────────
info "Checking Node.js & npx..."
if ! command -v node &>/dev/null || ! command -v npx &>/dev/null; then
    warn "Node.js or npx not found. Attempting to install via NVM..."
    export NVM_DIR="$HOME/.nvm"
    if [ ! -s "$NVM_DIR/nvm.sh" ]; then
        info "Installing NVM..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    fi
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    
    if command -v nvm &>/dev/null; then
        info "Installing Node.js 20 LTS..."
        nvm install 20
        nvm use 20
        nvm alias default 20
        ok "Node.js $(node -v) and npx installed via NVM"
    else
        fail "Failed to install NVM. Please install Node.js manually."
    fi
else
    ok "Node.js $(node -v) and npx ready"
fi

# ─── 3. Create venv ─────────────────────────────────────────────────────
info "Setting up virtual environment..."
if [[ ! -d "$REPO_ROOT/.venv" ]]; then
    python3 -m venv "$REPO_ROOT/.venv"
    ok "Created .venv"
else
    ok ".venv already exists"
fi
source "$REPO_ROOT/.venv/bin/activate"
ok "Activated .venv"

# ─── 4. Install ClawTeam ────────────────────────────────────────────────
info "Installing ClawTeam (editable)..."
pip install -e "$REPO_ROOT" --quiet 2>&1 | tail -3
ok "ClawTeam installed"

# ─── 5. Symlink ~/bin/clawteam ──────────────────────────────────────────
info "Setting up ~/bin/clawteam symlink..."
mkdir -p "$HOME/bin"
CT_BIN="$(which clawteam 2>/dev/null || echo "")"
if [[ -z "$CT_BIN" ]]; then
    fail "clawteam binary not found after install"
fi
ln -sf "$CT_BIN" "$HOME/bin/clawteam"
ok "~/bin/clawteam → $CT_BIN"

# ─── 6. Ensure ~/bin in PATH ────────────────────────────────────────────
info "Checking PATH..."
if echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/bin"; then
    ok "~/bin is in PATH"
else
    warn "~/bin is NOT in PATH. Adding to ~/.zshrc..."
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
    export PATH="$HOME/bin:$PATH"
    ok "Added to ~/.zshrc (run 'source ~/.zshrc' to apply)"
fi

# ─── 7. ClawTeam config ─────────────────────────────────────────────────
info "Setting up ClawTeam config..."
CLAWTEAM_DIR="$HOME/.clawteam"
mkdir -p "$CLAWTEAM_DIR"

if [[ ! -f "$CLAWTEAM_DIR/config.json" ]]; then
    cp "$REPO_ROOT/docs/sample-config.json" "$CLAWTEAM_DIR/config.json"
    ok "Config created at ~/.clawteam/config.json"
else
    ok "Config already exists at ~/.clawteam/config.json"
fi

# ─── 7b. BMAD Bridge config ─────────────────────────────────────────────
info "Setting up BMAD Bridge config..."
if [[ ! -f "$REPO_ROOT/config.json" ]]; then
    cp "$REPO_ROOT/config.example.json" "$REPO_ROOT/config.json"
    warn "BMAD Bridge config created at root config.json. PLEASE UPDATE IT WITH YOUR API KEYS."
else
    ok "BMAD Bridge config already exists at root config.json"
fi

# ─── 8. OpenClaw skill ──────────────────────────────────────────────────
info "Setting up OpenClaw skill..."
OC_SKILL_DIR="$HOME/.openclaw/workspace/skills/clawteam"
OC_SKILL_SRC="$REPO_ROOT/skills/openclaw/SKILL.md"

if [[ -f "$OC_SKILL_SRC" ]]; then
    mkdir -p "$OC_SKILL_DIR"
    cp "$OC_SKILL_SRC" "$OC_SKILL_DIR/SKILL.md"
    ok "OpenClaw skill installed at $OC_SKILL_DIR/SKILL.md"
else
    warn "OpenClaw skill source not found at $OC_SKILL_SRC"
fi

# ─── 9. OpenClaw exec-approvals ─────────────────────────────────────────
info "Configuring OpenClaw exec approvals..."
APPROVALS="$HOME/.openclaw/exec-approvals.json"
if [[ -f "$APPROVALS" ]]; then
    python3 -c "
import json
with open('$APPROVALS') as f:
    d = json.load(f)
d.setdefault('defaults', {})['security'] = 'allowlist'
with open('$APPROVALS', 'w') as f:
    json.dump(d, f, indent=2)
" 2>/dev/null && ok "exec-approvals: security = allowlist" || warn "Could not update exec-approvals"

    if command -v openclaw &>/dev/null; then
        openclaw approvals allowlist add --agent "*" "*/clawteam" &>/dev/null 2>&1 && \
            ok "clawteam added to allowlist" || \
            warn "Could not add to allowlist (gateway may not be running)"
    fi
else
    warn "exec-approvals.json not found — run 'openclaw' once first, then re-run"
fi

# ─── 10. Claude Code skill ──────────────────────────────────────────────
info "Setting up Claude Code skill..."
CC_SKILL_DIR="$REPO_ROOT/.claude/skills/clawteam"
CC_SKILL_SRC_DIR="$REPO_ROOT/skills/clawteam"

if [[ -d "$CC_SKILL_SRC_DIR" ]]; then
    mkdir -p "$CC_SKILL_DIR"
    cp "$CC_SKILL_SRC_DIR/SKILL.md" "$CC_SKILL_DIR/SKILL.md"
    if [[ -d "$CC_SKILL_SRC_DIR/references" ]]; then
        cp -r "$CC_SKILL_SRC_DIR/references" "$CC_SKILL_DIR/references"
    fi
    ok "Claude Code skill installed at $CC_SKILL_DIR/"
else
    warn "Claude Code skill source not found"
fi

# Copy CLAUDE.md to repo root
if [[ -f "$REPO_ROOT/docs/CLAUDE.md" ]]; then
    cp "$REPO_ROOT/docs/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"
    ok "CLAUDE.md copied to repo root"
fi

# ─── 11. Verify ─────────────────────────────────────────────────────────
info "Verifying installation..."
CT_VERSION=$("$HOME/bin/clawteam" --version 2>&1 || echo "failed")
if [[ "$CT_VERSION" == *"0.2.0"* ]] || [[ "$CT_VERSION" == *"clawteam"* ]]; then
    ok "clawteam --version: $CT_VERSION"
else
    warn "clawteam --version returned: $CT_VERSION"
fi

# ─── Done ────────────────────────────────────────────────────────────────
printf "\n${GREEN}"
cat << 'MSG'
  ╔══════════════════════════════════════════════════╗
  ║  ✅ Setup complete! ClawTeam is ready to use.    ║
  ╚══════════════════════════════════════════════════╝
MSG
printf "${NC}\n"

echo "Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. clawteam config health"
echo "  3. clawteam team spawn-team demo -d 'test' -n leader"
echo ""
