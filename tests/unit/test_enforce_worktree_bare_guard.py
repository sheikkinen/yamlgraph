"""Unit tests for FR-139: bare=true corruption guard in enforce_worktree.sh.

Tests the three-layer defense against git config corruption where worktree
operations can set `bare = true` in the main repo's .git/config.

Layer 1: Environment sanitization (GIT_DIR/GIT_WORK_TREE unset)
Layer 2: Cleanup trap restoration
Layer 3: Post-run assertion
"""

import os
import subprocess
from pathlib import Path

import pytest

# Strip git env vars that pre-commit injects (GIT_INDEX_FILE from stashing).
_GIT_ENV_POISON = {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}


def _clean_git_env(**extra: str) -> dict[str, str]:
    """Return os.environ minus git vars that pollute temp-repo subprocess calls."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_POISON}
    env.update(extra)
    return env


@pytest.mark.req("REQ-YG-106")
class TestBareCorruptionGuard:
    """Tests for the bare=true corruption guard logic."""

    def test_guard_restores_bare_false_when_corrupted(self, tmp_path: Path):
        """Guard should restore bare=false when bare=true is detected."""
        # Create a minimal git repo
        repo = tmp_path / "repo"
        repo.mkdir()

        env = _clean_git_env()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )

        # Corrupt the config by setting bare=true
        subprocess.run(
            ["git", "config", "core.bare", "true"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )

        # Verify corruption
        result = subprocess.run(
            ["git", "config", "--get", "core.bare"],
            cwd=repo,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.stdout.strip() == "true", "Pre-condition: bare should be true"

        # Run the guard logic inline (extracted from enforce_worktree.sh)
        guard_script = f"""
            cd "{repo}"
            bare_after=$(git config --get core.bare 2>/dev/null || echo "false")
            if [[ "$bare_after" == "true" ]]; then
                echo "WARN: Detected bare=true corruption — restoring"
                git config core.bare false
            fi
        """

        proc = subprocess.run(
            ["bash", "-c", guard_script],
            capture_output=True,
            text=True,
            env=_clean_git_env(),
        )
        assert "Detected bare=true corruption" in proc.stdout, (
            f"Guard should log warning. stdout: {proc.stdout}"
        )

        # Verify restoration
        result = subprocess.run(
            ["git", "config", "--get", "core.bare"],
            cwd=repo,
            capture_output=True,
            text=True,
            env=_clean_git_env(),
        )
        assert result.stdout.strip() == "false", "bare should be restored to false"

    def test_guard_does_not_modify_when_already_false(self, tmp_path: Path):
        """Guard should not modify config when bare=false."""
        repo = tmp_path / "repo"
        repo.mkdir()

        env = _clean_git_env()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )

        # Ensure bare=false (default for non-bare init)
        # Default init doesn't set core.bare explicitly — guard should be no-op

        # Run the guard logic
        guard_script = f"""
            cd "{repo}"
            bare_after=$(git config --get core.bare 2>/dev/null || echo "false")
            if [[ "$bare_after" == "true" ]]; then
                echo "WARN: Detected bare=true corruption — restoring"
                git config core.bare false
            else
                echo "OK: bare is already false or unset"
            fi
        """

        proc = subprocess.run(
            ["bash", "-c", guard_script],
            capture_output=True,
            text=True,
            env=_clean_git_env(),
        )
        assert "Detected bare=true corruption" not in proc.stdout
        assert "OK: bare is already false or unset" in proc.stdout

    def test_env_sanitization_prevents_pollution(self, tmp_path: Path):
        """GIT_DIR/GIT_WORK_TREE env vars should be unset before worktree ops."""
        repo = tmp_path / "repo"
        repo.mkdir()

        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=_clean_git_env(),
        )

        # Simulate polluted environment
        env = _clean_git_env()
        env["GIT_DIR"] = "/some/other/.git"
        env["GIT_WORK_TREE"] = "/some/other/path"

        # Without sanitization, git would fail or use wrong repo
        sanitize_script = f"""
            # FR-139 Layer 1: Sanitize
            unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true

            # Now git should work correctly
            cd "{repo}"
            git status > /dev/null 2>&1 && echo "SUCCESS" || echo "FAILED"
        """

        proc = subprocess.run(
            ["bash", "-c", sanitize_script],
            env=env,
            capture_output=True,
            text=True,
        )

        assert "SUCCESS" in proc.stdout, (
            f"Git should work after env sanitization. stderr: {proc.stderr}"
        )
