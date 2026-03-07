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


def validate_clean_working_tree(exclude_paths: list[str] | None = None) -> bool:
    """Validate that the working tree has no uncommitted changes.

    Checks both staged and unstaged changes. Creating a worktree from
    a dirty working tree would propagate uncommitted changes.

    Args:
        exclude_paths: Paths to exclude from the check (e.g., ["docs/diary.md"]).
                      Use for files that are expected to have changes (inquisitor diary).

    Returns:
        True if working tree is clean (excluding allowed paths)

    Raises:
        ValueError: If there are unstaged or staged changes in non-excluded files

    Example:
        >>> validate_clean_working_tree()  # When clean
        True
        >>> validate_clean_working_tree(exclude_paths=["docs/diary.md"])  # Ignore diary
        True
    """
    exclude_paths = exclude_paths or []

    # Check unstaged changes
    result_unstaged = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
    )
    unstaged_files = [f for f in result_unstaged.stdout.strip().split("\n") if f]
    non_excluded_unstaged = [f for f in unstaged_files if f not in exclude_paths]
    if non_excluded_unstaged:
        raise ValueError(f"Working tree has unstaged changes: {non_excluded_unstaged}")

    # Check staged changes
    result_staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
    )
    staged_files = [f for f in result_staged.stdout.strip().split("\n") if f]
    non_excluded_staged = [f for f in staged_files if f not in exclude_paths]
    if non_excluded_staged:
        raise ValueError(f"Working tree has staged changes: {non_excluded_staged}")

    return True
