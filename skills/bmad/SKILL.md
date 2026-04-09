---
name: BMAD Integration Workflow
description: Guide to integrating the BMAD (Breakthrough Method for Agile AI-Driven Development) framework with ClawTeam to automate agent spawning based on Specs.
---

# 🚀 BMAD Integration Workflow (ClawTeam Hybrid)

## The Problem
When dealing with complex projects, manually writing `.clawteam/spawn-task.txt` files consumes too much time and carries the risk of context loss or hallucination during manual delegation.

## The Solution: BMAD Bridge System
This system splits the workflow into 2 phases:
1. **Node.js (Original Tooling):** Use `npx bmad-method install` to scaffold the standard BMAD documentation structure.
2. **Python (ClawTeam Bridge):** Parse the YAML/Markdown spec files directly into ClawTeam Tasks, and automatically push them to the ClawTeam Spawner engine.

---

## 📋 Execution Workflow

Working procedure between Antigravity (Architect) and ClawTeam Worker Agents.

### Step 1: Initialize Project Structure
Inside the customer project directory (`apps/<my_project>/`), run the following shell command:
```bash
npx -y bmad-method@latest install
```

### Step 2: Architecture Design (Manual Write)
After setup, the `.bmad/` folder will be generated, containing files like `solution.md` or `architecture.md`.
Use the IDE File tool (`write_to_file`) to **fill in the detailed Solution and API Specs** inside these Markdown files. Be extremely specific and clear so that Builder Agents can implement tasks without ambiguity.

### Step 3: Task Syncing
Call the Bridge command to let the integrated LLM parse the `.bmad/` directory and map all specs into the local task database:
```bash
clawteam bmad sync <team_name> -p apps/<my_project>
```
*This command links tasks and auto-generates chunk spec files at `.clawteam/bmad-chunks/<id>.txt`.*

### Step 4: Verify via Board
Run the board command to ensure that the LLM has correctly divided sub-tasks and correctly established logical dependency constraints `blocked_by`:
```bash
clawteam board show <team_name>
```

### Step 5: Start Automated Execution
```bash
clawteam bmad run <team_name> -p apps/<my_project>
```
This command scans the team's system board. It finds all `pending` tasks that have successfully resolved their blockers, maps them to the appropriate Persona Role (e.g., Backend, QA), and automatically dispatches `clawteam spawn subprocess claude ... --from-file ...` in the background.

### Step 6: Wait & Standard Management
After spawning, monitor the cluster natively:
```bash
clawteam task wait <team_name> --timeout 600
clawteam workspace merge <team_name> <agent_name>
```
