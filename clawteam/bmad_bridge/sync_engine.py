import os
from pathlib import Path
from typing import Dict, Any, List

from .extractor import extract_bmad_tasks

def sync_bmad_to_team(project_path: str, team_name: str) -> List[Dict[str, Any]]:
    """Reads BMAD structured data, creates corresponding tasks in the ClawTeam team, 
    and writes out chunked contextual instruction files to be used with `--from-file`.
    """
    from clawteam.team.tasks import TaskStore
    from clawteam.team.manager import TeamManager

    # Ensure Team exists
    # we don't automatically create the team here entirely robustly because leader info is needed.
    # We assume the team logic is already handled, or user created it. 
    # Just checking if team directory exists is enough. if not TeamManager will fail gracefully when instantiating TaskStore
    
    store = TaskStore(team_name)
    
    # 1. Parse using LLM extractor
    parsed_tasks = extract_bmad_tasks(project_path)
    
    if not isinstance(parsed_tasks, list):
        raise ValueError("Invalid LLM parsing format. Expected a JSON List of tasks.")
        
    created_tasks_info = []
    
    # 2. Map temp_ids to internal ClawTeam task IDs
    temp_id_map = {}
    
    # Needs two passes. 
    # Pass A: Create tasks to get real IDs.
    for p_task in parsed_tasks:
        subject = p_task.get("task_name", "Untitled BMAD Task")
        description = p_task.get("description", "")
        owner = p_task.get("persona", "worker")
        
        # At creation we leave dependencies empty, we'll patch them in pass B
        actual_task = store.create(
            subject=subject,
            description=description,
            owner=owner
        )
        
        tid = actual_task.id
        temp_id = p_task.get("temp_id")
        if temp_id:
            temp_id_map[temp_id] = tid
            
        p_task["_actual_id"] = tid
        created_tasks_info.append(p_task)
        
        # Write context chunk for later runs
        chunk_dir = Path(project_path) / ".clawteam" / "bmad-chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        chunk_file = chunk_dir / f"{tid}.txt"
        
        prompt_content = f"BMAD Task: {subject}\nRole: {owner}\n\nTask Detail:\n{description}"
        chunk_file.write_text(prompt_content, encoding="utf-8")
        
    # Pass B: Update tasks with dependency blocks based on real IDs
    for p_task in created_tasks_info:
        real_id = p_task["_actual_id"]
        blocks_temp_ids = p_task.get("blocked_by_temp_ids", [])
        if not blocks_temp_ids:
            continue
            
        real_block_ids = []
        for b_id in blocks_temp_ids:
            mapped_val = temp_id_map.get(b_id)
            if mapped_val:
                real_block_ids.append(mapped_val)
                
        if real_block_ids:
            current_task_record = store.get(real_id)
            if current_task_record:
                current_task_record.blocked_by = list(set(current_task_record.blocked_by + real_block_ids))
                store._save_task(current_task_record)
                
                # Bi-directional update - if A blocked by B, B blocks A
                for bid in real_block_ids:
                    blocking_task = store.get(bid)
                    if blocking_task:
                        blocking_task.blocks = list(set(blocking_task.blocks + [real_id]))
                        store._save_task(blocking_task)

    return created_tasks_info
