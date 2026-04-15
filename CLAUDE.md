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

## Spawn Task Language Rule (CRITICAL)

All spawn task prompts are **English-only**:
- Any content written to `.clawteam/spawn-task.txt` MUST be in English.
- Any inline `--task` text and agent instructions sent during spawn MUST be in English.
- Do not use Vietnamese or mixed-language prompts for spawned-agent tasks.

## Figma UI Workflow Protocol

If your assigned task relates to building UI from a Figma design, ALWAYS check `apps/<current-project>/.clawteam/config.json` for the `Figma Personal Access Token` and `File ID`.

- **If you are spawned as the `designer` agent:** 
  1. Use `curl` to fetch the ENTIRE Figma JSON from `https://api.figma.com/v1/files/[File-ID]` using the credentials. Save it to a local temp file.
  2. Write a Python script to search the massive JSON document recursively, looking for the specific `name` of the Screen/Component assigned to you.
  3. Once you locate the node, precisely extract its physical properties:
     - `absoluteBoundingBox` (width, height, x, y)
     - `fills` (Exact Hex/RGBA colors)
     - `characters` and `style` (fontFamily, fontWeight, fontSize, lineHeight, letterSpacing)
     - `effects` (drop shadows, inner shadows)
     - `layoutMode` (flex box direction)
     - Spacing metrics: `itemSpacing`, `paddingLeft`, `paddingRight`, `paddingTop`, `paddingBottom`, `cornerRadius`
  4. Format these metrics into a strict Markdown "Design Spec".
  5. Send this exact Design Spec via `clawteam inbox send <team> frontend "Specs: ..."` to the frontend agent.

- **If you are spawned as the `frontend` agent:** 
  1. Loop `clawteam inbox receive <team>` to wait for the Design Specs from the designer agent.
  2. Build the React/HTML UI strictly enforcing every single pixel, color hex, padding value, and font size specified in the Specs. Do NOT estimate or guess the styling; map exactly to the provided JSON metrics.

- **SECURE CLEANUP:** Once the codebase is updated and complete, ensure that the Figma Token and File ID are deleted from `config.json`.

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
