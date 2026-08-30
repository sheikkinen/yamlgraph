#!/usr/bin/env python3
"""Shared fixtures for FR-902 session-lane lifecycle tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = HOOKS_ROOT.parents[1]
WORKTREE_SH = REPO_ROOT / "scripts" / "worktree.sh"
SESSION_WORKTREE = HOOKS_ROOT / "scripts" / "session-worktree.sh"
SESSION_CHECKPOINT = HOOKS_ROOT / "scripts" / "session-checkpoint.sh"
GUARD = HOOKS_ROOT / "scripts" / "pre-command-guard.sh"
JOIN_PY = REPO_ROOT / "scripts" / "vscode" / "session_join.py"
GIT = shutil.which("git") or "/usr/bin/git"

SID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeffff0000"
SID2 = "bbbbbbbb-cccc-4ddd-8eee-ffff00001111"


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


def run_hook_script(script: Path, payload: dict, env_extra: dict | None = None):
    env = {**os.environ}
    for k in ("FR902_ALLOW_OUTSIDE", "FR888_ALLOW_MAIN"):
        env.pop(k, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def write_lane_record(log_dir: Path, sid: str, lane: Path, branch: str) -> Path:
    d = Path(log_dir) / "session-lanes"
    d.mkdir(parents=True, exist_ok=True)
    rec = d / f"{sid}.json"
    rec.write_text(json.dumps({"session_id": sid, "branch": branch, "lane": str(lane)}))
    return rec


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


def stop_payload(sid: str, store: Path, cwd: Path) -> dict:
    return {
        "hook_event_name": "Stop",
        "session_id": sid,
        "transcript_path": str(store),
        "cwd": str(cwd),
    }


def start_payload(sid: str, cwd: Path) -> dict:
    return {
        "hook_event_name": "SessionStart",
        "session_id": sid,
        "cwd": str(cwd),
    }


def checkpoint_env(main: Path, log_dir: Path, retries: str = "0") -> dict:
    return {
        "HOOK_LOG_DIR": str(log_dir),
        "FR902_REPO": str(main),
        "FR902_RETRIES": retries,
    }


def read_audit(log_dir: Path) -> list[dict]:
    f = Path(log_dir) / "audit.jsonl"
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()]


def checkpoint_log(lane: Path) -> list[tuple[str, str, str]]:
    """(sha, subject, trailers-blob) for checkpoint commits on the lane HEAD."""
    out = subprocess.run(
        [GIT, "-C", str(lane), "log", "--format=%H%x00%s%x00%(trailers)%x01"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    entries = []
    for chunk in out.split("\x01"):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, subject, trailers = chunk.split("\x00")
        entries.append((sha, subject, trailers))
    return entries
