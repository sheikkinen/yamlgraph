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
import json
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


def orphan_worktree_lines(
    repo: Path,
    gh_available: bool | None = None,
    live_branches: set[str] | None = None,
) -> list[str]:
    """FR-888 AC-10: linked worktrees with no open PR and no live pipeline.

    live_branches: branches owned by a live pipeline (the caller's
    contract — chaplain runtime or FR-885 watcher supplies them);
    suppressed from the orphan list. Flagged, never deleted.
    """
    if gh_available is None:
        gh_available = shutil.which("gh") is not None
    live_branches = live_branches or set()
    lines: list[str] = []
    porcelain = _git(repo, "worktree", "list", "--porcelain")
    tree, branch = None, None
    entries = []
    for raw in porcelain.splitlines() + [""]:
        if raw.startswith("worktree "):
            tree = raw.split(" ", 1)[1]
        elif raw.startswith("branch "):
            branch = raw.split(" ", 1)[1].removeprefix("refs/heads/")
        elif not raw:
            if tree and branch and Path(tree).resolve() != repo.resolve():
                entries.append((tree, branch))
            tree, branch = None, None
    for tree, branch in entries:
        if branch in live_branches:
            continue  # live pipeline owns this tree — not an orphan
        age = _git(Path(tree), "log", "-1", "--format=%cr") or "unknown"
        untracked = sum(
            1
            for line in _git(
                Path(tree), "status", "--porcelain", "--untracked-files=all"
            ).splitlines()
            if line.startswith("??")
        )
        pr = "?"
        if gh_available:
            out = subprocess.run(  # noqa: S603  # CONF-390
                [
                    "gh",
                    "pr",
                    "list",
                    "--head",
                    branch,
                    "--state",
                    "open",  # noqa: S607  # CONF-390
                    "--json",
                    "number",
                    "--jq",
                    "length",
                ],
                capture_output=True,
                text=True,
                check=False,
                cwd=repo,
            ).stdout.strip()
            pr = out if out else "?"
        if pr in ("0", "?"):
            lines.append(
                f"  ⚠ orphan worktree {tree} [{branch}] age={age} "
                f"untracked={untracked} pr={pr} — disposition manually "
                f"(rm-safe refuses untracked)"
            )
    return lines


def session_lane_lines(repo: Path, gh_available: bool | None = None) -> list[str]:
    """FR-902 AC-10: session lanes listed for disposition — never deleted.

    gh_available kept for CLI symmetry with orphan_worktree_lines; lane
    disposition is local-only (gc classifies, human prunes).
    """
    del gh_available
    branches = [
        b
        for b in _git(
            repo, "for-each-ref", "--format=%(refname:short)", "refs/heads/session/*"
        ).splitlines()
        if b
    ]
    if not branches:
        return []
    trees: dict[str, str] = {}
    tree = None
    for raw in _git(repo, "worktree", "list", "--porcelain").splitlines() + [""]:
        if raw.startswith("worktree "):
            tree = raw.split(" ", 1)[1]
        elif raw.startswith("branch ") and tree:
            trees[raw.split(" ", 1)[1].removeprefix("refs/heads/")] = tree
        elif not raw:
            tree = None
    lines = []
    for br in branches:
        tree = trees.get(br)
        if tree:
            age = _git(Path(tree), "log", "-1", "--format=%cr") or "?"
            untracked = sum(
                1
                for ln in _git(
                    Path(tree), "status", "--porcelain", "--untracked-files=all"
                ).splitlines()
                if ln.startswith("??")
            )
            lines.append(
                f"  session lane {br} lane={tree} age={age} "
                f"untracked={untracked} — gc: scripts/worktree.sh gc"
            )
        else:
            age = _git(repo, "log", "-1", "--format=%cr", br) or "?"
            lines.append(
                f"  session lane {br} no-worktree age={age} — recover: "
                f"git worktree add tmp/worktrees/{br} {br}"
            )
    return lines


def main_lock_lines(repo: Path) -> list[str]:
    """FR-889 AC-10: report an unlocked main checkout — never fixes it."""
    marker = repo / ".github" / "hooks" / "state" / "main-lock.json"
    if not marker.is_file():
        return []
    try:
        state = json.loads(marker.read_text(encoding="utf-8")).get("state", "")
    except (OSError, ValueError):
        return [f"  ⚠ main-lock marker unreadable: {marker}"]
    if state != "unlocked":
        return []
    age_min = int((time.time() - marker.stat().st_mtime) / 60)
    return [
        f"  ⚠ main checkout unlocked for {age_min}m "
        f"(relock: scripts/worktree.sh lock-main)"
    ]


def workspace_folder(hash_dir: Path) -> Path | None:
    meta = hash_dir / "workspace.json"
    if not meta.is_file():
        return None
    m = re.search(r'"folder":\s*"file://([^"]+)"', meta.read_text(encoding="utf-8"))
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
                r"^\*\*Status:\*\*\s*(.+)$", fr.read_text(errors="replace", encoding="utf-8"), re.M
            )
            if m:
                status = re.split(r"[—(]", m.group(1))[0].strip()[:20]
            rows.append((repo.name, fr.name, status))
    rows.sort()
    return rows


def intentions_section(repos: set[Path]) -> list[str]:
    """FR-741 AC-02 + A1: orphaned intentions + live claims. In git we
    trust; todos we cross-examine."""
    import time as _time

    import todos

    all_todos = todos.load_todos()
    now = _time.time()
    sessions = {}
    live = set()
    for sid, items in all_todos.items():
        if not items:
            continue
        title, mtime = todos.session_meta(sid)
        sessions[sid] = {"todos": items, "title": title, "mtime": mtime}
        if mtime and now - mtime <= todos.LIVE_WINDOW_S:
            live.add(sid)
    return todos.briefing_lines(
        sessions, live, sorted(repos), todos.load_dispositions(), now
    )


def tap_ground_truth() -> list[str]:
    """FR-739 AC-02/03: liveness + altimeter from OTel events, not mtimes."""
    import os

    import tap  # same-dir import; script dir is on sys.path

    path = Path(os.environ.get("COPILOT_OTEL_FILE_EXPORTER_PATH", tap.DEFAULT_PATH))
    if not path.is_file():
        return ["  (no tap file — arm with otel-tap-on.sh and restart VS Code)"]
    # bounded tail: the tap file grows without rotation and full parse
    # broke the 5s briefing budget (witnessed 10.5s at 91K lines)
    sessions = tap.join_sessions(tap.load_events(path, tail_bytes=24_000_000))
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


def _print_repo_state(
    repos: set[Path], sessions: list[dict], window_h: float
) -> list[str]:
    window_s = window_h * 3600
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
            f"commits({window_h:g}h)={len(st['commits'])} live_sessions={n_live}{flag}"
        )
        if st["refs"]:
            print(f"    recent refs: {', '.join(st['refs'])}")
    return hazards


def brief_lines() -> list[str]:
    """FR-743 AC-01: ≤15-line headline briefing for SessionStart.

    Fail-open at every seam: any data-source failure degrades the
    briefing instead of killing it (a briefing hook that blocks
    session start is worse than no briefing).
    """
    lines = [
        "== session-start briefing (FR-743; full board: python3 scripts/vscode/now.py --tap) =="
    ]
    window_s = 2 * 3600
    try:
        sessions = live_sessions(window_s)
        repos = find_repos({s["folder"] for s in sessions if s["folder"]})
        staged_repos = [
            r.name for r in repos if _git(r, "diff", "--cached", "--name-only").strip()
        ]
        hazard = (
            f"⚠ staged work in {', '.join(staged_repos)} — one_session_one_repo"
            if staged_repos and len(sessions) > 1
            else "no interleave hazard"
        )
        lines.append(f"live sessions: {len(sessions)}  |  {hazard}")
    except Exception:
        lines.append("live sessions: unavailable")
        repos = set()
    try:
        import todos

        all_todos = todos.load_todos()
        dispositions = todos.load_dispositions()
        n_orphans = n_debts = 0
        for sid, items in all_todos.items():
            _, mtime = todos.session_meta(sid)
            if mtime and __import__("time").time() - mtime <= todos.LIVE_WINDOW_S:
                continue
            for t in items or []:
                if t.get("status") == "completed":
                    continue
                if todos.drop_key(sid, t.get("title", "")) in dispositions:
                    continue
                if todos.is_diary_class(t.get("title", "")):
                    n_debts += 1
                else:
                    n_orphans += 1
        lines.append(f"orphaned intentions: {n_orphans}  |  diary debts: {n_debts}")
    except Exception:
        lines.append("intentions: unavailable")
    try:
        import tap

        # bounded tail — full parse of the unrotated tap file broke the
        # 5s briefing budget (10.5s witnessed at 942MB / 91K lines)
        t_sessions = tap.join_sessions(
            tap.load_events(tap.DEFAULT_PATH, tail_bytes=24_000_000)
        )
        alti = tap.altimeter_lines(t_sessions)
        lines.extend(alti[:4])
    except Exception:
        lines.append("altimeter: unavailable (tap not armed?)")
    for repo in sorted(repos):
        state = live_plan_state(repo)
        if state:
            lines.append(state)
            break
    return lines[:15]


def live_plan_state(repo: Path) -> str | None:
    """Active-FR count computed live (FR-858: the committed board is retired).

    C-5: a failure is surfaced, never silently downgraded to stale state.
    """
    board = repo / "scripts" / "fr_board.py"
    if not board.is_file():
        return None
    try:
        import sys as _sys

        _sys.path.insert(0, str(repo / "scripts"))
        import fr_board  # noqa: PLC0415  # CONF-435

        gates = fr_board.load_gates(repo / "feature-requests" / "gates.yaml")
        rows = fr_board.active_rows(fr_board.collect_rows(repo))
        return f"plan state: {len(rows)} active FRs, {len(gates)} gates (live)"
    except Exception as exc:  # noqa: BLE001  # CONF-436
        return f"plan state: unavailable ({type(exc).__name__}: {exc})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=8.0, help="hours of 'now'")
    ap.add_argument("--tap", action="store_true", help="OTel ground truth (FR-739)")
    ap.add_argument("--brief", action="store_true", help="≤15-line briefing (FR-743)")
    args = ap.parse_args()
    if args.brief:
        print("\n".join(brief_lines()))
        return
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
    hazards = _print_repo_state(repos, sessions, args.window)

    # FR-888 AC-10: orphan worktrees — flagged for disposition, never deleted
    for repo in sorted(repos):
        for line in orphan_worktree_lines(repo):
            print(line)

    # FR-902 AC-10: session lanes — listed, never deleted
    for repo in sorted(repos):
        for line in session_lane_lines(repo):
            print(line)

    # FR-889 AC-10: unlocked main checkouts — reported, never relocked here
    for repo in sorted(repos):
        for line in main_lock_lines(repo):
            print(line)

    print("\n== FRs in motion (files touched in window) ==")
    for repo, name, status in frs_in_motion(repos, window_s):
        print(f"  {repo:<16} {status:<22} {name}")

    # FR-740 plan state, computed live (FR-858 retired the committed board)
    for repo in sorted(repos):
        state = live_plan_state(repo)
        if state:
            print(f"\n{state}")
            print("  full board: python scripts/fr_board.py")

    # deep history is a graph away (examples/demos/recap): narrative recap
    # of any window — workstreams + orphan commits, one LLM judgement
    print(
        "deep history: yamlgraph graph run examples/demos/recap/graph.yaml"
        ' --var since="1 week ago" --var repo_path=.'
    )

    # FR-744: world state — the age label IS the scheduler
    for repo in sorted(repos):
        wc = repo / "docs/world-context.md"
        if wc.is_file():
            age_d = (time.time() - wc.stat().st_mtime) / 86400
            stale = (
                "  ⚠ STALE — refresh: yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F)"
                if age_d > 14
                else ""
            )
            print(f"world: {wc} (updated {age_d:.0f}d ago){stale}")
            break

    if args.tap:
        print("\n== tap ground truth (OTel events, FR-739) ==")
        print("\n".join(tap_ground_truth()))

    intent = intentions_section(repos)
    if intent:
        print("\n== intentions (todos are claims; in git we trust — FR-741) ==")
        print("\n".join(intent))

    if hazards:
        print(
            f"\n⚠ one_session_one_repo: staged-check before add in: {', '.join(hazards)}"
        )


if __name__ == "__main__":
    main()
