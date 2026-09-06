#!/usr/bin/env python3
"""FR-745: pre-commit triage disposition gate — the floor under fr_triage.

F4: fires only when a staged feature-requests/*.md is Judged-or-later
AND carries ``- [pending]`` triage claims. Proposed drafts pass freely;
FRs without a ``## Triage`` section pass freely. The gate checks the
STAGED blob, never the working tree (same F2 discipline as FR-738).

F2 kill criterion: review after the 10th judged FR carrying triage;
unless ≥3 claims changed judgement outcomes, remove this gate and the
hook reminder.

Skippable via SKIP=triage-gate; --no-verify remains forbidden.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

GIT = shutil.which("git") or "git"

_spec = importlib.util.spec_from_file_location(
    "fr_triage_tools",
    Path(__file__).resolve().parents[4] / "graphs" / "fr_triage" / "tools.py",
)
_tools = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tools)


def _staged_blob(path: str) -> str:
    """The content being committed (never the working tree)."""
    r = subprocess.run(  # noqa: S603  # CONF-397
        [GIT, "show", f":0:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.stdout if r.returncode == 0 else ""


def main(argv: list[str]) -> int:
    failures = 0
    for raw in argv:
        path = raw.strip()
        text = _staged_blob(path)
        if not text:
            continue  # deleted or unreadable — not this gate's business
        if _tools.gate_check(text):
            continue
        failures += 1
        sys.stderr.write(
            f"❌ triage claims undispositioned in {path}: FR is Judged+ but "
            f"`## Triage` still has `- [pending]` entries. Replace each with "
            f"[accepted]/[rejected]/[deferred] + one-line rationale, re-stage, "
            f"commit again. (SKIP=triage-gate to bypass; FR-745 F4)\n"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
