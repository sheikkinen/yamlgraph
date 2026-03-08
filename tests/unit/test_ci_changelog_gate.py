"""Tests for CI CHANGELOG gate in commitlint.yml (FR-149).

Validates that the `changelog-gate` job in `.github/workflows/commitlint.yml`
correctly blocks feat/fix PRs without CHANGELOG.md in the diff and skips
for other PR types.

Two test layers:
1. YAML structure — parse the workflow and verify job config, conditions, steps.
2. Shell logic — run the verification script with mocked git diff output.
"""

import subprocess

import pytest
import yaml

WORKFLOW_PATH = ".github/workflows/commitlint.yml"

# The shell script from the changelog-gate step, extracted for unit testing.
# Mirrors the `run:` block in commitlint.yml; uses env vars BASE_SHA/HEAD_SHA.
CHANGELOG_GATE_SCRIPT = """\
if git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -qE '^CHANGELOG\\.md$'; then
  echo "✅ CHANGELOG.md is modified"
else
  echo "::error::feat/fix PRs must include changes to CHANGELOG.md"
  exit 1
fi
"""


def _load_workflow() -> dict:
    """Load and parse the commitlint workflow YAML."""
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


def _run_gate_script(diff_output: str) -> subprocess.CompletedProcess:
    """Run the changelog gate script with mocked git diff output.

    Replaces `git diff --name-only "$BASE_SHA" "$HEAD_SHA"` with an echo
    of the provided diff output to test the grep logic in isolation.
    """
    script = CHANGELOG_GATE_SCRIPT.replace(
        'git diff --name-only "$BASE_SHA" "$HEAD_SHA"',
        f"echo '{diff_output}'",
    )
    return subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
    )


# ── YAML Structure Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-148")
class TestChangelogGateJobStructure:
    """Verify the changelog-gate job exists with correct configuration."""

    def test_job_exists(self) -> None:
        """The commitlint workflow must contain a 'changelog-gate' job."""
        wf = _load_workflow()
        assert (
            "changelog-gate" in wf["jobs"]
        ), "Missing 'changelog-gate' job in commitlint.yml"

    def test_job_name(self) -> None:
        """The job display name indicates CHANGELOG is required for feat/fix."""
        wf = _load_workflow()
        job = wf["jobs"]["changelog-gate"]
        assert "CHANGELOG" in job["name"], "Job name must mention CHANGELOG"
        assert (
            "feat" in job["name"] or "fix" in job["name"]
        ), "Job name must mention feat or fix"

    def test_job_condition_checks_feat(self) -> None:
        """The job-level `if` condition must check for 'feat' PR titles."""
        wf = _load_workflow()
        job = wf["jobs"]["changelog-gate"]
        condition = job.get("if", "")
        assert (
            "startsWith(github.event.pull_request.title, 'feat')" in condition
        ), "Job must check for feat PR titles"

    def test_job_condition_checks_fix(self) -> None:
        """The job-level `if` condition must check for 'fix' PR titles."""
        wf = _load_workflow()
        job = wf["jobs"]["changelog-gate"]
        condition = job.get("if", "")
        assert (
            "startsWith(github.event.pull_request.title, 'fix')" in condition
        ), "Job must check for fix PR titles"

    def test_checkout_with_full_history(self) -> None:
        """The checkout step must use fetch-depth: 0 for full git history."""
        wf = _load_workflow()
        steps = wf["jobs"]["changelog-gate"]["steps"]
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
        steps = wf["jobs"]["changelog-gate"]["steps"]
        verify_steps = [s for s in steps if "run" in s and "CHANGELOG" in s["run"]]
        assert verify_steps, "Must have a step that checks CHANGELOG.md"
        run_script = verify_steps[0]["run"]
        assert "git diff --name-only" in run_script
        assert "CHANGELOG" in run_script

    def test_verify_step_has_sha_env_vars(self) -> None:
        """The verification step must receive BASE_SHA and HEAD_SHA from GitHub context."""
        wf = _load_workflow()
        steps = wf["jobs"]["changelog-gate"]["steps"]
        verify_steps = [s for s in steps if "run" in s and "CHANGELOG" in s["run"]]
        assert verify_steps, "Must have a verification step"
        env = verify_steps[0].get("env", {})
        assert "BASE_SHA" in env, "Must pass BASE_SHA env var"
        assert "HEAD_SHA" in env, "Must pass HEAD_SHA env var"


# ── Shell Script Logic Tests ───────────────────────────────────────────────


@pytest.mark.req("REQ-YG-148")
class TestChangelogGateShellLogic:
    """Test the actual bash script that verifies CHANGELOG.md in diff."""

    def test_changelog_in_diff_passes(self) -> None:
        """When CHANGELOG.md is in the diff, the gate passes."""
        result = _run_gate_script("CHANGELOG.md")
        assert result.returncode == 0, f"Should pass: {result.stderr}"
        assert "CHANGELOG.md is modified" in result.stdout

    def test_changelog_absent_from_diff_fails(self) -> None:
        """When CHANGELOG.md is NOT in the diff, the gate fails."""
        result = _run_gate_script("src/main.py\nREADME.md")
        assert result.returncode == 1, "Should fail without CHANGELOG.md"
        assert (
            "must include changes to CHANGELOG.md" in result.stderr
            or "must include changes to CHANGELOG.md" in result.stdout
        )

    def test_empty_diff_fails(self) -> None:
        """An empty diff (no changed files) fails the gate."""
        result = _run_gate_script("")
        assert result.returncode == 1, "Empty diff should fail"

    def test_changelog_among_many_files_passes(self) -> None:
        """CHANGELOG.md among other changed files still passes."""
        result = _run_gate_script("src/main.py\nCHANGELOG.md\ntests/test_foo.py")
        assert result.returncode == 0, "Should pass with CHANGELOG.md in file list"

    def test_partial_match_rejected(self) -> None:
        """A file like 'docs/CHANGELOG.md' should NOT satisfy the gate."""
        result = _run_gate_script("docs/CHANGELOG.md")
        assert (
            result.returncode == 1
        ), "Nested CHANGELOG.md should not satisfy root-level check"

    def test_substring_match_rejected(self) -> None:
        """A file like 'CHANGELOG.md.bak' should NOT satisfy the gate."""
        result = _run_gate_script("CHANGELOG.md.bak")
        assert result.returncode == 1, "CHANGELOG.md.bak should not satisfy the check"
