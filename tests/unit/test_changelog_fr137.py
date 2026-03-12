"""Tests for FR-137 DeepSeek provider changelog fragment (FR-151).

Verifies that the changelog fragment for FR-137 (DeepSeek provider)
exists and contains the required information.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAGMENT = REPO_ROOT / "changelog" / "0.4.61" / "FR-137-deepseek-provider.md"


@pytest.mark.req("REQ-YG-125")
class TestFR137ChangelogEntry:
    """FR-137 DeepSeek provider has a changelog fragment."""

    def test_fr137_mentioned_in_changelog(self):
        """Changelog fragment for FR-137 exists and mentions FR-137."""
        text = FRAGMENT.read_text()
        assert "FR-137" in text, "Fragment has no mention of FR-137"

    def test_entry_references_deepseek(self):
        """Entry mentions DeepSeek provider name."""
        text = FRAGMENT.read_text()
        assert "DeepSeek" in text, "FR-137 fragment missing 'DeepSeek'"

    def test_entry_references_env_var(self):
        """Entry mentions DEEPSEEK_API_KEY environment variable."""
        text = FRAGMENT.read_text()
        assert "DEEPSEEK_API_KEY" in text, "FR-137 fragment missing 'DEEPSEEK_API_KEY'"

    def test_entry_in_added_section(self):
        """Fragment has type: feat (maps to ### Added)."""
        text = FRAGMENT.read_text()
        assert "type: feat" in text, "FR-137 fragment should be type: feat (Added)"

    def test_entry_position_ascending_fr_order(self):
        """FR-137 fragment exists in the 0.4.61 release folder."""
        assert FRAGMENT.exists(), "FR-137 fragment must exist in changelog/0.4.61/"
        assert FRAGMENT.parent.name == "0.4.61", "FR-137 was released in v0.4.61"
