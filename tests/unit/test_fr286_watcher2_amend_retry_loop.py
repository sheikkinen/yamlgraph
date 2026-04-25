"""Acceptance tests for FR-286: Watcher2 AMEND Retry Loop.

Tests that AMEND verdicts trigger iterative revision cycles instead of
terminal failure, implementing the retry loop with judge feedback.

Testing approach:
- Check for missing functions and variables in watcher2.sh
- Verify missing step-revise.yaml graph
- Test current AMEND handling is terminal failure
- Validate missing retry loop components

All tests target the unmodified codebase and MUST fail (RED phase).
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"


@pytest.mark.req("REQ-YG-310")
class TestWatcher2AmendRetryLoop:
    """Test AMEND verdict retry loop implementation in watcher2.sh."""

    def test_amend_retry_functions_do_not_exist(self):
        """AC-01: AMEND retry functions should not exist in unmodified code."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # These functions should not exist yet
        missing_functions = [
            "handle_amend_verdict",
            "extract_judge_feedback", 
            "run_revision_step",
            "commit_revision_attempt",
            "handle_exhausted_amend_retries"
        ]
        
        for func in missing_functions:
            assert func not in watcher2_content, f"Function {func} should not exist yet"

    def test_amend_retry_variables_do_not_exist(self):
        """AC-02: AMEND retry variables should not exist in unmodified code."""
        # Check if retry-related variables are defined
        result = subprocess.run(
            ["bash", "-c", f"grep -n 'AMEND_RETRIES\\|MAX_AMEND_RETRIES' {WATCHER2_SH}"],
            capture_output=True,
            text=True
        )
        
        # These variables should not exist in the unmodified code
        assert result.returncode != 0, "AMEND retry variables should not exist yet"

    def test_step_revise_graph_does_not_exist(self):
        """AC-03: step-revise.yaml graph file should not exist yet."""
        revise_graph = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-revise.yaml"
        assert not revise_graph.exists(), "step-revise.yaml should not exist in unmodified code"

    def test_current_amend_handling_is_terminal_failure(self):
        """AC-04: Verify current AMEND handling calls handle_failure (baseline behavior)."""
        # Read watcher2.sh and verify current AMEND handling
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should find the current AMEND handling that calls handle_failure
        assert 'if [[ "$VERDICT" == "AMEND" || "$VERDICT" == "SPLIT" ]]' in watcher2_content
        assert 'handle_failure "judge $VERDICT"' in watcher2_content

    def test_no_amend_retry_loop_in_judge_section(self):
        """AC-05: Judge section should not contain retry loop logic yet."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Find the judge section and verify it doesn't have retry logic
        judge_section_start = watcher2_content.find("# ── Step 4: Judge")
        assert judge_section_start != -1, "Judge section should exist"
        
        # Extract judge section (until next major section or end)
        next_section = watcher2_content.find("# ── Phase 4:", judge_section_start)
        if next_section == -1:
            judge_section = watcher2_content[judge_section_start:]
        else:
            judge_section = watcher2_content[judge_section_start:next_section]
        
        # Should not contain retry loop logic
        assert 'while [[ "$VERDICT" == "AMEND"' not in judge_section
        assert 'AMEND_RETRIES' not in judge_section
        assert 'extract_judge_feedback' not in judge_section

    def test_judge_feedback_extraction_command_fails(self):
        """AC-06: Attempting to extract judge feedback should fail."""
        # This should fail because the function doesn't exist
        result = subprocess.run(
            ["bash", "-c", f"declare -f extract_judge_feedback"],
            capture_output=True,
            text=True
        )
        
        # Function should not be declared
        assert result.returncode != 0, "extract_judge_feedback function should not exist"

    def test_revision_commit_pattern_not_implemented(self):
        """AC-07: Revision commit message pattern should not exist."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should not find the revision commit message pattern
        assert 'FR revision (AMEND retry' not in watcher2_content
        assert 'commit_revision_attempt' not in watcher2_content

    def test_max_retries_enforcement_not_implemented(self):
        """AC-08: Maximum retry enforcement should not be implemented."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should not find retry limit enforcement
        assert 'MAX_AMEND_RETRIES' not in watcher2_content
        assert 'exhausted retries' not in watcher2_content

    def test_split_verdict_handling_unchanged(self):
        """AC-09: SPLIT verdict should still be handled with terminal failure."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # SPLIT should still be in the same condition as AMEND, calling handle_failure
        assert 'if [[ "$VERDICT" == "AMEND" || "$VERDICT" == "SPLIT" ]]' in watcher2_content
        # Should not have separate SPLIT handling for retry
        assert 'if [[ "$VERDICT" == "SPLIT" ]]' not in watcher2_content

    def test_judge_result_feedback_parsing_not_implemented(self):
        """AC-10: Judge result feedback parsing should not be implemented."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should not find judge feedback parsing logic
        feedback_patterns = [
            'judge_result.*feedback',
            'parse.*judge.*output',
            'extract.*AMEND.*message'
        ]
        
        for pattern in feedback_patterns:
            result = subprocess.run(
                ["bash", "-c", f"grep -E '{pattern}' {WATCHER2_SH}"],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, f"Pattern '{pattern}' should not exist yet"


@pytest.mark.req("REQ-YG-310")
class TestWatcher2AmendRetryStructuralChecks:
    """Structural checks for missing AMEND retry components."""

    def test_amend_specific_handling_missing(self):
        """Test that AMEND-specific handling (separate from SPLIT) is missing."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Should not have AMEND-only conditions (they're bundled with SPLIT currently)
        amend_only_patterns = [
            'if [[ "$VERDICT" == "AMEND" ]]',
            'case "$VERDICT" in.*AMEND',
            'VERDICT.*AMEND.*&&'
        ]
        
        for pattern in amend_only_patterns:
            result = subprocess.run(
                ["bash", "-c", f"grep -E '{pattern}' {WATCHER2_SH}"],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, f"AMEND-specific pattern '{pattern}' should not exist yet"

    def test_retry_loop_infrastructure_missing(self):
        """Test that retry loop infrastructure components are missing."""
        watcher2_content = WATCHER2_SH.read_text()
        
        # Check for retry-specific patterns that shouldn't exist
        retry_patterns = [
            'while.*AMEND',
            'AMEND.*retry',
            'retry.*AMEND',
            'increment.*AMEND',
            'AMEND.*count',
            'for.*retry.*AMEND'
        ]
        
        for pattern in retry_patterns:
            result = subprocess.run(
                ["bash", "-c", f"grep -iE '{pattern}' {WATCHER2_SH}"],
                capture_output=True,
                text=True
            )
            assert result.returncode != 0, f"AMEND retry pattern '{pattern}' should not exist yet"

    def test_copilot_session_resumption_for_revision_missing(self):
        """Test that copilot session resumption for revision is not implemented."""
        revise_graph = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-revise.yaml"
        assert not revise_graph.exists(), "step-revise.yaml should not exist"
        
        # Should not reference step-revise in watcher2.sh
        watcher2_content = WATCHER2_SH.read_text()
        assert 'step-revise.yaml' not in watcher2_content, "step-revise.yaml reference should not exist"