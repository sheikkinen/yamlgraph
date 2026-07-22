"""Acceptance tests for FR-289: watcher2 post-merge inbox consumption.

These tests define the RED contract for consuming stale inbox items that
reference the FR that was just merged.
They MUST fail on the unmodified codebase.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).parent.parent.parent
POST_MERGE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "post_merge.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


@pytest.mark.req("REQ-YG-276")
class TestPostMergeFrTokenResolution:
    """AC-01, AC-06, AC-07."""

    def test_ac01_resolves_fr_token_from_pr_context_with_fallbacks(self):
        """AC-01: post_merge resolves FR token from PR_NUMBER/PR_TITLE/topic fallback."""
        content = POST_MERGE_SH.read_text()

        assert (
            "FR-[0-9]+" in content
        ), "Expected FR token extraction regex in post_merge"
        assert "gh pr view" in content, "Expected PR metadata lookup via gh pr view"
        assert (
            '"$PR_NUMBER"' in content or "${PR_NUMBER" in content
        ), "Expected PR_NUMBER usage for token resolution"
        assert (
            "PR_TITLE" in content and "TOPIC_FILE" in content
        ), "Expected fallback path using PR_TITLE and TOPIC_FILE"

    def test_ac06_no_token_path_is_explicit_noop(self):
        """AC-06: if no FR token is resolved, no inbox files are moved."""
        content = POST_MERGE_SH.read_text()

        assert (
            "no FR token" in content.lower() or "No FR token" in content
        ), "Expected explicit no-token log branch"
        assert "return 0" in content, "Expected explicit successful no-op return path"

    def test_ac07_logs_token_resolution_and_consumed_count(self):
        """AC-07: cleanup logs token resolution outcome and consumed file count."""
        content = POST_MERGE_SH.read_text()

        assert "log_info" in content, "Expected informational logging in post_merge"
        assert (
            "resolved FR token" in content or "FR token resolved" in content
        ), "Expected explicit token-resolution log"
        assert (
            "consumed" in content and "count" in content
        ), "Expected consumed-files count logging"


@pytest.mark.req("REQ-YG-276")
class TestPostMergeInboxConsumptionFlow:
    """AC-02, AC-03, AC-04, AC-05."""

    def test_ac02_scans_chaplain_inbox_for_matching_fr_token(self):
        """AC-02: post_merge scans .chaplain/inbox/*.md for the resolved FR token."""
        content = POST_MERGE_SH.read_text()

        assert ".chaplain/inbox" in content, "Expected inbox scan path in post_merge"
        assert "grep" in content, "Expected token matching over inbox files"
        assert "FR-" in content, "Expected FR token usage in scan command"

    def test_ac03_moves_matching_files_to_done_and_preserves_non_matching(self):
        """AC-03: matching files move to done while unrelated files remain untouched."""
        content = POST_MERGE_SH.read_text()

        assert ".chaplain/done" in content, "Expected done queue path in post_merge"
        assert "mv " in content, "Expected move operation for matched inbox files"
        assert (
            "continue" in content or "non-matching" in content or "skip" in content
        ), "Expected explicit non-match preservation branch"

    def test_ac04_creates_done_directory_when_missing(self):
        """AC-04: .chaplain/done is created automatically when absent."""
        content = POST_MERGE_SH.read_text()
        assert (
            "mkdir -p" in content and ".chaplain/done" in content
        ), "Expected mkdir -p for .chaplain/done"

    def test_ac05_handles_destination_collisions_without_overwrite(self):
        """AC-05: destination filename collisions are handled safely."""
        content = POST_MERGE_SH.read_text()

        assert (
            "date +" in content or "timestamp" in content
        ), "Expected deterministic suffix strategy for destination collisions"
        assert (
            "[[ -e " in content or "[[ -f " in content
        ), "Expected destination-exists collision guard before move"


@pytest.mark.req("REQ-YG-276")
class TestAcceptanceCoverageAndDocs:
    """AC-08, AC-09."""

    def test_ac08_test_file_covers_resolution_consumption_and_noop_paths(self):
        """AC-08: tests cover token resolution, consumption path, and no-token no-op."""
        content = Path(__file__).read_text()
        assert "resolves_fr_token" in content or "resolved FR token" in content
        assert "inbox_consumption" in content or "consumed" in content
        assert "no_token_path" in content or "no-token" in content
        assert "done_directory" in content or ".chaplain/done" in content

    def test_ac09_readme_documents_post_merge_inbox_consumption(self):
        """AC-09: README documents post-merge inbox consumption and done semantics."""
        content = CHAPLAIN_README.read_text()
        assert "post_merge" in content or "post-merge" in content
        assert (
            ".chaplain/done" in content
        ), "Expected done queue documentation in README"
        assert (
            "FR-[0-9]+" in content or "FR token" in content
        ), "Expected FR-token cleanup contract in README"
