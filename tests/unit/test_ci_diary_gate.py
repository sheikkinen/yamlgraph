"""Tests for CI diary gate in commitlint.yml (FR-158 + FR-373)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
SEMANTICS_SCRIPT_PATH = Path("scripts/gate_artifact_semantics.sh")


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _diary_gate_run_script() -> str:
    workflow = _load_workflow()
    steps = workflow["jobs"]["diary-gate"]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and "diary reflection" in step.get("name", "").lower()
    ]
    assert verify_steps, "diary-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)


def _run_ci_diary_gate_check(
    changed_files: dict[str, str],
    pr_title: str = "feat(ci): FR-158 diary gate semantics",
) -> subprocess.CompletedProcess:
    run_script = _diary_gate_run_script()

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        semantics_dest = tmppath / "scripts" / "gate_artifact_semantics.sh"
        semantics_dest.parent.mkdir(parents=True, exist_ok=True)
        semantics_dest.write_text(SEMANTICS_SCRIPT_PATH.read_text())
        semantics_dest.chmod(0o755)

        (tmppath / "README.md").write_text("base\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmpdir, check=True)
        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        for relpath, content in changed_files.items():
            fpath = tmppath / relpath
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content)
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "head"], cwd=tmpdir, check=True)
        head_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        env = os.environ.copy()
        env["BASE_SHA"] = base_sha
        env["HEAD_SHA"] = head_sha
        env["PR_TITLE"] = pr_title
        env["PATH"] = "/usr/bin:/bin"
        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


def _valid_diary_body() -> str:
    return (
        "# Reflection FR-158\n\n"
        "## Trap\n"
        "Assuming file presence equals meaningful reflection caused a false green.\n\n"
        "## Heuristic\n"
        "Require structural evidence before passing merge-time compliance gates.\n\n"
        "## Seed\n"
        "Seed: How can we standardize substance checks across all merge gates?\n"
    )


@pytest.mark.req("REQ-YG-152")
class TestDiaryGateJobStructure:
    """Verify diary-gate wiring in commitlint.yml."""

    def test_job_exists(self) -> None:
        wf = _load_workflow()
        assert "diary-gate" in wf["jobs"]

    def test_job_name_mentions_diary_and_feat_fix(self) -> None:
        wf = _load_workflow()
        name = wf["jobs"]["diary-gate"]["name"].lower()
        assert "diary" in name
        assert "feat" in name or "fix" in name

    def test_job_condition_checks_feat_and_fix_titles(self) -> None:
        wf = _load_workflow()
        condition = wf["jobs"]["diary-gate"].get("if", "")
        assert "startsWith(github.event.pull_request.title, 'feat')" in condition
        assert "startsWith(github.event.pull_request.title, 'fix')" in condition

    def test_checkout_uses_fetch_depth_zero(self) -> None:
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        checkout_steps = [
            step
            for step in steps
            if step.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps
        assert checkout_steps[0].get("with", {}).get("fetch-depth") == 0

    def test_verify_step_has_required_env_vars(self) -> None:
        wf = _load_workflow()
        steps = wf["jobs"]["diary-gate"]["steps"]
        verify_steps = [
            step
            for step in steps
            if "run" in step and "diary reflection" in step.get("name", "").lower()
        ]
        assert verify_steps
        env = verify_steps[0].get("env", {})
        assert "BASE_SHA" in env
        assert "HEAD_SHA" in env
        assert "PR_TITLE" in env

    def test_verify_step_sources_shared_semantics_script(self) -> None:
        run_script = _diary_gate_run_script()
        assert "source scripts/gate_artifact_semantics.sh" in run_script
        assert "validate_diary_reflection_file" in run_script


@pytest.mark.req("REQ-YG-152")
class TestDiaryGateShellLogic:
    """Validate semantic behavior of the diary gate script."""

    def test_matching_valid_diary_reflection_passes(self) -> None:
        result = _run_ci_diary_gate_check(
            {"docs/diary/2026-05-13-reflection-fr-158.md": _valid_diary_body()},
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_diary_reflection_absent_from_diff_fails(self) -> None:
        result = _run_ci_diary_gate_check(
            {"src/main.py": "print('x')\n"},
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1
        assert "must include a diary reflection" in (result.stdout + result.stderr)

    def test_empty_diary_reflection_fails(self) -> None:
        result = _run_ci_diary_gate_check(
            {"docs/diary/2026-05-13-reflection-fr-158.md": "\n \t\n"},
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1
        assert "empty" in (result.stdout + result.stderr).lower()

    def test_diary_reflection_below_minimum_size_fails(self) -> None:
        result = _run_ci_diary_gate_check(
            {"docs/diary/2026-05-13-reflection-fr-158.md": "## Trap\nSeed: x\n"},
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1
        assert ">100 bytes" in (result.stdout + result.stderr)

    def test_diary_reflection_missing_header_fails(self) -> None:
        result = _run_ci_diary_gate_check(
            {
                "docs/diary/2026-05-13-reflection-fr-158.md": (
                    "Trap section without markdown headers. " * 8 + "Seed: yes\n"
                )
            },
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1
        assert "## header" in (result.stdout + result.stderr)

    def test_diary_reflection_missing_seed_fails(self) -> None:
        result = _run_ci_diary_gate_check(
            {
                "docs/diary/2026-05-13-reflection-fr-158.md": (
                    "## Trap\n" + ("Content line for size.\n" * 12)
                )
            },
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1
        assert "seed:" in (result.stdout + result.stderr).lower()

    def test_wrong_fr_number_does_not_satisfy_gate(self) -> None:
        result = _run_ci_diary_gate_check(
            {"docs/diary/2026-05-13-reflection-fr-999.md": _valid_diary_body()},
            pr_title="feat(ci): FR-158 enforce diary semantics",
        )
        assert result.returncode == 1

    def test_no_fr_reference_skips_gate(self) -> None:
        result = _run_ci_diary_gate_check(
            {"src/main.py": "print('x')\n"},
            pr_title="fix(readme): correct typo",
        )
        assert result.returncode == 0
        assert "diary gate skipped" in result.stdout
