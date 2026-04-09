"""Low-level git command wrappers — all subprocess calls centralized here."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    """Raised when a git command fails."""


def _run(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """Check if *path* is inside a git repository."""
    try:
        _run(["rev-parse", "--git-dir"], cwd=path)
        return True
    except (GitError, FileNotFoundError):
        return False


def repo_root(path: Path) -> Path:
    """Return the repository root for *path*."""
    return Path(_run(["rev-parse", "--show-toplevel"], cwd=path))


def current_branch(repo: Path) -> str:
    """Return the current branch name (or HEAD for detached)."""
    try:
        return _run(["symbolic-ref", "--short", "HEAD"], cwd=repo)
    except GitError:
        return _run(["rev-parse", "--short", "HEAD"], cwd=repo)


def create_worktree(
    repo: Path,
    worktree_path: Path,
    branch: str,
    base_ref: str = "HEAD",
) -> None:
    """Create a new worktree with a new branch based on *base_ref*."""
    _run(
        ["worktree", "add", "-b", branch, str(worktree_path), base_ref],
        cwd=repo,
    )


def remove_worktree(repo: Path, worktree_path: Path) -> None:
    """Remove a worktree directory."""
    _run(["worktree", "remove", "--force", str(worktree_path)], cwd=repo)


def delete_branch(repo: Path, branch: str) -> None:
    """Force-delete a local branch."""
    _run(["branch", "-D", branch], cwd=repo)


def _staged_summary(worktree_path: Path) -> str:
    """Build a short summary of staged changes for the commit message body."""
    try:
        raw = _run(["diff", "--cached", "--name-only"], cwd=worktree_path, check=False)
        if not raw:
            return ""
        files = [f.strip() for f in raw.splitlines() if f.strip()]
        if not files:
            return ""

        # Get insertions/deletions
        stat = _run(["diff", "--cached", "--shortstat"], cwd=worktree_path, check=False).strip()

        # Build summary: show up to 8 file basenames, then "..."
        from pathlib import PurePosixPath
        names = [PurePosixPath(f).name for f in files]
        if len(names) > 8:
            shown = ", ".join(names[:8]) + f", ... (+{len(names) - 8} more)"
        else:
            shown = ", ".join(names)

        parts = [f"Files ({len(files)}): {shown}"]
        if stat:
            parts.append(stat)
        return "\n".join(parts)
    except Exception:
        return ""


def commit_all(worktree_path: Path, message: str) -> bool:
    """Stage everything and commit. Returns True if a commit was created."""
    _run(["add", "-A"], cwd=worktree_path)
    # Check if there is anything to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=worktree_path,
        capture_output=True,
    )
    if result.returncode == 0:
        return False  # nothing staged

    # Enrich commit message with a summary of what changed
    summary = _staged_summary(worktree_path)
    if summary:
        message = f"{message}\n\n{summary}"

    _run(["commit", "-m", message], cwd=worktree_path)
    return True


def merge_branch(
    repo: Path,
    branch: str,
    target: str,
    no_ff: bool = True,
) -> tuple[bool, str]:
    """Merge *branch* into *target*. Returns (success, output)."""
    _run(["checkout", target], cwd=repo)
    args = ["merge"]
    if no_ff:
        args.append("--no-ff")
    args.append(branch)
    try:
        out = _run(args, cwd=repo)
        return True, out
    except GitError as e:
        # Abort on conflict
        subprocess.run(["git", "merge", "--abort"], cwd=repo, capture_output=True)
        return False, str(e)


def list_worktrees(repo: Path) -> list[dict[str, str]]:
    """Return list of worktrees as dicts with 'path' and 'branch' keys."""
    raw = _run(["worktree", "list", "--porcelain"], cwd=repo)
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in raw.splitlines():
        if line.startswith("worktree "):
            current = {"path": line.split(" ", 1)[1]}
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].removeprefix("refs/heads/")
        elif line == "" and current:
            worktrees.append(current)
            current = {}
    if current:
        worktrees.append(current)
    return worktrees


def diff_stat(worktree_path: Path) -> str:
    """Return ``git diff --stat`` output for the worktree."""
    staged = _run(["diff", "--cached", "--stat"], cwd=worktree_path, check=False)
    unstaged = _run(["diff", "--stat"], cwd=worktree_path, check=False)
    parts = []
    if staged:
        parts.append(f"Staged:\n{staged}")
    if unstaged:
        parts.append(f"Unstaged:\n{unstaged}")
    return "\n".join(parts) if parts else "Clean — no changes."
