"""Tests for FR-217: Enforcement Pipeline Smoke Test.

Validates that the Chaplain enforcement pipeline correctly routes an
approved, zero-scope FR through the full pipeline path (not skipped,
not routed to bugfix). The FR-217 file itself is the test payload.

REQ-YG-217: Approved zero-scope FRs enter and exit the enforcement
pipeline without error — no commits, no branch, no PR produced.
"""

import os
import subprocess
import textwrap

import pytest

_FR_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "feature-requests",
    "FR-217-enforcement-pipeline-smoke-test.md",
)

_WATCH_SH_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", ".chaplain", "watch.sh"
)


def _read_fr() -> str:
    """Read the FR-217 file content."""
    with open(_FR_PATH) as f:
        return f.read()


def _read_watch_sh() -> str:
    """Read the current watch.sh content."""
    with open(_WATCH_SH_PATH) as f:
        return f.read()


@pytest.mark.req("REQ-YG-217")
class TestFR217IsValidSmokePayload:
    """Verify FR-217 is structured as a valid enforcement pipeline payload."""

    def test_fr_file_exists(self):
        """FR-217 file must exist in feature-requests/."""
        assert os.path.isfile(_FR_PATH), "FR-217 file not found"

    def test_fr_status_is_approved_or_implemented(self):
        """FR-217 must not be Rejected (so enforcement runs)."""
        content = _read_fr()
        assert "**Status:** Approved" in content or "**Status:** Implemented" in content

    def test_fr_type_is_enhancement(self):
        """FR-217 must be Enhancement type (not Bug, so standard enforce route)."""
        content = _read_fr()
        assert "**Type:** Enhancement" in content

    def test_fr_effort_is_zero(self):
        """FR-217 must have zero effort (no-op payload)."""
        content = _read_fr()
        assert "**Effort:** 0 days" in content

    def test_fr_contains_no_action_instruction(self):
        """FR-217 must contain explicit no-action instruction for enforcer."""
        content = _read_fr()
        assert "NO ACTION REQUIRED" in content


@pytest.mark.req("REQ-YG-217")
class TestWatchRoutingForSmokeTest:
    """Verify watch.sh routing would correctly handle an approved non-Bug FR."""

    def test_approved_fr_not_skipped_by_rejection_filter(self, tmp_path):
        """An approved FR passes the rejection filter (grep Status.*Rejected)."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        # Write a minimal approved FR (mirrors FR-217 structure)
        (fr_dir / "FR-217-enforcement-pipeline-smoke-test.md").write_text(
            "**Status:** Approved\n**Type:** Enhancement\n"
        )

        detect_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            before=""
            after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
            new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

            if [[ -n "$new_fr" ]]; then
                if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:rejected"
                elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:bugfix"
                else
                    echo "ROUTE:enforce"
                fi
            else
                echo "ROUTE:none"
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", detect_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "ROUTE:enforce" in result.stdout.strip()

    def test_bug_fr_routes_to_bugfix_not_enforce(self, tmp_path):
        """A Bug-type FR routes to bugfix pipeline, not standard enforce."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-999-bug.md").write_text(
            "**Status:** Approved\n**Type:** Bug\n"
        )

        detect_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            before=""
            after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
            new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

            if [[ -n "$new_fr" ]]; then
                if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:rejected"
                elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:bugfix"
                else
                    echo "ROUTE:enforce"
                fi
            else
                echo "ROUTE:none"
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", detect_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "ROUTE:bugfix" in result.stdout.strip()

    def test_rejected_fr_is_skipped(self, tmp_path):
        """A Rejected FR is skipped entirely (enforcement not triggered)."""
        fr_dir = tmp_path / "feature-requests"
        fr_dir.mkdir()
        (fr_dir / "FR-999-rejected.md").write_text(
            "**Status:** Rejected\n**Type:** Enhancement\n"
        )

        detect_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            cd "$TEST_DIR"

            before=""
            after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
            new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

            if [[ -n "$new_fr" ]]; then
                if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:rejected"
                elif grep -q 'Type.*Bug' "$new_fr" 2>/dev/null; then
                    echo "ROUTE:bugfix"
                else
                    echo "ROUTE:enforce"
                fi
            else
                echo "ROUTE:none"
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", detect_script],
            env={**os.environ, "TEST_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "ROUTE:rejected" in result.stdout.strip()


@pytest.mark.req("REQ-YG-217")
class TestWatchShThreeWayRouting:
    """Verify watch.sh implements the full three-way routing (reject/bugfix/enforce)."""

    def test_watch_sh_has_rejection_check(self):
        """watch.sh checks Status.*Rejected before routing."""
        content = _read_watch_sh()
        assert "Status.*Rejected" in content

    def test_watch_sh_has_bug_type_check(self):
        """watch.sh checks Type.*Bug for bugfix routing."""
        content = _read_watch_sh()
        assert "Type.*Bug" in content

    def test_watch_sh_has_enforce_fallthrough(self):
        """watch.sh falls through to enforce_worktree.sh for non-rejected, non-bug FRs."""
        content = _read_watch_sh()
        assert "enforce_worktree.sh" in content

    def test_routing_order_is_reject_then_bug_then_enforce(self):
        """Routing checks rejection first, then bug type, then enforce (else)."""
        content = _read_watch_sh()
        reject_pos = content.find("Status.*Rejected")
        bug_pos = content.find("Type.*Bug")
        enforce_pos = content.find("enforce_worktree.sh")
        assert reject_pos < bug_pos < enforce_pos, (
            "Routing order must be: reject → bug → enforce"
        )


@pytest.mark.req("REQ-YG-217")
class TestEnforceScriptAcceptsAnyFR:
    """Verify enforce_worktree.sh has no content-based filtering that would reject a no-op FR."""

    def test_enforce_script_does_not_filter_by_effort(self):
        """enforce_worktree.sh does not reject FRs based on effort level."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "enforce_worktree.sh",
        )
        with open(script_path) as f:
            content = f.read()
        assert "Effort" not in content, (
            "enforce_worktree.sh should not filter by effort level"
        )

    def test_enforce_script_does_not_filter_by_type(self):
        """enforce_worktree.sh does not filter by FR type (routing is in watch.sh)."""
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "enforce_worktree.sh",
        )
        with open(script_path) as f:
            content = f.read()
        # enforce_worktree.sh should not grep for Type.*Bug — that's watch.sh's job
        assert "Type.*Bug" not in content


@pytest.mark.req("REQ-YG-217")
class TestChangelogEntry:
    """Verify changelog fragment documents FR-217."""

    def test_changelog_fragment_exists(self):
        """Changelog fragment for FR-217 must exist in unreleased/."""
        fragment_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "changelog",
            "unreleased",
            "FR-217-enforcement-pipeline-smoke-test.md",
        )
        assert os.path.isfile(fragment_path), (
            "Changelog fragment for FR-217 must exist"
        )

    def test_changelog_references_req(self):
        """Changelog fragment must reference REQ-YG-217."""
        fragment_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "changelog",
            "unreleased",
            "FR-217-enforcement-pipeline-smoke-test.md",
        )
        with open(fragment_path) as f:
            content = f.read()
        assert "REQ-YG-217" in content
