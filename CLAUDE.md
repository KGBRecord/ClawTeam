# ClawTeam — Instructions for Claude Code

You have access to the `clawteam` CLI for multi-agent swarm coordination. Use it when tasks are complex enough to benefit from parallel agents.

## When to Use ClawTeam

- User asks to "create a team", "spawn agents", "build X with multiple agents"
- Task is large enough to split across 2+ agents (e.g., full-stack app, refactor entire codebase)
- You need parallel agents working on independent subtasks

## Planning Protocol (CRITICAL)

Before executing any plan, you **MUST** explicitly ask the user:
*"Do you want to use the automated BMAD workflow for this task, or the traditional manual delegation?"*

- If BMAD is chosen: Do NOT spawn agents manually. Instead, use IDE tools to write specification files into the `.bmad/` directory (prd.md, solution.md), then trigger `clawteam bmad sync` and `clawteam bmad run`.
- If traditional is chosen: Proceed with the standard `clawteam spawn` process manually.

## Quick Reference

```bash
# Team lifecycle
clawteam team spawn-team <team> -d "description" -n leader
clawteam team discover
clawteam team status <team>
clawteam team cleanup <team> --force

# Spawn agents (each gets git worktree + tmux window)
clawteam spawn --team <team> --agent-name <name> --task "task description"

# Task management
clawteam task create <team> "subject" -o <owner> --blocked-by <id1>,<id2>
clawteam task update <team> <id> --status completed
clawteam task list <team>
clawteam task wait <team> --timeout 300

# Messaging
clawteam inbox send <team> <to> "message"
clawteam inbox broadcast <team> "message"
clawteam inbox receive <team>

# Monitoring
clawteam board show <team>
clawteam board attach <team>
clawteam board serve --port 8080

# Templates (one-command team launch)
clawteam launch hedge-fund --team fund1 --goal "Analyze stocks"
clawteam template list
```

## Key Rules

1. **Do NOT override the default agent command** — `clawteam spawn` defaults to `openclaw`. Using `claude` directly will cause permission prompt issues.
2. **Use `--blocked-by`** for task dependencies — auto-unblocks when blocking tasks complete.
3. **Start monitoring immediately** after spawning agents — don't wait for user to ask.
4. **Always cleanup** when done: `clawteam team cleanup <team> --force`.
5. All data stored in `~/.clawteam/` as JSON files — no database needed.

## Skill Files

For detailed command reference and workflows, see:
- `.claude/skills/clawteam/SKILL.md`
- `.claude/skills/clawteam/references/cli-reference.md`
- `.claude/skills/clawteam/references/workflows.md`
