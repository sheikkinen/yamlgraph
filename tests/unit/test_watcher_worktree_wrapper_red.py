"""Acceptance tests for FR-698 watcher wrapper delegation."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
SETUP_WRAPPER = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_setup.sh"
TEARDOWN_WRAPPER = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "worktree_teardown.sh"
CANONICAL_SCRIPT = REPO_ROOT / "scripts" / "worktree.sh"


@pytest.mark.req("REQ-YG-528")
def test_worktree_setup_wrapper_preserves_json_contract_keys() -> None:
    wrapper = SETUP_WRAPPER.read_text(encoding="utf-8")
    canonical = CANONICAL_SCRIPT.read_text(encoding="utf-8")
    assert "scripts/worktree.sh" in wrapper
    assert "new" in wrapper
    assert "--json" in wrapper
    assert "wt_dir" in canonical
    assert "wt_branch" in canonical
    assert "main_dir" in canonical
    assert "work_dir" in canonical


@pytest.mark.req("REQ-YG-528")
def test_worktree_teardown_wrapper_delegates_to_worktree_rm() -> None:
    wrapper = TEARDOWN_WRAPPER.read_text(encoding="utf-8")
    assert "scripts/worktree.sh" in wrapper
    assert "rm --dir" in wrapper
