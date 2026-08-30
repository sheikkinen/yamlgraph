"""Tests for FR-150: Branch protection documentation.

Verifies that branch protection rules and emergency bypass procedures
are documented per FR-150 acceptance criteria.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.req("REQ-YG-149")
class TestBreakGlassDocumentation:
    """Verify reference/break-glass.md exists with required sections."""

    def test_break_glass_file_exists(self):
        path = REPO_ROOT / "reference" / "break-glass.md"
        assert path.exists(), "reference/break-glass.md must exist (FR-150 AC-5)"

    def test_break_glass_contains_emergency_procedure(self):
        path = REPO_ROOT / "reference" / "break-glass.md"
        content = path.read_text()
        assert (
            "emergency" in content.lower()
        ), "break-glass.md must document the emergency bypass procedure"

    def test_break_glass_contains_audit_trail_requirement(self):
        path = REPO_ROOT / "reference" / "break-glass.md"
        content = path.read_text()
        assert (
            "audit" in content.lower()
        ), "break-glass.md must require an audit trail for overrides"

    def test_break_glass_contains_diary_entry_requirement(self):
        path = REPO_ROOT / "reference" / "break-glass.md"
        content = path.read_text()
        assert (
            "diary" in content.lower()
        ), "break-glass.md must require a docs/diary/ entry after bypass"

    def test_break_glass_contains_re_enable_steps(self):
        path = REPO_ROOT / "reference" / "break-glass.md"
        content = path.read_text()
        assert (
            "re-enable" in content.lower() or "restore" in content.lower()
        ), "break-glass.md must document how to re-enable protection"


@pytest.mark.req("REQ-YG-149")
class TestClaudeMdBranchProtection:
    """Verify CLAUDE.md contains branch protection section."""

    def test_claude_md_has_branch_protection_section(self):
        path = REPO_ROOT / "CLAUDE.md"
        content = path.read_text()
        assert (
            "## Branch Protection" in content
        ), "CLAUDE.md must have a 'Branch Protection' section (FR-150 AC-6)"

    def test_claude_md_references_squash_merge(self):
        path = REPO_ROOT / "CLAUDE.md"
        content = path.read_text()
        # Find the branch protection section and verify it mentions squash merge
        assert (
            "squash" in content.lower()
        ), "CLAUDE.md branch protection section must mention squash merge"

    def test_claude_md_references_break_glass(self):
        path = REPO_ROOT / "CLAUDE.md"
        content = path.read_text()
        assert (
            "break-glass" in content.lower()
        ), "CLAUDE.md must reference break-glass.md for emergency procedures"

    def test_claude_md_references_required_checks(self):
        path = REPO_ROOT / "CLAUDE.md"
        content = path.read_text()
        assert (
            "commitlint" in content.lower()
        ), "CLAUDE.md branch protection section must list required status checks"


@pytest.mark.req("REQ-YG-149")
class TestClaudeMdMergeQueue:
    """FR-934: CLAUDE.md must document the merge-queue platform blocker."""

    def test_claude_md_documents_merge_queue_blocker(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert "BLOCKED BY PLATFORM" in content, (
            "CLAUDE.md must record that the merge queue is unavailable "
            "on this user-owned repo (FR-934 implementation record)"
        )

    def test_claude_md_documents_dormant_merge_group_wiring(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert (
            "merge_group" in content
        ), "CLAUDE.md must state required contexts also report on merge_group"

    def test_claude_md_strict_up_to_date_still_enforced(self):
        content = (REPO_ROOT / "CLAUDE.md").read_text()
        assert "Enabled (strict)" in content, (
            "The strict up-to-date regime stays until the queue is "
            "available; CLAUDE.md must not claim it was retired"
        )
