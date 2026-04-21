"""Worktree creation tool for the Chaplain copilot pipeline (FR-260).

Commits FR draft to main and creates a git worktree for acceptance tests.
Follows the diary.py pattern: def tool_fn(state: dict) -> dict.
"""

import glob as glob_mod
import logging
import os
import subprocess
from pathlib import Path

from yamlgraph.utils.worktree_helpers import (
    construct_worktree_path,
    derive_branch_name,
    validate_venv_health,
    validate_venv_symlink,
)

logger = logging.getLogger(__name__)


def create_worktree(state: dict) -> dict:
    """Commit FR draft to main and create worktree for acceptance tests.

    Reads the FR draft from drafts_dir, commits it to main, then creates
    a git worktree with .venv symlink. Returns worktree_dir and branch
    as state update.

    Args:
        state: Graph state containing drafts_dir (path to FR drafts directory).

    Returns:
        Dict with worktree_dir and branch keys.
    """
    drafts_dir = state.get("drafts_dir", "")

    # Find FR draft file in drafts_dir
    fr_files = glob_mod.glob(os.path.join(drafts_dir, "*.md"))
    if not fr_files:
        raise FileNotFoundError(f"No FR draft found in {drafts_dir}")
    fr_path = fr_files[0]

    # Derive branch and worktree path
    branch = derive_branch_name(fr_path)
    worktree_dir = construct_worktree_path(branch)

    # Commit FR draft to main (--no-verify to avoid pre-commit circular dependency)
    subprocess.run(  # noqa: S603
        ["git", "add", fr_path],  # noqa: S607
        check=True,
        capture_output=True,
    )
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "commit",
            "--no-verify",
            "-m",
            f"docs(FR): add {Path(fr_path).stem} for enforce pipeline",
        ],
        check=False,
        capture_output=True,
    )

    # Create worktree directory structure
    os.makedirs(os.path.dirname(worktree_dir), exist_ok=True)

    # Create git worktree
    subprocess.run(  # noqa: S603
        ["git", "worktree", "add", worktree_dir, "-b", branch, "main"],  # noqa: S607
        check=True,
        capture_output=True,
    )

    # Symlink .venv from main repo
    main_venv = Path(".venv").resolve()
    worktree_venv = Path(worktree_dir) / ".venv"

    validate_venv_health(main_venv)
    os.symlink(str(main_venv), str(worktree_venv))
    validate_venv_symlink(worktree_venv, main_venv)

    logger.info("✓ Worktree created at %s on branch %s", worktree_dir, branch)

    return {"worktree_dir": worktree_dir, "branch": branch}
