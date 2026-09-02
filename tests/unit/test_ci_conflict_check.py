"""Tests for CI conflict marker check in commitlint.yml (FR-157).

Validates that the `conflict-check` job in `.github/workflows/commitlint.yml`
correctly blocks PRs containing unresolved merge conflict markers and passes
when no markers are present.

Two test layers:
1. YAML structure — parse the workflow and verify job config, steps, exclusions.
2. Shell logic — run the grep script with mocked file content.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = ".github/workflows/commitlint.yml"

# The shell script from the conflict-check step, extracted for unit testing.
# Uses git grep against the working tree; for testing we substitute with grep
# against a temp directory.
CONFLICT_CHECK_SCRIPT = """\
if git grep -n -E '^<{{7}} |^={{7}}$|^>{{7}} ' -- ':!.github' ':!*.md.bak'; then
  echo "::error::Unresolved merge conflict markers found in tracked files"
  exit 1
else
  echo "✅ No conflict markers found"
  exit 0
fi
"""


def _load_workflow() -> dict:
    """Load and parse the commitlint workflow YAML."""
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _run_conflict_check(
    file_content: str, filename: str = "test.py"
) -> subprocess.CompletedProcess:
    """Run conflict marker detection against a temp file.

    Creates a temp git repo with the given file content and runs
    the same regex pattern used in the CI job.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        # Initialize a git repo so git grep works
        subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmpdir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmpdir,
            check=True,
        )
        # Write the test file
        filepath = tmppath / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(file_content, encoding="utf-8")
        # Stage and commit so git grep can find it
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "test"],
            cwd=tmpdir,
            check=True,
        )
        # Run the same pattern used in CI
        script = (
            "if git grep -n -E '^<{7} |^={7}$|^>{7} ' -- ':!.github' ':!*.md.bak'; then\n"
            '  echo "::error::Unresolved merge conflict markers found in tracked files"\n'
            "  exit 1\n"
            "else\n"
            '  echo "✅ No conflict markers found"\n'
            "  exit 0\n"
            "fi\n"
        )
        return subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )


# ── YAML Structure Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-151")
class TestConflictCheckJobStructure:
    """Verify the conflict-check job exists with correct configuration."""

    def test_job_exists(self) -> None:
        """The commitlint workflow must contain a 'conflict-check' job."""
        wf = _load_workflow()
        assert (
            "conflict-check" in wf["jobs"]
        ), "Missing 'conflict-check' job in commitlint.yml"

    def test_job_name(self) -> None:
        """The job display name indicates conflict marker checking."""
        wf = _load_workflow()
        job = wf["jobs"]["conflict-check"]
        assert "conflict" in job["name"].lower(), "Job name must mention conflict"

    def test_checkout_step_present(self) -> None:
        """The job must check out the repo to run git grep."""
        wf = _load_workflow()
        steps = wf["jobs"]["conflict-check"]["steps"]
        checkout_steps = [
            s for s in steps if s.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps, "Must have an actions/checkout step"

    def test_grep_step_uses_conflict_patterns(self) -> None:
        """The check step must grep for all three conflict marker patterns."""
        wf = _load_workflow()
        steps = wf["jobs"]["conflict-check"]["steps"]
        grep_steps = [s for s in steps if "run" in s and "git grep" in s.get("run", "")]
        assert grep_steps, "Must have a step that runs git grep"
        run_script = grep_steps[0]["run"]
        assert (
            "<{7}" in run_script or "<<<<<<<" in run_script
        ), "Must check for <<<<<<< markers"
        assert (
            "={7}" in run_script or "=======" in run_script
        ), "Must check for ======= markers"
        assert (
            ">{7}" in run_script or ">>>>>>>" in run_script
        ), "Must check for >>>>>>> markers"

    def test_excludes_github_directory(self) -> None:
        """The git grep must exclude .github/ to avoid false positives on workflow files."""
        wf = _load_workflow()
        steps = wf["jobs"]["conflict-check"]["steps"]
        grep_steps = [s for s in steps if "run" in s and "git grep" in s.get("run", "")]
        assert grep_steps, "Must have a git grep step"
        run_script = grep_steps[0]["run"]
        assert ":!.github" in run_script, "Must exclude .github directory"

    def test_fails_on_markers_found(self) -> None:
        """The script must exit 1 when conflict markers are found."""
        wf = _load_workflow()
        steps = wf["jobs"]["conflict-check"]["steps"]
        grep_steps = [s for s in steps if "run" in s and "git grep" in s.get("run", "")]
        assert grep_steps, "Must have a git grep step"
        run_script = grep_steps[0]["run"]
        assert "exit 1" in run_script, "Must exit 1 on conflict marker detection"


# ── Shell Script Logic Tests ───────────────────────────────────────────────


@pytest.mark.slow
@pytest.mark.req("REQ-YG-151")
class TestConflictCheckShellLogic:
    """Test the actual grep pattern against real conflict marker content."""

    def test_clean_file_passes(self) -> None:
        """A file without conflict markers passes the check."""
        result = _run_conflict_check("def hello():\n    return 'world'\n")
        assert result.returncode == 0, f"Clean file should pass: {result.stderr}"
        assert "No conflict markers found" in result.stdout

    def test_start_marker_detected(self) -> None:
        """A file with <<<<<<< marker fails the check."""
        content = "line 1\n<<<<<<< HEAD\nline 2\n"
        result = _run_conflict_check(content)
        assert result.returncode == 1, "Start marker should be detected"

    def test_separator_marker_detected(self) -> None:
        """A file with ======= marker fails the check."""
        content = "line 1\n=======\nline 2\n"
        result = _run_conflict_check(content)
        assert result.returncode == 1, "Separator marker should be detected"

    def test_end_marker_detected(self) -> None:
        """A file with >>>>>>> marker fails the check."""
        content = "line 1\n>>>>>>> branch-name\nline 2\n"
        result = _run_conflict_check(content)
        assert result.returncode == 1, "End marker should be detected"

    def test_full_conflict_block_detected(self) -> None:
        """A full conflict block (all three markers) fails the check."""
        content = (
            "before\n"
            "<<<<<<< HEAD\n"
            "our change\n"
            "=======\n"
            "their change\n"
            ">>>>>>> feature-branch\n"
            "after\n"
        )
        result = _run_conflict_check(content)
        assert result.returncode == 1, "Full conflict block should be detected"

    def test_github_dir_excluded(self) -> None:
        """Files in .github/ directory are excluded from the check."""
        result = _run_conflict_check(
            "<<<<<<< HEAD\n=======\n>>>>>>> branch\n",
            filename=".github/workflows/test.yml",
        )
        assert result.returncode == 0, ".github/ files should be excluded"

    def test_md_bak_excluded(self) -> None:
        """Backup .md.bak files are excluded from the check."""
        result = _run_conflict_check(
            "<<<<<<< HEAD\n=======\n>>>>>>> branch\n",
            filename="notes.md.bak",
        )
        assert result.returncode == 0, ".md.bak files should be excluded"

    def test_partial_marker_not_detected(self) -> None:
        """Fewer than 7 angle brackets should NOT trigger detection."""
        content = "<<<<<< not enough\n>>>>>> also not enough\n"
        result = _run_conflict_check(content)
        assert result.returncode == 0, "Partial markers should not trigger detection"

    def test_inline_markers_not_detected(self) -> None:
        """Markers not at line start should NOT trigger detection."""
        content = "text <<<<<<< HEAD\ntext >>>>>>> branch\n"
        result = _run_conflict_check(content)
        assert result.returncode == 0, "Non-start-of-line markers should not trigger"


# ── Documentation Tests ────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-151")
class TestConflictCheckDocumentation:
    """Verify the ops reference documents the conflict-check status check.

    FR-942 moved branch protection / CI checks docs from CLAUDE.md to
    reference/development-operations.md.
    """

    def test_dev_ops_lists_conflict_check(self) -> None:
        """The CI checks section must list conflict-check."""
        content = Path("reference/development-operations.md").read_text(encoding="utf-8")
        assert (
            "conflict-check" in content
        ), "development-operations.md must list conflict-check as a status check"

    def test_dev_ops_describes_conflict_check(self) -> None:
        """The ops reference must describe what the conflict-check does."""
        content = Path("reference/development-operations.md").read_text(encoding="utf-8")
        assert (
            "conflict marker" in content.lower()
        ), "development-operations.md must describe conflict-check purpose"

    def test_dev_ops_notes_up_to_date_requirement(self) -> None:
        """The ops reference must note the 'require up-to-date' setting."""
        content = Path("reference/development-operations.md").read_text(encoding="utf-8")
        assert (
            "up to date" in content.lower() or "up-to-date" in content.lower()
        ), "development-operations.md must document the up-to-date setting"
