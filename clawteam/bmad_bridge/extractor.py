import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List

def load_bmad_config() -> Dict[str, Any]:
    # __file__ is in clawteam/bmad_bridge/extractor.py
    # Root is three levels up
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def parse_with_llm(markdown_content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    prompt = """
You are a technical Bridge. Your job is to extract tasks from the following Software Specification (BMAD Solution/Architecture/PRD) and translate them into a strictly structured JSON array.
Each task should represent an independent executable sub-task.
Return ONLY valid JSON. No markdown backticks, no explanations. Do not return ```json ... ```, just the raw list array.

The JSON schema per task:
{
    "task_name": "Short descriptive name",
    "description": "Full detailed context/spec that the agent needs to implement it. Provide EVERYTHING from the specs relevant to this task so the agent has full context.",
    "persona": "architect | backend | frontend | qa | worker",
    "blocked_by_temp_ids": ["temp_id_A", "temp_id_B"],
    "temp_id": "temp_id_C"
}

Markdown Content:
""" + markdown_content

    provider = config.get("provider", "anthropic").lower()
    api_key = config.get("api_key")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY") if provider == "anthropic" else os.environ.get("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(f"API key for {provider} not found in config.json or environment.")

    user_agent = config.get("user_agent", "ClawTeam-BMAD-Bridge/1.0")

    # Prepare request
    if provider == "openai":
        url = config.get("api_url", "https://api.openai.com/v1/chat/completions")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": user_agent
        }
        data = {
            "model": config.get("model", "gpt-4o"),
            "messages": [
                {"role": "system", "content": "You are a helpful JSON generator. Always return raw JSON array."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
    else:  # anthropic (default)
        url = config.get("api_url", "https://api.anthropic.com/v1/messages")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "User-Agent": user_agent
        }
        data = {
            "model": config.get("model", "claude-3-5-sonnet-latest"),
            "max_tokens": 4096,
            "system": "You are a helpful JSON generator. Always return raw JSON. No markdown blocks.",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }

    encoded_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            if provider == "openai":
                content = result["choices"][0]["message"]["content"]
            else:
                content = result["content"][0]["text"]
            
            # Clean up potential markdown formatting if LLM failed instruction
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content.strip())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"LLM API Call failed ({e.code}): {error_body}")
    except Exception as e:
        raise RuntimeError(f"LLM API Call failed: {str(e)}")

def extract_bmad_tasks(project_path: str) -> List[Dict[str, Any]]:
    """Extract tasks using LLM from the .bmad folder of the given project path."""
    bmad_dir = Path(project_path) / ".bmad"
    if not bmad_dir.exists() or not bmad_dir.is_dir():
        raise FileNotFoundError(f"Project path {project_path} does not contain an initialized .bmad/ directory.")
    
    # Priority order for BMAD files containing spec details
    target_files = [
        "solutioning/solution.md", 
        "solution.md",
        "planning/architecture.md", 
        "architecture.md", 
        "analysis/prd.md",
        "prd.md"
    ]
    
    content = ""
    for tf in target_files:
        fp = bmad_dir / tf
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            break
            
    if not content:
        raise FileNotFoundError("Could not find any suitable BMAD artifact (solution.md, architecture.md, etc.) inside .bmad/")
        
    config = load_bmad_config()
    
    # Attempt extraction
    return parse_with_llm(content, config)
