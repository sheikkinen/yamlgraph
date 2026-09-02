#!/usr/bin/env python3
"""FR-869 spike-end detector tests for pre-command-guard.sh.

Warn-only detector: foreign-cwd `git commit` in an unenforced repo emits
warnings on stderr; stdout stays exact approve JSON; audit entries carry
stable reason names with no diff content.

Run: pytest .github/hooks/tests/test_fr869_spike_detector.py -q --no-cov
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "scripts" / "pre-command-guard.sh"
REPO_ROOT = Path(__file__).resolve().parents[3]
GIT = shutil.which("git") or "git"
pytestmark = pytest.mark.req("REQ-YG-527")

WARN_UNENFORCED = (
    "⚠ this repo has no pre-commit hooks — scripts/ramp.sh <repo> --tier 1 exists"
)
WARN_SPIKE_END = "⚠ this commit takes an unenforced repo live"


def run_hook(payload, *, log_dir: str) -> tuple[int, str, str, list[dict]]:
    """Run hook, return (exit_code, stdout, stderr, audit_entries)."""
    env = {**os.environ, "HOOK_LOG_DIR": log_dir}
    r = subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    entries = []
    logfile = Path(log_dir) / "audit.jsonl"
    if logfile.exists():
        for line in logfile.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                entries.append(json.loads(line))
    return r.returncode, r.stdout.strip(), r.stderr, entries


def commit_payload(cwd: Path | str) -> dict:
    return {
        "toolName": "run_in_terminal",
        "toolInput": {"command": "git commit -F ./tmp/msg.txt"},
        "cwd": str(cwd),
    }


def make_repo(tmp_path: Path, name: str, *, hooks: str) -> Path:
    """Create a scratch git repo. hooks: none|empty-dir|zero-byte|real."""
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run([GIT, "init", "-q", repo], check=True, capture_output=True)
    hooks_dir = repo / ".git" / "hooks"
    # git init seeds sample hooks; normalize to the requested state
    if hooks_dir.exists():
        for f in hooks_dir.iterdir():
            f.unlink()
    if hooks == "none":
        pass  # empty hooks dir, no pre-commit
    elif hooks == "empty-dir":
        pass
    elif hooks == "zero-byte":
        (hooks_dir / "pre-commit").touch()
    elif hooks == "real":
        pc = hooks_dir / "pre-commit"
        pc.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        pc.chmod(0o755)
    elif hooks == "no-dir":
        for f in hooks_dir.iterdir():
            f.unlink()
        hooks_dir.rmdir()
    else:
        raise ValueError(hooks)
    return repo


def stage_file(repo: Path, relpath: str, content: str) -> None:
    p = repo / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    subprocess.run([GIT, "-C", repo, "add", relpath], check=True, capture_output=True)


def assert_approve(stdout: str) -> None:
    assert json.loads(stdout) == {"decision": "approve"}


# ── Check 1: unenforced repo (AC-02, AC-03) ─────────────────────────────


def test_missing_pre_commit_warns(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    rc, out, err, entries = run_hook(
        commit_payload(repo), log_dir=str(tmp_path / "logs")
    )
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED in err
    reasons = [e.get("reason") for e in entries]
    assert "ramp-unenforced" in reasons


def test_zero_byte_pre_commit_warns(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="zero-byte")
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED in err


def test_absent_hooks_dir_warns(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="no-dir")
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED in err


def test_real_pre_commit_no_warning(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="real")
    rc, out, err, entries = run_hook(
        commit_payload(repo), log_dir=str(tmp_path / "logs")
    )
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err
    assert WARN_SPIKE_END not in err
    assert all(e.get("reason", "").startswith("ramp") is False for e in entries)


def test_nested_dir_resolves_to_repo_root(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    nested = repo / "src" / "deep"
    nested.mkdir(parents=True)
    rc, out, err, _ = run_hook(commit_payload(nested), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED in err


# ── Check 2: spike ending (AC-04..AC-07) ────────────────────────────────


def test_added_schedule_line_fires_spike_end(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    stage_file(
        repo,
        ".github/workflows/pub.yml",
        "on:\n  schedule:\n    - cron: '0 6 * * *'\n",
    )
    rc, out, err, entries = run_hook(
        commit_payload(repo), log_dir=str(tmp_path / "logs")
    )
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED in err
    assert WARN_SPIKE_END in err
    reasons = [e.get("reason") for e in entries]
    assert "ramp-spike-end" in reasons


def test_added_secrets_ref_fires_spike_end(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    stage_file(
        repo,
        ".github/workflows/pub.yaml",
        "env:\n  TOKEN: ${{ secrets.DA_TOKEN }}\n",
    )
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_SPIKE_END in err


def test_spike_end_requires_unenforced(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="real")
    stage_file(
        repo,
        ".github/workflows/pub.yml",
        "on:\n  schedule:\n    - cron: '0 6 * * *'\n",
    )
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_SPIKE_END not in err
    assert WARN_UNENFORCED not in err


def test_non_workflow_file_does_not_fire(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    stage_file(repo, "README.md", "schedule: daily\nsecrets.TOKEN\n")
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert_approve(out)
    assert WARN_SPIKE_END not in err
    assert WARN_UNENFORCED in err


def test_deleted_schedule_line_does_not_fire(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    wf = ".github/workflows/pub.yml"
    stage_file(repo, wf, "on:\n  schedule:\n    - cron: '0 6 * * *'\n")
    subprocess.run(
        [GIT, "-C", repo, "commit", "-q", "-m", "seed", "--no-verify"],
        check=True,
        capture_output=True,
    )
    (repo / wf).write_text("on: workflow_dispatch\n", encoding="utf-8")
    subprocess.run([GIT, "-C", repo, "add", wf], check=True, capture_output=True)
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert_approve(out)
    assert WARN_SPIKE_END not in err


def test_no_staged_changes_does_not_fire_spike_end(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert_approve(out)
    assert WARN_SPIKE_END not in err


# ── Scope guards (AC-08) ────────────────────────────────────────────────


def test_this_repo_never_warns(tmp_path):
    rc, out, err, _ = run_hook(
        commit_payload(REPO_ROOT), log_dir=str(tmp_path / "logs")
    )
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err
    assert WARN_SPIKE_END not in err


def test_non_git_cwd_never_warns(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    rc, out, err, _ = run_hook(commit_payload(plain), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err


def test_worktree_git_file_never_warns(tmp_path):
    repo = tmp_path / "wt"
    repo.mkdir()
    (repo / ".git").write_text("gitdir: /somewhere/else\n", encoding="utf-8")
    rc, out, err, _ = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err


def test_non_commit_command_never_warns(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    payload = {
        "toolName": "run_in_terminal",
        "toolInput": {"command": "git status"},
        "cwd": str(repo),
    }
    rc, out, err, _ = run_hook(payload, log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err


def test_non_terminal_tool_never_warns(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    payload = {
        "toolName": "read_file",
        "toolInput": {"path": "x.py"},
        "cwd": str(repo),
    }
    rc, out, err, _ = run_hook(payload, log_dir=str(tmp_path / "logs"))
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err


# ── Suppression (AC-09) ─────────────────────────────────────────────────


def test_ramp_declined_suppresses_and_audits(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    (repo / ".ramp-declined").write_text("operator declined 2026-08-23\n", encoding="utf-8")
    stage_file(
        repo,
        ".github/workflows/pub.yml",
        "on:\n  schedule:\n    - cron: '0 6 * * *'\n",
    )
    rc, out, err, entries = run_hook(
        commit_payload(repo), log_dir=str(tmp_path / "logs")
    )
    assert rc == 0
    assert_approve(out)
    assert WARN_UNENFORCED not in err
    assert WARN_SPIKE_END not in err
    reasons = [e.get("reason") for e in entries]
    assert "ramp-declined" in reasons


def test_guard_never_creates_ramp_declined(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    assert not (repo / ".ramp-declined").exists()


# ── Audit hygiene (AC-10, AC-11) ────────────────────────────────────────


def test_audit_entries_contain_no_diff_content(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    stage_file(
        repo,
        ".github/workflows/pub.yml",
        "env:\n  X: ${{ secrets.SUPER_SECRET_NAME }}\n",
    )
    _, _, _, entries = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    blob = json.dumps(entries)
    assert "SUPER_SECRET_NAME" not in blob
    assert "cron" not in blob


def test_warning_entries_use_stable_reasons(tmp_path):
    repo = make_repo(tmp_path, "foreign", hooks="none")
    stage_file(
        repo,
        ".github/workflows/pub.yml",
        "on:\n  schedule:\n    - cron: '0 6 * * *'\n",
    )
    _, _, _, entries = run_hook(commit_payload(repo), log_dir=str(tmp_path / "logs"))
    ramp_reasons = {
        e["reason"] for e in entries if e.get("reason", "").startswith("ramp-")
    }
    assert ramp_reasons == {"ramp-unenforced", "ramp-spike-end"}


def test_no_mutating_git_in_detector_source():
    src = HOOK.read_text(encoding="utf-8")
    fr869 = src[src.find("FR-869") :] if "FR-869" in src else ""
    assert fr869, "FR-869 detector block missing from guard"
    for tok in ["git add", "git commit ", "git push", "git checkout", "git reset"]:
        assert tok not in fr869
