import json
import os
import subprocess
import typer
from pathlib import Path

from rich.console import Console

bmad_app = typer.Typer(help="BMAD Integration Bridge")
console = Console()

@bmad_app.command("sync")
def bmad_sync(
    team: str = typer.Argument(..., help="Team name to sync BMAD tasks into"),
    project_path: str = typer.Option(".", "--path", "-p", help="Path to project containing .bmad/")
):
    """Parse .bmad/ specs using LLM and sync them into ClawTeam Tasks."""
    from clawteam.bmad_bridge.sync_engine import sync_bmad_to_team
    
    console.print("[cyan]Extracting BMAD Specs using LLM...[/cyan] (This may take a minute)")
    
    try:
        tasks = sync_bmad_to_team(project_path, team)
        console.print(f"[green]Successfully synced {len(tasks)} tasks into team '{team}'![/green]")
        for t in tasks:
            console.print(f" - [{t['_actual_id']}] {t.get('task_name')} (owner: {t.get('persona')})")
        console.print("\nRun `clawteam board show <team>` to verify dependencies.")
    except Exception as e:
        console.print(f"[red]Error during BMAD sync: {str(e)}[/red]")
        raise typer.Exit(1)

@bmad_app.command("run")
def bmad_run(
    team: str = typer.Argument(..., help="Team name"),
    project_path: str = typer.Option(".", "--path", "-p", help="Path to project containing chunks")
):
    """Automatically execute pending BMAD tasks using `clawteam spawn`."""
    from clawteam.team.tasks import TaskStore
    
    store = TaskStore(team)
    chunk_dir = Path(project_path) / ".clawteam" / "bmad-chunks"
    
    all_tasks = store.list_tasks()
    
    # Simple dependency verification: 
    # To run, task must be 'pending' and all tasks in blocked_by must be 'completed'
    spawned_count = 0
    for task in all_tasks:
        if task.status != "pending":
            continue
            
        can_run = True
        for blocker_id in task.blocked_by:
            blocker = store.get(blocker_id)
            if not blocker or blocker.status != "completed":
                can_run = False
                break
                
        if can_run:
            console.print(f"[cyan]Spawning agent '{task.owner}' for task '{task.subject}' ({task.id})...[/cyan]")
            chunk_file = chunk_dir / f"{task.id}.txt"
            if not chunk_file.exists():
                console.print(f"[yellow]Warning: Chunk file missing for {task.id}, skipping auto-spawn.[/yellow]")
                continue
                
            cmd = [
                "clawteam", "spawn", "subprocess", "claude",
                "-t", team,
                "-n", task.owner or "worker",
                "--from-file", str(chunk_file)
            ]
            
            # Fire and detach using Popen
            try:
                subprocess.Popen(cmd, cwd=project_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                spawned_count += 1
                task.status = "in_progress"
                store._save_task(task)
            except Exception as e:
                console.print(f"[red]Failed to spawn agent for task {task.id}: {str(e)}[/red]")
                
    if spawned_count > 0:
        console.print(f"[green]Spawned {spawned_count} agents successfully.[/green] Use `clawteam board live {team}` to monitor.")
    else:
        console.print("[dim]No pending unblocked BMAD tasks to run right now.[/dim]")
