"""Acceptance tests for FR-409 CI Co-authored-by gate generalization."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
CAP_148_PATH = Path("capabilities/CAP-148-ci-copilot-trailer-gate.yaml")
ARCHITECTURE_PATH = Path("ARCHITECTURE.md")
CLAUDE_PATH = Path("CLAUDE.md")

NON_COPILOT_TRAILER = "Co-authored-by: Test <test@example.com>"
COPILOT_TRAILER_SHORT = "Co-authored-by: Copilot"
COPILOT_TRAILER_FULL = (
    "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
)


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _gate_run_script() -> str:
    steps = _load_workflow()["jobs"]["copilot-trailer-gate"]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and "co-authored-by trailer" in step.get("name", "").lower()
    ]
    assert verify_steps, "copilot-trailer-gate must include a verification step"
    return str(verify_steps[0]["run"])


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)


def _commit_with_message(
    tmpdir: str, message: str, filename: str, content: str
) -> None:
    tmppath = Path(tmpdir)
    file_path = tmppath / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    msg_file = tmppath / "commit-message.txt"
    msg_file.write_text(message)
    subprocess.run(["git", "commit", "-q", "-F", str(msg_file)], cwd=tmpdir, check=True)


def _run_trailer_gate(
    commit_messages: list[str], pr_body: str = ""
) -> subprocess.CompletedProcess:
    run_script = _gate_run_script()

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)

        _commit_with_message(tmpdir, "base", "README.md", "base\n")
        base_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmpdir,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        if commit_messages:
            for index, message in enumerate(commit_messages, start=1):
                _commit_with_message(
                    tmpdir,
                    message,
                    f"src/file_{index}.txt",
                    f"change {index}\n",
                )
        else:
            _commit_with_message(tmpdir, "head", "src/file_1.txt", "change\n")

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
        env["PR_BODY"] = pr_body
        env["PATH"] = "/usr/bin:/bin"

        return subprocess.run(
            ["bash", "-lc", run_script],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )


@pytest.mark.req("REQ-YG-358")
def test_ac01_commit_scan_rejects_non_copilot_coauthored_by_trailer() -> None:
    result = _run_trailer_gate([f"feat(ci): test gate\n\n{NON_COPILOT_TRAILER}"])
    assert result.returncode == 1
    assert "commit messages" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac02_pr_body_scan_rejects_non_copilot_coauthored_by_trailer() -> None:
    result = _run_trailer_gate(
        ["feat(ci): clean commit"],
        pr_body=f"This PR body contains a trailer.\n\n{NON_COPILOT_TRAILER}",
    )
    assert result.returncode == 1
    assert "pr body" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
@pytest.mark.parametrize(
    "trailer",
    [COPILOT_TRAILER_SHORT, COPILOT_TRAILER_FULL],
)
def test_ac03_commit_scan_still_rejects_copilot_short_and_full_forms(
    trailer: str,
) -> None:
    result = _run_trailer_gate([f"feat(ci): test gate\n\n{trailer}"])
    assert result.returncode == 1
    assert "commit messages" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac04_clean_commits_and_pr_body_pass_without_trailers() -> None:
    result = _run_trailer_gate(
        ["feat(ci): safe commit message"],
        pr_body="Normal body content without co-author trailers.",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no co-authored-by trailers found" in result.stdout.lower()


@pytest.mark.req("REQ-YG-358")
def test_ac05_workflow_script_no_longer_depends_on_copilot_literal_constants() -> None:
    script = _gate_run_script()
    assert "TRAILER_SHORT" not in script
    assert "TRAILER_FULL" not in script
    assert "Co-authored-by: Copilot" not in script
    assert "TRAILER_PATTERN" in script
    assert "Co-authored-by:" in script


@pytest.mark.req("REQ-YG-358")
def test_ac06_traceability_docs_use_generalized_coauthored_by_language() -> None:
    cap = CAP_148_PATH.read_text()
    architecture = ARCHITECTURE_PATH.read_text()
    # FR-942 moved the CI checks list from CLAUDE.md to the ops reference.
    dev_ops = Path("reference/development-operations.md").read_text()

    assert "any `Co-authored-by:` trailer" in cap
    assert "any `Co-authored-by:` trailer" in architecture
    assert "any `Co-authored-by:` trailer" in dev_ops
