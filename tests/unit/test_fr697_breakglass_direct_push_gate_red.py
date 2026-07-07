"""Acceptance tests for FR-697 direct-push break-glass ledger gate."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

BREAKGLASS_PATH = Path("reference/break-glass.md")
WORKFLOW_PATH = Path(".github/workflows/commitlint.yml")
SCRIPT_PATH = Path("scripts/check_direct_push_breakglass.py")
CAP_190_PATH = Path("capabilities/CAP-190-breakglass-direct-push-gate.yaml")
ARCHITECTURE_PATH = Path("ARCHITECTURE.md")

EXPECTED_LEDGER_HEADER = "| sha | date | rationale | corrective_action | evidence |"
EXPECTED_RETROACTIVE_SHAS = ["56230029", "caf14330", "2b265793", "b17a8b5e"]


def _load_workflow() -> dict:
    with WORKFLOW_PATH.open() as f:
        return yaml.safe_load(f)


def _setup_git_repo(tmpdir: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmpdir, check=True)
    subprocess.run(
        ["git", "config", "user.email", "valid@example.com"], cwd=tmpdir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Valid User"], cwd=tmpdir, check=True)


def _commit_file(tmpdir: str, filename: str, content: str, message: str) -> str:
    tmppath = Path(tmpdir)
    file_path = tmppath / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
    msg_file = tmppath / "commit-message.txt"
    msg_file.write_text(message)
    subprocess.run(["git", "commit", "-q", "-F", str(msg_file)], cwd=tmpdir, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmpdir,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def _write_ledger(ledger_path: Path, rows: list[str]) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(rows)
    ledger_path.write_text(
        "\n".join(
            [
                "# Test Break Glass",
                "",
                "## Direct-to-main incident ledger",
                "",
                EXPECTED_LEDGER_HEADER,
                "| --- | --- | --- | --- | --- |",
                body,
                "",
            ]
        )
    )


def _run_breakglass_check(
    *,
    tmpdir: str,
    since_sha: str,
    until_sha: str,
    ledger_path: Path,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "python",
            str(SCRIPT_PATH.resolve()),
            "--since-sha",
            since_sha,
            "--until-sha",
            until_sha,
            "--ledger-path",
            str(ledger_path),
        ],
        cwd=tmpdir,
        capture_output=True,
        text=True,
    )


@pytest.mark.req("REQ-YG-525")
def test_ac01_breakglass_ledger_contains_bounded_retroactive_sha_set() -> None:
    content = BREAKGLASS_PATH.read_text().lower()
    for sha in EXPECTED_RETROACTIVE_SHAS:
        assert sha in content


@pytest.mark.req("REQ-YG-525")
def test_ac02_breakglass_ledger_header_matches_contract() -> None:
    content = BREAKGLASS_PATH.read_text()
    assert "## Direct-to-main incident ledger" in content
    assert EXPECTED_LEDGER_HEADER in content


@pytest.mark.req("REQ-YG-525")
def test_ac03_script_fails_when_commit_missing_from_ledger() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        since_sha = _commit_file(tmpdir, "README.md", "base\n", "base")
        until_sha = _commit_file(tmpdir, "src/change.txt", "next\n", "next")

        ledger_path = Path(tmpdir) / "reference/break-glass.md"
        _write_ledger(
            ledger_path,
            rows=[
                f"| {since_sha[:8]} | 2026-07-07 | emergency fix | add gate | FR-697 |",
            ],
        )
        result = _run_breakglass_check(
            tmpdir=tmpdir,
            since_sha=since_sha,
            until_sha=until_sha,
            ledger_path=ledger_path,
        )
        assert result.returncode == 1
        assert "MISSING sha=" in (result.stdout + result.stderr)


@pytest.mark.req("REQ-YG-525")
def test_ac04_script_fails_when_required_ledger_fields_are_blank() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        since_sha = _commit_file(tmpdir, "README.md", "base\n", "base")
        until_sha = _commit_file(tmpdir, "src/change.txt", "next\n", "next")

        ledger_path = Path(tmpdir) / "reference/break-glass.md"
        _write_ledger(
            ledger_path,
            rows=[
                f"| {since_sha[:8]} | 2026-07-07 | emergency fix | add gate | FR-697 |",
                f"| {until_sha[:8]} | 2026-07-07 |  | add gate | FR-697 |",
            ],
        )
        result = _run_breakglass_check(
            tmpdir=tmpdir,
            since_sha=since_sha,
            until_sha=until_sha,
            ledger_path=ledger_path,
        )
        assert result.returncode == 1
        assert "INVALID" in (result.stdout + result.stderr)
        assert "field=rationale" in (result.stdout + result.stderr)


@pytest.mark.req("REQ-YG-525")
def test_ac05_script_passes_when_ledger_covers_all_in_scope_commits() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        since_sha = _commit_file(tmpdir, "README.md", "base\n", "base")
        until_sha = _commit_file(tmpdir, "src/change.txt", "next\n", "next")

        ledger_path = Path(tmpdir) / "reference/break-glass.md"
        _write_ledger(
            ledger_path,
            rows=[
                f"| {since_sha[:8]} | 2026-07-07 | emergency fix | add gate | FR-697 |",
                f"| {until_sha[:8]} | 2026-07-07 | emergency fix | add gate | docs/diary/example.md |",
            ],
        )
        result = _run_breakglass_check(
            tmpdir=tmpdir,
            since_sha=since_sha,
            until_sha=until_sha,
            ledger_path=ledger_path,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "SUMMARY checked=2 missing=0 invalid=0" in result.stdout


@pytest.mark.req("REQ-YG-525")
def test_ac06_commitlint_workflow_defines_breakglass_gate_with_since_sha_56230029() -> (
    None
):
    wf = _load_workflow()
    assert "breakglass-gate" in wf["jobs"]
    job = wf["jobs"]["breakglass-gate"]
    assert job.get("if") == "github.event_name == 'pull_request'"

    run_steps = [step for step in job.get("steps", []) if "run" in step]
    assert run_steps, "breakglass-gate must include a run step"
    run_script = str(run_steps[0]["run"])
    assert "python scripts/check_direct_push_breakglass.py" in run_script
    assert "--since-sha 56230029" in run_script


@pytest.mark.req("REQ-YG-525")
def test_ac07_breakglass_gate_is_advisory_continue_on_error_true() -> None:
    wf = _load_workflow()
    job = wf["jobs"]["breakglass-gate"]
    assert job.get("continue-on-error") is True


@pytest.mark.req("REQ-YG-525")
def test_ac08_traceability_artifacts_reference_req_yg_525() -> None:
    cap = CAP_190_PATH.read_text().lower()
    architecture = ARCHITECTURE_PATH.read_text().lower()

    assert "cap-190" in cap
    assert "req-yg-525" in cap
    assert "fr-697" in cap
    assert "req-yg-525" in architecture
    assert "cap-190 break-glass direct push ledger gate" in architecture
