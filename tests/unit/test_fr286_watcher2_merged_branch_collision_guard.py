"""Acceptance tests for FR-286: watcher2 merged-branch collision guard.

These tests define the RED contract for branch-collision prevention in watcher2.
They MUST fail on the unmodified codebase.
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")

REPO_ROOT = Path(__file__).parent.parent.parent
WORKTREE_SETUP_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_setup.sh"
WATCHER2_SH = REPO_ROOT / ".chaplain" / "start-system.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


@pytest.mark.req("REQ-YG-276")
class TestMergedBranchGuardInWorktreeSetup:
    """AC-01, AC-02, AC-06, AC-07."""

    def test_ac01_checks_merged_pr_history_before_worktree_creation(self):
        """AC-01: worktree_setup.sh checks merged PR history before git worktree add."""
        content = WORKTREE_SETUP_SH.read_text()
        assert "gh pr list" in content, "Expected merged-PR query via gh pr list"
        assert "--state merged" in content, "Expected merged PR state filter"
        assert '--head "$WT_BRANCH"' in content, "Expected head branch filter"
        assert (
            "--json number,url,mergedAt" in content
        ), "Expected merged PR metadata query"

        merged_query_pos = content.find("gh pr list")
        worktree_add_pos = content.find(
            'git worktree add "$WT_DIR" -b "$WT_BRANCH" main'
        )
        assert merged_query_pos != -1, "Expected merged query in worktree_setup.sh"
        assert worktree_add_pos != -1, "Expected existing worktree add command"
        assert (
            merged_query_pos < worktree_add_pos
        ), "Merged PR history check must occur before git worktree add"

    def test_ac02_returns_dedicated_skip_code_and_logs_merged_reference(self):
        """AC-02: merged-branch collision returns dedicated skip code and logs merged PR."""
        content = WORKTREE_SETUP_SH.read_text()
        assert "return 2" in content, "Expected dedicated skip return code (2)"
        assert (
            "merged pr" in content.lower() or "previously merged" in content.lower()
        ), "Expected explicit merged PR collision log message"

    def test_ac06_no_collision_path_keeps_existing_worktree_create_behavior(self):
        """AC-06: when no merged PR exists, standard worktree creation path remains."""
        content = WORKTREE_SETUP_SH.read_text()
        assert (
            'git worktree add "$WT_DIR" -b "$WT_BRANCH" main' in content
        ), "Expected existing worktree creation command"
        assert (
            "existing_merged_pr" in content
        ), "Expected explicit merged-collision branch check variable"

    def test_ac07_gh_query_failure_degrades_gracefully(self):
        """AC-07: merged-history query failure is non-fatal and guarded."""
        content = WORKTREE_SETUP_SH.read_text()
        assert "gh pr list" in content, "Expected merged-history gh query"
        assert re.search(
            r"gh pr list[\s\S]{0,200}\|\| true", content
        ), "Expected non-fatal gh query guard (|| true)"


@pytest.mark.req("REQ-YG-276")
class TestWatcher2SkipControlFlow:
    """AC-03, AC-04, AC-05."""

    def test_ac03_handles_collision_skip_without_handle_failure(self):
        """AC-03: start-system.sh handles skip code as non-failure (no handle_failure)."""
        content = WATCHER2_SH.read_text()
        assert (
            "if ! worktree_setup; then" not in content
        ), "Expected explicit handling for worktree_setup return code (including skip code)"
        assert re.search(
            r"worktree_setup[\s\S]{0,180}==\s*2", content
        ), "Expected dedicated branch for skip code 2"

    def test_ac04_skip_path_consumes_processing_topic_file(self):
        """AC-04: skip path removes processing topic file to avoid immediate retry."""
        content = WATCHER2_SH.read_text()
        assert re.search(
            r"skip[\s\S]{0,220}rm \"\$TOPIC_FILE\"",
            content,
            flags=re.IGNORECASE,
        ), "Expected explicit skip path that removes TOPIC_FILE"

    def test_ac05_skip_path_writes_metrics_with_skip_outcome(self):
        """AC-05: skip path records explicit skip outcome metrics."""
        content = WATCHER2_SH.read_text()
        assert re.search(
            r'CYCLE_OUTCOME="skip(?:ped)?"', content
        ), "Expected explicit skip outcome value"
        assert re.search(
            r'CYCLE_OUTCOME="skip(?:ped)?"[\s\S]{0,300}write_cycle_metrics',
            content,
        ), "Expected metrics write after setting skip outcome"


@pytest.mark.req("REQ-YG-276")
class TestChaplainDocumentationForCollisionGuard:
    """AC-09."""

    def test_ac09_readme_documents_merged_branch_collision_guard(self):
        """AC-09: .chaplain/README.md documents merged-branch collision guard."""
        content = CHAPLAIN_README.read_text()
        assert (
            "merged" in content.lower() and "branch" in content.lower()
        ), "Expected merged-branch guard documentation in .chaplain/README.md"
        assert (
            "--state merged" in content
        ), "Expected gh merged PR query pattern documented"
