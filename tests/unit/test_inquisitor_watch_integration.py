"""Unit tests for FR-261: Inquisitor moved from pre-commit hook to watch.sh loop.

Validates that:
1. The `inquisitor-background` post-commit hook is removed from `.pre-commit-config.yaml`
2. The watch.sh loop runs `.chaplain/inquisitor.sh --propose` after each enforce cycle
3. Inquisitor failure does not block the watch loop (`|| true`)
4. Inquisitor log output is captured to a timestamped file
"""

import os
import re

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _read_file(relative_path: str) -> str:
    """Read a file relative to the repository root."""
    path = os.path.join(REPO_ROOT, relative_path)
    assert os.path.exists(path), f"File not found: {relative_path}"
    with open(path) as f:
        return f.read()


@pytest.mark.req("REQ-YG-262")
class TestInquisitorHookRemoved:
    """Verify the inquisitor-background hook is no longer in pre-commit config."""

    def test_no_inquisitor_background_hook(self):
        """inquisitor-background hook must not exist in .pre-commit-config.yaml."""
        content = _read_file(".pre-commit-config.yaml")
        assert "inquisitor-background" not in content, (
            "inquisitor-background hook must be removed from .pre-commit-config.yaml (FR-261)"
        )

    def test_no_post_commit_inquisitor_entry(self):
        """No post-commit stage hook should reference inquisitor.sh."""
        content = _read_file(".pre-commit-config.yaml")
        # Should not have any nohup inquisitor pattern
        assert "nohup .chaplain/inquisitor.sh" not in content, (
            "Fire-and-forget inquisitor invocation must be removed (FR-261)"
        )


@pytest.mark.req("REQ-YG-262")
class TestInquisitorInWatchLoop:
    """Verify watch.sh runs the Inquisitor after each enforce cycle."""

    def test_watch_runs_inquisitor_with_propose(self):
        """watch.sh must invoke .chaplain/inquisitor.sh --propose."""
        content = _read_file(".chaplain/watch.sh")
        assert ".chaplain/inquisitor.sh --propose" in content, (
            "watch.sh must run inquisitor with --propose flag (FR-261)"
        )

    def test_inquisitor_failure_does_not_block_loop(self):
        """Inquisitor step must have || true to prevent watch loop blockage."""
        content = _read_file(".chaplain/watch.sh")
        # Find lines containing inquisitor.sh and verify || true
        lines = content.splitlines()
        inquisitor_lines = [
            line for line in lines if ".chaplain/inquisitor.sh" in line
        ]
        assert len(inquisitor_lines) > 0, (
            "watch.sh must contain .chaplain/inquisitor.sh invocation"
        )
        assert any("|| true" in line for line in inquisitor_lines), (
            "Inquisitor invocation must include '|| true' to prevent blocking (FR-261)"
        )

    def test_inquisitor_log_timestamped(self):
        """Inquisitor output must be captured to a timestamped log file."""
        content = _read_file(".chaplain/watch.sh")
        # The log filename should contain a date/time pattern
        assert re.search(r"inquisitor-.*\$\(date", content), (
            "Inquisitor log must use timestamped filename (FR-261)"
        )

    def test_inquisitor_after_enforce_before_finalization(self):
        """Inquisitor step must appear after enforce and before post-merge finalization."""
        content = _read_file(".chaplain/watch.sh")
        enforce_pos = content.find("enforce_worktree.sh")
        inquisitor_pos = content.find(".chaplain/inquisitor.sh --propose")
        finalize_pos = content.find("Post-merge finalization")
        assert enforce_pos != -1, "enforce_worktree.sh not found in watch.sh"
        assert inquisitor_pos != -1, (
            "inquisitor.sh --propose not found in watch.sh"
        )
        assert finalize_pos != -1, "Post-merge finalization section not found"
        assert enforce_pos < inquisitor_pos < finalize_pos, (
            "Inquisitor must run after enforce and before post-merge finalization"
        )

    def test_inquisitor_references_fr_261(self):
        """Inquisitor section in watch.sh must reference FR-261."""
        content = _read_file(".chaplain/watch.sh")
        assert "FR-261" in content, (
            "watch.sh inquisitor section must reference FR-261"
        )
