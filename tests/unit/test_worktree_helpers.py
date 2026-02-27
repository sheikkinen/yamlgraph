"""Unit tests for worktree helpers (FR-106).

Tests branch name derivation and worktree path construction for the
parallel development pipeline.
"""

import pytest


@pytest.mark.req("REQ-YG-106")
class TestWorktreeBranchDerivation:
    """Tests for derive_branch_name()."""

    def test_derive_branch_from_uppercase_fr(self):
        """FR path with uppercase converts to lowercase branch name."""
        from yamlgraph.utils.worktree_helpers import derive_branch_name

        result = derive_branch_name(
            "feature-requests/FR-106-parallel-worktree-pipeline.md"
        )
        assert result == "feat/fr-106-parallel-worktree-pipeline"

    def test_derive_branch_from_path_with_directory(self):
        """Directory prefix is stripped, only filename used."""
        from yamlgraph.utils.worktree_helpers import derive_branch_name

        result = derive_branch_name("some/nested/path/FR-999-test.md")
        assert result == "feat/fr-999-test"

    def test_derive_branch_strips_md_extension(self):
        """The .md extension is removed from branch name."""
        from yamlgraph.utils.worktree_helpers import derive_branch_name

        result = derive_branch_name("FR-001-simple.md")
        assert result == "feat/fr-001-simple"

    def test_derive_branch_handles_no_extension(self):
        """Paths without .md are handled gracefully."""
        from yamlgraph.utils.worktree_helpers import derive_branch_name

        result = derive_branch_name("FR-001-simple")
        assert result == "feat/fr-001-simple"


@pytest.mark.req("REQ-YG-106")
class TestWorktreePathConstruction:
    """Tests for construct_worktree_path()."""

    def test_worktree_path_under_tmp_worktrees(self):
        """Worktree path lives under tmp/worktrees/."""
        from yamlgraph.utils.worktree_helpers import construct_worktree_path

        result = construct_worktree_path("feat/fr-106-test")
        assert result == "tmp/worktrees/feat/fr-106-test"

    def test_worktree_path_preserves_branch_structure(self):
        """Branch name is preserved in path."""
        from yamlgraph.utils.worktree_helpers import construct_worktree_path

        result = construct_worktree_path("feat/my-feature-branch")
        assert result == "tmp/worktrees/feat/my-feature-branch"


@pytest.mark.req("REQ-YG-106")
class TestWorktreeValidation:
    """Tests for validate_clean_working_tree()."""

    def test_validate_clean_returns_true_for_clean_tree(self, tmp_path, monkeypatch):
        """Clean working tree returns True."""
        import subprocess

        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        # Mock subprocess to simulate clean tree (no files in output)
        def mock_run(cmd, **kwargs):
            result = subprocess.CompletedProcess(
                cmd, returncode=0, stdout="", stderr=""
            )
            return result

        monkeypatch.setattr(subprocess, "run", mock_run)
        assert validate_clean_working_tree() is True

    def test_validate_raises_for_unstaged_changes(self, monkeypatch):
        """Unstaged changes raise ValueError."""
        import subprocess

        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        call_count = [0]

        def mock_run(cmd, **kwargs):
            call_count[0] += 1
            # First call: git diff --name-only (unstaged) - has changes
            if call_count[0] == 1:
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="src/foo.py\n", stderr=""
                )
            # Second call: git diff --cached --name-only (staged) - clean
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(ValueError, match="unstaged changes"):
            validate_clean_working_tree()

    def test_validate_raises_for_staged_changes(self, monkeypatch):
        """Staged changes raise ValueError."""
        import subprocess

        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        call_count = [0]

        def mock_run(cmd, **kwargs):
            call_count[0] += 1
            # First call: git diff --name-only (unstaged) - clean
            if call_count[0] == 1:
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
            # Second call: git diff --cached --name-only (staged) - has changes
            return subprocess.CompletedProcess(
                cmd, returncode=0, stdout="src/bar.py\n", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        with pytest.raises(ValueError, match="staged changes"):
            validate_clean_working_tree()

    def test_validate_excludes_diary_from_check(self, monkeypatch):
        """Excluded paths are ignored in validation."""
        import subprocess

        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        def mock_run(cmd, **kwargs):
            # Return diary.md as modified - should be excluded
            return subprocess.CompletedProcess(
                cmd, returncode=0, stdout="docs/diary.md\n", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Should pass because diary.md is excluded
        assert validate_clean_working_tree(exclude_paths=["docs/diary.md"]) is True

    def test_validate_raises_when_non_excluded_files_dirty(self, monkeypatch):
        """Non-excluded files in dirty state still cause failure."""
        import subprocess

        from yamlgraph.utils.worktree_helpers import validate_clean_working_tree

        def mock_run(cmd, **kwargs):
            # Return both excluded and non-excluded files
            return subprocess.CompletedProcess(
                cmd, returncode=0, stdout="docs/diary.md\nsrc/foo.py\n", stderr=""
            )

        monkeypatch.setattr(subprocess, "run", mock_run)

        # Should fail because src/foo.py is not excluded
        with pytest.raises(ValueError, match="src/foo.py"):
            validate_clean_working_tree(exclude_paths=["docs/diary.md"])
