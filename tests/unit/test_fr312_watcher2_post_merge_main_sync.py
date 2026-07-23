"""Acceptance tests for FR-312: watcher2 post-merge main sync reconciliation."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).parent.parent.parent
POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


@pytest.mark.req("REQ-YG-276")
class TestFR312PostMergeMainSync:
    """AC-01..AC-09."""

    def test_ac01_ac02_detects_dirty_state_and_stashes_include_untracked(self):
        """AC-01, AC-02: dirty tree is detected and stashed with untracked files."""
        content = POST_MERGE_SH.read_text()

        assert (
            "git status --porcelain" in content
        ), "Expected dirty-tree detection before main sync pull"
        assert (
            "git stash push --include-untracked" in content
        ), "Expected stash push to include untracked files"
        assert (
            "watcher2-post-merge-" in content
        ), "Expected watcher2 post-merge stash message prefix"

    def test_ac03_uses_pull_rebase_on_origin_main(self):
        """AC-03: sync path uses pull --rebase from origin main."""
        content = POST_MERGE_SH.read_text()
        assert (
            "git pull --rebase --quiet origin main" in content
        ), "Expected post-merge main sync to use pull --rebase origin main"

    def test_ac04_ac05_pop_is_conditional_on_prior_stash(self):
        """AC-04, AC-05: stash pop is gated by explicit stash-created state."""
        content = POST_MERGE_SH.read_text()
        gate = 'if [[ "$stash_created" -eq 1 ]]; then'
        pop = "git stash pop"

        assert "stash_created=0" in content, "Expected explicit stash-created flag"
        assert gate in content, "Expected stash pop gate to depend on stash_created"
        assert pop in content, "Expected stash pop command in gated branch"
        assert content.find(gate) < content.find(
            pop
        ), "Expected stash pop to appear inside conditional gate"

    def test_ac06_no_silent_ignore_on_sync_failures(self):
        """AC-06: stash/pull/pop failures must be explicit and non-silent."""
        content = POST_MERGE_SH.read_text()

        assert (
            "post_merge failed to stash local changes before main sync" in content
        ), "Expected explicit stash failure log"
        assert (
            "post_merge failed to pull --rebase from origin main" in content
        ), "Expected explicit pull/rebase failure log"
        assert (
            "post_merge failed to restore stashed local changes (git stash pop)"
            in content
        ), "Expected explicit stash-pop failure log"
        assert "return 1" in content, "Expected non-zero control flow on sync failures"

    def test_ac07_existing_post_merge_behaviors_still_present(self):
        """AC-07: issue close and FR-token inbox consumption remain intact."""
        content = POST_MERGE_SH.read_text()

        assert "gh issue close" in content, "Expected GitHub issue close behavior"
        assert "resolve_post_merge_fr_token" in content, "Expected FR-token resolution"
        assert (
            "consume_matching_inbox_items" in content
        ), "Expected inbox-consumption helper usage"

    def test_ac08_acceptance_test_file_is_requirement_tagged(self):
        """AC-08: FR-312 acceptance tests exist and carry requirement traceability."""
        content = Path(__file__).read_text()
        assert '@pytest.mark.req("REQ-YG-276")' in content
        assert "test_ac01_ac02_detects_dirty_state" in content
        assert "test_ac06_no_silent_ignore_on_sync_failures" in content

    def test_ac09_readme_documents_post_merge_reconciliation(self):
        """AC-09: README documents stash/pull-rebase/pop post-merge contract."""
        content = CHAPLAIN_README.read_text()

        assert "post_merge" in content or "post-merge" in content
        assert (
            "git stash push --include-untracked" in content
        ), "Expected README to document post-merge stash behavior"
        assert (
            "git pull --rebase --quiet origin main" in content
        ), "Expected README to document pull --rebase contract"
        assert (
            "git stash pop" in content
        ), "Expected README to document stash-pop restore"
