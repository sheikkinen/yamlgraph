"""Unit tests for .chaplain/lib/worktree.py create_worktree() (FR-265).

Tests force-add staging, multi-draft guard, commit idempotency,
and draft file survival using mocked subprocess + real tmp_path filesystem.
"""

import importlib.util
import subprocess
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

# Load create_worktree from non-package .chaplain/lib/worktree.py
import pytest

pytestmark = pytest.mark.process

_WORKTREE_PY = (
    Path(__file__).resolve().parent.parent.parent / ".chaplain" / "lib" / "worktree.py"
)


def _load_create_worktree():
    """Import create_worktree via importlib (non-package path)."""
    spec = importlib.util.spec_from_file_location("chaplain_worktree", _WORKTREE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.create_worktree


@contextmanager
def _mock_git_and_venv(run_side_effect):
    """Patch subprocess.run, Path.symlink_to, and venv validators."""
    with (
        patch("subprocess.run", side_effect=run_side_effect),
        patch.object(Path, "symlink_to"),
        patch("yamlgraph.utils.worktree_helpers.validate_venv_health"),
        patch("yamlgraph.utils.worktree_helpers.validate_venv_symlink"),
    ):
        yield


def _ok_run(cmd, **kwargs):
    """Default mock returning success for all subprocess calls."""
    return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")


@pytest.mark.req("REQ-YG-106")
class TestCreateWorktreeForceAdd:
    """AC-01: create_worktree() stages draft FR file with git add -f."""

    def test_force_adds_draft_file(self, tmp_path):
        """git add -f is called, not plain git add."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        draft = drafts / "FR-100-test-feature.md"
        draft.write_text("# FR-100 Test Feature\n", encoding="utf-8")

        calls_made = []

        def mock_run(cmd, **kwargs):
            calls_made.append(list(cmd))
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        with _mock_git_and_venv(mock_run):
            create_worktree({"drafts_dir": str(drafts)})

        # Find the git add (not git worktree add) call
        add_calls = [c for c in calls_made if c[:2] == ["git", "add"]]
        assert len(add_calls) == 1, f"Expected one git add call, got: {add_calls}"
        assert "-f" in add_calls[0], f"Expected -f flag: {add_calls[0]}"


@pytest.mark.req("REQ-YG-106")
class TestCreateWorktreeMultiDraftGuard:
    """AC-03: create_worktree() fails fast with ValueError for multiple drafts."""

    def test_raises_on_multiple_drafts(self, tmp_path):
        """Multiple draft files raise ValueError naming candidates."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "FR-100-first.md").write_text("# First\n", encoding="utf-8")
        (drafts / "FR-101-second.md").write_text("# Second\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Multiple draft files"):
            create_worktree({"drafts_dir": str(drafts)})

    def test_raises_on_no_drafts(self, tmp_path):
        """No draft files raise FileNotFoundError."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()

        with pytest.raises(FileNotFoundError, match="No draft files"):
            create_worktree({"drafts_dir": str(drafts)})


@pytest.mark.req("REQ-YG-106")
class TestCreateWorktreeHappyPath:
    """AC-04: Single-draft happy path succeeds and returns correct dict."""

    def test_single_draft_returns_worktree_dir_and_branch(self, tmp_path):
        """Returns dict with worktree_dir and branch keys."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        draft = drafts / "FR-100-test-feature.md"
        draft.write_text("# FR-100 Test Feature\n", encoding="utf-8")

        with _mock_git_and_venv(_ok_run):
            result = create_worktree({"drafts_dir": str(drafts)})

        assert "worktree_dir" in result
        assert "branch" in result
        assert result["branch"] == "feat/fr-100-test-feature"
        assert "tmp/worktrees/" in result["worktree_dir"]


@pytest.mark.req("REQ-YG-106")
class TestCreateWorktreeCommitIdempotency:
    """AC-05/AC-06: Commit idempotency and error handling."""

    def test_nothing_to_commit_in_stdout_continues(self, tmp_path):
        """git commit returning 'nothing to commit' in stdout does not raise."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "FR-100-test.md").write_text("# Test\n", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            if "commit" in list(cmd):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=1,
                    stdout="On branch main\nnothing to commit, working tree clean\n",
                    stderr="",
                )
            return _ok_run(cmd, **kwargs)

        with _mock_git_and_venv(mock_run):
            result = create_worktree({"drafts_dir": str(drafts)})

        assert result["branch"] == "feat/fr-100-test"

    def test_nothing_to_commit_in_stderr_continues(self, tmp_path):
        """git commit returning 'nothing to commit' in stderr does not raise."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "FR-100-test.md").write_text("# Test\n", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            if "commit" in list(cmd):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=1,
                    stdout="",
                    stderr="nothing to commit\n",
                )
            return _ok_run(cmd, **kwargs)

        with _mock_git_and_venv(mock_run):
            result = create_worktree({"drafts_dir": str(drafts)})

        assert result["branch"] == "feat/fr-100-test"

    def test_other_commit_error_raises(self, tmp_path):
        """git commit failure (not 'nothing to commit') raises RuntimeError."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        (drafts / "FR-100-test.md").write_text("# Test\n", encoding="utf-8")

        def mock_run(cmd, **kwargs):
            if "commit" in list(cmd):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=128,
                    stdout="",
                    stderr="fatal: not a git repository\n",
                )
            return _ok_run(cmd, **kwargs)

        with (
            patch("subprocess.run", side_effect=mock_run),
            pytest.raises(RuntimeError, match="git commit failed"),
        ):
            create_worktree({"drafts_dir": str(drafts)})


@pytest.mark.req("REQ-YG-106")
class TestCreateWorktreeDraftSurvival:
    """AC-09: Draft file remains on disk after commit."""

    def test_draft_file_not_deleted(self, tmp_path):
        """After create_worktree(), draft file still exists on disk."""
        create_worktree = _load_create_worktree()

        drafts = tmp_path / "drafts"
        drafts.mkdir()
        draft = drafts / "FR-100-test.md"
        draft.write_text("# FR-100 Test\n", encoding="utf-8")

        with _mock_git_and_venv(_ok_run):
            create_worktree({"drafts_dir": str(drafts)})

        assert draft.exists(), "Draft file should still exist after create_worktree()"
        assert draft.read_text(encoding="utf-8") == "# FR-100 Test\n"
