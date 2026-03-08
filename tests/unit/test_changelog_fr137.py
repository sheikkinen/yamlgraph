"""Tests for FR-137 DeepSeek provider CHANGELOG entry (FR-151).

Verifies that the CHANGELOG.md [Unreleased] → Added section contains
a properly formatted entry for FR-137 (DeepSeek provider).
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


@pytest.mark.req("REQ-YG-125")
class TestFR137ChangelogEntry:
    """FR-137 DeepSeek provider has a CHANGELOG entry."""

    def test_fr137_mentioned_in_changelog(self):
        """grep -c 'FR-137' CHANGELOG.md returns >= 1."""
        text = CHANGELOG.read_text()
        assert "FR-137" in text, "CHANGELOG.md has no mention of FR-137"

    def test_entry_references_deepseek(self):
        """Entry mentions DeepSeek provider name."""
        text = CHANGELOG.read_text()
        fr137_lines = [ln for ln in text.splitlines() if "FR-137" in ln]
        assert fr137_lines, "No FR-137 line found"
        entry = fr137_lines[0]
        assert "DeepSeek" in entry, f"FR-137 entry missing 'DeepSeek': {entry}"

    def test_entry_references_env_var(self):
        """Entry mentions DEEPSEEK_API_KEY environment variable."""
        text = CHANGELOG.read_text()
        fr137_lines = [ln for ln in text.splitlines() if "FR-137" in ln]
        assert fr137_lines, "No FR-137 line found"
        entry = fr137_lines[0]
        assert (
            "DEEPSEEK_API_KEY" in entry
        ), f"FR-137 entry missing 'DEEPSEEK_API_KEY': {entry}"

    def test_entry_in_added_section(self):
        """Entry lives under an ### Added section (released in v0.4.61)."""
        lines = CHANGELOG.read_text().splitlines()
        version_idx = next((i for i, ln in enumerate(lines) if "[0.4.61]" in ln), None)
        assert version_idx is not None, "No [0.4.61] section"

        # Find ### Added after [0.4.61]
        added_idx = next(
            (
                i
                for i, ln in enumerate(lines[version_idx:], start=version_idx)
                if ln.strip() == "### Added"
            ),
            None,
        )
        assert added_idx is not None, "No ### Added under [0.4.61]"

        # Find next section header after ### Added
        next_section_idx = next(
            (
                i
                for i, ln in enumerate(lines[added_idx + 1 :], start=added_idx + 1)
                if ln.startswith("## ") or ln.startswith("### ")
            ),
            len(lines),
        )

        added_block = "\n".join(lines[added_idx:next_section_idx])
        assert "FR-137" in added_block, "FR-137 not in [0.4.61] → ### Added section"

    def test_entry_position_descending_fr_order(self):
        """FR-137 appears after FR-138 and before FR-136 (descending order)."""
        lines = CHANGELOG.read_text().splitlines()

        fr138_idx = next((i for i, ln in enumerate(lines) if "FR-138" in ln), None)
        fr137_idx = next((i for i, ln in enumerate(lines) if "FR-137" in ln), None)
        fr136_idx = next((i for i, ln in enumerate(lines) if "FR-136" in ln), None)

        assert fr138_idx is not None, "FR-138 not found in CHANGELOG"
        assert fr137_idx is not None, "FR-137 not found in CHANGELOG"
        assert fr136_idx is not None, "FR-136 not found in CHANGELOG"

        assert (
            fr138_idx < fr137_idx < fr136_idx
        ), f"Wrong order: FR-138@{fr138_idx}, FR-137@{fr137_idx}, FR-136@{fr136_idx}"
