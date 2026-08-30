"""REQ-YG-629/630: retained session-lane tooling surfaces exist.

Framework-scope witness (FR-436 pattern): behavioral coverage lives in
.github/hooks/tests/test_session_lane_gc_join.py; this asserts the shipped
surfaces. The FR-902 hook machinery was retired by FR-927 — its absence is
pinned by .github/hooks/tests/test_fr902_retired.py.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-629")
def test_session_lane_surfaces_shipped() -> None:
    worktree = Path("scripts/worktree.sh").read_text()
    assert "session_lane()" in worktree


@pytest.mark.req("REQ-YG-630")
def test_gc_join_surfaces_shipped() -> None:
    worktree = Path("scripts/worktree.sh").read_text()
    assert "gc_session_lanes()" in worktree
    assert Path("scripts/vscode/session_join.py").exists()
    assert "session_lane_lines" in Path("scripts/vscode/now.py").read_text()
