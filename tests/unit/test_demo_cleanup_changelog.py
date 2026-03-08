"""Unit tests for FR-153: Stale demo cleanup CHANGELOG entry.

Verifies that CHANGELOG.md documents the removal of stale demo files
from commit a0e6f00, per Commandment 8: "record significant removals
in commit notes."
"""

import os
import re

import pytest


def _read_changelog() -> str:
    """Read the current CHANGELOG.md content."""
    changelog_path = os.path.join(os.path.dirname(__file__), "..", "..", "CHANGELOG.md")
    with open(changelog_path) as f:
        return f.read()


def _unreleased_block() -> str:
    """Extract the [Unreleased] section from CHANGELOG.md."""
    changelog = _read_changelog()
    unreleased_start = changelog.index("[Unreleased]")
    next_section = changelog.find("\n## [0.", unreleased_start)
    return changelog[unreleased_start:next_section]


@pytest.mark.req("REQ-YG-146")
class TestDemoCleanupChangelog:
    """Verify CHANGELOG.md documents the stale demo cleanup (FR-153)."""

    def test_changelog_has_removed_section(self):
        """AC1: CHANGELOG.md [Unreleased] contains a ### Removed section."""
        unreleased = _unreleased_block()
        assert "### Removed" in unreleased

    def test_removed_entry_references_deleted_files(self):
        """AC2: Entry references the three deleted files and commit a0e6f00."""
        unreleased = _unreleased_block()
        assert "poc_granite" in unreleased
        assert "loopback-poc" in unreleased
        assert "a0e6f00" in unreleased

    def test_removed_entry_describes_stale_cleanup(self):
        """AC3: Entry describes the removal as stale demo cleanup."""
        unreleased = _unreleased_block()
        # Must mention stale and demo/cleanup context
        lower = unreleased.lower()
        assert "stale" in lower
        assert "demo" in lower or "cleanup" in lower

    def test_grep_matches_deleted_files(self):
        """AC4: grep -c 'poc_granite|loopback-poc' CHANGELOG.md returns >= 1."""
        changelog = _read_changelog()
        matches = len(re.findall(r"poc_granite|loopback-poc", changelog))
        assert matches >= 1

    def test_section_ordering_follows_convention(self):
        """AC5: Section ordering follows Keep a Changelog (Added → Removed → Fixed)."""
        unreleased = _unreleased_block()
        added_pos = unreleased.index("### Added")
        removed_pos = unreleased.index("### Removed")
        fixed_pos = unreleased.index("### Fixed")
        assert added_pos < removed_pos < fixed_pos
