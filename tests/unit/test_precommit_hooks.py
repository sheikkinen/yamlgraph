"""Integration tests for pre-commit hook entries.

FR-083: Validates that commit-msg hooks work correctly.

These tests invoke the bash hook entries directly via subprocess
with temporary commit message files to verify the conditional logic.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# The exact entry strings from .pre-commit-config.yaml (AFTER fix)
# Note: These include the `_` placeholder for $0
import pytest

pytestmark = pytest.mark.process

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


def run_hook_entry(entry: str, commit_msg: str) -> subprocess.CompletedProcess:
    """Run a hook entry with a commit message.

    Args:
        entry: The full bash -c entry string (must end with ' _')
        commit_msg: The commit message to test

    Returns:
        CompletedProcess with exit code and output
    """
    with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w", suffix=".txt", delete=False) as f:
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


# ── FR-144: Diary Reflection Content Enforcement ────────────────────────────

# The exact entry from .pre-commit-config.yaml for diary-reflection-check hook.
# Uses staged reflection files to scan for placeholders and Seed:.
DIARY_REFLECTION_CHECK_ENTRY = (
    "bash -c '"
    'FILES=$(git diff --cached --name-only -- "docs/diary/*reflection*.md"); '
    'if [ -n "$FILES" ]; then '
    'STUBS=$(echo "$FILES" | xargs grep -l '
    '"\\[What cognitive trap\\|\\[What lesson\\|\\[What question" '
    "2>/dev/null); "
    'if [ -n "$STUBS" ]; then '
    'echo "❌ Unfilled diary reflection stubs:"; '
    'echo "$STUBS"; '
    'echo "Fill Trap/Heuristic/Seed sections before committing."; '
    "exit 1; fi; "
    'MISSING_SEED=$(echo "$FILES" | xargs grep -L "Seed:" 2>/dev/null); '
    'if [ -n "$MISSING_SEED" ]; then '
    'echo "❌ Diary reflections missing Seed: marker:"; '
    'echo "$MISSING_SEED"; '
    'echo "Add literal Seed: marker to each reflection before committing."; '
    "exit 1; fi; fi'"
)


def run_diary_hook(entry: str, file_paths: list[str]) -> subprocess.CompletedProcess:
    """Run the diary-reflection-check hook with mocked file list.

    Replaces the staged-file command with an echo of the given file paths
    so the grep pattern is tested against real temp files.
    """
    mock_ls = 'echo "' + " ".join(file_paths) + '"' if file_paths else "echo ''"
    modified = entry
    modified = modified.replace(
        'git diff --cached --name-only -- "docs/diary/*reflection*.md"', mock_ls
    )
    modified = modified.replace('git ls-files "docs/diary/*reflection*.md"', mock_ls)
    result = subprocess.run(
        modified,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result


UNFILLED_STUB = """\
## 2026-03-08: FR-999 — Implementation Reflection

**Context:** Implemented Something.

**Trap:** [What cognitive trap was encountered?]

**Heuristic:** [What lesson was learned?]

**Seed:** [What question remains?]
"""

FILLED_REFLECTION = """\
## 2026-03-08: FR-999 — Implementation Reflection

**Context:** Implemented Something.

**Trap:** quick_confidence — felt certain the regex was right, skipped verification.

**Heuristic:** Always run the pattern against real data before committing.

**Seed:** Can we auto-generate a test fixture from the detection pattern?
"""


@pytest.mark.req("REQ-YG-144")
class TestDiaryReflectionCheck:
    """Tests for diary-reflection-check pre-commit hook (FR-144)."""

    def test_hook_entry_checks_missing_seed_marker(self) -> None:
        """Hook entry must include missing-Seed detection for parity with CI gate."""
        assert 'grep -L "Seed:"' in DIARY_REFLECTION_CHECK_ENTRY

    def test_unfilled_trap_placeholder_rejected(self, tmp_path: Path) -> None:
        """A reflection with [What cognitive trap] placeholder is rejected."""
        f = tmp_path / "reflection.md"
        f.write_text("**Trap:** [What cognitive trap was encountered?]\n", encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert result.returncode == 1, f"Unfilled trap should fail: {result.stdout}"
        assert "Unfilled" in result.stdout

    def test_unfilled_lesson_placeholder_rejected(self, tmp_path: Path) -> None:
        """A reflection with [What lesson] placeholder is rejected."""
        f = tmp_path / "reflection.md"
        f.write_text("**Heuristic:** [What lesson was learned?]\n", encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert result.returncode == 1, f"Unfilled lesson should fail: {result.stdout}"

    def test_unfilled_question_placeholder_rejected(self, tmp_path: Path) -> None:
        """A reflection with [What question] placeholder is rejected."""
        f = tmp_path / "reflection.md"
        f.write_text("**Seed:** [What question remains?]\n", encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert result.returncode == 1, f"Unfilled question should fail: {result.stdout}"

    def test_missing_seed_marker_rejected(self, tmp_path: Path) -> None:
        """A reflection without literal Seed: marker is rejected."""
        f = tmp_path / "reflection.md"
        f.write_text(
            "## Reflection\n\n"
            "**Trap:** Assumed checks were aligned.\n\n"
            "**Heuristic:** Keep local and CI semantics in parity.\n"
        , encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert (
            result.returncode == 1
        ), f"Missing Seed marker should fail: {result.stdout}"
        assert "Seed:" in result.stdout

    def test_filled_reflection_accepted(self, tmp_path: Path) -> None:
        """A reflection with real content passes the hook."""
        f = tmp_path / "reflection.md"
        f.write_text(FILLED_REFLECTION, encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert result.returncode == 0, f"Filled reflection should pass: {result.stdout}"

    def test_no_reflection_files_accepted(self) -> None:
        """When no reflection files exist, the hook passes."""
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [])
        assert result.returncode == 0, "No files should pass"

    def test_mixed_filled_and_unfilled_rejected(self, tmp_path: Path) -> None:
        """If any reflection is unfilled, the hook fails even if others are filled."""
        filled = tmp_path / "filled.md"
        filled.write_text(FILLED_REFLECTION, encoding="utf-8")
        unfilled = tmp_path / "unfilled.md"
        unfilled.write_text(UNFILLED_STUB, encoding="utf-8")
        result = run_diary_hook(
            DIARY_REFLECTION_CHECK_ENTRY, [str(filled), str(unfilled)]
        )
        assert result.returncode == 1, "Mixed should fail due to unfilled stub"

    def test_full_stub_template_rejected(self, tmp_path: Path) -> None:
        """The exact stub template from finalize_merge.sh is rejected."""
        f = tmp_path / "reflection.md"
        f.write_text(UNFILLED_STUB, encoding="utf-8")
        result = run_diary_hook(DIARY_REFLECTION_CHECK_ENTRY, [str(f)])
        assert result.returncode == 1, "Full stub template should fail"


@pytest.mark.req("REQ-YG-144")
class TestFinalizeMergeUnstagedDiary:
    """Tests that finalize_merge.sh leaves diary stubs unstaged (FR-144).

    Static verification — reads the script content to verify the git add
    line excludes docs/diary/ and the commit message says 'untracked'.
    """

    SCRIPT_PATH = Path("scripts/finalize_merge.sh")

    def test_git_add_excludes_diary(self) -> None:
        """The git add line must NOT include docs/diary/."""
        content = self.SCRIPT_PATH.read_text(encoding="utf-8")
        # Find the git add line in step 4
        git_add_lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("git add ")
        ]
        assert git_add_lines, "Expected a git add line in the script"
        for line in git_add_lines:
            assert (
                "docs/diary" not in line
            ), f"git add must not include docs/diary/: {line}"

    def test_commit_message_says_untracked(self) -> None:
        """The commit message template must say 'untracked', not 'appended'."""
        content = self.SCRIPT_PATH.read_text(encoding="utf-8")
        assert (
            "stub appended" not in content
        ), "Commit message should not say 'appended'"
        assert (
            "untracked" in content.lower()
        ), "Commit message should mention 'untracked'"


# ── FR-212: Block AI Co-Author Trailers ─────────────────────────────────────

BLOCK_AI_COAUTHOR_SCRIPT = Path("scripts/block_ai_coauthor.py")


def run_block_ai_coauthor(commit_msg: str) -> subprocess.CompletedProcess:
    """Run block_ai_coauthor.py with a commit message written to a temp file."""
    with tempfile.NamedTemporaryFile(encoding="utf-8", mode="w", suffix=".txt", delete=False) as f:
        f.write(commit_msg)
        f.flush()
        msg_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, str(BLOCK_AI_COAUTHOR_SCRIPT), msg_file],
            capture_output=True,
            text=True,
        )
        return result
    finally:
        Path(msg_file).unlink()


@pytest.mark.req("REQ-YG-215")
class TestBlockAICoAuthor:
    """Tests for block-ai-coauthor commit-msg hook (FR-212)."""

    def test_copilot_trailer_rejected(self) -> None:
        """Co-authored-by: Copilot trailer must be blocked."""
        msg = "feat: FR-212 add hook\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "Copilot trailer should fail"

    def test_claude_trailer_rejected(self) -> None:
        """Co-authored-by: Claude trailer must be blocked."""
        msg = "fix: correct bug\n\nCo-authored-by: Claude <claude@anthropic.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "Claude trailer should fail"

    def test_github_copilot_trailer_rejected(self) -> None:
        """Co-authored-by: GitHub Copilot trailer must be blocked."""
        msg = (
            "fix: correct bug\n\nCo-authored-by: GitHub Copilot <copilot@github.com>\n"
        )
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "GitHub Copilot trailer should fail"

    def test_chatgpt_trailer_rejected(self) -> None:
        """Co-authored-by: ChatGPT trailer must be blocked."""
        msg = "fix: bug\n\nCo-authored-by: ChatGPT <chatgpt@openai.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "ChatGPT trailer should fail"

    def test_gemini_trailer_rejected(self) -> None:
        """Co-authored-by: Gemini trailer must be blocked."""
        msg = "fix: bug\n\nCo-authored-by: Gemini <gemini@google.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "Gemini trailer should fail"

    def test_gpt4_trailer_rejected(self) -> None:
        """Co-authored-by: GPT-4 trailer must be blocked."""
        msg = "fix: bug\n\nCo-authored-by: GPT-4 <gpt4@openai.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 1, "GPT-4 trailer should fail"

    def test_clean_commit_accepted(self) -> None:
        """Commit with no AI trailer must pass."""
        msg = "feat: FR-212 add hook\n\nAdded enforcement hook.\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 0, f"Clean commit should pass: {result.stdout}"

    def test_human_coauthor_accepted(self) -> None:
        """Human Co-authored-by trailer must pass."""
        msg = "feat: FR-212 pair programming\n\nCo-authored-by: Alice Smith <alice@example.com>\n"
        result = run_block_ai_coauthor(msg)
        assert result.returncode == 0, f"Human co-author should pass: {result.stdout}"

    def test_rejection_output_contains_offending_line(self) -> None:
        """Rejection must print the offending trailer line."""
        msg = "fix: bug\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>\n"
        result = run_block_ai_coauthor(msg)
        combined = result.stdout + result.stderr
        assert "Co-authored-by" in combined, "Output must show offending line"

    def test_rejection_output_contains_penance(self) -> None:
        """Rejection must include the penance liturgy."""
        msg = "fix: bug\n\nCo-authored-by: Claude <claude@anthropic.com>\n"
        result = run_block_ai_coauthor(msg)
        combined = result.stdout + result.stderr
        assert "Confession required" in combined, "Penance liturgy must be printed"

    def test_script_exists_and_is_executable(self) -> None:
        """scripts/block_ai_coauthor.py must exist and be executable."""
        assert BLOCK_AI_COAUTHOR_SCRIPT.exists(), "Script file must exist"
        assert os.access(BLOCK_AI_COAUTHOR_SCRIPT, os.X_OK), "Script must be executable"

    def test_hook_registered_in_precommit_config(self) -> None:
        """block-ai-coauthor hook must be in .pre-commit-config.yaml at commit-msg stage."""
        config = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")
        assert "block-ai-coauthor" in config, "Hook ID must be in pre-commit config"
        assert "commit-msg" in config, "Hook must use commit-msg stage"
