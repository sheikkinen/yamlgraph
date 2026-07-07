"""Acceptance tests for FR-698 shared worktree CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKTREE_SCRIPT = REPO_ROOT / "scripts" / "worktree.sh"
WORKTREE_ALIAS = REPO_ROOT / "scripts" / "wt"


@pytest.mark.req("REQ-YG-524")
def test_worktree_usage_lists_new_spike_list_rm() -> None:
    result = subprocess.run(
        ["bash", str(WORKTREE_SCRIPT)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "new" in output
    assert "spike" in output
    assert "list" in output
    assert "rm" in output


@pytest.mark.req("REQ-YG-524")
def test_worktree_alias_executes_canonical_script() -> None:
    alias_text = WORKTREE_ALIAS.read_text()
    assert "worktree.sh" in alias_text
    assert "exec" in alias_text


@pytest.mark.req("REQ-YG-524")
def test_worktree_rm_runs_self_heal_sequence() -> None:
    text = WORKTREE_SCRIPT.read_text()
    assert "core.bare false" in text
    assert "clean_stale_pth_entries" in text
    assert "validate_editable_install" in text
    assert "pip install -e" in text


@pytest.mark.req("REQ-YG-524")
def test_worktree_spike_rm_requires_note_and_blocks_without_it(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    subprocess.run(
        ["bash", str(WORKTREE_SCRIPT), "spike", "fr-697-note-test", "--json"],
        cwd=repo,
        check=True,
    )
    remove = subprocess.run(
        ["bash", str(WORKTREE_SCRIPT), "rm", "fr-697-note-test"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert remove.returncode != 0
    assert "requires --note" in (remove.stdout + remove.stderr)
    assert (repo / "tmp/worktrees/feat/fr-697-note-test").exists()


@pytest.mark.req("REQ-YG-524")
def test_worktree_spike_rm_appends_spike_note_log_line(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("seed\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True)

    subprocess.run(
        ["bash", str(WORKTREE_SCRIPT), "spike", "fr-697-log-test", "--json"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        [
            "bash",
            str(WORKTREE_SCRIPT),
            "rm",
            "fr-697-log-test",
            "--note",
            "Captured useful teardown insight",
        ],
        cwd=repo,
        check=True,
    )
    log_file = repo / "docs/diary/spike-notes.log"
    assert log_file.exists()
    assert "fr-697-log-test: Captured useful teardown insight" in log_file.read_text()
