"""Integration tests for pre-commit hook entries.

FR-083: Validates that commit-msg hooks work correctly.

These tests invoke the bash hook entries directly via subprocess
with temporary commit message files to verify the conditional logic.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest

# The exact entry strings from .pre-commit-config.yaml (AFTER fix)
# Note: These include the `_` placeholder for $0

FEAT_REQUIRES_FR_ENTRY = (
    "bash -c '"
    'msg=$(cat "$1"); '
    'if echo "$msg" | grep -qE "^feat(\\(.*\\))?:" && '
    '! echo "$msg" | grep -qE "FR-[0-9]+"; then '
    'echo "ERROR: feat: commits require FR-XXX reference"; '
    'echo "Example: feat: FR-038 add commit enforcement"; '
    "exit 1; fi' _"
)

CHANGELOG_REQUIRED_ENTRY = (
    "bash -c '"
    'msg=$(cat "$1"); '
    'if echo "$msg" | grep -qE "^(feat|fix)(\\(.*\\))?:" && '
    '! git diff --cached --name-only | grep -qE "^CHANGELOG\\.md$"; then '
    'echo "ERROR: feat:/fix: commits must include CHANGELOG.md changes"; '
    'echo "Add your entry under the current [Unreleased] or version heading."; '
    "exit 1; fi' _"
)

COPILOT_TRAILER_ENTRY = (
    "bash -c '"
    'grep -q "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>" "$1" '
    '|| { echo "✗ Missing Co-authored-by: Copilot trailer"; exit 1; }'
    "' _"
)


def run_hook_entry(entry: str, commit_msg: str) -> subprocess.CompletedProcess:
    """Run a hook entry with a commit message.

    Args:
        entry: The full bash -c entry string (must end with ' _')
        commit_msg: The commit message to test

    Returns:
        CompletedProcess with exit code and output
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(commit_msg)
        f.flush()
        msg_file = f.name

    try:
        # Entry format: bash -c '...' _
        # Pre-commit appends the commit-msg file as an additional argument
        # So: bash -c '...' _ /path/to/COMMIT_EDITMSG
        # The _ becomes $0, the filename becomes $1
        if not entry.endswith("' _"):
            raise ValueError(f"Entry must end with ' _', got: {entry[-10:]}")

        cmd = entry + " " + msg_file

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
        )
        return result
    finally:
        Path(msg_file).unlink()


@pytest.mark.req("REQ-YG-002")  # CI/CD infrastructure requirement
class TestFeatRequiresFR:
    """Tests for feat-requires-fr commit-msg hook."""

    def test_feat_without_fr_rejected(self) -> None:
        """A feat: commit without FR-XXX should be rejected."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "feat: add new feature\n")
        assert result.returncode == 1, "feat: without FR-XXX should fail"
        assert "FR-XXX" in result.stdout or "FR-XXX" in result.stderr

    def test_feat_with_fr_accepted(self) -> None:
        """A feat: commit with FR-XXX should be accepted."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "feat: FR-083 fix hook bug\n")
        assert result.returncode == 0, f"feat: with FR-XXX should pass: {result.stdout}"

    def test_feat_scoped_with_fr_accepted(self) -> None:
        """A feat(scope): commit with FR-XXX should be accepted."""
        result = run_hook_entry(
            FEAT_REQUIRES_FR_ENTRY, "feat(hooks): FR-083 fix commit hooks\n"
        )
        assert result.returncode == 0, "feat(scope): with FR-XXX should pass"

    def test_feat_scoped_without_fr_rejected(self) -> None:
        """A feat(scope): commit without FR-XXX should be rejected."""
        result = run_hook_entry(
            FEAT_REQUIRES_FR_ENTRY, "feat(parser): improve performance\n"
        )
        assert result.returncode == 1, "feat(scope): without FR-XXX should fail"

    def test_fix_without_fr_accepted(self) -> None:
        """A fix: commit without FR-XXX should be accepted (FR not required)."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "fix: correct typo\n")
        assert result.returncode == 0, "fix: without FR-XXX should pass"

    def test_chore_without_fr_accepted(self) -> None:
        """A chore: commit without FR-XXX should be accepted."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "chore: update deps\n")
        assert result.returncode == 0, "chore: without FR-XXX should pass"

    def test_refactor_without_fr_accepted(self) -> None:
        """A refactor: commit without FR-XXX should be accepted."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "refactor: simplify parser\n")
        assert result.returncode == 0, "refactor: without FR-XXX should pass"

    def test_test_without_fr_accepted(self) -> None:
        """A test: commit without FR-XXX should be accepted."""
        result = run_hook_entry(FEAT_REQUIRES_FR_ENTRY, "test: add coverage\n")
        assert result.returncode == 0, "test: without FR-XXX should pass"


@pytest.mark.req("REQ-YG-002")  # CI/CD infrastructure requirement
class TestChangelogRequired:
    """Tests for changelog-required commit-msg hook.

    Note: These tests mock `git diff --cached --name-only` to simulate
    staged files without requiring actual git state.
    """

    def test_feat_without_changelog_rejected(self) -> None:
        """A feat: commit without CHANGELOG.md staged should be rejected."""
        # Mock git diff to return no CHANGELOG.md
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "feat: FR-083 add feature\n")
        assert result.returncode == 1, "feat: without CHANGELOG.md should fail"
        assert "CHANGELOG" in result.stdout or "CHANGELOG" in result.stderr

    def test_feat_with_changelog_accepted(self) -> None:
        """A feat: commit with CHANGELOG.md staged should be accepted."""
        # Mock git diff to return CHANGELOG.md
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'CHANGELOG.md'"
        )
        result = run_hook_entry(entry_with_mock, "feat: FR-083 add feature\n")
        assert (
            result.returncode == 0
        ), f"feat: with CHANGELOG.md should pass: {result.stdout}"

    def test_fix_without_changelog_rejected(self) -> None:
        """A fix: commit without CHANGELOG.md staged should be rejected."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "fix: correct bug\n")
        assert result.returncode == 1, "fix: without CHANGELOG.md should fail"

    def test_fix_with_changelog_accepted(self) -> None:
        """A fix: commit with CHANGELOG.md staged should be accepted."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'CHANGELOG.md'"
        )
        result = run_hook_entry(entry_with_mock, "fix: correct bug\n")
        assert result.returncode == 0, "fix: with CHANGELOG.md should pass"

    def test_chore_without_changelog_accepted(self) -> None:
        """A chore: commit without CHANGELOG.md should be accepted."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "chore: update deps\n")
        assert result.returncode == 0, "chore: without CHANGELOG.md should pass"

    def test_refactor_without_changelog_accepted(self) -> None:
        """A refactor: commit without CHANGELOG.md should be accepted (deferred)."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "refactor: simplify code\n")
        assert result.returncode == 0, "refactor: without CHANGELOG.md should pass"

    def test_test_without_changelog_accepted(self) -> None:
        """A test: commit without CHANGELOG.md should be accepted."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'tests/test_foo.py'"
        )
        result = run_hook_entry(entry_with_mock, "test: add coverage\n")
        assert result.returncode == 0, "test: without CHANGELOG.md should pass"

    def test_feat_scoped_without_changelog_rejected(self) -> None:
        """A feat(scope): commit without CHANGELOG.md should be rejected."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "feat(hooks): FR-083 new hook\n")
        assert result.returncode == 1, "feat(scope): without CHANGELOG.md should fail"

    def test_fix_scoped_without_changelog_rejected(self) -> None:
        """A fix(scope): commit without CHANGELOG.md should be rejected."""
        entry_with_mock = CHANGELOG_REQUIRED_ENTRY.replace(
            "git diff --cached --name-only", "echo 'src/main.py'"
        )
        result = run_hook_entry(entry_with_mock, "fix(parser): correct parsing\n")
        assert result.returncode == 1, "fix(scope): without CHANGELOG.md should fail"


@pytest.mark.req("REQ-YG-002")
class TestHookEntryFormat:
    """Tests for hook entry format correctness."""

    def test_feat_requires_fr_has_placeholder(self) -> None:
        """The feat-requires-fr entry should have _ placeholder at end."""
        assert FEAT_REQUIRES_FR_ENTRY.endswith(
            "' _"
        ), "Entry must end with ' _' for proper $1 handling"

    def test_changelog_required_has_placeholder(self) -> None:
        """The changelog-required entry should have _ placeholder at end."""
        assert CHANGELOG_REQUIRED_ENTRY.endswith(
            "' _"
        ), "Entry must end with ' _' for proper $1 handling"

    def test_copilot_trailer_has_placeholder(self) -> None:
        """The copilot-trailer entry should have _ placeholder at end."""
        assert COPILOT_TRAILER_ENTRY.endswith(
            "' _"
        ), "Entry must end with ' _' for proper $1 handling"


@pytest.mark.req("REQ-YG-002")  # CI/CD infrastructure requirement
class TestCopilotTrailer:
    """Tests for copilot-trailer commit-msg hook (FR-132)."""

    def test_commit_without_trailer_rejected(self) -> None:
        """A commit without Copilot Co-authored-by trailer should be rejected."""
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, "feat: FR-132 add feature\n")
        assert result.returncode == 1, "commit without Copilot trailer should fail"
        assert (
            "Missing Co-authored-by" in result.stdout
            or "Missing Co-authored-by" in result.stderr
        )

    def test_commit_with_trailer_accepted(self) -> None:
        """A commit with Copilot Co-authored-by trailer should be accepted."""
        msg = (
            "feat: FR-132 add trailer enforcement\n"
            "\n"
            "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\n"
        )
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, msg)
        assert (
            result.returncode == 0
        ), f"commit with Copilot trailer should pass: {result.stdout}"

    def test_trailer_with_body_text_accepted(self) -> None:
        """A commit with trailer among other body content should be accepted."""
        msg = (
            "chore: update dependencies\n"
            "\n"
            "Updated all dev dependencies to latest versions.\n"
            "\n"
            "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\n"
        )
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, msg)
        assert result.returncode == 0, "commit with trailer and body should pass"

    def test_wrong_copilot_email_rejected(self) -> None:
        """A commit with wrong Copilot email should be rejected."""
        msg = (
            "feat: FR-132 add feature\n"
            "\n"
            "Co-authored-by: Copilot <wrong@email.com>\n"
        )
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, msg)
        assert result.returncode == 1, "wrong Copilot email should fail"

    def test_other_coauthor_without_copilot_rejected(self) -> None:
        """A commit with another Co-authored-by but not Copilot should be rejected."""
        msg = (
            "feat: FR-132 add feature\n"
            "\n"
            "Co-authored-by: Someone <someone@example.com>\n"
        )
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, msg)
        assert result.returncode == 1, "non-Copilot co-author should still fail"

    def test_empty_commit_message_rejected(self) -> None:
        """An empty commit message should be rejected."""
        result = run_hook_entry(COPILOT_TRAILER_ENTRY, "\n")
        assert result.returncode == 1, "empty message should fail"
