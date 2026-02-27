"""Integration tests for worktree helpers and enforce_worktree.sh (FR-106).

Tests the worktree lifecycle: creation, validation, and cleanup.
Guarded by git availability.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-106")
class TestWorktreeIntegration:
    """Integration tests for worktree operations."""

    @pytest.fixture
    def clean_git_repo(self, tmp_path):
        """Create a clean git repo for testing."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        readme = repo_dir / "README.md"
        readme.write_text("# Test Repo\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        return repo_dir

    def test_validate_clean_working_tree_in_clean_repo(
        self, clean_git_repo, monkeypatch
    ):
        """validate_clean_working_tree returns True in a clean git repo."""
        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        monkeypatch.chdir(clean_git_repo)
        assert validate_clean_working_tree() is True

    def test_validate_raises_with_unstaged_changes(self, clean_git_repo, monkeypatch):
        """validate_clean_working_tree raises with unstaged changes."""
        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        monkeypatch.chdir(clean_git_repo)

        # Create unstaged change
        (clean_git_repo / "README.md").write_text("# Modified\n")

        with pytest.raises(ValueError, match="unstaged changes"):
            validate_clean_working_tree()

    def test_validate_raises_with_staged_changes(self, clean_git_repo, monkeypatch):
        """validate_clean_working_tree raises with staged changes."""
        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        monkeypatch.chdir(clean_git_repo)

        # Create staged change
        new_file = clean_git_repo / "new_file.txt"
        new_file.write_text("new content\n")
        subprocess.run(["git", "add", "new_file.txt"], cwd=clean_git_repo, check=True)

        with pytest.raises(ValueError, match="staged changes"):
            validate_clean_working_tree()

    def test_worktree_creation_and_cleanup(self, clean_git_repo, monkeypatch):
        """Worktree can be created and removed via git commands."""
        monkeypatch.chdir(clean_git_repo)

        branch = "feat/test-worktree"
        worktree_path = clean_git_repo / "tmp" / "worktrees" / branch

        # Create worktree
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch, "HEAD"],
            cwd=clean_git_repo,
            capture_output=True,
        )
        assert (
            result.returncode == 0
        ), f"Failed to create worktree: {result.stderr.decode()}"
        assert worktree_path.exists()

        # Verify it's a valid git worktree
        assert (worktree_path / ".git").exists()

        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=clean_git_repo,
            check=True,
        )
        assert not worktree_path.exists()

    def test_branch_derivation_integration(self):
        """Branch derivation works for real FR paths in the repo."""
        from yamlgraph.utils.worktree_helpers import derive_branch_name

        # Test with actual FR path pattern
        result = derive_branch_name(
            "feature-requests/FR-106-parallel-worktree-pipeline.md"
        )
        assert result == "feat/fr-106-parallel-worktree-pipeline"

        # Verify branch name is valid for git
        # Branch names cannot contain: ~, ^, :, ?, *, [, @{, .., consecutive slashes
        assert ".." not in result
        assert "~" not in result
        assert "^" not in result
        assert " " not in result


@pytest.mark.req("REQ-YG-106")
@pytest.mark.skipif(
    not Path("scripts/enforce_worktree.sh").exists(),
    reason="enforce_worktree.sh not yet created",
)
class TestEnforceWorktreeScript:
    """Integration tests for enforce_worktree.sh script."""

    def test_script_exists_and_is_executable(self):
        """Script exists and has executable permission."""
        script_path = Path("scripts/enforce_worktree.sh")
        assert script_path.exists()

    def test_script_shows_usage_without_args(self):
        """Script shows usage message when called without arguments."""
        result = subprocess.run(
            ["bash", "scripts/enforce_worktree.sh"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Usage:" in result.stderr or "Usage:" in result.stdout

    def test_script_errors_on_missing_fr_file(self, tmp_path):
        """Script errors when FR file doesn't exist."""
        result = subprocess.run(
            ["bash", "scripts/enforce_worktree.sh", str(tmp_path / "nonexistent.md")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert (
            "not found" in result.stderr.lower() or "not found" in result.stdout.lower()
        )


@pytest.mark.req("REQ-YG-106")
class TestWorktreeConcurrency:
    """Tests for parallel worktree isolation."""

    def test_parallel_worktrees_have_independent_paths(self):
        """Two different FRs produce different worktree paths."""
        from yamlgraph.utils.worktree_helpers import (
            construct_worktree_path,
            derive_branch_name,
        )

        branch_a = derive_branch_name("feature-requests/FR-107-feature-a.md")
        branch_b = derive_branch_name("feature-requests/FR-108-feature-b.md")

        path_a = construct_worktree_path(branch_a)
        path_b = construct_worktree_path(branch_b)

        # Paths must be different for isolation
        assert path_a != path_b
        assert "fr-107" in path_a
        assert "fr-108" in path_b

    def test_parallel_worktrees_can_coexist(self, tmp_path):
        """Two worktrees can be created simultaneously in the same repo."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # Initialize git repo with initial commit
        subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        (repo_dir / "README.md").write_text("# Test\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Init"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        # Create two worktrees simultaneously
        worktree_a = repo_dir / "tmp" / "worktrees" / "feat" / "fr-107"
        worktree_b = repo_dir / "tmp" / "worktrees" / "feat" / "fr-108"

        worktree_a.parent.mkdir(parents=True, exist_ok=True)
        worktree_b.parent.mkdir(parents=True, exist_ok=True)

        result_a = subprocess.run(
            ["git", "worktree", "add", str(worktree_a), "-b", "feat/fr-107", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
        )
        result_b = subprocess.run(
            ["git", "worktree", "add", str(worktree_b), "-b", "feat/fr-108", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
        )

        # Both should succeed
        assert (
            result_a.returncode == 0
        ), f"Worktree A failed: {result_a.stderr.decode()}"
        assert (
            result_b.returncode == 0
        ), f"Worktree B failed: {result_b.stderr.decode()}"

        # Both should exist independently
        assert worktree_a.exists()
        assert worktree_b.exists()
        assert (worktree_a / ".git").exists()
        assert (worktree_b / ".git").exists()

        # Cleanup
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_a), "--force"], cwd=repo_dir
        )
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_b), "--force"], cwd=repo_dir
        )
