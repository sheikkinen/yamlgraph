#!/usr/bin/env python3
"""FR-902 AC-04..AC-08: fenced checkpoint commits on the Stop hook.

Run:  pytest .github/hooks/tests/test_fr902_checkpoint.py -q --no-cov
"""

import pytest
from fr902_fixtures import (
    SESSION_CHECKPOINT,
    SID,
    checkpoint_env,
    checkpoint_log,
    git,
    lane_path,
    make_repo,
    read_audit,
    run_hook_script,
    run_session_verb,
    stop_payload,
    write_lane_record,
    write_store,
)

pytestmark = pytest.mark.req("REQ-YG-630")


@pytest.fixture
def laned(tmp_path):
    main = make_repo(tmp_path)
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main).resolve()
    log_dir = tmp_path / "logs"
    write_lane_record(log_dir, SID, lane, f"session/{SID}")
    store = write_store(tmp_path / f"{SID}.jsonl", 3)
    return {"main": main, "lane": lane, "log_dir": log_dir, "store": store}


def fire_stop(fx, store=None):
    return run_hook_script(
        SESSION_CHECKPOINT,
        stop_payload(SID, store or fx["store"], fx["main"]),
        checkpoint_env(fx["main"], fx["log_dir"]),
    )


# ── AC-04: commit on tree change with message + trailers ─────────────


def test_checkpoint_commits_on_tree_change(laned):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    r = fire_stop(laned)
    assert r.returncode == 0, r.stderr
    sha, subject, trailers = checkpoint_log(laned["lane"])[0]
    assert subject == "checkpoint(session): turn 3"
    assert f"Session-Id: {SID}" in trailers
    assert "Request-Index: 3" in trailers


def test_setup_alone_produces_no_checkpoint(laned):
    main_tip = git(laned["main"], "rev-parse", "main")
    r = fire_stop(laned)
    assert r.returncode == 0
    assert git(laned["lane"], "rev-parse", "HEAD") == main_tip


# ── AC-05: duplicate Stop idempotency ────────────────────────────────


def test_duplicate_stop_creates_no_second_commit(laned):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    assert fire_stop(laned).returncode == 0
    count_after_first = len(checkpoint_log(laned["lane"]))
    assert fire_stop(laned).returncode == 0
    assert len(checkpoint_log(laned["lane"])) == count_after_first


def test_later_tree_change_creates_new_checkpoint(laned):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    assert fire_stop(laned).returncode == 0
    (laned["lane"] / "docs" / "turn.md").write_text("more work\n")
    assert fire_stop(laned).returncode == 0
    subjects = [s for _, s, _ in checkpoint_log(laned["lane"])]
    assert subjects.count("checkpoint(session): turn 3") == 2


# ── AC-06: request-index from store replay; skip when not flushed ────


def test_request_index_tracks_store_growth(laned, tmp_path):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    store5 = write_store(tmp_path / "grown.jsonl", 5)
    assert fire_stop(laned, store=store5).returncode == 0
    _, subject, trailers = checkpoint_log(laned["lane"])[0]
    assert subject == "checkpoint(session): turn 5"
    assert "Request-Index: 5" in trailers


def test_store_missing_skips_with_audit_and_no_commit(laned, tmp_path):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    r = fire_stop(laned, store=tmp_path / "not-flushed.jsonl")
    assert r.returncode == 0
    assert checkpoint_log(laned["lane"]) == checkpoint_log(laned["main"])
    assert any(
        e.get("hook") == "session-checkpoint" and "store" in e.get("reason", "")
        for e in read_audit(laned["log_dir"])
    )


# ── guard rails: no lane record / wrong branch ───────────────────────


def test_no_lane_record_is_noop(tmp_path):
    main = make_repo(tmp_path)
    assert run_session_verb(main, SID).returncode == 0
    lane = lane_path(main)
    (lane / "docs" / "turn.md").write_text("work\n")
    store = write_store(tmp_path / "s.jsonl", 1)
    r = run_hook_script(
        SESSION_CHECKPOINT,
        stop_payload(SID, store, main),
        checkpoint_env(main, tmp_path / "logs"),
    )
    assert r.returncode == 0
    assert git(lane, "rev-parse", "HEAD") == git(main, "rev-parse", "main")


def test_head_off_session_branch_refuses(laned):
    git(laned["lane"], "checkout", "-b", "feat/hijack")
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    r = fire_stop(laned)
    assert r.returncode != 0
    assert git(laned["lane"], "rev-parse", "HEAD") == git(
        laned["main"], "rev-parse", "main"
    )


# ── AC-07: .gitignore respected ──────────────────────────────────────


def test_gitignore_respected_secrets_never_staged(laned):
    (laned["lane"] / ".env").unlink(missing_ok=True)
    (laned["lane"] / ".env").write_text("SECRET=x\n")
    (laned["lane"] / ".env.local").write_text("SECRET=y\n")
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    assert fire_stop(laned).returncode == 0
    tree = git(laned["lane"], "ls-tree", "-r", "--name-only", "HEAD")
    assert ".env" not in tree.split()
    assert ".env.local" not in tree.split()
    assert "docs/turn.md" in tree.split()


# ── AC-08: checkpoints never land on main via squash merge ───────────


def test_squash_merge_keeps_checkpoints_off_main(laned):
    (laned["lane"] / "docs" / "turn.md").write_text("work\n")
    assert fire_stop(laned).returncode == 0
    git(laned["main"], "merge", "--squash", f"session/{SID}")
    git(laned["main"], "commit", "-m", "feat(x): FR-902 squashed result")
    main_log = git(laned["main"], "log", "--format=%s%n%(trailers)")
    assert "checkpoint(session)" not in main_log
    assert "Request-Index" not in main_log
    assert (laned["main"] / "docs" / "turn.md").exists()
