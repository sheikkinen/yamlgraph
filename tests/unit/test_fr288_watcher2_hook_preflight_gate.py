"""Acceptance tests for FR-288: watcher2 hook preflight gate.

These tests define the RED contract for hook-integrity validation in watcher2
preflight. They must fail on the unmodified codebase.
"""

from __future__ import annotations

import re
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
PREFLIGHT_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "preflight.sh"
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"
CHAPLAIN_README = REPO_ROOT / ".chaplain" / "README.md"


def _init_temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "checkout", "-b", "main", "-q"], cwd=repo, check=True)
    return repo


def _create_hook(path: Path, executable: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nexit 0\n")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _run_preflight(repo: Path) -> tuple[int, str, str]:
    script = f"""
log_info() {{ :; }}
log_warn() {{ :; }}
log_error() {{ :; }}
python3() {{ return 0; }}
ruff() {{ return 0; }}
source "{PREFLIGHT_SH}"
preflight
rc=$?
echo "__PREFLIGHT_RC=$rc"
"""
    proc = subprocess.run(
        ["bash", "-lc", script], cwd=repo, text=True, capture_output=True, check=True
    )
    match = re.search(r"__PREFLIGHT_RC=(\d+)", proc.stdout)
    assert match, f"Could not parse preflight return code from: {proc.stdout!r}"
    return int(match.group(1)), proc.stdout, proc.stderr


@pytest.mark.slow
@pytest.mark.req("REQ-YG-276")
class TestFR288PreflightHookGate:
    """AC-01..AC-05."""

    def test_ac01_validates_core_hookspath_before_preflight_complete(self):
        """AC-01: preflight validates core.hooksPath before completion."""
        content = PREFLIGHT_SH.read_text()
        lower = content.lower()

        assert (
            "core.hookspath" in lower
        ), "Expected preflight to read core.hooksPath from local git config"

        hook_check_pos = lower.find("core.hookspath")
        complete_pos = content.find('log_info "Preflight complete"')
        assert complete_pos != -1, "Expected existing preflight completion log"
        assert (
            hook_check_pos < complete_pos
        ), "Hook-path validation must run before preflight completion log"

    def test_ac02_fails_when_core_hookspath_is_explicitly_empty(self, tmp_path: Path):
        """AC-02: preflight fails when core.hooksPath is empty."""
        repo = _init_temp_repo(tmp_path)
        subprocess.run(
            ["git", "config", "--local", "core.hooksPath", ""], cwd=repo, check=True
        )
        _create_hook(repo / ".git" / "hooks" / "pre-commit", executable=True)
        _create_hook(repo / ".git" / "hooks" / "commit-msg", executable=True)

        rc, _, _ = _run_preflight(repo)
        assert rc != 0, "Expected preflight failure for empty core.hooksPath"

    def test_ac03_fails_when_core_hookspath_is_non_default(self, tmp_path: Path):
        """AC-03: preflight fails when hooksPath points outside .git/hooks."""
        repo = _init_temp_repo(tmp_path)
        subprocess.run(
            ["git", "config", "--local", "core.hooksPath", ".githooks"],
            cwd=repo,
            check=True,
        )
        _create_hook(repo / ".githooks" / "pre-commit", executable=True)
        _create_hook(repo / ".githooks" / "commit-msg", executable=True)

        rc, _, _ = _run_preflight(repo)
        assert rc != 0, "Expected preflight failure for non-default core.hooksPath"

    def test_ac04_requires_pre_commit_and_commit_msg_hooks_executable(
        self, tmp_path: Path
    ):
        """AC-04: preflight requires both hooks and execute bits."""
        content = PREFLIGHT_SH.read_text()
        lower = content.lower()
        assert "pre-commit" in lower, "Expected preflight hook check for pre-commit"
        assert "commit-msg" in lower, "Expected preflight hook check for commit-msg"
        assert (
            "-x " in content or " -x" in content
        ), "Expected executable-bit check (`-x`) for hook scripts"

        repo = _init_temp_repo(tmp_path)
        _create_hook(repo / ".git" / "hooks" / "pre-commit", executable=True)
        _create_hook(repo / ".git" / "hooks" / "commit-msg", executable=False)

        rc, _, _ = _run_preflight(repo)
        assert rc != 0, "Expected preflight failure for non-executable commit-msg hook"

    def test_ac05_logs_actionable_hook_remediation_commands(self):
        """AC-05: preflight logs explicit remediation commands."""
        content = PREFLIGHT_SH.read_text()
        assert (
            "git config --local --unset core.hooksPath" in content
            or "git config --local --unset core.hookspath" in content.lower()
        ), "Expected remediation command to unset core.hooksPath"
        assert (
            "pre-commit install" in content
        ), "Expected remediation command pre-commit install"
        assert (
            "pre-commit install --hook-type commit-msg" in content
        ), "Expected remediation command for commit-msg hook install"


@pytest.mark.slow
@pytest.mark.req("REQ-YG-276")
class TestFR288Watcher2PreflightBoundary:
    """AC-06, AC-07, AC-08."""

    def test_ac06_hook_preflight_failure_blocks_plan_phase(self):
        """AC-06: hook validation failures stop cycle before plan step."""
        watcher = WATCHER2_SH.read_text()
        preflight_gate_pos = watcher.find("if ! preflight; then")
        plan_step_pos = watcher.find("Step 1/4: Plan")

        assert preflight_gate_pos != -1, "Expected watcher2 preflight guard"
        assert plan_step_pos != -1, "Expected watcher2 plan step"
        assert (
            preflight_gate_pos < plan_step_pos
        ), "Preflight guard must run before plan step"
        assert (
            "core.hooksPath" in PREFLIGHT_SH.read_text()
            or "core.hookspath" in PREFLIGHT_SH.read_text().lower()
        ), "Expected preflight guard to include hook-integrity validation"

    def test_ac07_healthy_hooks_keep_preflight_pass_through_behavior(
        self, tmp_path: Path
    ):
        """AC-07: healthy hooks still allow normal preflight success."""
        repo = _init_temp_repo(tmp_path)
        _create_hook(repo / ".git" / "hooks" / "pre-commit", executable=True)
        _create_hook(repo / ".git" / "hooks" / "commit-msg", executable=True)

        rc, _, _ = _run_preflight(repo)
        assert rc == 0, "Expected preflight to succeed when hooks are healthy"
        assert (
            "core.hooksPath" in PREFLIGHT_SH.read_text()
            or "core.hookspath" in PREFLIGHT_SH.read_text().lower()
        ), "Expected additive hook validation logic in preflight"

    @pytest.mark.slow
    def test_ac08_scenario_coverage_matrix_for_hook_gate(self, tmp_path: Path):
        """AC-08: acceptance suite covers misconfigured and healthy hook scenarios."""
        repo_empty = _init_temp_repo(tmp_path / "empty")
        subprocess.run(
            ["git", "config", "--local", "core.hooksPath", ""],
            cwd=repo_empty,
            check=True,
        )
        _create_hook(repo_empty / ".git" / "hooks" / "pre-commit", executable=True)
        _create_hook(repo_empty / ".git" / "hooks" / "commit-msg", executable=True)
        rc_empty, _, _ = _run_preflight(repo_empty)

        repo_non_default = _init_temp_repo(tmp_path / "non-default")
        subprocess.run(
            ["git", "config", "--local", "core.hooksPath", ".githooks"],
            cwd=repo_non_default,
            check=True,
        )
        _create_hook(repo_non_default / ".githooks" / "pre-commit", executable=True)
        _create_hook(repo_non_default / ".githooks" / "commit-msg", executable=True)
        rc_non_default, _, _ = _run_preflight(repo_non_default)

        repo_missing_hook = _init_temp_repo(tmp_path / "missing-hook")
        _create_hook(
            repo_missing_hook / ".git" / "hooks" / "commit-msg", executable=True
        )
        rc_missing_hook, _, _ = _run_preflight(repo_missing_hook)

        repo_healthy = _init_temp_repo(tmp_path / "healthy")
        _create_hook(repo_healthy / ".git" / "hooks" / "pre-commit", executable=True)
        _create_hook(repo_healthy / ".git" / "hooks" / "commit-msg", executable=True)
        rc_healthy, _, _ = _run_preflight(repo_healthy)

        assert rc_empty != 0, "Expected empty hooksPath scenario to fail preflight"
        assert (
            rc_non_default != 0
        ), "Expected non-default hooksPath scenario to fail preflight"
        assert rc_missing_hook != 0, "Expected missing pre-commit hook scenario to fail"
        assert rc_healthy == 0, "Expected healthy hooks scenario to pass"


@pytest.mark.req("REQ-YG-276")
class TestFR288DocumentationContract:
    """AC-09."""

    def test_ac09_readme_documents_enforced_hook_preflight_contract(self):
        """AC-09: README documents hook-path + executable-hook preflight contract."""
        content = CHAPLAIN_README.read_text()
        lower = content.lower()

        assert (
            "core.hookspath" in lower
        ), "Expected README to document core.hooksPath validation"
        assert (
            "pre-commit" in lower and "executable" in lower
        ), "Expected README to document pre-commit executable requirement"
        assert (
            "commit-msg" in lower and "executable" in lower
        ), "Expected README to document commit-msg executable requirement"
