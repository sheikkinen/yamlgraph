#!/usr/bin/env python3
"""Now: what the agents are doing RIGHT NOW — sessions × git × FRs.

Spike (scripts/vscode, 2026-07-16). The situation board:
- live sessions (chatSessions mtime within --window), with titles;
- git state per implicated repo: branch, STAGED files (the interleave
  tripwire), recent commits with FR/NC refs;
- FRs in motion: feature-request files modified within the window;
- collision flags: repos with staged work AND >1 live session.

Read-only everywhere. Intended as a session-start briefing delivered
on reception rung 2 (a tool result), per the reception-hierarchy diary.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

USER_DIR = Path.home() / "Library/Application Support/Code/User"
WS_STORAGE = USER_DIR / "workspaceStorage"
GIT = shutil.which("git") or "git"

TITLE_RE = re.compile(r'"customTitle":"([^"]{1,120})"')
MODEL_RE = re.compile(r'"modelId":"([^"]+)"')
FR_REF_RE = re.compile(r"\b(FR|NC)-\d{2,4}\b")


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(  # noqa: S603  # CONF-390
        [GIT, "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    return r.stdout.strip()


def workspace_folder(hash_dir: Path) -> Path | None:
    meta = hash_dir / "workspace.json"
    if not meta.is_file():
        return None
    m = re.search(r'"folder":\s*"file://([^"]+)"', meta.read_text())
    return Path(m.group(1)) if m else None


def live_sessions(window_s: float) -> list[dict]:
    now = time.time()
    out = []
    for chat in WS_STORAGE.glob("*/chatSessions/*.jsonl"):
        age = now - chat.stat().st_mtime
        if age > window_s:
            continue
        head = chat.open(errors="replace").read(4000)
        title = TITLE_RE.search(head)
        tail = chat.open(errors="replace").read()[-200_000:]
        model = None
        for model in MODEL_RE.finditer(tail):  # noqa: B007  # CONF-391
            pass
        out.append(
            {
                "title": title.group(1) if title else chat.stem[:8],
                "folder": workspace_folder(chat.parent.parent),
                "ago_min": age / 60,
                "model": (model.group(1).removeprefix("copilot/") if model else "?"),
            }
        )
    out.sort(key=lambda s: s["ago_min"])
    return out


def find_repos(folders: set[Path]) -> set[Path]:
    repos = set()
    for folder in folders:
        if folder and (folder / ".git").exists():
            repos.add(folder)
        # nested project repos (workspace_is_not_boundary)
        if folder:
            for git_dir in folder.glob("projects/*/.git"):
                repos.add(git_dir.parent)
    return repos


def repo_state(repo: Path, window_s: float) -> dict:
    staged = [
        ln for ln in _git(repo, "diff", "--cached", "--name-only").splitlines() if ln
    ]
    since = datetime.fromtimestamp(time.time() - window_s).strftime("%Y-%m-%dT%H:%M")
    commits = _git(repo, "log", f"--since={since}", "--format=%h %s").splitlines()
    refs = sorted({m.group(0) for c in commits for m in FR_REF_RE.finditer(c)})
    return {
        "branch": _git(repo, "branch", "--show-current"),
        "staged": staged,
        "commits": commits,
        "refs": refs,
    }


def frs_in_motion(repos: set[Path], window_s: float) -> list[tuple[str, str, str]]:
    now = time.time()
    rows = []
    for repo in repos:
        fr_dir = repo / "feature-requests"
        if not fr_dir.is_dir():
            continue
        for fr in fr_dir.glob("*.md"):
            if fr.name == "TEMPLATE.md" or ".judgement." in fr.name:
                continue
            if now - fr.stat().st_mtime > window_s:
                continue
            status = "?"
            m = re.search(
                r"^\*\*Status:\*\*\s*(.+)$", fr.read_text(errors="replace"), re.M
            )
            if m:
                status = re.split(r"[—(]", m.group(1))[0].strip()[:20]
            rows.append((repo.name, fr.name, status))
    rows.sort()
    return rows


def tap_ground_truth() -> list[str]:
    """FR-739 AC-02/03: liveness + altimeter from OTel events, not mtimes."""
    import os

    import tap  # same-dir import; script dir is on sys.path

    path = Path(os.environ.get("COPILOT_OTEL_FILE_EXPORTER_PATH", tap.DEFAULT_PATH))
    if not path.is_file():
        return ["  (no tap file — arm with otel-tap-on.sh and restart VS Code)"]
    sessions = tap.join_sessions(tap.load_events(path))
    live = tap.live_session_ids(sessions)
    now = time.time()
    lines = []
    for sid, sess in sorted(sessions.items(), key=lambda kv: -kv[1]["last_ts"]):
        ago = (now - sess["last_ts"]) / 60
        mark = "LIVE" if sid in live else f"{ago:.0f}m ago"
        models = ",".join(sorted(m for m in sess["models"] if "mini" not in m))
        lines.append(f"  {sid[:8]}  {mark:<8} turns={len(sess['turns'])}  {models}")
    lines.extend(tap.altimeter_lines(sessions))
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=8.0, help="hours of 'now'")
    ap.add_argument("--tap", action="store_true", help="OTel ground truth (FR-739)")
    args = ap.parse_args()
    window_s = args.window * 3600

    sessions = live_sessions(window_s)
    print(f"== live sessions (last {args.window:g}h) ==")
    for s in sessions:
        folder = s["folder"].name if s["folder"] else "?"
        print(
            f"  {s['ago_min']:>5.0f}m ago  {folder:<22} {s['model']:<18} {s['title']}"
        )

    repos = find_repos({s["folder"] for s in sessions if s["folder"]})
    print("\n== repo state ==")
    hazards = []
    folder_sessions: dict[Path, int] = {}
    for s in sessions:
        if s["folder"]:
            folder_sessions[s["folder"]] = folder_sessions.get(s["folder"], 0) + 1
    for repo in sorted(repos):
        st = repo_state(repo, window_s)
        n_live = sum(
            n for f, n in folder_sessions.items() if repo == f or repo.is_relative_to(f)
        )
        flag = ""
        if st["staged"] and n_live > 1:
            flag = "  ⚠ INTERLEAVE HAZARD (staged work + multiple live sessions)"
            hazards.append(repo.name)
        print(
            f"  {repo.name} [{st['branch']}] staged={len(st['staged'])} "
            f"commits({args.window:g}h)={len(st['commits'])} live_sessions={n_live}{flag}"
        )
        if st["refs"]:
            print(f"    recent refs: {', '.join(st['refs'])}")

    print("\n== FRs in motion (files touched in window) ==")
    for repo, name, status in frs_in_motion(repos, window_s):
        print(f"  {repo:<16} {status:<22} {name}")

    if args.tap:
        print("\n== tap ground truth (OTel events, FR-739) ==")
        print("\n".join(tap_ground_truth()))

    if hazards:
        print(
            f"\n⚠ one_session_one_repo: staged-check before add in: {', '.join(hazards)}"
        )


if __name__ == "__main__":
    main()
