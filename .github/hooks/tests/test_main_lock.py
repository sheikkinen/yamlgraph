"""FR-889 OS lock — worktree.sh lock-main / unlock-main / sync.

Split from test_main_write_guard.py (size-gate ratchet): the kernel-level
write barrier, carve-outs, marker/audit rows, sync relock invariants.
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

WORKTREE_SH = Path(__file__).resolve().parents[3] / "scripts" / "worktree.sh"
GIT = shutil.which("git") or "/usr/bin/git"
pytestmark = pytest.mark.req("REQ-YG-631")


def _git(cwd, *args):
    subprocess.run([GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)


def wt_sh(cwd, *args):
    return subprocess.run(
        [str(WORKTREE_SH), *args], cwd=cwd, capture_output=True, text=True
    )


@pytest.fixture
def lock_repo(tmp_path):
    """Cloned main checkout with governed roots; unlocked again on exit."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(origin, "init", "-b", "main")
    _git(origin, "config", "user.email", "t@t")
    _git(origin, "config", "user.name", "t")
    for d in (
        "yamlgraph",
        "tests",
        "scripts",
        "capabilities",
        ".github/hooks/scripts",
        "docs",
        "feature-requests",
        "changelog",
    ):
        (origin / d).mkdir(parents=True)
        (origin / d / ".keep").write_text("")
    (origin / "scripts" / "tool.sh").write_text("#!/bin/sh\n")
    (origin / "scripts" / "tool.sh").chmod(0o755)
    (origin / "yamlgraph" / "x.py").write_text("x = 1\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-m", "init")
    main = tmp_path / "mainclone"
    subprocess.run(
        [GIT, "clone", "-q", str(origin), str(main)],
        check=True,
        capture_output=True,
        text=True,
    )
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    yield main
    subprocess.run(["/bin/chmod", "-R", "u+w", str(tmp_path)], check=False)


def _is_locked(main):
    return not os.access(main / "yamlgraph", os.W_OK)


def test_lock_main_makes_terminal_write_fail_at_the_kernel(lock_repo):
    r = wt_sh(lock_repo, "lock-main")
    assert r.returncode == 0, r.stderr
    w = subprocess.run(
        ["/bin/sh", "-c", "echo x > yamlgraph/f.py"],
        cwd=lock_repo,
        capture_output=True,
        text=True,
    )
    assert w.returncode != 0
    assert "ermission denied" in w.stderr  # the kernel, zero hook lines
    assert not (lock_repo / "yamlgraph" / "f.py").exists()


def test_lock_covers_in_place_edit_of_existing_file(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    with pytest.raises(PermissionError):
        (lock_repo / "yamlgraph" / "x.py").write_text("clobber")


def test_lock_and_unlock_are_idempotent(lock_repo):
    for _ in range(2):
        assert wt_sh(lock_repo, "lock-main").returncode == 0
        assert _is_locked(lock_repo)
    for _ in range(2):
        assert wt_sh(lock_repo, "unlock-main").returncode == 0
        assert not _is_locked(lock_repo)


def test_lock_cycle_preserves_exec_and_group_bits(lock_repo):
    tool = lock_repo / "scripts" / "tool.sh"
    before = stat.S_IMODE(tool.stat().st_mode)
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    assert wt_sh(lock_repo, "unlock-main").returncode == 0
    assert stat.S_IMODE(tool.stat().st_mode) == before


def test_unlock_writes_audit_row_and_state_marker(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    marker = lock_repo / ".github/hooks/state/main-lock.json"
    assert json.loads(marker.read_text())["state"] == "locked"
    assert wt_sh(lock_repo, "unlock-main").returncode == 0
    assert json.loads(marker.read_text())["state"] == "unlocked"
    rows = (lock_repo / ".github/hooks/logs/audit.jsonl").read_text()
    assert "fr889-main-unlock" in rows


def test_carveouts_stay_writable_under_lock(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    with (lock_repo / ".github/hooks/logs/audit.jsonl").open("a") as fh:
        fh.write("{}\n")
    (lock_repo / ".github/hooks/state/probe.json").write_text("{}")
    with pytest.raises(PermissionError):
        (lock_repo / ".github/hooks/scripts/probe.sh").write_text("")
    with pytest.raises(PermissionError):
        (lock_repo / "docs" / "note.md").write_text("docs locked too")


def test_docs_and_feature_requests_locked(lock_repo):
    # operator amendment 2026-08-30: docs exception removed
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    for lane in ("docs", "feature-requests"):
        with pytest.raises(PermissionError):
            (lock_repo / lane / "note.md").write_text("no business on main")
    (lock_repo / "changelog" / "fragment.md").write_text("runtime lane open")


def test_sync_pulls_and_relocks(lock_repo, tmp_path):
    origin = tmp_path / "origin"
    (origin / "docs" / "update.md").write_text("upstream\n")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-m", "upstream")
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    r = wt_sh(lock_repo, "sync")
    assert r.returncode == 0, r.stderr
    assert (lock_repo / "docs" / "update.md").exists()
    assert _is_locked(lock_repo)


def test_sync_relocks_even_when_pull_fails(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    _git(lock_repo, "remote", "set-url", "origin", "/nonexistent/void")
    r = wt_sh(lock_repo, "sync")
    assert r.returncode != 0
    assert _is_locked(lock_repo)
    marker = lock_repo / ".github/hooks/state/main-lock.json"
    assert json.loads(marker.read_text())["state"] == "locked"


def test_worktree_new_functions_on_locked_main(lock_repo):
    assert wt_sh(lock_repo, "lock-main").returncode == 0
    r = wt_sh(lock_repo, "new", "lockedwt")
    assert r.returncode == 0, r.stderr
    wt = lock_repo / "tmp/worktrees/feat/lockedwt"
    (wt / "yamlgraph" / "new.py").write_text("writable = True\n")
