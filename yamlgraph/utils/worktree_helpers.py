"""Worktree helpers for parallel development pipeline (FR-106).

Provides utility functions for git worktree orchestration:
- derive_branch_name: Extract branch name from FR path
- construct_worktree_path: Build worktree directory path
- validate_clean_working_tree: Check for uncommitted changes
- validate_venv_health: Assert .venv exists with working python (FR-174)
- validate_venv_symlink: Assert .venv symlink resolves correctly (FR-174)
- clean_stale_pth_entries: Remove dangling .pth/.egg-link files (FR-174)
- validate_editable_install: Probe import health after cleanup (FR-241)
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def derive_branch_name(fr_path: str) -> str:
    """Derive git branch name from feature request path.

    Extracts the filename (without directory), removes .md extension,
    converts to lowercase, and prefixes with 'feat/'.

    Args:
        fr_path: Path to the feature request file (e.g., "feature-requests/FR-106-test.md")

    Returns:
        Branch name (e.g., "feat/fr-106-test")

    Example:
        >>> derive_branch_name("feature-requests/FR-106-parallel-worktree-pipeline.md")
        'feat/fr-106-parallel-worktree-pipeline'
    """
    filename = Path(fr_path).stem  # Removes extension and directory
    return f"feat/{filename.lower()}"


def construct_worktree_path(branch: str) -> str:
    """Construct the worktree directory path for a given branch.

    Worktrees live under tmp/worktrees/ which is covered by .gitignore.

    Args:
        branch: Git branch name (e.g., "feat/fr-106-test")

    Returns:
        Worktree path (e.g., "tmp/worktrees/feat/fr-106-test")

    Example:
        >>> construct_worktree_path("feat/fr-106-test")
        'tmp/worktrees/feat/fr-106-test'
    """
    return f"tmp/worktrees/{branch}"


def validate_clean_working_tree(exclude_paths: list[str] | None = None) -> bool:
    """Validate that the working tree has no uncommitted changes.

    Checks both staged and unstaged changes. Creating a worktree from
    a dirty working tree would propagate uncommitted changes.

    Args:
        exclude_paths: Paths to exclude from the check (e.g., ["docs/diary/"]).
                      Use for files that are expected to have changes (inquisitor diary).

    Returns:
        True if working tree is clean (excluding allowed paths)

    Raises:
        ValueError: If there are unstaged or staged changes in non-excluded files

    Example:
        >>> validate_clean_working_tree()  # When clean
        True
        >>> validate_clean_working_tree(exclude_paths=["docs/diary/"])  # Ignore diary
        True
    """
    exclude_paths = exclude_paths or []

    def is_excluded(filepath: str) -> bool:
        """Check if filepath matches any exclude pattern (exact or prefix for dirs)."""
        for pattern in exclude_paths:
            if pattern.endswith("/"):
                if filepath.startswith(pattern):
                    return True
            elif filepath == pattern:
                return True
        return False

    # Check unstaged changes
    result_unstaged = subprocess.run(  # noqa: S603
        ["git", "diff", "--name-only"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    unstaged_files = [f for f in result_unstaged.stdout.strip().split("\n") if f]
    non_excluded_unstaged = [f for f in unstaged_files if not is_excluded(f)]
    if non_excluded_unstaged:
        raise ValueError(f"Working tree has unstaged changes: {non_excluded_unstaged}")

    # Check staged changes
    result_staged = subprocess.run(  # noqa: S603
        ["git", "diff", "--cached", "--name-only"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    staged_files = [f for f in result_staged.stdout.strip().split("\n") if f]
    non_excluded_staged = [f for f in staged_files if not is_excluded(f)]
    if non_excluded_staged:
        raise ValueError(f"Working tree has staged changes: {non_excluded_staged}")

    return True


def validate_venv_health(venv_path: Path) -> None:
    """Validate that a .venv directory exists and has a working Python binary.

    Fails loudly instead of silently skipping — Commandment 6.

    Args:
        venv_path: Path to the .venv directory.

    Raises:
        FileNotFoundError: If .venv is missing, bin/python is absent, or not executable.
    """
    if not venv_path.is_dir():
        raise FileNotFoundError(
            f".venv does not exist at {venv_path}. "
            f"Create it with: python -m venv {venv_path}"
        )

    python_bin = venv_path / "bin" / "python"
    if not python_bin.exists():
        raise FileNotFoundError(
            f".venv/bin/python not found at {python_bin}. "
            f"The virtual environment may be corrupted — recreate it."
        )

    if not os.access(python_bin, os.X_OK):
        raise FileNotFoundError(
            f".venv/bin/python is not executable at {python_bin}. "
            f"Fix with: chmod +x {python_bin}"
        )


def validate_venv_symlink(symlink_path: Path, target_path: Path) -> None:
    """Validate that a .venv symlink in a worktree resolves correctly.

    Args:
        symlink_path: Path to the .venv symlink in the worktree.
        target_path: Expected target (the main repo's .venv).

    Raises:
        OSError: If path is not a symlink or target doesn't resolve.
    """
    if not symlink_path.is_symlink():
        raise OSError(
            f"{symlink_path} is not a symlink. Expected symlink to {target_path}."
        )

    if not symlink_path.resolve().exists():
        raise OSError(
            f"Symlink {symlink_path} does not resolve — "
            f"target {target_path} may have been deleted."
        )


def clean_stale_pth_entries(venv_path: Path, worktree_dir: str) -> list[Path]:
    """Remove .pth, .egg-link, and direct_url.json files referencing a worktree.

    After a worktree is removed, editable installs (pip install -e .) leave
    dangling .pth/.egg-link files in site-packages pointing to the deleted
    worktree. Modern pip (21.3+) also writes direct_url.json inside
    *.dist-info/ with the worktree path. Both corrupt import resolution.

    Args:
        venv_path: Path to the .venv directory.
        worktree_dir: Absolute path to the worktree being cleaned up.

    Returns:
        List of Path objects that were removed (empty if none found).
    """
    removed: list[Path] = []

    lib_dir = venv_path / "lib"
    if not lib_dir.is_dir():
        return removed

    for site_packages in lib_dir.glob("python*/site-packages"):
        if not site_packages.is_dir():
            continue

        for pattern in ("*.pth", "*.egg-link"):
            for pth_file in site_packages.glob(pattern):
                try:
                    content = pth_file.read_text(encoding="utf-8")
                except OSError:
                    continue

                if worktree_dir in content:
                    logger.warning(
                        "Removing stale %s referencing worktree %s",
                        pth_file.name,
                        worktree_dir,
                    )
                    pth_file.unlink()
                    removed.append(pth_file)

        # Modern pip (21.3+) editable installs also write direct_url.json
        # inside *.dist-info/ with a file:// URL pointing at the source tree.
        for dist_info in site_packages.glob("*.dist-info"):
            direct_url = dist_info / "direct_url.json"
            if not direct_url.is_file():
                continue
            try:
                data = json.loads(direct_url.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            url = data.get("url", "")
            if worktree_dir in url:
                logger.warning(
                    "Removing stale %s referencing worktree %s",
                    direct_url,
                    worktree_dir,
                )
                direct_url.unlink()
                removed.append(direct_url)

    return removed


def validate_editable_install(package: str = "yamlgraph") -> bool:
    """Validate that a package can be imported by the current Python interpreter.

    Uses sys.executable to ensure venv isolation is respected. Returns a bool
    instead of raising so callers can decide on self-heal strategy.

    Args:
        package: Package name to try importing (default: "yamlgraph").

    Returns:
        True if the package imports successfully, False otherwise.
    """
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", f"import {package}"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    return result.returncode == 0
