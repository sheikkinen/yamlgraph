#!/usr/bin/env python3
"""FR-888 AC-10: orphan-worktree detection on the situation board.

A worktree whose branch has no open PR and no live pipeline is flagged
with age and untracked-file count; auto-deletion is explicitly absent.
Fixtures only — never the operator's real trees.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import now  # noqa: E402  # CONF-392 idiom

GIT = shutil.which("git") or "/usr/bin/git"


def _git(cwd, *args):
    subprocess.run([GIT, *args], cwd=cwd, check=True, capture_output=True)


def test_orphan_worktree_flagged_with_age_and_untracked(tmp_path):
    main = tmp_path / "repo"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    (main / "README.md").write_text("x", encoding="utf-8")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "init")
    wt = tmp_path / "wt-orphan"
    _git(main, "worktree", "add", str(wt), "-b", "feat/orphan", "main")
    (wt / "unlanded-draft.md").write_text("no recovery path", encoding="utf-8")

    lines = now.orphan_worktree_lines(main, gh_available=False)
    assert len(lines) == 1
    line = lines[0]
    assert "feat/orphan" in line
    assert "untracked=1" in line
    assert "pr=?" in line  # gh unavailable → unknown, reported not assumed


def test_live_pipeline_branch_suppressed(tmp_path):
    # AC-10 second branch: a tree owned by a live pipeline is not an orphan
    main = tmp_path / "repo"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    (main / "README.md").write_text("x", encoding="utf-8")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "init")
    wt = tmp_path / "wt-live"
    _git(main, "worktree", "add", str(wt), "-b", "feat/live", "main")
    assert (
        now.orphan_worktree_lines(main, gh_available=False, live_branches={"feat/live"})
        == []
    )
    assert len(now.orphan_worktree_lines(main, gh_available=False)) == 1


def test_main_checkout_never_listed_as_orphan(tmp_path):
    main = tmp_path / "repo"
    main.mkdir()
    _git(main, "init", "-b", "main")
    _git(main, "config", "user.email", "t@t")
    _git(main, "config", "user.name", "t")
    (main / "README.md").write_text("x", encoding="utf-8")
    _git(main, "add", "-A")
    _git(main, "commit", "-m", "init")
    assert now.orphan_worktree_lines(main, gh_available=False) == []
