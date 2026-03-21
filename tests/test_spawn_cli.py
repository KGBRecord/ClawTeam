from __future__ import annotations

from typer.testing import CliRunner

from clawteam.cli.commands import app
from clawteam.team.manager import TeamManager


class ErrorBackend:
    def spawn(self, **kwargs):
        return (
            "Error: command 'nanobot' not found in PATH. "
            "Install the agent CLI first or pass an executable path."
        )

    def list_running(self):
        return []


class RecordingBackend:
    def __init__(self):
        self.calls = []

    def spawn(self, **kwargs):
        self.calls.append(kwargs)
        return f"Agent '{kwargs['agent_name']}' spawned"

    def list_running(self):
        return []


def test_spawn_cli_exits_nonzero_and_rolls_back_failed_member(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    TeamManager.create_team(
        name="demo",
        leader_name="leader",
        leader_id="leader001",
    )
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: ErrorBackend())

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["spawn", "tmux", "nanobot", "--team", "demo", "--agent-name", "alice", "--no-workspace"],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert "Error: command 'nanobot' not found in PATH" in result.output
    assert [member.name for member in TeamManager.list_members("demo")] == ["leader"]


def test_launch_cli_passes_skip_permissions_from_config(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    backend = RecordingBackend()
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: backend)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["launch", "hedge-fund", "--team", "fund1", "--goal", "Analyze AAPL"],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 0
    assert backend.calls
    assert all(call["skip_permissions"] is True for call in backend.calls)


def test_spawn_cli_rejects_removed_acpx_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    TeamManager.create_team(
        name="demo",
        leader_name="leader",
        leader_id="leader001",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["spawn", "acpx", "claude", "--team", "demo", "--agent-name", "alice", "--no-workspace"],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert "Unknown spawn backend: acpx. Available: subprocess, tmux" in result.output


def test_launch_cli_rejects_removed_acpx_backend(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["launch", "hedge-fund", "--backend", "acpx", "--team", "fund1", "--goal", "Analyze AAPL"],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert "Unknown spawn backend: acpx. Available: subprocess, tmux" in result.output


def test_spawn_cli_applies_profile_command_and_env(monkeypatch, tmp_path):
    monkeypatch.setenv("MOONSHOT_API_KEY", "moonshot-secret")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path / ".clawteam"))
    from clawteam.config import AgentProfile, ClawTeamConfig, save_config

    save_config(
        ClawTeamConfig(
            profiles={
                "moonshot-kimi": AgentProfile(
                    agent="kimi",
                    model="kimi-k2-thinking-turbo",
                    base_url="https://api.moonshot.cn/v1",
                    api_key_env="MOONSHOT_API_KEY",
                    args=["--config-file", "/tmp/kimi.toml"],
                )
            }
        )
    )
    TeamManager.create_team(
        name="demo",
        leader_name="leader",
        leader_id="leader001",
    )
    backend = RecordingBackend()
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: backend)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["spawn", "subprocess", "--profile", "moonshot-kimi", "--team", "demo", "--agent-name", "alice", "--no-workspace", "--task", "say hi"],
        env={"HOME": str(tmp_path), "CLAWTEAM_DATA_DIR": str(tmp_path / ".clawteam"), "MOONSHOT_API_KEY": "moonshot-secret"},
    )

    assert result.exit_code == 0
    call = backend.calls[0]
    assert call["command"] == ["kimi", "--model", "kimi-k2-thinking-turbo", "--config-file", "/tmp/kimi.toml"]
    assert call["env"]["KIMI_BASE_URL"] == "https://api.moonshot.cn/v1"
    assert call["env"]["KIMI_API_KEY"] == "moonshot-secret"


def test_launch_cli_applies_profile_to_template_agents(monkeypatch, tmp_path):
    monkeypatch.setenv("MOONSHOT_API_KEY", "moonshot-secret")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path / ".clawteam"))
    from clawteam.config import AgentProfile, ClawTeamConfig, save_config

    save_config(
        ClawTeamConfig(
            profiles={
                "moonshot-kimi": AgentProfile(
                    agent="kimi",
                    model="kimi-k2-thinking-turbo",
                    base_url="https://api.moonshot.cn/v1",
                    api_key_env="MOONSHOT_API_KEY",
                )
            }
        )
    )
    backend = RecordingBackend()
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: backend)
    monkeypatch.chdir(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["launch", "hedge-fund", "--team", "fund1", "--goal", "Analyze AAPL", "--profile", "moonshot-kimi"],
        env={"HOME": str(tmp_path), "CLAWTEAM_DATA_DIR": str(tmp_path / ".clawteam"), "MOONSHOT_API_KEY": "moonshot-secret"},
    )

    assert result.exit_code == 0
    assert backend.calls
    assert all(call["command"][:3] == ["kimi", "--model", "kimi-k2-thinking-turbo"] for call in backend.calls)
    assert all(call["env"]["KIMI_API_KEY"] == "moonshot-secret" for call in backend.calls)


def test_spawn_cli_auto_creates_team_for_orchestrator(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    backend = RecordingBackend()
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: backend)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "spawn",
            "tmux",
            "claude",
            "--team",
            "auto-team",
            "--agent-name",
            "leader",
            "--agent-type",
            "orchestrator",
            "--no-workspace",
            "--task",
            "Build a todo app",
        ],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 0
    team = TeamManager.get_team("auto-team")
    assert team is not None
    assert team.members[0].name == "leader"
    assert team.members[0].agent_type == "orchestrator"


def test_spawn_cli_rolls_back_auto_created_team_on_spawn_error(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWTEAM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("clawteam.spawn.get_backend", lambda _: ErrorBackend())

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "spawn",
            "tmux",
            "nanobot",
            "--team",
            "auto-team",
            "--agent-name",
            "leader",
            "--agent-type",
            "orchestrator",
            "--no-workspace",
        ],
        env={"CLAWTEAM_DATA_DIR": str(tmp_path)},
    )

    assert result.exit_code == 1
    assert TeamManager.get_team("auto-team") is None
