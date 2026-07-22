"""FR-372 acceptance tests for gitignore boundary pre-commit guard."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

PRECOMMIT_PATH = ".pre-commit-config.yaml"
SCRIPT_PATH = "scripts/check_gitignore_boundary.sh"
DIARY_REF = "docs/diary/2026-05-12-private-repo-dataloss-recovery.md"


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


def _run_gitignore_boundary_check(
    staged_files: dict[str, str],
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run check_gitignore_boundary.sh against staged files in a temp git repo."""
    script_abs = str(Path(SCRIPT_PATH).resolve())

    with tempfile.TemporaryDirectory() as tmpdir:
        _setup_git_repo(tmpdir)
        tmppath = Path(tmpdir)

        # Create an initial commit so HEAD exists.
        readme = tmppath / "README.md"
        readme.write_text("init\n")
        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "init"],
            cwd=tmpdir,
            check=True,
        )

        for relpath, content in staged_files.items():
            fpath = tmppath / relpath
            fpath.parent.mkdir(parents=True, exist_ok=True)
            fpath.write_text(content)

        subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)

        run_env = os.environ.copy()
        # Strip bypass vars unless explicitly provided — prevents env leakage
        # when pre-commit runs pytest with bypass vars set for the commit itself.
        for key in ("YAMLGRAPH_ALLOW_GITIGNORE_EDIT", "YAMLGRAPH_GITIGNORE_REASON"):
            if (env is None or key not in env) and key in run_env:
                del run_env[key]
        if env:
            run_env.update(env)

        return subprocess.run(
            ["bash", script_abs],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=run_env,
        )


@pytest.mark.req("REQ-YG-002")
class TestFR372GitignoreBoundaryGuard:
    """Acceptance tests for FR-372."""

    def test_ac01_root_gitignore_staged_fails(self) -> None:
        """AC-01: staged root .gitignore must fail by default."""
        result = _run_gitignore_boundary_check({".gitignore": "tmp/\n"})
        assert result.returncode == 1

    def test_ac02_nested_gitignore_staged_fails(self) -> None:
        """AC-02: staged nested .gitignore must fail by default."""
        result = _run_gitignore_boundary_check({".chaplain/.gitignore": "*.tmp\n"})
        assert result.returncode == 1

    def test_ac03_non_gitignore_commit_passes(self) -> None:
        """AC-03: non-gitignore staged changes must pass."""
        result = _run_gitignore_boundary_check({"src/example.py": "print('ok')\n"})
        assert result.returncode == 0

    def test_ac04_failure_output_mentions_boundary_and_diary(self) -> None:
        """AC-04: failure output must explain boundary risk and cite diary."""
        result = _run_gitignore_boundary_check({".gitignore": "tmp/\n"})
        combined = f"{result.stdout}\n{result.stderr}"
        assert "boundary" in combined.lower()
        assert DIARY_REF in combined

    def test_ac05_hook_registered_in_precommit_config(self) -> None:
        """AC-05: hook must be registered with expected contract."""
        with open(PRECOMMIT_PATH) as f:
            config = yaml.safe_load(f)

        for repo in config.get("repos", []):
            for hook in repo.get("hooks", []):
                if hook.get("id") == "gitignore-boundary-guard":
                    assert hook.get("entry") == "scripts/check_gitignore_boundary.sh"
                    assert hook.get("language") == "script"
                    assert hook.get("pass_filenames") is False
                    assert "pre-commit" in hook.get("stages", [])
                    return
        pytest.fail("Missing gitignore-boundary-guard hook in .pre-commit-config.yaml")

    def test_ac06_explicit_bypass_with_reason_passes(self) -> None:
        """AC-06: explicit bypass with valid reason should pass."""
        result = _run_gitignore_boundary_check(
            {".gitignore": "tmp/\n"},
            env={
                "YAMLGRAPH_ALLOW_GITIGNORE_EDIT": "1",
                "YAMLGRAPH_GITIGNORE_REASON": "FR-372 intentional boundary update",
            },
        )
        assert result.returncode == 0
        combined = f"{result.stdout}\n{result.stderr}"
        assert "bypass" in combined.lower()

    def test_ac07_bypass_without_reason_fails(self) -> None:
        """AC-07: bypass flag without reason must fail closed."""
        result = _run_gitignore_boundary_check(
            {".gitignore": "tmp/\n"},
            env={"YAMLGRAPH_ALLOW_GITIGNORE_EDIT": "1"},
        )
        assert result.returncode == 1
        combined = f"{result.stdout}\n{result.stderr}"
        assert "YAMLGRAPH_GITIGNORE_REASON" in combined
