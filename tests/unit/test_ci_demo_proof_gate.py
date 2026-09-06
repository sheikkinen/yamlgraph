"""Tests for CI demo proof gate in commitlint.yml (FR-206).

Validates that the `demo-gate` job in `.github/workflows/commitlint.yml`
blocks PRs that modify demo files without including a `demo-output.log`,
and that `scripts/check_demo_proof.sh` enforces the same locally via
pre-commit.

Three test layers:
1. YAML structure — parse the workflow and verify job config.
2. Shell logic — run check_demo_proof.sh against temp git repos.
3. Documentation — CLAUDE.md and .pre-commit-config.yaml updated.
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKFLOW_PATH = ".github/workflows/commitlint.yml"
PRECOMMIT_PATH = ".pre-commit-config.yaml"
SCRIPT_PATH = "scripts/check_demo_proof.sh"


def _load_workflow() -> dict:
    """Load and parse the commitlint workflow YAML."""
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_precommit() -> dict:
    """Load and parse the pre-commit config YAML."""
    with open(PRECOMMIT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _setup_git_repo(tmpdir: str) -> None:
    """Initialize a git repo with basic config in tmpdir."""
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


def _run_demo_proof_check(
    staged_files: dict[str, str],
) -> subprocess.CompletedProcess:
    """Run check_demo_proof.sh against staged files in a temp git repo.

    Args:
        staged_files: Mapping of relative path -> file content to stage.

    Returns:
        CompletedProcess with stdout, stderr, returncode.
    """
    script_abs = str(Path(SCRIPT_PATH).resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        # Create an initial commit so HEAD exists
        readme = tmppath / "README.md"
        readme.write_text("init\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"],
            cwd=tmpdir,
            check=True,
        )

        # Write and stage the test files
        for relpath, content in staged_files.items():
            fpath = tmppath / relpath
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content, encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)

        return subprocess.run(
            ["bash", script_abs],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )


# ── YAML Structure Tests ───────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-200")
class TestDemoGateJobStructure:
    """Verify the demo-gate job exists with correct configuration."""

    def test_job_exists(self) -> None:
        """The commitlint workflow must contain a 'demo-gate' job."""
        wf = _load_workflow()
        assert "demo-gate" in wf["jobs"], "Missing 'demo-gate' job in commitlint.yml"

    def test_job_name(self) -> None:
        """The job display name indicates demo proof checking."""
        wf = _load_workflow()
        job = wf["jobs"]["demo-gate"]
        assert "demo" in job["name"].lower(), "Job name must mention demo"

    def test_job_restricted_to_feat_fix(self) -> None:
        """The job runs only on feat/fix PRs via if condition."""
        wf = _load_workflow()
        job = wf["jobs"]["demo-gate"]
        condition = job.get("if", "")
        assert "feat" in condition, "Job must filter for feat PRs"
        assert "fix" in condition, "Job must filter for fix PRs"

    def test_checkout_with_full_history(self) -> None:
        """The job must check out with fetch-depth: 0 for diff access."""
        wf = _load_workflow()
        steps = wf["jobs"]["demo-gate"]["steps"]
        checkout_steps = [
            s for s in steps if s.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps, "Must have an actions/checkout step"
        checkout = checkout_steps[0]
        assert (
            checkout.get("with", {}).get("fetch-depth") == 0
        ), "Must use fetch-depth: 0"

    def test_uses_base_head_sha_env(self) -> None:
        """The verification step must use BASE_SHA and HEAD_SHA env vars."""
        wf = _load_workflow()
        steps = wf["jobs"]["demo-gate"]["steps"]
        verify_steps = [
            s for s in steps if "run" in s and "demo" in s.get("run", "").lower()
        ]
        assert verify_steps, "Must have a step that checks demo output"
        step = verify_steps[0]
        env = step.get("env", {})
        assert "BASE_SHA" in env, "Must set BASE_SHA env var"
        assert "HEAD_SHA" in env, "Must set HEAD_SHA env var"

    def test_fails_on_missing_log(self) -> None:
        """The script must exit 1 when demo-output.log is missing."""
        wf = _load_workflow()
        steps = wf["jobs"]["demo-gate"]["steps"]
        verify_steps = [
            s for s in steps if "run" in s and "demo" in s.get("run", "").lower()
        ]
        assert verify_steps, "Must have a demo check step"
        run_script = verify_steps[0]["run"]
        assert "exit 1" in run_script, "Must exit 1 on missing demo proof"

    def test_skips_when_no_demos_changed(self) -> None:
        """The script must skip gracefully when no demo files changed."""
        wf = _load_workflow()
        steps = wf["jobs"]["demo-gate"]["steps"]
        verify_steps = [
            s for s in steps if "run" in s and "demo" in s.get("run", "").lower()
        ]
        assert verify_steps, "Must have a demo check step"
        run_script = verify_steps[0]["run"]
        assert "exit 0" in run_script, "Must exit 0 when no demos changed"


# ── Shell Script Logic Tests ───────────────────────────────────────────────


@pytest.mark.slow
@pytest.mark.req("REQ-YG-200")
class TestDemoProofShellLogic:
    """Test check_demo_proof.sh against real temp git repos."""

    def test_script_exists(self) -> None:
        """The check_demo_proof.sh script must exist."""
        assert Path(SCRIPT_PATH).exists(), f"Missing {SCRIPT_PATH}"

    def test_script_is_executable(self) -> None:
        """The script must be executable."""
        assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} must be executable"

    def test_no_demo_files_passes(self) -> None:
        """When no demo files are staged, the check passes."""
        result = _run_demo_proof_check({"src/main.py": "print('hello')\n"})
        assert result.returncode == 0, f"Should pass: {result.stdout}"

    def test_demo_with_log_passes(self) -> None:
        """When a demo file and its demo-output.log are both staged, passes."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": (
                    "2026-01-01 00:00:00 [INFO] yamlgraph.node_factory.llm_nodes: "
                    "Node greet completed successfully\n"
                    "✓ Graph execution completed successfully\n"
                ),
            }
        )
        assert result.returncode == 0, f"Should pass with log: {result.stdout}"

    def test_demo_without_log_fails(self) -> None:
        """When a demo file is staged without demo-output.log, fails."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
            }
        )
        assert result.returncode == 1, f"Should fail without log: {result.stdout}"
        assert (
            "demo-output.log" in result.stdout.lower()
            or "demo-output.log" in result.stderr.lower()
        )

    def test_multiple_demos_all_need_logs(self) -> None:
        """Each changed demo directory needs its own demo-output.log."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/graph.yaml": "nodes: {}\n",
                "examples/demos/hello/demo-output.log": "output\n",
                "examples/demos/router/graph.yaml": "nodes: {}\n",
                # router is missing its log
            }
        )
        assert result.returncode == 1, f"Should fail for router: {result.stdout}"

    def test_only_log_changed_passes(self) -> None:
        """When only demo-output.log is staged (no other demo files), passes."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/demo-output.log": "new output\n",
            }
        )
        assert result.returncode == 0, f"Log-only change should pass: {result.stdout}"

    def test_readme_change_needs_log(self) -> None:
        """Changing any file in a demo dir (not just graph.yaml) requires log."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/README.md": "# Hello\n",
            }
        )
        assert (
            result.returncode == 1
        ), f"README change should require log: {result.stdout}"

    def test_nested_demo_file_needs_log(self) -> None:
        """Changing a file in a subdirectory of a demo requires log."""
        result = _run_demo_proof_check(
            {
                "examples/demos/hello/prompts/main.yaml": "system: hi\n",
            }
        )
        assert (
            result.returncode == 1
        ), f"Nested file change should require log: {result.stdout}"


# ── Pre-commit Hook Tests ──────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-200")
class TestDemoProofPrecommitHook:
    """Verify .pre-commit-config.yaml includes demo-proof-check hook."""

    def test_hook_exists(self) -> None:
        """The pre-commit config must include a demo-proof-check hook."""
        config = _load_precommit()
        hook_ids = []
        for repo in config.get("repos", []):
            for hook in repo.get("hooks", []):
                hook_ids.append(hook["id"])
        assert (
            "demo-proof-check" in hook_ids
        ), "Missing 'demo-proof-check' hook in .pre-commit-config.yaml"

    def test_hook_uses_script(self) -> None:
        """The hook must point to scripts/check_demo_proof.sh."""
        config = _load_precommit()
        for repo in config.get("repos", []):
            for hook in repo.get("hooks", []):
                if hook["id"] == "demo-proof-check":
                    assert "check_demo_proof" in hook.get(
                        "entry", ""
                    ), "Hook must use check_demo_proof script"
                    return
        pytest.fail("Hook not found")

    def test_hook_stage_is_precommit(self) -> None:
        """The hook must run at pre-commit stage."""
        config = _load_precommit()
        for repo in config.get("repos", []):
            for hook in repo.get("hooks", []):
                if hook["id"] == "demo-proof-check":
                    stages = hook.get("stages", [])
                    assert "pre-commit" in stages, "Hook must run at pre-commit stage"
                    return
        pytest.fail("Hook not found")


# ── Gitignore Tests ────────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-200")
class TestDemoOutputLogNotIgnored:
    """Verify demo-output.log is explicitly NOT gitignored."""

    def test_gitignore_negation_exists(self) -> None:
        """The .gitignore must have a negation pattern for demo-output.log."""
        content = Path(".gitignore").read_text(encoding="utf-8")
        assert (
            "!examples/demos/*/demo-output.log" in content
        ), ".gitignore must negate *.log for demo-output.log files"


# ── Documentation Tests ────────────────────────────────────────────────────


@pytest.mark.req("REQ-YG-200")
class TestDemoGateDocumentation:
    """Verify the ops reference documents the demo-gate status check.

    FR-942 moved the CI checks list from CLAUDE.md to
    reference/development-operations.md.
    """

    def test_dev_ops_lists_demo_gate(self) -> None:
        """The CI checks section must list demo-gate."""
        content = Path("reference/development-operations.md").read_text(encoding="utf-8")
        assert (
            "demo-gate" in content
        ), "development-operations.md must list demo-gate as a status check"

    def test_dev_ops_describes_demo_gate(self) -> None:
        """The ops reference must describe what the demo-gate does."""
        content = Path("reference/development-operations.md").read_text(encoding="utf-8")
        assert (
            "demo-output.log" in content or "demo proof" in content.lower()
        ), "development-operations.md must describe demo-gate purpose"

