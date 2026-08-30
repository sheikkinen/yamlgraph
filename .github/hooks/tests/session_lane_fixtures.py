#!/usr/bin/env python3
"""Shared fixtures for the retained session-lane substrate tests.

Covers only what survived FR-927: `scripts/worktree.sh session`/`gc`,
`scripts/vscode/now.py`, and `scripts/vscode/session_join.py`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = HOOKS_ROOT.parents[1]
WORKTREE_SH = REPO_ROOT / "scripts" / "worktree.sh"
JOIN_PY = REPO_ROOT / "scripts" / "vscode" / "session_join.py"
GIT = shutil.which("git") or "/usr/bin/git"

SID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeffff0000"


def git(cwd, *args) -> str:
    r = subprocess.run(
        [GIT, *args], cwd=cwd, check=True, capture_output=True, text=True
    )
    return r.stdout.strip()


def make_repo(tmp_path: Path) -> Path:
    """Fixture main checkout shaped like the real repo's ignore contract."""
    main = tmp_path / "main"
    main.mkdir()
    git(main, "init", "-b", "main")
    git(main, "config", "user.email", "t@t")
    git(main, "config", "user.name", "t")
    (main / ".gitignore").write_text(".venv\n.venv/\n.env\n.env.*\ntmp/\n")
    (main / "docs").mkdir()
    (main / "docs" / "a.md").write_text("seed\n")
    (main / "yamlgraph").mkdir()
    (main / "yamlgraph" / "x.py").write_text("x = 1\n")
    git(main, "add", "-A")
    git(main, "commit", "-m", "init")
    return main


def lane_path(main: Path, sid: str = SID) -> Path:
    return main / "tmp" / "worktrees" / "session" / sid


def run_session_verb(main: Path, sid: str, *extra: str):
    return subprocess.run(
        [str(WORKTREE_SH), "session", sid, *extra],
        cwd=main,
        capture_output=True,
        text=True,
    )


def run_gc(main: Path, *extra: str):
    return subprocess.run(
        [str(WORKTREE_SH), "gc", *extra],
        cwd=main,
        capture_output=True,
        text=True,
    )


def write_store(path: Path, n_requests: int, model: str = "claude-x") -> Path:
    """Minimal chatSessions-format store: one kind-0 snapshot line."""
    reqs = [
        {
            "message": {"parts": [{"text": f"prompt {i}"}]},
            "modelId": f"copilot/{model}",
            "copilotCredits": 1.5,
            "timestamp": 1700000000000 + i,
        }
        for i in range(n_requests)
    ]
    path.write_text(
        json.dumps({"kind": 0, "v": {"sessionId": SID, "requests": reqs}}) + "\n"
    )
    return path


def commit_checkpoint(lane: Path, sid: str, request_index: int) -> str:
    """Historical-shape checkpoint commit: the provenance the join reads."""
    (lane / "docs" / f"t{request_index}.md").write_text(f"turn {request_index}\n")
    git(lane, "add", "-A")
    git(
        lane,
        "commit",
        "-m",
        f"checkpoint(session): turn {request_index}\n\n"
        f"Session-Id: {sid}\nRequest-Index: {request_index}",
    )
    return git(lane, "rev-parse", "HEAD")
