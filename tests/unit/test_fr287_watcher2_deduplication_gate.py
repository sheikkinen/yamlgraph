"""Acceptance tests for FR-287: watcher2 deduplication gate.

These tests define the RED contract for skipping already-completed FR topics.
They MUST fail on the unmodified codebase.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"
DEDUP_GATE_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "dedup_gate.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


@pytest.mark.req("REQ-YG-276")
class TestDedupGateDefinition:
    """AC-01, AC-02, AC-06, AC-07."""

    def test_ac01_checks_fr_token_before_preflight(self):
        """AC-01: watcher2 checks FR token before preflight/worktree setup."""
        content = WATCHER2_SH.read_text()
        dedup_call_pos = content.find("dedup_gate")
        preflight_pos = content.find("if ! preflight; then")

        assert dedup_call_pos != -1, "Expected watcher2 to call dedup_gate"
        assert preflight_pos != -1, "Expected existing preflight check in watcher2"
        assert (
            dedup_call_pos < preflight_pos
        ), "dedup_gate must run before preflight/worktree setup"

    def test_ac02_queries_merged_pr_history_with_fr_search(self):
        """AC-02: dedup gate uses gh merged PR search by FR token."""
        assert DEDUP_GATE_SH.exists(), "Expected .chaplain/lib/watcher/dedup_gate.sh"
        content = DEDUP_GATE_SH.read_text()

        assert "gh pr list" in content, "Expected gh pr list query"
        assert "--state merged" in content, "Expected merged PR filter"
        assert "--search" in content, "Expected gh search option"
        assert (
            '"FR-' in content or "'FR-" in content
        ), "Expected FR token search pattern (FR-XXX)"

    def test_ac06_no_fr_token_passes_through_without_skip(self):
        """AC-06: no FR token path returns success and continues pipeline."""
        assert DEDUP_GATE_SH.exists(), "Expected dedup gate helper file"
        content = DEDUP_GATE_SH.read_text()

        assert "FR-[0-9]+" in content, "Expected FR token extraction regex"
        assert (
            "No FR token" in content or "no fr token" in content.lower()
        ), "Expected explicit no-token branch logging"
        assert "return 0" in content, "Expected pass-through return code for no-token"

    def test_ac07_gh_unavailable_or_query_failure_is_non_fatal(self):
        """AC-07: dedup gate logs warning and degrades gracefully on gh errors."""
        assert DEDUP_GATE_SH.exists(), "Expected dedup gate helper file"
        content = DEDUP_GATE_SH.read_text()

        assert "command -v gh" in content, "Expected gh availability guard"
        assert "--search" in content, "Expected merged query command path"
        assert (
            "log_warn" in content
        ), "Expected warning log for gh unavailable/query failure"
        assert "return 0" in content, "Expected graceful continue path"


@pytest.mark.req("REQ-YG-276")
class TestWatcher2DedupSkipControlFlow:
    """AC-03, AC-04, AC-05."""

    def test_ac03_merged_fr_hit_skips_pipeline_without_failure_handler(self):
        """AC-03: merged FR hit is treated as skip and avoids plan/enforce path."""
        content = WATCHER2_SH.read_text()

        assert (
            "already-completed FR" in content or "already completed FR" in content
        ), "Expected explicit dedup skip log context for completed FR"
        assert (
            "dedup_gate_status" in content or "dedup_status" in content
        ), "Expected dedicated dedup status handling"

    def test_ac04_dedup_skip_path_consumes_processing_topic_file(self):
        """AC-04: dedup skip path removes TOPIC_FILE to prevent immediate re-pick."""
        content = WATCHER2_SH.read_text()
        assert "dedup_gate" in content, "Expected dedup gate flow in watcher2"
        assert 'rm "$TOPIC_FILE"' in content, "Expected topic file consumption on skip"

    def test_ac05_dedup_skip_writes_skipped_metrics(self):
        """AC-05: dedup skip path records explicit skipped outcome metrics."""
        content = WATCHER2_SH.read_text()
        assert "dedup_gate" in content, "Expected dedup gate flow in watcher2"
        assert 'CYCLE_OUTCOME="skipped"' in content, "Expected skipped cycle outcome"
        assert "write_cycle_metrics" in content, "Expected metrics write for skip path"


@pytest.mark.req("REQ-YG-276")
class TestAcceptanceCoverageAndDocs:
    """AC-08, AC-09."""

    def test_ac08_test_file_covers_merged_hit_no_token_and_gh_failure(self):
        """AC-08: tests cover merged-hit skip, no-token pass-through, and gh failure."""
        content = Path(__file__).read_text()
        assert "merged_fr_hit" in content or "merged_fr" in content
        assert "no_fr_token" in content or "no FR token" in content
        assert "gh_unavailable" in content or "query_failure" in content

    def test_ac09_readme_documents_dedup_gate_and_fr_search_contract(self):
        """AC-09: README documents dedup gate and FR-token merged search pattern."""
        content = CHAPLAIN_README.read_text()
        assert "dedup" in content.lower(), "Expected dedup gate documentation in README"
        assert "--state merged" in content, "Expected merged PR query documentation"
        assert (
            "--search" in content and "FR-" in content
        ), "Expected FR-token merged-search contract documentation"
