"""Tests for FR-150: Branch protection documentation.

Verifies that branch protection rules and emergency bypass procedures
are documented per FR-150 acceptance criteria.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# FR-942 moved branch protection / CI checks docs from CLAUDE.md here:
DEV_OPS = REPO_ROOT / "reference" / "development-operations.md"


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
    """Verify the ops reference contains the branch protection section."""

    def test_dev_ops_has_branch_protection_section(self):
        content = DEV_OPS.read_text()
        assert (
            "## Branch Protection" in content
        ), "development-operations.md must have a 'Branch Protection' section"

    def test_claude_md_references_squash_merge(self):
        path = REPO_ROOT / "CLAUDE.md"
        content = path.read_text()
        # Find the branch protection section and verify it mentions squash merge
        assert (
            "squash" in content.lower()
        ), "CLAUDE.md branch protection section must mention squash merge"

    def test_dev_ops_references_break_glass(self):
        content = DEV_OPS.read_text()
        assert (
            "break-glass" in content.lower()
        ), "development-operations.md must reference break-glass.md"

    def test_dev_ops_references_required_checks(self):
        content = DEV_OPS.read_text()
        assert (
            "commitlint" in content.lower()
        ), "development-operations.md must list required status checks"


@pytest.mark.req("REQ-YG-149")
class TestClaudeMdMergeQueue:
    """FR-934: the ops reference must document the merge-queue blocker."""

    def test_dev_ops_documents_merge_queue_blocker(self):
        content = DEV_OPS.read_text()
        assert "BLOCKED BY PLATFORM" in content, (
            "development-operations.md must record that the merge queue is "
            "unavailable on this user-owned repo (FR-934 implementation record)"
        )

    def test_dev_ops_documents_dormant_merge_group_wiring(self):
        content = DEV_OPS.read_text()
        assert (
            "merge_group" in content
        ), "ops reference must state required contexts also report on merge_group"

    def test_dev_ops_strict_up_to_date_still_enforced(self):
        content = DEV_OPS.read_text()
        assert "Enabled (strict)" in content, (
            "The strict up-to-date regime stays until the queue is "
            "available; the ops reference must not claim it was retired"
        )
