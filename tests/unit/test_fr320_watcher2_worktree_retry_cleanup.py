"""RED acceptance tests for FR-320: watcher2 retry-safe worktree setup cleanup."""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WORKTREE_SETUP_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_setup.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


@pytest.mark.req("REQ-YG-276")
class TestWatcher2WorktreeRetryCleanup:
    """Acceptance tests AC-01..AC-07 for FR-320."""

    def test_ac01_removes_branch_attached_worktree_before_branch_delete(self):
        """AC-01: cleanup removes branch-attached worktree entries before branch delete."""
        content = WORKTREE_SETUP_SH.read_text()
        assert (
            "git worktree list --porcelain" in content
        ), "Expected explicit worktree binding enumeration for WT_BRANCH cleanup"
        assert re.search(
            r"git worktree list --porcelain[\s\S]{0,500}git worktree remove",
            content,
        ), "Expected branch-attached worktree removal sequence"

    def test_ac02_removes_stale_wt_dir_before_worktree_add(self):
        """AC-02: stale WT_DIR is removed before git worktree add."""
        content = WORKTREE_SETUP_SH.read_text()
        assert (
            'if [[ -d "$WT_DIR" ]]' in content
        ), "Expected explicit stale WT_DIR guard before creating worktree"
        wt_dir_cleanup_pos = content.find('if [[ -d "$WT_DIR" ]]')
        worktree_add_pos = content.find(
            'git worktree add "$WT_DIR" -b "$WT_BRANCH" main'
        )
        assert wt_dir_cleanup_pos != -1, "Expected WT_DIR cleanup block"
        assert worktree_add_pos != -1, "Expected worktree add command"
        assert (
            wt_dir_cleanup_pos < worktree_add_pos
        ), "WT_DIR cleanup must occur before git worktree add"

    def test_ac03_no_silent_branch_delete_swallow_pattern(self):
        """AC-03: branch delete cleanup path must not silently swallow failures."""
        content = WORKTREE_SETUP_SH.read_text()
        assert (
            'git branch -D "$WT_BRANCH" 2>/dev/null || true' not in content
        ), "Silent branch-delete swallow must be removed from retry cleanup path"

    def test_ac04_unrecoverable_local_cleanup_returns_error_path(self):
        """AC-04: unrecoverable local cleanup must emit explicit error path."""
        content = WORKTREE_SETUP_SH.read_text()
        assert re.search(
            r'if ! git branch -D "\$WT_BRANCH"[\s\S]{0,220}log_error[\s\S]{0,120}return 1',
            content,
        ), "Expected explicit failure path when local branch cleanup cannot recover"

    def test_ac05_remote_delete_attempt_is_best_effort(self):
        """AC-05: setup attempts remote stale-branch delete as warning-only cleanup."""
        content = WORKTREE_SETUP_SH.read_text()
        assert (
            'git push origin --delete "$WT_BRANCH"' in content
        ), "Expected remote stale branch cleanup attempt in setup path"
        assert re.search(
            r'git push origin --delete "\$WT_BRANCH"[\s\S]{0,80}(?:\|\|\s*log_warn|&&\s*log_info)',
            content,
        ), "Expected best-effort remote delete handling (warn-only on failure)"

    def test_ac06_merged_pr_collision_guard_still_present(self):
        """AC-06: merged-PR collision guard remains intact."""
        content = WORKTREE_SETUP_SH.read_text()
        assert "gh pr list" in content, "Expected merged-PR collision query"
        assert "--state merged" in content, "Expected merged PR filter"
        assert '--head "$WT_BRANCH"' in content, "Expected branch-specific merged query"

    def test_ac07_readme_retry_section_documents_automated_cleanup(self):
        """AC-07: README retry section documents automated setup cleanup."""
        content = CHAPLAIN_README.read_text()
        assert (
            "worktree_setup.sh" in content and "automated cleanup" in content.lower()
        ), "Expected README to document automated retry cleanup in worktree_setup.sh"
