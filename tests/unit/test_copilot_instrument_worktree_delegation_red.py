"""Acceptance tests for FR-698 copilot instrumentation worktree delegation."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTRUMENT_SCRIPT = REPO_ROOT / "scripts" / "copilot_instrument.sh"


@pytest.mark.req("REQ-YG-526")
def test_instrument_script_calls_shared_worktree_new_rm() -> None:
    text = INSTRUMENT_SCRIPT.read_text()
    assert "scripts/worktree.sh" in text
    assert 'worktree.sh" new' in text
    assert 'worktree.sh" rm' in text


@pytest.mark.req("REQ-YG-526")
def test_instrument_script_has_no_direct_worktree_add_remove() -> None:
    text = INSTRUMENT_SCRIPT.read_text()
    assert "worktree add --detach" not in text
    assert "worktree remove --force" not in text
