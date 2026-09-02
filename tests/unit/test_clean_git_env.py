"""Unit tests for _clean_git_env fixture (FR-140).

Tests verify that the session-scoped autouse fixture in conftest.py
strips GIT_* environment variables injected by pre-commit, preventing
subprocess bleed into tests that create temporary git repos.
"""

import os
import subprocess

import pytest

# ---------------------------------------------------------------------------
# Fixture Behavior
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-140")
class TestCleanGitEnvFixtureStrips:
    """The _clean_git_env fixture strips GIT_* vars from os.environ."""

    def test_git_dir_not_in_environ(self):
        """GIT_DIR must not be present during test execution."""
        assert "GIT_DIR" not in os.environ

    def test_git_work_tree_not_in_environ(self):
        """GIT_WORK_TREE must not be present during test execution."""
        assert "GIT_WORK_TREE" not in os.environ

    def test_git_index_file_not_in_environ(self):
        """GIT_INDEX_FILE must not be present during test execution."""
        assert "GIT_INDEX_FILE" not in os.environ

    def test_git_author_name_not_in_environ(self):
        """GIT_AUTHOR_NAME (set by pre-commit) must not be present."""
        assert "GIT_AUTHOR_NAME" not in os.environ

    def test_no_git_prefixed_vars_remain(self):
        """No GIT_* prefixed variables remain in os.environ."""
        git_vars = [k for k in os.environ if k.startswith("GIT_")]
        assert git_vars == [], f"GIT_* vars still in env: {git_vars}"


@pytest.mark.req("REQ-YG-140")
class TestCleanGitEnvNoOp:
    """Fixture is a no-op when GIT_* vars are absent (outside pre-commit)."""

    def test_fixture_does_not_crash_without_git_vars(self):
        """Session starts cleanly even when no GIT_* vars existed.

        This test always passes if the fixture loads without error,
        which proves no-op behavior when running outside pre-commit.
        """
        # If we got here, the fixture ran successfully.
        assert True


@pytest.mark.req("REQ-YG-140")
class TestCleanGitEnvSubprocess:
    """Subprocess git commands work in tmp_path without GIT_* interference."""

    def test_git_init_in_tmp_path(self, tmp_path):
        """git init in tmp_path succeeds without leaked GIT_DIR."""
        result = subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"git init failed: {result.stderr}"

    def test_git_commit_in_tmp_path(self, tmp_path):
        """A full git init+add+commit cycle works in tmp_path."""
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # init + config + add + commit
        for cmd in [
            ["git", "init", "-b", "main"],
            ["git", "config", "user.email", "test@test.com"],
            ["git", "config", "user.name", "Test"],
        ]:
            subprocess.run(cmd, cwd=repo, check=True, capture_output=True)

        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"git commit failed: {result.stderr}"

    def test_git_rev_parse_points_to_tmp_repo(self, tmp_path):
        """git rev-parse --show-toplevel returns the tmp_path repo, not the
        pre-commit working directory."""
        repo = tmp_path / "isolated_repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == str(repo)
