#!/usr/bin/env python3
"""FR-858: the committed FR board is retired; fr_board.py is a pure query.

Unmarked per FR-737 F5 precedent (process infrastructure follows its
target's convention). Run: pytest scripts/tests/ -q

Witnesses the retirement contract (judgement 2026-08-30):
- AC-04/AC-07 the CLI renders to stdout and writes nothing.
- AC-05 no repo-writing or drift-check CLI modes survive.
- AC-01/AC-02/AC-03 the committed cache, its hook, and active runtime
  readers are gone.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REPO_ROOT = Path(__file__).resolve().parents[2]
BOARD = REPO_ROOT / "docs" / "fr-board.md"


def test_committed_board_is_untracked():
    tracked = subprocess.run(  # noqa: S603
        ["git", "ls-files", "docs/fr-board.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert tracked.stdout.strip() == ""


def test_no_active_drift_hook():
    config = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "fr-board-check" not in config
    assert "fr_board.py --check" not in config


def test_cli_renders_to_stdout_and_writes_nothing():
    before = BOARD.exists()
    result = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/fr_board.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "| FR-" in result.stdout
    assert BOARD.exists() == before, "query mode must not create the board"


def test_cli_rejects_retired_write_and_check_flags():
    for flag in (["--out", "docs/fr-board.md"], ["--check"]):
        result = subprocess.run(  # noqa: S603
            [sys.executable, "scripts/fr_board.py", *flag],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0, f"{flag} should no longer be accepted"


def test_now_py_reads_live_state_not_the_committed_board():
    source = (REPO_ROOT / "scripts" / "vscode" / "now.py").read_text(encoding="utf-8")
    assert "docs/fr-board.md" not in source


def test_session_introspection_skill_routes_to_the_live_command():
    skill = (
        REPO_ROOT / ".github" / "skills" / "session-introspection" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "docs/fr-board.md" not in skill
    assert "fr_board.py" in skill
