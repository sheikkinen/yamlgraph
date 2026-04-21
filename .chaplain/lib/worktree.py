"""Worktree creation tool for Chaplain copilot pipeline (FR-260, FR-265).

Graph tool function ``create_worktree(state)`` commits a draft FR from
``.chaplain/drafts/`` to main and creates an isolated git worktree for
the enforce pipeline.

FR-265 fixes:
- Uses ``git add -f`` to stage drafts under gitignored paths.
- Raises ``ValueError`` when multiple drafts exist (deterministic selection).
- Handles ``nothing to commit`` idempotently; raises on other commit errors.
"""

import logging
import subprocess  # noqa: S404
from pathlib import Path

logger = logging.getLogger(__name__)


def create_worktree(state: dict) -> dict:
    """Commit FR draft to main and create worktree for acceptance tests.

    Uses existing helpers from ``yamlgraph.utils.worktree_helpers``.
    Returns ``worktree_dir`` and ``branch`` as state update.

    Args:
        state: Graph state dict with ``drafts_dir`` key.

    Returns:
        Dict with ``worktree_dir`` and ``branch`` keys.

    Raises:
        FileNotFoundError: No draft files found in ``drafts_dir``.
        ValueError: Multiple draft files found (nondeterministic).
        RuntimeError: ``git commit`` failed for reasons other than
            "nothing to commit".
    """
    from yamlgraph.utils.worktree_helpers import (
        construct_worktree_path,
        derive_branch_name,
        validate_venv_health,
        validate_venv_symlink,
    )

    drafts_dir = Path(state["drafts_dir"])

    # --- Deterministic draft selection (FR-265 AC-03) ---
    fr_files = sorted(drafts_dir.glob("*.md"))
    if not fr_files:
        raise FileNotFoundError(f"No draft files found in {drafts_dir}")
    if len(fr_files) > 1:
        candidates = [str(f) for f in fr_files]
        raise ValueError(f"Multiple draft files found in {drafts_dir}: {candidates}")

    draft_path = fr_files[0]
    logger.info("Staging draft: %s", draft_path)

    # --- Force-add to handle .gitignore (FR-265 AC-01) ---
    subprocess.run(  # noqa: S603
        ["git", "add", "-f", str(draft_path)],  # noqa: S607
        check=True,
    )

    # --- Idempotent commit (FR-265 AC-05/AC-06) ---
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "git",
            "commit",
            "--no-verify",
            "-m",
            f"docs(FR): stage draft {draft_path.name}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        combined = result.stdout + result.stderr
        if "nothing to commit" in combined:
            logger.info("Draft already committed (nothing to commit)")
        else:
            raise RuntimeError(f"git commit failed: {result.stderr}")

    # --- Derive branch and worktree path ---
    branch = derive_branch_name(str(draft_path))
    worktree_dir = construct_worktree_path(branch)

    # --- Create worktree with parent dirs ---
    Path(worktree_dir).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603
        ["git", "worktree", "add", worktree_dir, "-b", branch, "main"],  # noqa: S607
        check=True,
    )

    # --- Symlink .venv (FR-174: validate BEFORE symlinking) ---
    main_venv = Path(".venv")
    validate_venv_health(main_venv)

    wt_venv = Path(worktree_dir) / ".venv"
    wt_venv.symlink_to(main_venv.resolve())
    validate_venv_symlink(wt_venv, main_venv)

    logger.info("Worktree ready: %s (branch: %s)", worktree_dir, branch)
    return {"worktree_dir": worktree_dir, "branch": branch}
