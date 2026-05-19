"""Acceptance tests for FR-410 CI author identity gate."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _gate_run_script() -> str:
    job = _load_workflow()["jobs"].get("author-identity-gate")
    assert job is not None, "author-identity-gate job must exist"

    verify_steps = [
        step
        for step in job.get("steps", [])
        if "run" in step and "author identity" in step.get("name", "").lower()
    ]
    assert verify_steps, "author-identity-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)


def _commit_as(tmpdir: str, *, name: str, email: str, message: str, index: int) -> None:
    tmppath = Path(tmpdir)
    file_path = tmppath / f"src/file_{index}.txt"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(f"change {index}\n")
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)

    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = name
    env["GIT_AUTHOR_EMAIL"] = email
    env["GIT_COMMITTER_NAME"] = name
    env["GIT_COMMITTER_EMAIL"] = email

    msg_file = tmppath / f"msg_{index}.txt"
    msg_file.write_text(message)
    subprocess.run(
        ["git", "commit", "-q", "-F", str(msg_file)], cwd=tmpdir, check=True, env=env
    )


def _run_author_identity_gate(
    head_author: tuple[str, str],
) -> subprocess.CompletedProcess:
    run_script = _gate_run_script()

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)

        _commit_as(
            tmpdir,
            name="Valid User",
            email="valid@example.com",
            message="base",
            index=0,
        )
        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        _commit_as(
            tmpdir,
            name=head_author[0],
            email=head_author[1],
            message="head",
            index=1,
        )
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


@pytest.mark.req("REQ-YG-002")
def test_ac05_workflow_contains_author_identity_gate() -> None:
    wf = _load_workflow()
    assert "author-identity-gate" in wf["jobs"]

    script = _gate_run_script()
    assert "BASE_SHA" in script
    assert "HEAD_SHA" in script
    assert "git log" in script
    assert "test@test.com" in script


@pytest.mark.req("REQ-YG-002")
def test_ac06_gate_rejects_blocklisted_identity_in_commit_range() -> None:
    result = _run_author_identity_gate(("Test", "test@test.com"))
    assert result.returncode == 1
    output = (result.stdout + result.stderr).lower()
    assert "blocked" in output or "author" in output


@pytest.mark.req("REQ-YG-002")
def test_ac07_gate_allows_clean_commit_range() -> None:
    result = _run_author_identity_gate(("Another User", "another@example.com"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no blocked author identities" in result.stdout.lower()
