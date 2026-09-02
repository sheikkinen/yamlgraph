"""Unit tests for copilot_session_gc.sh (FR-138).

Tests verify the shell script correctly prunes stale Copilot CLI sessions
based on age, respects --dry-run, protects active sessions, and handles
edge cases (missing directory, idempotency).

All tests use a temporary directory as COPILOT_SESSION_DIR to avoid
touching real session state.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "copilot_session_gc.sh"


def _make_session(session_dir: Path, uuid: str, age_days: int = 0) -> Path:
    """Create a fake session directory with controlled mtime."""
    d = session_dir / uuid
    d.mkdir(parents=True)
    (d / "workspace.yaml").write_text(f"session: {uuid}\n", encoding="utf-8")
    if age_days > 0:
        old_ts = time.time() - (age_days * 86400 + 60)
        os.utime(d, (old_ts, old_ts))
        os.utime(d / "workspace.yaml", (old_ts, old_ts))
    return d


def _run_gc(
    session_dir: Path,
    *,
    max_age: int | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    active_session: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run the GC script against a test session directory."""
    cmd = [str(SCRIPT)]
    if max_age is not None:
        cmd += ["--max-age", str(max_age)]
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    env = {**os.environ, "COPILOT_SESSION_DIR": str(session_dir)}
    if active_session:
        env["COPILOT_SESSION_ID"] = active_session

    return subprocess.run(cmd, capture_output=True, text=True, env=env)


# ---------------------------------------------------------------------------
# Age-Based Filtering
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-141")
class TestAgeFiltering:
    """Sessions older than --max-age are removed; newer ones are kept."""

    def test_old_sessions_removed(self, tmp_path):
        """Sessions older than max-age are deleted."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "old-session-aaa", age_days=10)
        _make_session(session_dir, "new-session-bbb", age_days=0)

        result = _run_gc(session_dir, max_age=7)
        assert result.returncode == 0

        assert not (session_dir / "old-session-aaa").exists()
        assert (session_dir / "new-session-bbb").exists()

    def test_custom_max_age(self, tmp_path):
        """--max-age 2 removes sessions older than 2 days."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "three-day-old", age_days=3)
        _make_session(session_dir, "one-day-old", age_days=1)

        result = _run_gc(session_dir, max_age=2)
        assert result.returncode == 0

        assert not (session_dir / "three-day-old").exists()
        assert (session_dir / "one-day-old").exists()

    def test_default_max_age_is_7(self, tmp_path):
        """Default max-age of 7 days: 8-day-old removed, 5-day-old kept."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "eight-day-old", age_days=8)
        _make_session(session_dir, "five-day-old", age_days=5)

        result = _run_gc(session_dir)
        assert result.returncode == 0

        assert not (session_dir / "eight-day-old").exists()
        assert (session_dir / "five-day-old").exists()


# ---------------------------------------------------------------------------
# Dry Run
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-141")
class TestDryRun:
    """--dry-run lists sessions without deleting them."""

    def test_dry_run_preserves_sessions(self, tmp_path):
        """--dry-run does not delete any sessions."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "old-to-delete", age_days=10)

        result = _run_gc(session_dir, max_age=7, dry_run=True)
        assert result.returncode == 0

        # Session must still exist
        assert (session_dir / "old-to-delete").exists()

    def test_dry_run_lists_candidates(self, tmp_path):
        """--dry-run output mentions the session UUID."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "old-to-delete", age_days=10)

        result = _run_gc(session_dir, max_age=7, dry_run=True)
        assert "old-to-delete" in result.stdout


# ---------------------------------------------------------------------------
# Active Session Protection
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-141")
class TestActiveSessionProtection:
    """The session matching $COPILOT_SESSION_ID is never deleted."""

    def test_active_session_preserved(self, tmp_path):
        """Active session is kept even when older than max-age."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "active-uuid", age_days=30)
        _make_session(session_dir, "stale-uuid", age_days=30)

        result = _run_gc(session_dir, max_age=7, active_session="active-uuid")
        assert result.returncode == 0

        assert (session_dir / "active-uuid").exists()
        assert not (session_dir / "stale-uuid").exists()

    def test_active_session_logged_as_skipped(self, tmp_path):
        """Output notes the active session was skipped."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "active-uuid", age_days=30)

        result = _run_gc(session_dir, max_age=7, active_session="active-uuid")
        assert "active-uuid" in result.stdout
        assert "skip" in result.stdout.lower() or "active" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-141")
class TestEdgeCases:
    """Script handles missing directory, empty directory, and non-session files."""

    def test_missing_directory_exits_cleanly(self, tmp_path):
        """Script exits 0 when session directory does not exist."""
        nonexistent = tmp_path / "does-not-exist"
        result = _run_gc(nonexistent)
        assert result.returncode == 0

    def test_empty_directory(self, tmp_path):
        """Script exits 0 when session directory is empty."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        result = _run_gc(session_dir)
        assert result.returncode == 0

    def test_idempotent(self, tmp_path):
        """Running GC twice produces the same result (no errors on second run)."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "old-one", age_days=10)

        result1 = _run_gc(session_dir, max_age=7)
        assert result1.returncode == 0
        assert not (session_dir / "old-one").exists()

        result2 = _run_gc(session_dir, max_age=7)
        assert result2.returncode == 0

    def test_non_directory_files_ignored(self, tmp_path):
        """Regular files in session-state/ are not deleted."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        (session_dir / "some-file.txt").write_text("not a session\n", encoding="utf-8")
        old_ts = time.time() - (30 * 86400)
        os.utime(session_dir / "some-file.txt", (old_ts, old_ts))

        result = _run_gc(session_dir, max_age=7)
        assert result.returncode == 0
        assert (session_dir / "some-file.txt").exists()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-141")
class TestLogging:
    """Deleted sessions are logged with UUID and age."""

    def test_deleted_session_logged_with_uuid(self, tmp_path):
        """Output includes the UUID of each deleted session."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "logged-uuid-123", age_days=10)

        result = _run_gc(session_dir, max_age=7)
        assert "logged-uuid-123" in result.stdout

    def test_deleted_session_logged_with_age(self, tmp_path):
        """Output includes the age in days of each deleted session."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "aged-session", age_days=10)

        result = _run_gc(session_dir, max_age=7)
        # Should mention "10" days somewhere in the output
        assert "10" in result.stdout

    def test_summary_count(self, tmp_path):
        """Output includes a summary count of removed sessions."""
        session_dir = tmp_path / "session-state"
        session_dir.mkdir()
        _make_session(session_dir, "rm-1", age_days=10)
        _make_session(session_dir, "rm-2", age_days=10)
        _make_session(session_dir, "keep-1", age_days=1)

        result = _run_gc(session_dir, max_age=7)
        # Should mention "2" removed
        assert "2" in result.stdout
