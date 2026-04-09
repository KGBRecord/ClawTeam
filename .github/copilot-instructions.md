# Copilot Instructions for ClawTeam (Project Local)

These instructions are repository-scoped and should guide AI behavior only in this project.

## Operating model

- Think as a coordinator first: plan, delegate, verify.
- Use `clawteam` for complex tasks that can be split across agents.
- Before starting a delegation workflow, ask:
  "Do you want to use the automated BMAD workflow for this task, or the traditional manual delegation?"

## GEMINI.md-first policy (hard requirement)

- Read `GEMINI.md` before executing substantial tasks in this repository.
- Treat `GEMINI.md` as the authoritative operating manual for orchestration behavior.
- If any instruction here conflicts with `GEMINI.md`, prefer `GEMINI.md`.
- Mirror `GEMINI.md` behavior into assistant output: planning structure,
  delegation process, path constraints, and verification steps.
- When `GEMINI.md` changes, apply the latest version immediately.

## Mandatory Implementation Plan format

Before writing code or spawning agents, always output a Markdown
`Implementation Plan` that matches Antigravity structure:

- Epic -> User story -> Task -> Subtask -> MP
- ID format:
  - Epic: `E-01`, `E-02`
  - User story: `US-01`, `US-02`
  - Task: `US-01.T1`
  - Subtask: `US-01.T1.S1`
  - MP: `MP-01`, `MP-02`
- One MP = one execution milestone/delegation cycle.

Required section order:

1. `## Implementation Plan`
2. `### Epic list`
3. `### User stories`
4. `### Task breakdown`
5. `### Subtasks`
6. `### MP execution order`
7. `### Acceptance criteria`

If the user asks for immediate execution, still provide this plan first.

## Safety and boundaries

- Do not directly edit customer application code in `apps/` from the coordinator role.
- Delegate implementation in `apps/` through `clawteam spawn ... --from-file`.
- Never commit secrets (`.env`, tokens, private keys).
- Avoid destructive git operations unless the user explicitly requests them.

## Preferred direct-edit areas

- `clawteam/`, `skills/`, `scripts/`, `tests/`
- `.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.github/`
- Documentation and repo-level configs

## Execution quality

- Keep tasks small, explicit, and testable.
- Track dependencies between tasks when using multi-agent flows.
- Mandatory task file path: `apps/<working_dir>/.clawteam/spawn-task.txt`
  (inside the target app). Do not write task files to root `.clawteam/`.
- Run spawn from `apps/<working_dir>` when using `--from-file`.
- Verify outputs before merge and clean up temporary teams/worktrees after completion.
