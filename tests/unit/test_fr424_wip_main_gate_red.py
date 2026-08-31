"""Acceptance tests for FR-424 WIP commit-subject gate."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

PRECOMMIT_PATH = Path(".pre-commit-config.yaml")
WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
CAP_156_PATH = Path("capabilities/CAP-156-wip-commit-subject-gate.yaml")
ARCHITECTURE_PATH = Path("ARCHITECTURE.md")
CLAUDE_PATH = Path("CLAUDE.md")


def _load_precommit() -> dict:
    with PRECOMMIT_PATH.open() as f:
        return yaml.safe_load(f)


def _wip_main_hook_entry() -> str:
    config = _load_precommit()
    for repo in config.get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") == "block-wip-main-subject":
                return str(hook["entry"])
    raise AssertionError("block-wip-main-subject hook must exist")


def _setup_git_repo(tmpdir: str, branch: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "valid@example.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Valid User"], cwd=tmpdir, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "init"],
        cwd=tmpdir,
        check=True,
    )


def _run_precommit_wip_hook(
    *, branch: str, commit_msg: str
) -> subprocess.CompletedProcess:
    entry = _wip_main_hook_entry()
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir, branch)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(commit_msg)
            f.flush()
            msg_file = f.name

        try:
            cmd = f"{entry} {msg_file}"
            return subprocess.run(
                cmd, shell=True, cwd=tmpdir, capture_output=True, text=True
            )
        finally:
            Path(msg_file).unlink()


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _wip_gate_run_script() -> str:
    job = _load_workflow()["jobs"].get("wip-gate")
    assert job is not None, "wip-gate job must exist"

    verify_steps = [
        step
        for step in job.get("steps", [])
        if "run" in step and "wip" in step.get("name", "").lower()
    ]
    assert verify_steps, "wip-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo_with_identity(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "valid@example.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Valid User"], cwd=tmpdir, check=True)


def _commit_with_message(tmpdir: str, *, message: str, index: int) -> None:
    tmppath = Path(tmpdir)
    file_path = tmppath / f"src/file_{index}.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"change {index}\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)

    msg_file = tmppath / f"msg_{index}.txt"
    msg_file.write_text(message)
    subprocess.run(
        ["git", "commit", "-q", "-F", str(msg_file)],
        cwd=tmpdir,
        check=True,
    )


def _run_wip_gate(subjects: list[str]) -> subprocess.CompletedProcess:
    run_script = _wip_gate_run_script()

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo_with_identity(tmpdir)
        _commit_with_message(tmpdir, message="base", index=0)

        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        for index, message in enumerate(subjects, start=1):
            _commit_with_message(tmpdir, message=message, index=index)

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
        env["PATH"] = "/usr/bin:/bin"

        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


@pytest.mark.req("REQ-YG-419")
def test_ac01_precommit_hook_blocks_wip_subject_on_main() -> None:
    result = _run_precommit_wip_hook(branch="main", commit_msg="fix: WIP parser path\n")
    assert result.returncode == 1
    output = (result.stdout + result.stderr).lower()
    assert "wip" in output


@pytest.mark.req("REQ-YG-419")
def test_ac02_precommit_hook_allows_wip_subject_on_feature_branch() -> None:
    result = _run_precommit_wip_hook(
        branch="feature/fr-424", commit_msg="fix: wip parser path\n"
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.req("REQ-YG-419")
def test_ac03_precommit_hook_uses_word_boundary_not_substring() -> None:
    result = _run_precommit_wip_hook(
        branch="main", commit_msg="fix: swipe parser path\n"
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.req("REQ-YG-419")
def test_ac04_commitlint_workflow_has_wip_gate_job() -> None:
    wf = _load_workflow()
    assert "wip-gate" in wf["jobs"]

    script = _wip_gate_run_script()
    assert "BASE_SHA" in script
    assert "HEAD_SHA" in script
    assert "git log --format=%s" in script
    assert "wip" in script.lower()


@pytest.mark.req("REQ-YG-419")
def test_ac05_wip_gate_rejects_wip_subject_in_commit_range() -> None:
    result = _run_wip_gate(["chore: investigate hooks, WIP"])
    assert result.returncode == 1
    output = (result.stdout + result.stderr).lower()
    assert "wip" in output


@pytest.mark.req("REQ-YG-419")
def test_ac06_wip_gate_allows_clean_commit_range() -> None:
    result = _run_wip_gate(["chore: stabilize hook behavior"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no wip subjects found" in result.stdout.lower()


@pytest.mark.req("REQ-YG-419")
def test_ac07_traceability_docs_reference_req_yg_419() -> None:
    cap = CAP_156_PATH.read_text().lower()
    architecture = ARCHITECTURE_PATH.read_text().lower()
    # FR-942 moved the CI checks list from CLAUDE.md to the ops reference.
    dev_ops = Path("reference/development-operations.md").read_text().lower()

    assert "req-yg-419" in cap
    assert "wip-gate" in cap
    assert "req-yg-419" in architecture
    assert "wip-gate" in architecture
    assert "wip-gate" in dev_ops
