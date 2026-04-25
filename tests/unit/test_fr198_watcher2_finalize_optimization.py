"""Acceptance tests for FR-198: Watcher2 Finalize Pre-commit Optimization.

Tests the enhanced watcher2.sh finalize step to pre-format code before
pre-commit loops and increase retry attempts from 3 to 5.

Acceptance Criteria from FR-198:
- [ ] AC-01: `ruff check --fix` runs before pre-commit loop
- [ ] AC-02: `ruff format` runs before pre-commit loop
- [ ] AC-03: Pre-commit loop allows 5 attempts (was 3)
- [ ] AC-04: Failure message updated to reflect "5 attempts"
- [ ] AC-05: No copilot fallback triggered for auto-fixable cascading issues
- [ ] AC-06: Tests added for the optimization logic

Testing approach:
- Parse watcher2.sh to verify the structural changes exist
- Mock filesystem to test the optimization flow without real git operations
- Verify that ruff commands are called before the pre-commit loop
- Verify that the loop runs up to 5 attempts
- Verify that success after 4 attempts avoids copilot fallback

All tests target the unmodified code and MUST fail (RED phase).
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"


@pytest.mark.req("REQ-YG-286")
class TestWatcher2FinalizeOptimization:
    """Tests for watcher2.sh finalize step optimization."""

    def test_ac01_ruff_check_fix_before_loop(self):
        """AC-01: `ruff check --fix` runs before pre-commit loop."""
        # Read the watcher2.sh file and parse the finalize section
        watcher_content = WATCHER2_SH.read_text()

        # Find the finalize section (between step 4 comment and the pre-commit loop)
        finalize_section = re.search(
            r"# ── Enforce Step 4: Finalize.*?for attempt in",
            watcher_content,
            re.DOTALL,
        )

        assert finalize_section, "Could not find finalize section in watcher2.sh"
        finalize_text = finalize_section.group(0)

        # Verify ruff check --fix is called before the loop
        assert "ruff check --fix" in finalize_text, (
            "ruff check --fix command not found before pre-commit loop"
        )

        # Verify it's targeting the right directories
        assert "yamlgraph/" in finalize_text and "tests/" in finalize_text, (
            "ruff check --fix should target yamlgraph/ and tests/ directories"
        )

    def test_ac02_ruff_format_before_loop(self):
        """AC-02: `ruff format` runs before pre-commit loop."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the finalize section
        finalize_section = re.search(
            r"# ── Enforce Step 4: Finalize.*?for attempt in",
            watcher_content,
            re.DOTALL,
        )

        assert finalize_section, "Could not find finalize section in watcher2.sh"
        finalize_text = finalize_section.group(0)

        # Verify ruff format is called before the loop
        assert "ruff format" in finalize_text, (
            "ruff format command not found before pre-commit loop"
        )

        # Verify it's targeting the right directories
        assert "yamlgraph/" in finalize_text and "tests/" in finalize_text, (
            "ruff format should target yamlgraph/ and tests/ directories"
        )

    def test_ac03_precommit_loop_five_attempts(self):
        """AC-03: Pre-commit loop allows 5 attempts (was 3)."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the pre-commit loop definition
        loop_match = re.search(r"for attempt in ([0-9\s]+);", watcher_content)
        assert loop_match, "Could not find pre-commit loop in watcher2.sh"

        loop_attempts = loop_match.group(1).split()

        # Verify loop goes from 1 to 5
        expected_attempts = ["1", "2", "3", "4", "5"]
        assert loop_attempts == expected_attempts, (
            f"Pre-commit loop should allow 5 attempts, found: {loop_attempts}"
        )

    def test_ac04_failure_message_five_attempts(self):
        """AC-04: Failure message updated to reflect "5 attempts"."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the failure message after pre-commit loop
        failure_msg_match = re.search(
            r"Pre-commit still failing after (\d+) attempts", watcher_content
        )

        assert failure_msg_match, "Could not find pre-commit failure message"

        attempts_in_msg = failure_msg_match.group(1)
        assert attempts_in_msg == "5", (
            f"Failure message should mention '5 attempts', found: '{attempts_in_msg} attempts'"
        )

    def test_ac05_loop_attempt_logging_consistent(self):
        """AC-05: Loop attempt logging shows correct total (N/5 format)."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the loop logging statement
        log_match = re.search(r"Pre-commit attempt \$attempt/(\d+)", watcher_content)
        assert log_match, "Could not find pre-commit attempt logging statement"

        total_in_log = log_match.group(1)
        assert total_in_log == "5", (
            "Loop logging should show 'attempt $attempt/5', found: '/$total_in_log'"
        )

    def test_ac06_git_add_before_ruff_commands(self):
        """AC-06: git add runs before ruff commands to stage files."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the section before the pre-commit loop
        pre_loop_section = re.search(
            r"# ── Enforce Step 4: Finalize.*?for attempt in",
            watcher_content,
            re.DOTALL,
        )

        assert pre_loop_section, "Could not find finalize section"
        pre_loop_text = pre_loop_section.group(0)

        # Verify git add comes before ruff commands
        git_add_pos = pre_loop_text.find("git add -A")
        ruff_check_pos = pre_loop_text.find("ruff check --fix")
        ruff_format_pos = pre_loop_text.find("ruff format")

        assert git_add_pos != -1, "git add -A not found before pre-commit loop"
        assert ruff_check_pos != -1, "ruff check --fix not found"
        assert ruff_format_pos != -1, "ruff format not found"

        assert git_add_pos < ruff_check_pos, (
            "git add -A should come before ruff check --fix"
        )
        assert ruff_check_pos < ruff_format_pos, (
            "ruff check --fix should come before ruff format"
        )

    def test_ac07_git_add_after_ruff_commands(self):
        """AC-07: git add runs after ruff commands to stage fixes."""
        watcher_content = WATCHER2_SH.read_text()

        # Find the section before the pre-commit loop
        pre_loop_section = re.search(
            r"# ── Enforce Step 4: Finalize.*?for attempt in",
            watcher_content,
            re.DOTALL,
        )

        assert pre_loop_section, "Could not find finalize section"
        pre_loop_text = pre_loop_section.group(0)

        # Find all git add -A positions
        git_add_positions = [
            m.start() for m in re.finditer(r"git add -A", pre_loop_text)
        ]
        ruff_format_pos = pre_loop_text.find("ruff format")

        assert len(git_add_positions) >= 2, (
            "Should have git add -A both before and after ruff commands"
        )
        assert ruff_format_pos != -1, "ruff format not found"

        # The last git add should be after ruff format
        last_git_add_pos = max(git_add_positions)
        assert last_git_add_pos > ruff_format_pos, (
            "git add -A should run after ruff format to stage the fixes"
        )


@pytest.mark.req("REQ-YG-286")
def test_current_watcher2_has_five_attempts():
    """Optimized watcher2.sh should have 5 attempts for pre-commit resilience."""
    watcher_content = WATCHER2_SH.read_text()

    loop_match = re.search(r"for attempt in ([0-9\s]+);", watcher_content)
    assert loop_match, "Could not find pre-commit loop"

    loop_attempts = loop_match.group(1).split()
    assert len(loop_attempts) == 5, (
        f"Optimized code should have 5 attempts, found: {len(loop_attempts)}"
    )
    assert loop_attempts == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ], f"Attempts should be [1..5], found: {loop_attempts}"


@pytest.mark.req("REQ-YG-286")
def test_current_watcher2_has_pre_formatting():
    """Optimized watcher2.sh should have pre-formatting before the pre-commit loop."""
    watcher_content = WATCHER2_SH.read_text()

    # Find the finalize section (between step 4 comment and the pre-commit loop)
    finalize_section = re.search(
        r"# ── Enforce Step 4: Finalize.*?for attempt in", watcher_content, re.DOTALL
    )

    assert finalize_section, "Could not find finalize section"
    finalize_text = finalize_section.group(0)

    # Pre-formatting should exist to reduce auto-fix cascades
    assert "ruff check --fix" in finalize_text, (
        "Optimized code should have ruff check --fix before loop"
    )
    assert "ruff format" in finalize_text, (
        "Optimized code should have ruff format before loop"
    )
