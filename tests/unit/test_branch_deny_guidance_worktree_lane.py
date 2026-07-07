"""REQ-YG-527: branch-create denial guidance includes manual worktree lane."""

from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-527")
def test_pre_command_guard_mentions_manual_worktree_lane() -> None:
    hook = Path(".github/hooks/scripts/pre-command-guard.sh").read_text()
    assert "scripts/worktree.sh new <name>" in hook
