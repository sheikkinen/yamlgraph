"""Worktree helpers for parallel development pipeline (FR-106, FR-114).

Provides utility functions for git worktree orchestration:
- derive_branch_name: Extract branch name from FR path
- construct_worktree_path: Build worktree directory path
- validate_clean_working_tree: Check for uncommitted changes
- read_enforce_sha: Read last-checked SHA from state file (FR-114)
- write_enforce_sha: Write SHA to state file (FR-114)
- detect_new_feature_requests: Detect new FRs via git diff (FR-114)
"""

import re
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


# --- FR-114: Enforce detection helpers ---

_FR_PATTERN = re.compile(r"FR-\d+-")


def read_enforce_sha(state_file: str) -> str | None:
    """Read last-checked commit SHA from state file.

    Args:
        state_file: Path to the SHA state file.

    Returns:
        The SHA string, or None if the file doesn't exist or is empty.

    Example:
        >>> read_enforce_sha(".chaplain/.last-enforce-sha")
        'abc123def'
    """
    path = Path(state_file)
    if not path.exists():
        return None
    content = path.read_text().strip()
    return content if content else None


def write_enforce_sha(state_file: str, sha: str) -> None:
    """Write commit SHA to state file.

    Creates parent directories if they don't exist.

    Args:
        state_file: Path to the SHA state file.
        sha: The commit SHA to persist.

    Example:
        >>> write_enforce_sha(".chaplain/.last-enforce-sha", "abc123def")
    """
    path = Path(state_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{sha}\n")


def detect_new_feature_requests(from_sha: str, to_sha: str) -> list[str]:
    """Detect feature requests added between two git SHAs.

    Uses ``git diff --name-only`` scoped to ``feature-requests/`` and filters
    to files matching the ``FR-[0-9]+-`` pattern, excluding TEMPLATE.md and
    README.md. Only returns files that exist on disk.

    Args:
        from_sha: The starting commit SHA.
        to_sha: The ending commit SHA.

    Returns:
        List of FR file paths that were added/modified between the SHAs.

    Example:
        >>> detect_new_feature_requests("abc123", "def456")
        ['feature-requests/FR-107-new-feature.md']
    """
    if from_sha == to_sha:
        return []

    result = subprocess.run(
        ["git", "diff", "--name-only", from_sha, to_sha, "--", "feature-requests/"],
        capture_output=True,
        text=True,
    )

    files = [f for f in result.stdout.strip().split("\n") if f]

    matched = []
    for f in files:
        basename = Path(f).name
        if basename in ("TEMPLATE.md", "README.md"):
            continue
        if not _FR_PATTERN.search(basename):
            continue
        matched.append(f)

    return matched
