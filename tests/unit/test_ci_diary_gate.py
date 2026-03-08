"""Tests for CI diary reflection gate in commitlint.yml (FR-158).

Validates that the `diary-gate` job in `.github/workflows/commitlint.yml`
correctly blocks feat/fix PRs without a diary reflection file for the
referenced FR number, and skips for PRs without an FR reference.

Two test layers:
1. YAML structure — parse the workflow and verify job config, conditions, steps.
2. Shell logic — run the verification script with mocked git diff output.
"""

import subprocess

import pytest
import yaml

WORKFLOW_PATH = ".github/workflows/commitlint.yml"

# The shell script from the diary-gate step, extracted for unit testing.
# Mirrors the `run:` block in commitlint.yml; uses env vars BASE_SHA/HEAD_SHA/PR_TITLE.
DIARY_GATE_SCRIPT = """\
FR_NUM=$(echo "$PR_TITLE" | grep -oE 'FR-[0-9]+' | head -1 | sed 's/FR-//')

if [ -z "$FR_NUM" ]; then
  echo "⏭️ No FR-XXX reference in title — diary gate skipped"
  exit 0
fi

echo "🔍 Checking for diary reflection for FR-$FR_NUM..."

if git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE "docs/diary/.*reflection.*fr-${FR_NUM}[^0-9]"; then
  echo "✅ Diary reflection found for FR-$FR_NUM"
else
  echo "::error::feat/fix PRs referencing FR-$FR_NUM must include a diary reflection in docs/diary/"
  echo ""
  echo "Expected: docs/diary/YYYY-MM-DD-reflection-fr-${FR_NUM}.md"
  echo ""
  echo "The diary reflection should document:"
  echo "  - Cognitive traps encountered"
  echo "  - Heuristics learned"
  echo "  - A Seed question for future work"
  echo ""
  echo "See docs/diary/ for examples."
  exit 1
fi
"""


def _load_workflow() -> dict:
    """Load and parse the commitlint workflow YAML."""
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


def _run_gate_script(
    diff_output: str, pr_title: str = "feat(core): FR-158 add diary gate"
) -> subprocess.CompletedProcess:
    """Run the diary gate script with mocked git diff output.

    Replaces `git diff --name-only "$BASE_SHA" "$HEAD_SHA"` with an echo
    of the provided diff output to test the grep logic in isolation.
    """
    script = DIARY_GATE_SCRIPT.replace(
        'git diff --name-only "$BASE_SHA" "$HEAD_SHA"',
        f"echo '{diff_output}'",
    )
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        env={"PR_TITLE": pr_title, "PATH": "/usr/bin:/bin"},
    )


# ── YAML Structure Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-151")
class TestDiaryGateJobStructure:
    """Verify the diary-gate job exists with correct configuration."""

    def test_job_exists(self) -> None:
        """The commitlint workflow must contain a 'diary-gate' job."""
        wf = _load_workflow()
        assert (
            "diary-gate" in wf["jobs"]
        ), "Missing 'diary-gate' job in commitlint.yml"

    def test_job_name(self) -> None:
        """The job display name indicates diary is required for feat/fix."""
        wf = _load_workflow()
        job = wf["jobs"]["diary-gate"]
        name = job["name"].lower()
        assert "diary" in name, "Job name must mention diary"
        assert (
            "feat" in name or "fix" in name
        ), "Job name must mention feat or fix"

    def test_job_condition_checks_feat(self) -> None:
        """The job-level `if` condition must check for 'feat' PR titles."""
        wf = _load_workflow()
        job = wf["jobs"]["diary-gate"]
        condition = job.get("if", "")
        assert (
            "startsWith(github.event.pull_request.title, 'feat')" in condition
        ), "Job must check for feat PR titles"

    def test_job_condition_checks_fix(self) -> None:
        """The job-level `if` condition must check for 'fix' PR titles."""
        wf = _load_workflow()
        job = wf["jobs"]["diary-gate"]
        condition = job.get("if", "")
        assert (
            "startsWith(github.event.pull_request.title, 'fix')" in condition
        ), "Job must check for fix PR titles"

    def test_checkout_with_full_history(self) -> None:
        """The checkout step must use fetch-depth: 0 for full git history."""
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        checkout_steps = [
            s for s in steps if s.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps, "Must have an actions/checkout step"
        checkout = checkout_steps[0]
        assert (
            checkout.get("with", {}).get("fetch-depth") == 0
        ), "Checkout must use fetch-depth: 0"

    def test_verify_step_uses_git_diff(self) -> None:
        """The verification step must use git diff with base/head SHAs."""
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        verify_steps = [s for s in steps if "run" in s and "diary" in s["run"].lower()]
        assert verify_steps, "Must have a step that checks diary reflection"
        run_script = verify_steps[0]["run"]
        assert "git diff --name-only" in run_script
        assert "diary" in run_script.lower()

    def test_verify_step_has_required_env_vars(self) -> None:
        """The verification step must receive BASE_SHA, HEAD_SHA, and PR_TITLE."""
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        verify_steps = [s for s in steps if "run" in s and "diary" in s["run"].lower()]
        assert verify_steps, "Must have a verification step"
        env = verify_steps[0].get("env", {})
        assert "BASE_SHA" in env, "Must pass BASE_SHA env var"
        assert "HEAD_SHA" in env, "Must pass HEAD_SHA env var"
        assert "PR_TITLE" in env, "Must pass PR_TITLE env var"

    def test_error_message_includes_guidance(self) -> None:
        """The error message must include expected path pattern and content guidance."""
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        verify_steps = [s for s in steps if "run" in s and "diary" in s["run"].lower()]
        assert verify_steps, "Must have a verification step"
        run_script = verify_steps[0]["run"]
        assert "reflection" in run_script, "Error must mention reflection"
        assert "Seed" in run_script, "Error must mention Seed question"
        assert "Cognitive traps" in run_script or "traps" in run_script.lower(), (
            "Error must mention cognitive traps"
        )


# ── Shell Script Logic Tests ───────────────────────────────────────────────


@pytest.mark.req("REQ-YG-151")
class TestDiaryGateShellLogic:
    """Test the actual bash script that verifies diary reflection in diff."""

    def test_diary_reflection_in_diff_passes(self) -> None:
        """When a matching diary reflection is in the diff, the gate passes."""
        result = _run_gate_script(
            "docs/diary/2026-03-08-reflection-fr-158.md",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 0, f"Should pass: {result.stderr}"
        assert "Diary reflection found" in result.stdout

    def test_diary_reflection_absent_from_diff_fails(self) -> None:
        """When no diary reflection is in the diff, the gate fails."""
        result = _run_gate_script(
            "src/main.py\nREADME.md",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 1, "Should fail without diary reflection"
        assert "must include a diary reflection" in result.stdout

    def test_empty_diff_fails(self) -> None:
        """An empty diff (no changed files) fails the gate."""
        result = _run_gate_script(
            "",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 1, "Empty diff should fail"

    def test_diary_among_many_files_passes(self) -> None:
        """A matching diary file among other changed files still passes."""
        result = _run_gate_script(
            "src/main.py\ndocs/diary/2026-03-08-reflection-fr-158.md\ntests/test_foo.py",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 0, "Should pass with diary in file list"

    def test_wrong_fr_number_rejected(self) -> None:
        """A diary file for a different FR number should NOT satisfy the gate."""
        result = _run_gate_script(
            "docs/diary/2026-03-08-reflection-fr-999.md",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 1, "Wrong FR number should not satisfy the check"

    def test_no_fr_reference_skips(self) -> None:
        """A PR without FR-XXX reference skips the gate (passes)."""
        result = _run_gate_script(
            "src/main.py",
            pr_title="fix(typo): correct spelling in README",
        )
        assert result.returncode == 0, "No FR reference should skip"
        assert "diary gate skipped" in result.stdout

    def test_fix_pr_with_fr_enforced(self) -> None:
        """A fix PR with FR reference must also include diary reflection."""
        result = _run_gate_script(
            "src/main.py",
            pr_title="fix(core): FR-042 resolve edge case",
        )
        assert result.returncode == 1, "fix PR with FR reference should enforce diary"

    def test_fix_pr_with_fr_and_diary_passes(self) -> None:
        """A fix PR with FR reference and matching diary file passes."""
        result = _run_gate_script(
            "src/main.py\ndocs/diary/2026-03-08-reflection-fr-042.md",
            pr_title="fix(core): FR-042 resolve edge case",
        )
        assert result.returncode == 0, "fix PR with FR and diary should pass"

    def test_substring_fr_number_not_matched(self) -> None:
        """FR-15 should NOT match a diary file for FR-158."""
        result = _run_gate_script(
            "docs/diary/2026-03-08-reflection-fr-158.md",
            pr_title="feat(ci): FR-15 some feature",
        )
        assert result.returncode == 1, "FR-15 should not match fr-158 diary file"

    def test_diary_file_with_extra_suffix_passes(self) -> None:
        """Diary files with extra descriptive suffixes should still match."""
        result = _run_gate_script(
            "docs/diary/2026-03-08-reflection-fr-158-diary-gate.md",
            pr_title="feat(ci): FR-158 add diary gate",
        )
        assert result.returncode == 0, "Descriptive suffix should still match"
