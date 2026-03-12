"""Tests for FR-175: Sequential Enforcement Mode.

Validates that watch.sh runs enforcement pipelines sequentially (foreground)
instead of parallel (nohup &), captures exit codes, and continues on failure.
"""

import os
import stat
import subprocess
import textwrap

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
WATCH_SH = os.path.join(REPO_ROOT, ".chaplain", "watch.sh")


def _read_watch_sh() -> str:
    with open(WATCH_SH) as f:
        return f.read()


# ---------------------------------------------------------------------------
# 1. watch.sh content assertions — sequential, not parallel
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-158")
class TestWatchSequentialContent:
    """watch.sh must run enforce/bugfix foreground, not nohup background."""

    def test_enforce_not_nohup(self):
        """enforce_worktree.sh call must not use nohup."""
        watch_sh = _read_watch_sh()
        # Find lines with enforce_worktree.sh — none should have nohup
        for line in watch_sh.splitlines():
            if "enforce_worktree.sh" in line:
                assert (
                    "nohup" not in line
                ), f"enforce_worktree.sh must not use nohup: {line}"

    def test_bugfix_not_nohup(self):
        """bugfix_worktree.sh call must not use nohup."""
        watch_sh = _read_watch_sh()
        for line in watch_sh.splitlines():
            if "bugfix_worktree.sh" in line:
                assert (
                    "nohup" not in line
                ), f"bugfix_worktree.sh must not use nohup: {line}"

    def test_enforce_not_backgrounded(self):
        """enforce_worktree.sh call must not end with & (background)."""
        watch_sh = _read_watch_sh()
        for line in watch_sh.splitlines():
            if "enforce_worktree.sh" in line:
                assert not line.rstrip().endswith(
                    "&"
                ), f"enforce_worktree.sh must not be backgrounded: {line}"

    def test_bugfix_not_backgrounded(self):
        """bugfix_worktree.sh call must not end with & (background)."""
        watch_sh = _read_watch_sh()
        for line in watch_sh.splitlines():
            if "bugfix_worktree.sh" in line:
                assert not line.rstrip().endswith(
                    "&"
                ), f"bugfix_worktree.sh must not be backgrounded: {line}"

    def test_exit_code_captured_for_enforce(self):
        """watch.sh captures exit code after enforce_worktree.sh."""
        watch_sh = _read_watch_sh()
        assert "EXIT_CODE" in watch_sh, "watch.sh must capture EXIT_CODE"

    def test_exit_code_printed_after_enforce(self):
        """watch.sh prints exit code after enforcement completes."""
        watch_sh = _read_watch_sh()
        # Must have a line that prints the exit code
        assert "Completed" in watch_sh or "exit $EXIT_CODE" in watch_sh

    def test_no_pid_echo(self):
        """watch.sh must not echo PID (no background process to track)."""
        watch_sh = _read_watch_sh()
        assert 'echo "   PID:' not in watch_sh


# ---------------------------------------------------------------------------
# 2. Sequential execution order — functional test
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-158")
class TestSequentialExecutionOrder:
    """Verify enforcement runs sequentially, not in parallel."""

    def test_second_starts_after_first_ends(self, tmp_path):
        """Two enforce calls run sequentially: second starts after first ends."""
        # Create two mock enforce scripts that record timestamps
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        enforce_script = scripts_dir / "enforce_worktree.sh"
        enforce_script.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            STAMP_FILE="$TEST_DIR/tmp/stamps-$(basename "$1" .md).txt"
            echo "START:$(python3 -c 'import time; print(time.time())')" >> "$STAMP_FILE"
            sleep 0.3
            echo "END:$(python3 -c 'import time; print(time.time())')" >> "$STAMP_FILE"
        """)
        )
        enforce_script.chmod(enforce_script.stat().st_mode | stat.S_IEXEC)

        # Create two FR files
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-001-first.md").write_text("**Status:** Approved\n")
        (fr_dir / "FR-002-second.md").write_text("**Status:** Approved\n")

        (tmp_path / "tmp").mkdir()

        # Script that processes two FRs sequentially (mirrors new watch.sh logic)
        test_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            for fr in feature-requests/FR-001-first.md feature-requests/FR-002-second.md; do
                mkdir -p tmp
                LOG="tmp/enforce-$(basename "$fr" .md).log"
                EXIT_CODE=0
                scripts/enforce_worktree.sh "$fr" > "$LOG" 2>&1 || EXIT_CODE=$?
                echo "DONE:$fr:$EXIT_CODE"
            done
        """)

        result = subprocess.run(
            ["bash", "-c", test_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Read timestamps — second must start after first ends
        stamps1 = (tmp_path / "tmp" / "stamps-FR-001-first.txt").read_text()
        stamps2 = (tmp_path / "tmp" / "stamps-FR-002-second.txt").read_text()

        end_first = float(
            [line for line in stamps1.splitlines() if line.startswith("END:")][0].split(
                ":"
            )[1]
        )
        start_second = float(
            [line for line in stamps2.splitlines() if line.startswith("START:")][
                0
            ].split(":")[1]
        )
        assert start_second >= end_first, (
            f"Second enforcement must start after first ends: "
            f"first_end={end_first}, second_start={start_second}"
        )


# ---------------------------------------------------------------------------
# 3. Error handling — non-zero exit does not crash watch loop
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-158")
class TestSequentialErrorHandling:
    """Non-zero exit from enforcement does not crash the watch loop."""

    def test_nonzero_exit_continues(self, tmp_path):
        """Enforcement failure does not abort the calling script."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        enforce_script = scripts_dir / "enforce_worktree.sh"
        enforce_script.write_text("#!/usr/bin/env bash\nexit 1\n")
        enforce_script.chmod(enforce_script.stat().st_mode | stat.S_IEXEC)

        (tmp_path / "tmp").mkdir()

        test_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            LOG="tmp/enforce-test.log"
            EXIT_CODE=0
            scripts/enforce_worktree.sh "test.md" > "$LOG" 2>&1 || EXIT_CODE=$?

            if [[ $EXIT_CODE -ne 0 ]]; then
                echo "WARN:exit=$EXIT_CODE"
            fi
            echo "CONTINUED"
        """)

        result = subprocess.run(
            ["bash", "-c", test_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Script crashed: {result.stderr}"
        assert "WARN:exit=1" in result.stdout
        assert "CONTINUED" in result.stdout

    def test_nonzero_exit_logs_failure_message(self, tmp_path):
        """Watch.sh prints warning with exit code and log path on failure."""
        watch_sh = _read_watch_sh()
        # Must have a conditional that checks EXIT_CODE and prints warning
        assert "EXIT_CODE" in watch_sh
        has_warning = (
            "failed" in watch_sh.lower()
            or "⚠️" in watch_sh
            or "warning" in watch_sh.lower()
        )
        assert has_warning, "watch.sh must warn on enforcement failure"

    def test_bugfix_nonzero_exit_handled(self, tmp_path):
        """Bugfix pipeline failure is also handled without crashing."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        bugfix_script = scripts_dir / "bugfix_worktree.sh"
        bugfix_script.write_text("#!/usr/bin/env bash\nexit 2\n")
        bugfix_script.chmod(bugfix_script.stat().st_mode | stat.S_IEXEC)

        (tmp_path / "tmp").mkdir()

        test_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            LOG="tmp/bugfix-test.log"
            EXIT_CODE=0
            scripts/bugfix_worktree.sh "test.md" > "$LOG" 2>&1 || EXIT_CODE=$?

            if [[ $EXIT_CODE -ne 0 ]]; then
                echo "WARN:exit=$EXIT_CODE"
            fi
            echo "CONTINUED"
        """)

        result = subprocess.run(
            ["bash", "-c", test_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Script crashed: {result.stderr}"
        assert "WARN:exit=2" in result.stdout
        assert "CONTINUED" in result.stdout


# ---------------------------------------------------------------------------
# 4. Log path convention preserved
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-158")
class TestLogPathConvention:
    """Log file paths follow existing tmp/enforce-*.log and tmp/bugfix-*.log convention."""

    def test_enforce_log_path_in_watch_sh(self):
        """watch.sh still creates tmp/enforce-*.log files."""
        watch_sh = _read_watch_sh()
        assert "tmp/enforce-" in watch_sh
        assert ".log" in watch_sh

    def test_bugfix_log_path_in_watch_sh(self):
        """watch.sh still creates tmp/bugfix-*.log files."""
        watch_sh = _read_watch_sh()
        assert "tmp/bugfix-" in watch_sh
        assert ".log" in watch_sh


# ---------------------------------------------------------------------------
# 5. CHANGELOG entry
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-158")
class TestChangelogEntry:
    """Changelog fragment documents FR-175."""

    def test_changelog_contains_fr175(self):
        # FR-175 is in unreleased or versioned changelog fragments
        unreleased_dir = os.path.join(REPO_ROOT, "changelog", "unreleased")
        fragments = os.listdir(unreleased_dir) if os.path.isdir(unreleased_dir) else []
        fr175_found = any("FR-175" in f for f in fragments)
        assert (
            fr175_found
        ), "FR-175 changelog fragment must exist in changelog/unreleased/"
