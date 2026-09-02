#!/usr/bin/env python3
"""Retained session-lane substrate: lossless GC, now.py lane visibility, and
the request->checkpoint->credits join (FR-902 AC-09/AC-10/AC-11, kept by
FR-927 after the hook machinery was retired).

Run:  pytest .github/hooks/tests/test_session_lane_gc_join.py -q --no-cov
"""

import importlib.util
import subprocess
import sys

import pytest
from session_lane_fixtures import (
    GIT,
    JOIN_PY,
    REPO_ROOT,
    SID,
    commit_checkpoint,
    git,
    lane_path,
    make_repo,
    run_gc,
    run_session_verb,
    write_store,
)

pytestmark = pytest.mark.req("REQ-YG-630")

SID_MERGED = "11111111-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SID_DIRTY = "22222222-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SID_UNTRACKED = "33333333-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SID_UNPUSHED = "44444444-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SID_UNMERGED = "55555555-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SID_CLEAN = "66666666-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def lane_commit(main, sid, fname="work.md"):
    lane = lane_path(main, sid)
    (lane / "docs" / fname).write_text(f"work {sid}\n", encoding="utf-8")
    git(lane, "add", "-A")
    git(lane, "commit", "-m", "checkpoint(session): turn 1")
    return lane


@pytest.fixture
def zoo(tmp_path):
    """One lane per GC class, plus a bare origin for push-status checks."""
    main = make_repo(tmp_path)
    origin = tmp_path / "origin.git"
    subprocess.run(
        [GIT, "init", "--bare", "-b", "main", str(origin)],
        check=True,
        capture_output=True,
    )
    git(main, "remote", "add", "origin", str(origin))
    git(main, "push", "-q", "origin", "main")
    for sid in (
        SID_MERGED,
        SID_DIRTY,
        SID_UNTRACKED,
        SID_UNPUSHED,
        SID_UNMERGED,
        SID_CLEAN,
    ):
        assert run_session_verb(main, sid).returncode == 0
    lane_commit(main, SID_MERGED)
    git(main, "merge", "--no-ff", "-m", "merge session", f"session/{SID_MERGED}")
    dirty_lane = lane_path(main, SID_DIRTY)
    (dirty_lane / "docs" / "a.md").write_text("modified\n", encoding="utf-8")
    (lane_path(main, SID_UNTRACKED) / "orphan.txt").write_text("precious\n", encoding="utf-8")
    lane_commit(main, SID_UNPUSHED)
    lane_commit(main, SID_UNMERGED)
    git(main, "push", "-q", "origin", f"session/{SID_UNMERGED}")
    return main


# ── AC-09: dry-run classification ────────────────────────────────────


def test_gc_dry_run_reports_all_classes(zoo):
    r = run_gc(zoo, "--days", "0")
    assert r.returncode == 0, r.stderr
    out = r.stdout
    for cls, sid in [
        ("merged", SID_MERGED),
        ("dirty", SID_DIRTY),
        ("untracked", SID_UNTRACKED),
        ("unpushed", SID_UNPUSHED),
        ("unmerged", SID_UNMERGED),
        ("stale-clean", SID_CLEAN),
    ]:
        line = next((ln for ln in out.splitlines() if f"session/{sid}" in ln), "")
        assert line.startswith(cls), f"{sid}: expected {cls}, got: {line!r}"


def test_gc_dry_run_reports_live_lane(zoo):
    r = run_gc(zoo, "--days", "14")
    line = next(
        (ln for ln in r.stdout.splitlines() if f"session/{SID_CLEAN}" in ln), ""
    )
    assert line.startswith("live")


def test_gc_dry_run_deletes_nothing(zoo):
    run_gc(zoo, "--days", "0")
    for sid in (SID_MERGED, SID_DIRTY, SID_UNTRACKED, SID_UNPUSHED, SID_CLEAN):
        assert lane_path(zoo, sid).is_dir()
        assert git(zoo, "branch", "--list", f"session/{sid}")


# ── AC-09: prune deletes only merged + stale-clean, refuses the rest ──


def test_gc_prune_deletes_only_safe_lanes(zoo):
    r = run_gc(zoo, "--prune", "--days", "0")
    assert r.returncode == 0, r.stderr
    # pruned: merged + stale-clean
    assert not lane_path(zoo, SID_MERGED).exists()
    assert not git(zoo, "branch", "--list", f"session/{SID_MERGED}")
    assert not lane_path(zoo, SID_CLEAN).exists()
    assert not git(zoo, "branch", "--list", f"session/{SID_CLEAN}")
    # refused with reasons: every loss-bearing class survives
    for sid in (SID_DIRTY, SID_UNTRACKED, SID_UNPUSHED, SID_UNMERGED):
        assert lane_path(zoo, sid).is_dir(), sid
        assert git(zoo, "branch", "--list", f"session/{sid}"), sid
    assert (lane_path(zoo, SID_UNTRACKED) / "orphan.txt").exists()


def test_gc_prune_keeps_live_lanes(zoo):
    r = run_gc(zoo, "--prune", "--days", "14")
    assert r.returncode == 0
    assert lane_path(zoo, SID_CLEAN).is_dir()


def test_gc_ignores_feat_worktrees(zoo):
    git(
        zoo,
        "worktree",
        "add",
        str(zoo / "tmp" / "worktrees" / "feat" / "x"),
        "-b",
        "feat/x",
        "main",
    )
    r = run_gc(zoo, "--prune", "--days", "0")
    assert r.returncode == 0
    assert (zoo / "tmp" / "worktrees" / "feat" / "x").is_dir()
    assert git(zoo, "branch", "--list", "feat/x")


# ── AC-10: now.py session lane visibility ────────────────────────────


def _load_now():
    spec = importlib.util.spec_from_file_location(
        "now_mod", REPO_ROOT / "scripts" / "vscode" / "now.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["now_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_now_py_lists_session_lanes(zoo):
    now = _load_now()
    lines = now.session_lane_lines(zoo, gh_available=False)
    joined = "\n".join(lines)
    assert f"session/{SID_UNTRACKED}" in joined
    lane_line = next(ln for ln in lines if SID_UNTRACKED in ln)
    assert "untracked=1" in lane_line
    assert str(lane_path(zoo, SID_UNTRACKED)) in lane_line
    # never deletes: every lane still present
    assert lane_path(zoo, SID_UNTRACKED).is_dir()


def test_now_py_lists_orphan_session_branch(zoo):
    git(zoo, "branch", f"session/{SID}", "main")
    now = _load_now()
    lines = now.session_lane_lines(zoo, gh_available=False)
    assert any(f"session/{SID}" in ln and "no-worktree" in ln for ln in lines)


# ── AC-11: request → checkpoint → credits join ───────────────────────


def test_join_emits_request_checkpoint_credit_rows(tmp_path):
    main = make_repo(tmp_path)
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main)
    sha1 = commit_checkpoint(lane, SID, 1)
    sha2 = commit_checkpoint(lane, SID, 2)
    # request 3 exists in the store but produced no checkpoint
    store = write_store(tmp_path / f"{SID}.jsonl", 3)

    r = subprocess.run(
        [
            sys.executable,
            str(JOIN_PY),
            "--repo",
            str(main),
            "--store",
            str(store),
            "--session",
            SID,
        ],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    rows = [ln.split("\t") for ln in r.stdout.strip().splitlines()]
    header, body = rows[0], rows[1:]
    assert header[:5] == ["request", "checkpoint", "model", "credits", "prompt"]
    assert len(body) == 3
    assert body[0][1] == sha1
    assert body[1][1] == sha2
    assert body[2][1] == "-"
    assert body[0][2] == "claude-x"
    assert body[0][3] == "1.5"
    assert body[0][4] == "yes"
