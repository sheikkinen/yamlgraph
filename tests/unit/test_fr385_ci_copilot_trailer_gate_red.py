"""Acceptance tests for FR-385 CI Copilot trailer gate."""

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

TRAILER_SHORT = "Co-authored-by: Copilot"
TRAILER_FULL = "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _copilot_trailer_gate_run_script() -> str:
    steps = _load_workflow()["jobs"]["copilot-trailer-gate"]["steps"]
    verify_steps = [
        step
        for step in steps
        if "run" in step and "copilot trailer" in step.get("name", "").lower()
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


def _run_copilot_trailer_gate(
    commit_messages: list[str], pr_body: str = ""
) -> subprocess.CompletedProcess:
    run_script = _copilot_trailer_gate_run_script()

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
def test_ac01_workflow_has_copilot_trailer_gate_job() -> None:
    wf = _load_workflow()
    assert "copilot-trailer-gate" in wf["jobs"]
    name = wf["jobs"]["copilot-trailer-gate"]["name"].lower()
    assert "copilot" in name and "trailer" in name


@pytest.mark.req("REQ-YG-358")
def test_ac01_commit_scan_detects_short_form_copilot_trailer() -> None:
    result = _run_copilot_trailer_gate([f"feat(ci): test gate\n\n{TRAILER_SHORT}"])
    assert result.returncode == 1
    assert "commit messages" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac02_commit_scan_detects_full_form_copilot_trailer() -> None:
    result = _run_copilot_trailer_gate([f"feat(ci): test gate\n\n{TRAILER_FULL}"])
    assert result.returncode == 1
    assert "commit messages" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac03_pr_body_scan_detects_short_form_copilot_trailer() -> None:
    result = _run_copilot_trailer_gate(
        ["feat(ci): clean commit"],
        pr_body=f"This PR body contains a trailer.\n\n{TRAILER_SHORT}",
    )
    assert result.returncode == 1
    assert "pr body" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac04_pr_body_scan_detects_full_form_copilot_trailer() -> None:
    result = _run_copilot_trailer_gate(
        ["feat(ci): clean commit"],
        pr_body=f"This PR body contains a trailer.\n\n{TRAILER_FULL}",
    )
    assert result.returncode == 1
    assert "pr body" in (result.stdout + result.stderr).lower()


@pytest.mark.req("REQ-YG-358")
def test_ac05_clean_commit_messages_and_pr_body_pass() -> None:
    result = _run_copilot_trailer_gate(
        ["feat(ci): safe commit message"],
        pr_body="Normal body content without co-author trailers.",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no copilot co-author trailers found" in result.stdout.lower()


@pytest.mark.req("REQ-YG-358")
def test_ac06_workflow_step_uses_deterministic_grep_without_llm() -> None:
    script = _copilot_trailer_gate_run_script()
    assert "git log --format=%B" in script
    assert "grep -Fq" in script
    assert "PR_BODY" in script
    assert "TRAILER_SHORT" in script
    assert "TRAILER_FULL" in script
    assert "llm" not in script.lower()
    assert "execute_prompt" not in script


@pytest.mark.req("REQ-YG-358")
def test_ac07_architecture_and_capability_entries_reference_new_req() -> None:
    cap = CAP_148_PATH.read_text().lower()
    architecture = ARCHITECTURE_PATH.read_text().lower()
    claude = CLAUDE_PATH.read_text().lower()

    assert "req-yg-358" in cap
    assert "copilot-trailer-gate" in cap
    assert "req-yg-358" in architecture
    assert "copilot-trailer-gate" in architecture
    assert "copilot-trailer-gate" in claude
    assert "co-authored-by: copilot" in claude
