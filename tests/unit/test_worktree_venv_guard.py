"""Unit tests for FR-174: worktree .venv corruption guard.

Tests three guards:
1. validate_venv_health — fail loud when .venv is missing/broken
2. validate_venv_symlink — fail loud when symlink is broken
3. clean_stale_pth_entries — remove dangling .pth/.egg-link files after worktree cleanup
"""

from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-156")
class TestValidateVenvHealth:
    """Guard 1: .venv must exist with a working bin/python."""

    def test_raises_when_venv_dir_missing(self, tmp_path: Path) -> None:
        """FileNotFoundError when .venv directory does not exist."""
        from yamlgraph.utils.worktree_helpers import validate_venv_health

        missing = tmp_path / ".venv"
        with pytest.raises(FileNotFoundError, match="does not exist"):
            validate_venv_health(missing)

    def test_raises_when_bin_python_missing(self, tmp_path: Path) -> None:
        """FileNotFoundError when .venv/bin/python is absent."""
        from yamlgraph.utils.worktree_helpers import validate_venv_health

        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        # No python binary inside bin/

        with pytest.raises(FileNotFoundError, match="bin/python"):
            validate_venv_health(venv)

    def test_raises_when_bin_python_not_executable(self, tmp_path: Path) -> None:
        """FileNotFoundError when .venv/bin/python exists but is not executable."""
        from yamlgraph.utils.worktree_helpers import validate_venv_health

        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        python_bin = venv / "bin" / "python"
        python_bin.write_text("not-executable", encoding="utf-8")
        python_bin.chmod(0o444)  # read-only, not executable

        with pytest.raises(FileNotFoundError, match="not executable"):
            validate_venv_health(venv)

    def test_returns_none_for_healthy_venv(self, tmp_path: Path) -> None:
        """No error when .venv is a valid directory with executable bin/python."""
        from yamlgraph.utils.worktree_helpers import validate_venv_health

        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        python_bin = venv / "bin" / "python"
        python_bin.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        python_bin.chmod(0o755)

        result = validate_venv_health(venv)
        assert result is None


@pytest.mark.req("REQ-YG-156")
class TestValidateVenvSymlink:
    """Guard 2: .venv symlink in worktree must resolve correctly."""

    def test_raises_when_not_a_symlink(self, tmp_path: Path) -> None:
        """OSError when path is a regular directory, not a symlink."""
        from yamlgraph.utils.worktree_helpers import validate_venv_symlink

        regular_dir = tmp_path / ".venv"
        regular_dir.mkdir()
        target = tmp_path / "target"
        target.mkdir()

        with pytest.raises(OSError, match="not a symlink"):
            validate_venv_symlink(regular_dir, target)

    def test_raises_when_symlink_target_missing(self, tmp_path: Path) -> None:
        """OSError when symlink points to a non-existent target."""
        from yamlgraph.utils.worktree_helpers import validate_venv_symlink

        target = tmp_path / "missing-venv"
        link = tmp_path / "worktree" / ".venv"
        (tmp_path / "worktree").mkdir()
        link.symlink_to(target)

        with pytest.raises(OSError, match="does not resolve"):
            validate_venv_symlink(link, target)

    def test_returns_none_for_valid_symlink(self, tmp_path: Path) -> None:
        """No error when symlink resolves to a valid .venv with bin/python."""
        from yamlgraph.utils.worktree_helpers import validate_venv_symlink

        # Create a valid .venv target
        target = tmp_path / "main-venv"
        target.mkdir()
        (target / "bin").mkdir()
        python_bin = target / "bin" / "python"
        python_bin.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        python_bin.chmod(0o755)

        # Create symlink
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        link = worktree / ".venv"
        link.symlink_to(target)

        result = validate_venv_symlink(link, target)
        assert result is None


@pytest.mark.req("REQ-YG-156")
class TestCleanStalePthEntries:
    """Guard 3: remove .pth/.egg-link files referencing deleted worktree."""

    def _make_venv_with_site_packages(self, tmp_path: Path) -> Path:
        """Create a minimal .venv structure with site-packages directory."""
        venv = tmp_path / ".venv"
        site_packages = venv / "lib" / "python3.11" / "site-packages"
        site_packages.mkdir(parents=True)
        return venv

    def test_removes_pth_file_referencing_worktree(self, tmp_path: Path) -> None:
        """Stale .pth file containing worktree path should be removed."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv = self._make_venv_with_site_packages(tmp_path)
        site_packages = venv / "lib" / "python3.11" / "site-packages"
        worktree_dir = "/tmp/worktrees/feat/fr-174-test"

        # Create a .pth file with worktree reference
        pth = site_packages / "yamlgraph.pth"
        pth.write_text(f"{worktree_dir}\n", encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)
        assert len(removed) == 1
        assert removed[0] == pth
        assert not pth.exists(), ".pth file should have been deleted"

    def test_removes_egg_link_referencing_worktree(self, tmp_path: Path) -> None:
        """Stale .egg-link file containing worktree path should be removed."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv = self._make_venv_with_site_packages(tmp_path)
        site_packages = venv / "lib" / "python3.11" / "site-packages"
        worktree_dir = "/tmp/worktrees/feat/fr-174-test"

        # Create .egg-link with worktree reference
        egg_link = site_packages / "yamlgraph.egg-link"
        egg_link.write_text(f"{worktree_dir}\n.\n", encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)
        assert len(removed) == 1
        assert removed[0] == egg_link
        assert not egg_link.exists(), ".egg-link file should have been deleted"

    def test_returns_empty_when_no_stale_entries(self, tmp_path: Path) -> None:
        """No files removed when no .pth/.egg-link reference worktree."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv = self._make_venv_with_site_packages(tmp_path)
        site_packages = venv / "lib" / "python3.11" / "site-packages"
        worktree_dir = "/tmp/worktrees/feat/fr-174-test"

        # Create a .pth that does NOT reference the worktree
        pth = site_packages / "other-package.pth"
        pth.write_text("/some/other/path\n", encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)
        assert removed == []
        assert pth.exists(), "Unrelated .pth should be preserved"

    def test_preserves_pth_with_mixed_content(self, tmp_path: Path) -> None:
        """Only removes files where worktree path appears; preserves others."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv = self._make_venv_with_site_packages(tmp_path)
        site_packages = venv / "lib" / "python3.11" / "site-packages"
        worktree_dir = "/tmp/worktrees/feat/fr-174-test"

        # Stale file
        stale = site_packages / "stale.pth"
        stale.write_text(f"{worktree_dir}/src\n", encoding="utf-8")

        # Clean file
        clean = site_packages / "clean.pth"
        clean.write_text("/usr/lib/python3/dist-packages\n", encoding="utf-8")

        removed = clean_stale_pth_entries(venv, worktree_dir)
        assert len(removed) == 1
        assert stale in removed
        assert not stale.exists()
        assert clean.exists(), "Clean .pth should be preserved"

    def test_handles_missing_site_packages(self, tmp_path: Path) -> None:
        """Gracefully returns empty list when site-packages doesn't exist."""
        from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries

        venv = tmp_path / ".venv"
        venv.mkdir()
        # No lib/ directory at all

        removed = clean_stale_pth_entries(venv, "/tmp/worktrees/feat/fr-test")
        assert removed == []
