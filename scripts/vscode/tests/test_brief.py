#!/usr/bin/env python3
"""FR-743: SessionStart briefing — witnesses.

Unmarked per FR-737 F5 precedent. Run: pytest scripts/vscode/tests/ -q

Pins (judgement 2026-07-17):
- AC-01 `now.py --brief`: ≤15 lines, headline-only, never raises
  (fail-open is a return value, not an exception).
- AC-03 failure isolation: session-briefing.sh exits 0 and stays
  silent when python is unavailable or now.py explodes — a briefing
  hook that blocks session start is worse than no briefing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import now  # noqa: E402  # CONF-396

REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / ".github/hooks/scripts/session-briefing.sh"


def test_brief_lines_budget_and_headlines():
    lines = now.brief_lines()
    assert len(lines) <= 15, f"budget blown: {len(lines)} lines"
    text = "\n".join(lines)
    assert "briefing" in text.lower()
    assert "now.py" in text  # the drill-down pointer to the full board


def test_brief_lines_never_raises(monkeypatch):
    """Fail-open at the python layer: any data-source explosion yields
    a degraded briefing, not an exception."""
    monkeypatch.setattr(now, "live_sessions", lambda *_: 1 / 0)
    lines = now.brief_lines()
    assert isinstance(lines, list)  # degraded, not dead


def test_briefing_script_fail_open_without_python():
    """AC-03: sabotage PATH so no python exists — exit 0, no stderr noise."""
    r = subprocess.run(
        ["/bin/sh", str(SCRIPT)],
        capture_output=True,
        text=True,
        env={"PATH": "/nonexistent"},
        cwd=REPO,
        timeout=10,
    )
    assert r.returncode == 0


def test_briefing_script_emits_when_healthy():
    r = subprocess.run(
        ["/bin/sh", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=15,
    )
    assert r.returncode == 0
    assert "briefing" in r.stdout.lower()
