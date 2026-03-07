"""Unit tests for watch.sh → enforce_worktree.sh integration (FR-116).

Tests the post-graph hook in watch.sh that detects new feature request files
and spawns enforce_worktree.sh in the background via nohup.

The detection logic is pure shell (ls + comm -13), so tests exercise it
via subprocess with temporary directory structures.
"""

import contextlib
import os
import stat
import subprocess
import textwrap

import pytest

# Shell snippet that mirrors the detection logic added to watch.sh.
# We test this in isolation so we don't need the full watch loop or yamlgraph.
_DETECT_SCRIPT = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    cd "$TEST_DIR"

    # Simulate "before" snapshot (passed via env)
    before="$BEFORE_SNAPSHOT"

    # Simulate "after" snapshot (find is safe with empty dirs unlike ls glob)
    after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)

    # Detect new FR
    new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

    if [[ -n "$new_fr" ]]; then
        if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
            echo "SKIPPED:$new_fr"
        else
            echo "SPAWN:$new_fr"
            mkdir -p tmp
            echo "MKDIR_OK"
        fi
    else
        echo "NO_NEW_FR"
    fi
""")


def _run_detect(test_dir: str, before_snapshot: str) -> str:
    """Run the detection script and return stdout."""
    result = subprocess.run(
        ["bash", "-c", _DETECT_SCRIPT],
        env={
            **os.environ,
            "TEST_DIR": str(test_dir),
            "BEFORE_SNAPSHOT": before_snapshot,
        },
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


@pytest.mark.req("REQ-YG-116")
class TestFRDetection:
    """Tests for new FR detection via ls + comm -13."""

    def test_no_new_fr_detected(self, tmp_path):
        """When no new FR files appear, output is NO_NEW_FR."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-001-existing.md").write_text("**Status:** Approved\n")

        before = "feature-requests/FR-001-existing.md"
        output = _run_detect(str(tmp_path), before)
        assert output == "NO_NEW_FR"

    def test_new_fr_detected(self, tmp_path):
        """When a new FR appears after graph run, it is detected for spawn."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-001-existing.md").write_text("**Status:** Approved\n")
        (fr_dir / "FR-116-new-feature.md").write_text("**Status:** Approved\n")

        before = "feature-requests/FR-001-existing.md"
        output = _run_detect(str(tmp_path), before)
        assert "SPAWN:feature-requests/FR-116-new-feature.md" in output
        assert "MKDIR_OK" in output

    def test_empty_feature_requests_before_and_after(self, tmp_path):
        """When feature-requests/ is empty before and after, no detection."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()

        output = _run_detect(str(tmp_path), "")
        assert output == "NO_NEW_FR"


@pytest.mark.req("REQ-YG-116")
class TestRejectedFRSkip:
    """Tests that rejected FRs are skipped with log message."""

    def test_rejected_fr_is_skipped(self, tmp_path):
        """FR with Status.*Rejected in content is skipped."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-200-rejected.md").write_text(
            "# FR\n\n**Status:** Rejected\n\nNot viable.\n"
        )

        output = _run_detect(str(tmp_path), "")
        assert "SKIPPED:feature-requests/FR-200-rejected.md" in output

    def test_approved_fr_is_not_skipped(self, tmp_path):
        """FR with Status: Approved is spawned, not skipped."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-201-approved.md").write_text(
            "# FR\n\n**Status:** Approved\n\nGood to go.\n"
        )

        output = _run_detect(str(tmp_path), "")
        assert "SPAWN:feature-requests/FR-201-approved.md" in output

    def test_status_rejected_with_bold_markdown(self, tmp_path):
        """Bold markdown status format (**Status:** Rejected) is detected."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-202-bold.md").write_text(
            "**Priority:** HIGH\n**Status:** Rejected\n"
        )

        output = _run_detect(str(tmp_path), "")
        assert "SKIPPED:feature-requests/FR-202-bold.md" in output


@pytest.mark.req("REQ-YG-116")
class TestLogDirectory:
    """Tests that tmp/ directory is created for enforce logs."""

    def test_mkdir_p_tmp_on_spawn(self, tmp_path):
        """tmp/ directory is created when spawning enforce."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-300-new.md").write_text("**Status:** Approved\n")

        output = _run_detect(str(tmp_path), "")
        assert "MKDIR_OK" in output
        assert (tmp_path / "tmp").is_dir()

    def test_mkdir_p_tmp_idempotent(self, tmp_path):
        """mkdir -p tmp succeeds even if tmp/ already exists."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (tmp_path / "tmp").mkdir()
        (fr_dir / "FR-301-new.md").write_text("**Status:** Approved\n")

        output = _run_detect(str(tmp_path), "")
        assert "MKDIR_OK" in output


@pytest.mark.req("REQ-YG-116")
class TestNohupSpawnIsolation:
    """Tests that enforce is spawned via nohup in background."""

    def test_nohup_spawn_does_not_block(self, tmp_path):
        """Spawned enforce process does not block the caller."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-400-spawn.md").write_text("**Status:** Approved\n")

        # Create a mock enforce script that sleeps (simulates long-running)
        enforce_script = tmp_path / "scripts" / "enforce_worktree.sh"
        enforce_script.parent.mkdir(parents=True)
        enforce_script.write_text("#!/usr/bin/env bash\nsleep 60\n")
        enforce_script.chmod(enforce_script.stat().st_mode | stat.S_IEXEC)

        # Script that spawns enforce via nohup (mirrors watch.sh logic)
        spawn_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            before=""
            after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
            new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

            if [[ -n "$new_fr" ]]; then
                if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
                    echo "SKIPPED"
                else
                    mkdir -p tmp
                    LOG="tmp/enforce-$(basename "$new_fr" .md).log"
                    nohup scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 &
                    ENFORCE_PID=$!
                    echo "PID:$ENFORCE_PID"
                    echo "LOG:$LOG"
                fi
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", spawn_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=5,  # Must complete quickly — enforce is backgrounded
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        output = result.stdout.strip()

        # Verify PID was reported (enforce is running in background)
        assert "PID:" in output
        pid_line = [line for line in output.split("\n") if line.startswith("PID:")][0]
        pid = int(pid_line.split(":")[1])
        assert pid > 0

        # Verify log path follows convention
        assert "LOG:tmp/enforce-FR-400-spawn.log" in output

        # Clean up the sleeping background process
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, 9)

    def test_enforce_log_path_derived_from_fr_slug(self, tmp_path):
        """Log file path is tmp/enforce-<slug>.log based on FR filename."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-116-enforce-worktree-watch-integration.md").write_text(
            "**Status:** Approved\n"
        )

        enforce_script = tmp_path / "scripts" / "enforce_worktree.sh"
        enforce_script.parent.mkdir(parents=True)
        enforce_script.write_text("#!/usr/bin/env bash\nexit 0\n")
        enforce_script.chmod(enforce_script.stat().st_mode | stat.S_IEXEC)

        spawn_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            before=""
            after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
            new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

            if [[ -n "$new_fr" ]]; then
                mkdir -p tmp
                LOG="tmp/enforce-$(basename "$new_fr" .md).log"
                nohup scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 &
                echo "LOG:$LOG"
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", spawn_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert (
            "LOG:tmp/enforce-FR-116-enforce-worktree-watch-integration.log"
            in result.stdout
        )


@pytest.mark.req("REQ-YG-116")
class TestWatchShellIntegration:
    """Integration test verifying watch.sh contains the enforce spawn logic."""

    def test_watch_sh_snapshots_before_graph(self):
        """watch.sh captures feature-requests/ listing before graph run."""
        watch_sh = _read_watch_sh()
        assert "before=$(" in watch_sh and "feature-requests" in watch_sh

    def test_watch_sh_diffs_after_graph(self):
        """watch.sh uses comm -13 to detect new FR files."""
        watch_sh = _read_watch_sh()
        assert "comm -13" in watch_sh

    def test_watch_sh_checks_rejected_status(self):
        """watch.sh greps for rejected status before spawning."""
        watch_sh = _read_watch_sh()
        assert "Status.*Rejected" in watch_sh

    def test_watch_sh_uses_nohup_background(self):
        """watch.sh spawns enforce with nohup and & for background."""
        watch_sh = _read_watch_sh()
        assert "nohup" in watch_sh
        assert "enforce_worktree.sh" in watch_sh

    def test_watch_sh_creates_log_directory(self):
        """watch.sh creates tmp/ directory for logs."""
        watch_sh = _read_watch_sh()
        assert "mkdir -p tmp" in watch_sh

    def test_watch_sh_redirects_enforce_output_to_log(self):
        """watch.sh redirects enforce output to tmp/enforce-*.log."""
        watch_sh = _read_watch_sh()
        assert "tmp/enforce-" in watch_sh
        assert ".log" in watch_sh


@pytest.mark.req("REQ-YG-116")
class TestChangelogEntry:
    """Verify CHANGELOG.md documents FR-116."""

    def test_changelog_contains_fr116_entry(self):
        """CHANGELOG.md must have an FR-116 entry."""
        changelog = _read_changelog()
        assert "FR-116" in changelog

    def test_changelog_fr116_in_unreleased_section(self):
        """FR-116 entry must appear in the [Unreleased] section."""
        changelog = _read_changelog()
        unreleased_start = changelog.index("[Unreleased]")
        # Find the next versioned section (pattern: ## [x.y.z])
        next_section = changelog.find("\n## [0.", unreleased_start)
        unreleased_block = changelog[unreleased_start:next_section]
        assert "FR-116" in unreleased_block

    def test_changelog_fr116_describes_watch_enforce_integration(self):
        """FR-116 entry must mention key implementation details."""
        changelog = _read_changelog()
        # Must reference the core components
        assert "watch.sh" in changelog or "watch→enforce" in changelog.lower()
        assert "enforce_worktree.sh" in changelog or "enforce" in changelog

    def test_changelog_fr116_references_requirement(self):
        """FR-116 entry must reference REQ-YG-116."""
        changelog = _read_changelog()
        assert "REQ-YG-116" in changelog


def _read_watch_sh() -> str:
    """Read the current watch.sh content."""
    watch_path = os.path.join(
        os.path.dirname(__file__), "..", "..", ".chaplain", "watch.sh"
    )
    with open(watch_path) as f:
        return f.read()


def _read_changelog() -> str:
    """Read the current CHANGELOG.md content."""
    changelog_path = os.path.join(os.path.dirname(__file__), "..", "..", "CHANGELOG.md")
    with open(changelog_path) as f:
        return f.read()
