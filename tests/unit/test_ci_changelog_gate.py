"""Tests for CI changelog gate in commitlint.yml (FR-149 + FR-373)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
SEMANTICS_SCRIPT_PATH = Path("scripts/gate_artifact_semantics.sh")


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _changelog_gate_run_script() -> str:
    workflow = _load_workflow()
    steps = workflow["jobs"]["changelog-gate"]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and "changelog fragment" in step.get("name", "").lower()
    ]
    assert verify_steps, "changelog-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)


def _run_ci_changelog_gate_check(
    changed_files: dict[str, str],
) -> subprocess.CompletedProcess:
    run_script = _changelog_gate_run_script()

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
        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


@pytest.mark.req("REQ-YG-148")
class TestChangelogGateJobStructure:
    """Verify changelog-gate wiring in commitlint.yml."""

    def test_job_exists(self) -> None:
        wf = _load_workflow()
        assert "changelog-gate" in wf["jobs"]

    def test_job_name_mentions_changelog_and_feat_fix(self) -> None:
        wf = _load_workflow()
        name = wf["jobs"]["changelog-gate"]["name"].lower()
        assert "changelog" in name
        assert "feat" in name or "fix" in name

    def test_job_condition_checks_feat_and_fix_titles(self) -> None:
        wf = _load_workflow()
        condition = wf["jobs"]["changelog-gate"].get("if", "")
        assert "startsWith(github.event.pull_request.title, 'feat')" in condition
        assert "startsWith(github.event.pull_request.title, 'fix')" in condition

    def test_checkout_uses_fetch_depth_zero(self) -> None:
        wf = _load_workflow()
        steps = wf["jobs"]["changelog-gate"]["steps"]
        checkout_steps = [
            step
            for step in steps
            if step.get("uses", "").startswith("actions/checkout")
        ]
        assert checkout_steps
        assert checkout_steps[0].get("with", {}).get("fetch-depth") == 0

    def test_verify_step_has_required_sha_env_vars(self) -> None:
        wf = _load_workflow()
        steps = wf["jobs"]["changelog-gate"]["steps"]
        verify_steps = [
            step
            for step in steps
            if "run" in step and "changelog fragment" in step.get("name", "").lower()
        ]
        assert verify_steps
        env = verify_steps[0].get("env", {})
        assert "BASE_SHA" in env
        assert "HEAD_SHA" in env

    def test_verify_step_sources_shared_semantics_script(self) -> None:
        run_script = _changelog_gate_run_script()
        assert "source scripts/gate_artifact_semantics.sh" in run_script
        assert "validate_changelog_fragment_file" in run_script


@pytest.mark.req("REQ-YG-148")
class TestChangelogGateShellLogic:
    """Validate semantic behavior of the changelog gate script."""

    def test_valid_fragment_in_diff_passes(self) -> None:
        result = _run_ci_changelog_gate_check(
            {
                "changelog/unreleased/fr-373-valid.md": (
                    "---\n"
                    "type: feat\n"
                    "scope: ci\n"
                    "---\n"
                    "- Added robust changelog substance checks.\n"
                )
            }
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def test_empty_fragment_fails(self) -> None:
        result = _run_ci_changelog_gate_check(
            {"changelog/unreleased/fr-373-empty.md": "  \n\t\n"}
        )
        assert result.returncode == 1
        assert "empty" in (result.stdout + result.stderr).lower()

    def test_missing_type_in_front_matter_fails(self) -> None:
        result = _run_ci_changelog_gate_check(
            {
                "changelog/unreleased/fr-373-no-type.md": (
                    "---\nscope: ci\n---\n- Body item exists but type is missing.\n"
                )
            }
        )
        assert result.returncode == 1
        assert "type" in (result.stdout + result.stderr).lower()

    def test_missing_body_list_item_fails(self) -> None:
        result = _run_ci_changelog_gate_check(
            {
                "changelog/unreleased/fr-373-no-list.md": (
                    "---\n"
                    "type: feat\n"
                    "scope: ci\n"
                    "---\n"
                    "Body exists but not as a markdown bullet.\n"
                )
            }
        )
        assert result.returncode == 1
        assert "list item" in (result.stdout + result.stderr).lower()

    def test_fragment_absent_from_diff_fails(self) -> None:
        result = _run_ci_changelog_gate_check({"src/main.py": "print('x')\n"})
        assert result.returncode == 1
        assert "must include a changelog fragment" in (result.stdout + result.stderr)

    def test_versioned_changelog_paths_do_not_satisfy_gate(self) -> None:
        result = _run_ci_changelog_gate_check(
            {"changelog/0.5.0/fr-373-old.md": "---\ntype: feat\n---\n- old\n"}
        )
        assert result.returncode == 1
