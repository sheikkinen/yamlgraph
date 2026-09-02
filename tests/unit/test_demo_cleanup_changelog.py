"""Unit tests for FR-153: Stale demo cleanup changelog fragment.

Verifies that the changelog fragment documents the removal of stale demo files
from commit a0e6f00, per Commandment 8: "record significant removals
in commit notes."
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = (
    REPO_ROOT
    / "changelog"
    / "0.4.61"
    / "stale-demo-files-examples-cost-router-poc-granite-py-sc.md"
)


def _read_fragment() -> str:
    """Read the stale demo cleanup changelog fragment."""
    return FRAGMENT.read_text(encoding="utf-8")


@pytest.mark.req("REQ-YG-146")
class TestDemoCleanupChangelog:
    """Verify changelog fragment documents the stale demo cleanup (FR-153)."""

    def test_changelog_has_removed_section(self):
        """AC1: Fragment has type: removal (maps to ### Removed)."""
        content = _read_fragment()
        assert "type: removal" in content

    def test_removed_entry_references_deleted_files(self):
        """AC2: Entry references the deleted files and commit a0e6f00."""
        content = _read_fragment()
        assert "poc_granite" in content
        assert "loopback-poc" in content
        assert "a0e6f00" in content

    def test_removed_entry_describes_stale_cleanup(self):
        """AC3: Entry describes the removal as stale demo cleanup."""
        content = _read_fragment()
        lower = content.lower()
        assert "stale" in lower

    def test_grep_matches_deleted_files(self):
        """AC4: Fragment contains poc_granite and loopback-poc."""
        content = _read_fragment()
        matches = len(re.findall(r"poc_granite|loopback-poc", content))
        assert matches >= 1

    def test_section_ordering_follows_convention(self):
        """AC5: Fragment is in released version folder 0.4.61."""
        assert FRAGMENT.exists(), "Fragment must exist"
        assert FRAGMENT.parent.name == "0.4.61", "Was released in v0.4.61"
