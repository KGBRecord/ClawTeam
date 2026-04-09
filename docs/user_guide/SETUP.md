# 🦞 ClawTeam-OpenClaw — End-to-End Setup Guide

> This guide is intended for **macOS** (tested on a machine with Python 3.11, tmux 3.6a, openclaw, claude).

---

## Step 1: Clone the repository (if you haven't already)

```bash
git clone https://github.com/win4r/ClawTeam-OpenClaw.git
cd ClawTeam-OpenClaw
```

---

## Step 1.5: Automated Setup & Node.js (Recommended)

We provide an automated setup script that handles everything from A to Z. This script will automatically create the `.venv`, install `clawteam`, and importantly, **install Node.js/npx (via NVM)** which is highly recommended and required for the BMAD Bridge feature.

```bash
bash scripts/setup-all.sh
```

If the script runs successfully (✅ Setup complete!), you can **skip steps 2 through 6** and go straight to **Step 7**. If you prefer to install things manually, please follow the steps below.

*(Note for manual installation: You must install Node.js v20+ yourself to use the BMAD ecosystem).*

---

## Step 2: Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Every time you open a new terminal**, you must run `source .venv/bin/activate` before using `clawteam`.
> Alternatively, you can add an alias to your `~/.zshrc` (see Step 10).

---

## Step 3: Install dependencies

```bash
# Install ClawTeam + all dependencies (editable mode)
pip install -e .

# (Optional) Dev tools — pytest, ruff
pip install -e ".[dev]"

# (Optional) P2P transport — ZeroMQ
pip install -e ".[p2p]"
```

> ⚠️ **DO NOT** use `pip install clawteam` — that is the upstream PyPI package, which lacks the OpenClaw integration.
> ⚠️ **DO NOT** use `npm install -g clawteam` — that is a counterfeit npm package.

---

## Step 4: Create a symlink to make `clawteam` globally accessible

Spawned agents run in a fresh shell which might not see the virtual environment. A symlink solves this:

```bash
mkdir -p ~/bin
ln -sf "$(which clawteam)" ~/bin/clawteam
```

---

## Step 5: Add `~/bin` to PATH

Append the following line to the **end of your** `~/.zshrc` file:

```bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## Step 6: Verify basic installation

```bash
clawteam --version
# → clawteam v0.2.0+openclaw1

clawteam config health
# → Shows data dir, writable: yes, latency
```

If both commands succeed, ClawTeam is ready. The next steps cover **advanced configuration**.

---

## Step 7: Configure ClawTeam

```bash
# Set your username (used for multi-user setups)
clawteam config set user hanhvs

# (Optional) Set the default model for agents
clawteam config set default_model sonnet-4.6

# View all configuration settings
clawteam config show
```

The configuration file is stored at `~/.clawteam/config.json`. You can also configure ClawTeam via environment variables - see the table below.

### Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `CLAWTEAM_DATA_DIR` | `~/.clawteam` | Directory to store state |
| `CLAWTEAM_USER` | (empty) | Username |
| `CLAWTEAM_TRANSPORT` | `file` | `file` or `p2p` |
| `CLAWTEAM_WORKSPACE` | `auto` | `auto` / `always` / `never` |
| `CLAWTEAM_DEFAULT_BACKEND` | `tmux` | `tmux` / `subprocess` |
| `CLAWTEAM_DEFAULT_MODEL` | (empty) | Default language model |

---

## Step 7.5: Configure BMAD Bridge

If you plan to use the automated `BMAD` integration, the bridge engine requires API keys to parse specification documents.

Look for a `config.json` file in the root directory. If you used the `setup-all.sh/bat` script, it was already copied from `config.example.json`. If not, copy it manually:

```bash
cp config.example.json config.json
```

Then, open `config.json` and insert your Anthropic or OpenAI API keys:

```json
{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-latest",
  "api_key": "sk-ant-...",
}
```

> **Note:** If you leave `api_key` blank here, the bridge will strictly attempt to read from your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variables.

---

## Step 8: Setup OpenClaw integration

### 8a. Copy the skill file

The skill file teaches OpenClaw agents how to use `clawteam` commands:

```bash
mkdir -p ~/.openclaw/workspace/skills/clawteam
cp skills/openclaw/SKILL.md ~/.openclaw/workspace/skills/clawteam/SKILL.md
```

Verify it:

```bash
openclaw skills list 2>/dev/null | grep clawteam
```

### 8b. Configure exec-approvals (REQUIRED)

#### Why is this necessary?

When `clawteam spawn` creates worker agents, each worker runs in an **isolated shell** (tmux window). 
The worker needs to invoke `clawteam` commands to update tasks, send messages, and report status.

If OpenClaw is in `security: full` mode (the default), **every single shell command** is blocked and requires manual confirmation. This causes the agents to get stuck and prevents autonomy.

**Solution**: switch to `allowlist` mode and add `clawteam` to the list of permitted commands.

#### Step 8b.1: Check current status

```bash
openclaw approvals get
```

You should see an output similar to this:

```
┌───────────┬──────────────────────────────────────────────┐
│ Exists    │ no                                           │  ← File does not exist yet
│ Agents    │ 0                                            │
│ Allowlist │ 0                                            │  ← No rules yet
└───────────┴──────────────────────────────────────────────┘
```

#### Step 8b.2: Add `clawteam` to the allowlist

Add a pattern allowing **all agents** (wildcard `*`) to invoke `clawteam`:

```bash
# Allow the clawteam binary (regardless of the specific path)
openclaw approvals allowlist add --agent "*" "*/clawteam"
```

> **Explanation**:
> - `--agent "*"` = applies to all agents (not just a specific one)
> - `"*/clawteam"` = glob pattern, matching any path ending with `/clawteam`
>   (e.g., `/Users/hanhvs/bin/clawteam`, `/opt/homebrew/bin/clawteam`...)

#### Step 8b.3: (Recommended) Allow other common tools

Spawned agents often need to invoke `git`, `python3`, and `tmux`:

```bash
# Git — agents need git for worktree operations
openclaw approvals allowlist add --agent "*" "*/git"

# Python — for scripts running tests
openclaw approvals allowlist add --agent "*" "*/python3"

# tmux — session management
openclaw approvals allowlist add --agent "*" "*/tmux"
```

#### Step 8b.4: Create exec-approvals.json (if you need to set the security mode manually)

If `openclaw approvals get` showed `Exists: no`, you must create the config file:

```bash
mkdir -p ~/.openclaw
cat << 'EOF' > ~/.openclaw/exec-approvals.json
{
  "version": 1,
  "defaults": {
    "security": "allowlist"
  },
  "agents": {}
}
EOF
```

> **Understanding security modes**:
> | Mode | Behavior | When to use |
> |---|---|---|
> | `full` | All shell commands are blocked and must be manually approved | Secure local development |
> | `allowlist` | Only commands in the list are allowed, the rest are blocked | **ClawTeam requires this mode** |
> | `none` | Allow all commands (dangerous) | Only use for testing |

#### Step 8b.5: Verify

```bash
openclaw approvals get
```

Expected output:

```
┌───────────┬──────────────────────────────────────────────┐
│ Exists    │ yes                                          │
│ Allowlist │ 1  (or more)                                 │
└───────────┴──────────────────────────────────────────────┘

Allowlist:
  agent=*  */clawteam
  agent=*  */git          (if added)
  agent=*  */python3      (if added)
  agent=*  */tmux         (if added)
```

#### What happens if you skip this step?

When you spawn an agent, you will see this in the tmux window:

```
⚠️  openclaw wants to execute: clawteam task list my-team --owner worker1
   Allow? [y/N]
```

The agent will be stuck here and **will never run autonomously**. You would have to switch to every single tmux window and press `y` for every command — an impossible task in a multi-agent system.

---

## Step 9: Setup Claude Code integration

### 9a. Copy CLAUDE.md to the project root

Claude Code reads the `CLAUDE.md` file in the repository root to learn how to interact with ClawTeam. This file is already provided in the `docs/CLAUDE.md` directory:

```bash
cp docs/CLAUDE.md ./CLAUDE.md
```

> **Note**: The `CLAUDE.md` file only needs to be in the repository where you want Claude Code to use ClawTeam. It does **not** affect your entire system.

### 9b. Copy the skill for Claude Code

Claude Code reads skills from the `.claude/skills/` directory in the project:

```bash
mkdir -p .claude/skills/clawteam
cp skills/clawteam/SKILL.md .claude/skills/clawteam/SKILL.md
cp -r skills/clawteam/references .claude/skills/clawteam/references
```

---

## Step 10: Handy Aliases (Optional)

Add the following to your `~/.zshrc`:

```bash
cat << 'EOF' >> ~/.zshrc

# ── ClawTeam shortcuts ──────────────────────────────────────
alias ct="clawteam"
alias ct-teams="clawteam team discover"
alias ct-board="clawteam board show"
alias ct-live="clawteam board live"
alias ct-health="clawteam config health"

# Quickly activate the ClawTeam venv when navigating into the repo
ct-activate() {
  source ~/Projects/ClawTeam-OpenClaw/.venv/bin/activate
}
EOF

source ~/.zshrc
```

---

## ✅ Checklist — Ensure everything is OK

Run these commands one by one, ensuring each succeeds:

```bash
# 1. Python in venv
source .venv/bin/activate
python3 --version
# → Python 3.10+

# 2. ClawTeam version
clawteam --version
# → clawteam v0.2.0+openclaw1

# 3. Health check
clawteam config health
# → exists: yes, writable: yes

# 4. Config
clawteam config show
# → Shows configuration table

# 5. tmux
tmux -V
# → tmux 3.x

# 6. Agent CLI
openclaw --version 2>/dev/null || claude --version 2>/dev/null
# → Shows version

# 7. (Optional) Run tests
python3 -m pytest tests/ -q --tb=short
# → 34 test files, all passed
```

---

## 🚀 Test Run — Create your first team

```bash
# Activate venv
source .venv/bin/activate

# Set identity for the leader
export CLAWTEAM_AGENT_NAME="leader"
export CLAWTEAM_AGENT_TYPE="leader"

# Create a team
clawteam team spawn-team demo-team -d "Demo team" -n leader

# Create tasks
clawteam task create demo-team "Task 1: Hello World" -o worker1
clawteam task create demo-team "Task 2: Testing" -o worker2

# View the board
clawteam board show demo-team

# Spawn 1 worker (requires tmux + openclaw/claude)
clawteam spawn --team demo-team --agent-name worker1 \
  --task "Create hello.py with a hello() function. When done, mark task completed."

# View currently running agents
clawteam board attach demo-team

# Cleanup when finished
clawteam team cleanup demo-team --force
```

---

## 📂 Configuration file structure after setup

```
~/.clawteam/
├── config.json              ← Auto-created by `clawteam config set`
├── teams/                   ← Auto-created when spawning a team
├── tasks/                   ← Auto-created when dispatching a task
└── templates/               ← (Optional) Custom templates

~/.openclaw/
├── exec-approvals.json      ← You must change security → allowlist
└── workspace/
    └── skills/
        └── clawteam/
            └── SKILL.md     ← Copied from skills/openclaw/SKILL.md

~/bin/
└── clawteam                 ← Symlink → .venv/bin/clawteam
```

---

## ❓ Troubleshooting

| Issue | Solution |
|---|---|
| `clawteam: command not found` | `source .venv/bin/activate` or verify your `~/bin/clawteam` symlink |
| `pip install -e .` fails | Run `pip install hatchling` first |
| Agents stuck at permission prompt | Re-run Step 8b (exec-approvals) |
| `clawteam --version` = "Coming Soon" | Run `npm uninstall -g clawteam` and reinstall |
| `tmux: command not found` | `brew install tmux` |
| Spawn fails with "command not found" | Verify `openclaw --version` or `claude --version` |
