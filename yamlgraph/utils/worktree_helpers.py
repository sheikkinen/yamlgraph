"""Worktree helpers for parallel development pipeline (FR-106).

Provides utility functions for git worktree orchestration:
- derive_branch_name: Extract branch name from FR path
- construct_worktree_path: Build worktree directory path
- validate_clean_working_tree: Check for uncommitted changes
"""

import subprocess
from pathlib import Path


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


def validate_clean_working_tree() -> bool:
    """Validate that the working tree has no uncommitted changes.

    Checks both staged and unstaged changes. Creating a worktree from
    a dirty working tree would propagate uncommitted changes.

    Returns:
        True if working tree is clean

    Raises:
        ValueError: If there are unstaged or staged changes

    Example:
        >>> validate_clean_working_tree()  # When clean
        True
        >>> validate_clean_working_tree()  # When dirty
        Traceback: ValueError: Working tree has unstaged changes
    """
    # Check unstaged changes
    result_unstaged = subprocess.run(
        ["git", "diff", "--quiet"],
        capture_output=True,
    )
    if result_unstaged.returncode != 0:
        raise ValueError("Working tree has unstaged changes")

    # Check staged changes
    result_staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
    )
    if result_staged.returncode != 0:
        raise ValueError("Working tree has staged changes")

    return True
