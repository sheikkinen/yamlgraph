#!/usr/bin/env python3
"""FR-902 AC-01/AC-02/AC-07: session lane creation via worktree.sh session
verb and the SessionStart hook wrapper.

Run:  pytest .github/hooks/tests/test_fr902_session_worktree.py -q --no-cov
"""

import json

import pytest
from fr902_fixtures import (
    SESSION_WORKTREE,
    SID,
    WORKTREE_SH,
    git,
    lane_path,
    make_repo,
    read_audit,
    run_hook_script,
    run_session_verb,
    start_payload,
)

pytestmark = pytest.mark.req("REQ-YG-629")


# ── AC-01: create, emit lane path, idempotent re-fire ────────────────


def test_session_verb_creates_lane_and_branch(tmp_path):
    main = make_repo(tmp_path)
    r = run_session_verb(main, SID)
    assert r.returncode == 0, r.stderr
    lane = lane_path(main)
    assert lane.is_dir()
    assert git(main, "branch", "--list", f"session/{SID}")
    last_line = r.stdout.strip().splitlines()[-1]
    assert last_line == str(lane.resolve())


def test_session_verb_refire_is_noop(tmp_path):
    main = make_repo(tmp_path)
    assert run_session_verb(main, SID).returncode == 0
    head_before = git(lane_path(main), "rev-parse", "HEAD")
    r = run_session_verb(main, SID)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == str(lane_path(main).resolve())
    assert git(lane_path(main), "rev-parse", "HEAD") == head_before


def test_session_verb_provisions_env_links(tmp_path):
    main = make_repo(tmp_path)
    (main / ".venv").mkdir()
    (main / ".env").write_text("KEY=v\n")
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main)
    assert (lane / ".venv").is_symlink()
    assert (lane / ".env").is_symlink()


# ── AC-02: refusal cases; never delete a session/* branch ────────────


@pytest.mark.parametrize(
    "bad_sid",
    [
        "../../evil",
        "session/../../../etc",
        "short",
        "aaaaaaaa-bbbb-4ccc-8ddd-eeeeffff0000; rm -rf /",
        "AAAAAAAA-BBBB-4CCC-8DDD-EEEEFFFF0000/nested",
        "",
    ],
)
def test_session_verb_rejects_unsafe_ids(tmp_path, bad_sid):
    main = make_repo(tmp_path)
    r = run_session_verb(main, bad_sid)
    assert r.returncode != 0
    assert not (main / "tmp" / "worktrees" / "session").exists()


def test_branch_exists_without_lane_refuses_with_recovery(tmp_path):
    main = make_repo(tmp_path)
    git(main, "branch", f"session/{SID}")
    r = run_session_verb(main, SID)
    assert r.returncode != 0
    combined = r.stdout + r.stderr
    assert "git worktree add" in combined  # recovery instruction
    # never deleted as recovery
    assert git(main, "branch", "--list", f"session/{SID}")


def test_lane_exists_with_wrong_branch_refuses(tmp_path):
    main = make_repo(tmp_path)
    lane = lane_path(main)
    lane.parent.mkdir(parents=True)
    git(main, "worktree", "add", str(lane), "-b", "feat/imposter", "main")
    r = run_session_verb(main, SID)
    assert r.returncode != 0
    assert git(lane, "branch", "--show-current") == "feat/imposter"


# ── AC-07 (setup half): setup produces no diff, no .gitignore append ──


def test_setup_produces_no_tree_diff(tmp_path):
    main = make_repo(tmp_path)
    (main / ".venv").mkdir()
    (main / ".env").write_text("KEY=v\n")
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main)
    status = git(lane, "status", "--porcelain", "--untracked-files=all")
    assert status == ""
    assert (lane / ".gitignore").read_text() == (main / ".gitignore").read_text()


# ── SessionStart hook wrapper ────────────────────────────────────────


def hook_env(main, log_dir, flag=None):
    env = {
        "HOOK_LOG_DIR": str(log_dir),
        "FR902_REPO": str(main),
        "FR902_WORKTREE_SH": str(WORKTREE_SH),
    }
    if flag is not None:
        env["FR902_LIVE_FLAG"] = str(flag)
    return env


def test_hook_not_live_is_noop(tmp_path):
    main = make_repo(tmp_path)
    log_dir = tmp_path / "logs"
    r = run_hook_script(
        SESSION_WORKTREE,
        start_payload(SID, main),
        hook_env(main, log_dir, flag=tmp_path / "missing-flag"),
    )
    assert r.returncode == 0
    assert not lane_path(main).exists()


def test_hook_live_creates_lane_and_record(tmp_path):
    main = make_repo(tmp_path)
    log_dir = tmp_path / "logs"
    flag = tmp_path / "fr902.live"
    flag.write_text("armed\n")
    r = run_hook_script(
        SESSION_WORKTREE, start_payload(SID, main), hook_env(main, log_dir, flag)
    )
    assert r.returncode == 0, r.stderr
    lane = lane_path(main)
    assert lane.is_dir()
    rec = log_dir / "session-lanes" / f"{SID}.json"
    assert rec.exists()
    data = json.loads(rec.read_text())
    assert data["lane"] == str(lane.resolve())
    assert data["branch"] == f"session/{SID}"
    assert str(lane.resolve()) in r.stdout


def test_hook_invalid_sid_nonzero_and_audited(tmp_path):
    main = make_repo(tmp_path)
    log_dir = tmp_path / "logs"
    flag = tmp_path / "fr902.live"
    flag.write_text("armed\n")
    r = run_hook_script(
        SESSION_WORKTREE,
        start_payload("../../evil", main),
        hook_env(main, log_dir, flag),
    )
    assert r.returncode != 0
    assert not (main / "tmp" / "worktrees" / "session").exists()
    assert any(
        e.get("hook") == "session-worktree" and e.get("decision") == "reject"
        for e in read_audit(log_dir)
    )
