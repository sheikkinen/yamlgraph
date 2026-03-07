"""Integration tests for enforce detection logic (FR-114).

End-to-end tests using real git repos to verify FR detection
via git diff between SHAs.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-114")
class TestEnforceDetectionIntegration:
    """Integration tests for enforce detection with real git repos."""

    @pytest.fixture
    def git_repo_with_frs(self, tmp_path):
        """Create a git repo with an initial commit, return (repo_dir, initial_sha)."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

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

        # Create initial commit with feature-requests dir
        fr_dir = repo_dir / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "TEMPLATE.md").write_text("# Template\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        initial_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )

        return repo_dir, initial_sha

    def test_detect_new_fr_after_commit(self, git_repo_with_frs, monkeypatch):
        """Detects a newly committed FR file between two SHAs."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        repo_dir, initial_sha = git_repo_with_frs
        monkeypatch.chdir(repo_dir)

        # Add a new FR and commit
        fr_file = repo_dir / "feature-requests" / "FR-200-test-feature.md"
        fr_file.write_text("# FR-200: Test Feature\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add FR-200"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        current_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )

        result = detect_new_feature_requests(initial_sha, current_sha)
        assert len(result) == 1
        assert "FR-200-test-feature.md" in result[0]

    def test_ignores_template_in_real_repo(self, git_repo_with_frs, monkeypatch):
        """TEMPLATE.md modifications are not detected as new FRs."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        repo_dir, initial_sha = git_repo_with_frs
        monkeypatch.chdir(repo_dir)

        # Modify TEMPLATE.md
        (repo_dir / "feature-requests" / "TEMPLATE.md").write_text("# Updated\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Update template"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        current_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )

        result = detect_new_feature_requests(initial_sha, current_sha)
        assert result == []

    def test_multiple_frs_in_single_push(self, git_repo_with_frs, monkeypatch):
        """Multiple FRs committed together are all detected."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        repo_dir, initial_sha = git_repo_with_frs
        monkeypatch.chdir(repo_dir)

        # Add multiple FRs in one commit
        (repo_dir / "feature-requests" / "FR-201-feature-a.md").write_text("# A\n")
        (repo_dir / "feature-requests" / "FR-202-feature-b.md").write_text("# B\n")
        subprocess.run(
            ["git", "add", "."], cwd=repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add two FRs"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )

        current_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            .stdout.strip()
        )

        result = detect_new_feature_requests(initial_sha, current_sha)
        assert len(result) == 2

    def test_sha_state_file_roundtrip(self, tmp_path):
        """SHA can be written and read back from state file."""
        from yamlgraph.utils.worktree_helpers import (
            read_enforce_sha,
            write_enforce_sha,
        )

        state_file = str(tmp_path / ".last-enforce-sha")
        test_sha = "abc123def456"

        write_enforce_sha(state_file, test_sha)
        result = read_enforce_sha(state_file)
        assert result == test_sha

    def test_idempotent_no_reprocess(self, git_repo_with_frs, monkeypatch):
        """Re-running with same SHA range returns empty (no re-enforcement)."""
        from yamlgraph.utils.worktree_helpers import detect_new_feature_requests

        repo_dir, initial_sha = git_repo_with_frs
        monkeypatch.chdir(repo_dir)

        result = detect_new_feature_requests(initial_sha, initial_sha)
        assert result == []
