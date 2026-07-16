#!/usr/bin/env python3
"""FR-738: pre-commit prior-art disposition gate — the floor under FR-737.

The PostToolUse hook is advisory *when its delivery channel works*
(FR-737 U-1 proved it dropped its first real payload); this gate is the
floor whether or not it does: a newly ADDED feature-requests/*.md with
prior-art hits and no ``**Prior art:**`` disposition line fails the
commit. F2: both the addedness check and the marker check read git
state, not the working tree — an unstaged marker does not count.

Skippable via SKIP=prior-art-gate like every local hook (F4);
--no-verify remains forbidden by the pre-command guard.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

GIT = shutil.which("git") or "git"
MARKER = "**Prior art:**"

_spec = importlib.util.spec_from_file_location(
    "prior_art", Path(__file__).resolve().parent / "prior_art.py"
)
_prior_art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_prior_art)


def _staged_added() -> set[str]:
    """Paths staged as ADDED (not modified) in the index."""
    r = subprocess.run(  # noqa: S603  # CONF-388
        [GIT, "diff", "--cached", "--diff-filter=A", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {line.strip() for line in r.stdout.splitlines() if line.strip()}


def _staged_blob(path: str) -> str:
    """The content being committed (F2: never the working tree)."""
    r = subprocess.run(  # noqa: S603  # CONF-389
        [GIT, "show", f":0:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def main(argv: list[str]) -> int:
    added = _staged_added()
    failures = 0
    for raw in argv:
        path = raw.strip()
        if path not in added:
            continue  # modified/renamed files never gate
        hits = _prior_art.build_prior_art(Path(path))
        if not hits:
            continue  # A1 floor already makes silence meaningful
        if MARKER in _staged_blob(path):
            continue  # dispositioned — substance stays with the judge
        failures += 1
        sys.stderr.write(
            f"❌ prior-art disposition missing for {path}:\n{hits}"
            f"Add a `{MARKER}` line dispositioning the hits (and re-stage), "
            f"then commit again.\n"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
