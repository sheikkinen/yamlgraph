"""REQ-YG-631: OS-enforced main-write lock surfaces exist and are wired.

Framework-scope witness (FR-436 pattern): behavioral coverage lives in
.github/hooks/tests/test_main_write_guard.py and test_size_gate.py;
this asserts the shipped surfaces.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process


@pytest.mark.req("REQ-YG-631")
def test_main_write_lock_surfaces_shipped() -> None:
    worktree = Path("scripts/worktree.sh").read_text(encoding="utf-8")
    assert "lock_main()" in worktree
    assert "unlock_main()" in worktree
    assert "sync_main()" in worktree
    check = Path(".github/hooks/scripts/checks/main_write.py").read_text(encoding="utf-8")
    assert "FENCE_VERBS" in check
    guard = Path(".github/hooks/scripts/pre-command-guard.sh").read_text(encoding="utf-8")
    assert "checks/main_write.py" in guard
    gate = Path("scripts/size_gate.py").read_text(encoding="utf-8")
    assert "LIMIT = 450" in gate
