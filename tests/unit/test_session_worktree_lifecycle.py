"""REQ-YG-629/630: session worktree lifecycle surfaces exist and are wired.

Framework-scope witness (FR-436 pattern): behavioral coverage lives in
.github/hooks/tests/test_fr902_*.py; this asserts the shipped surfaces.
"""

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-629")
def test_session_lane_surfaces_shipped() -> None:
    worktree = Path("scripts/worktree.sh").read_text()
    assert "session_lane()" in worktree
    guard = Path(".github/hooks/scripts/pre-command-guard.sh").read_text()
    assert "FR902_ALLOW_OUTSIDE" in guard
    hook = Path(".github/hooks/scripts/session-worktree.sh")
    assert hook.exists()
    assert "fr902.live" in hook.read_text()


@pytest.mark.req("REQ-YG-630")
def test_checkpoint_gc_join_surfaces_shipped() -> None:
    worktree = Path("scripts/worktree.sh").read_text()
    assert "gc_session_lanes()" in worktree
    checkpoint = Path(".github/hooks/scripts/session-checkpoint.sh").read_text()
    assert "Request-Index" in checkpoint
    assert Path("scripts/vscode/session_join.py").exists()
    probe = json.loads(Path(".github/hooks/session-probe.json").read_text())
    start_cmds = [h["command"] for h in probe["hooks"]["SessionStart"]]
    stop_cmds = [h["command"] for h in probe["hooks"]["Stop"]]
    assert ".github/hooks/scripts/session-worktree.sh" in start_cmds
    assert ".github/hooks/scripts/session-checkpoint.sh" in stop_cmds
