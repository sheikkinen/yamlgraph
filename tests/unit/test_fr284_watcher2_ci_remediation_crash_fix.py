"""Acceptance tests for FR-284: Watcher2 CI Remediation Crash Fix.

Tests the fix for missing run ID in gh run view --log-failed command.
These tests target the unmodified code and MUST fail (RED phase).

AC-01: gh run view --log-failed gets proper run ID from gh run list --branch "$WT_BRANCH" --status failure --limit 1
AC-02: CI log capture uses absolute path "$MAIN_DIR/tmp/ci-failure.log" for consistent resolution
AC-03: Command is guarded with || true to prevent set -e crash on transient GH API failures
AC-04: When no failed run exists, creates informative placeholder log instead of crashing
AC-05: Script continues to remediation graph execution instead of exiting with code 1
AC-06: Remediation graph receives actual CI failure logs, not gh usage error text
AC-07: Tests added to verify CI remediation pathway doesn't crash
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "start-system.sh"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_ci_log_capture_uses_run_id():
    """AC-01: gh run view --log-failed gets proper run ID from gh run list command.

    Current bug: Line 383 uses 'gh run view --log-failed --repo "..." > ...' without run ID.
    Expected fix: Should use 'gh run list' to get run ID first, then pass to 'gh run view'.

    This test MUST fail because the current start-system.sh doesn't get the run ID.
    """
    # Read the start-system.sh script
    watcher2_content = WATCHER2_SH.read_text()

    # Check if the current implementation uses gh run list to get run ID before gh run view
    # This should FAIL on current code because it doesn't use run list
    assert (
        "gh run list --branch" in watcher2_content
    ), "start-system.sh should query run ID with gh run list"
    assert (
        'gh run view "$RUN_ID"' in watcher2_content
    ), "start-system.sh should pass run ID to gh run view"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_ci_log_path_uses_absolute_path():
    """AC-02: CI log capture uses absolute path "$MAIN_DIR/tmp/ci-failure.log".

    Current bug: Line 383 writes to 'tmp/ci-failure.log' (relative) from $MAIN_DIR,
                but line 388 passes 'ci_log_path="tmp/ci-failure.log"' (relative) after cd $WT_DIR.
    Expected fix: Use absolute path in both places.

    This test MUST fail because current implementation uses relative path.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Check if both the write and the variable use absolute paths
    # This should FAIL on current code because it uses relative paths
    assert (
        '"$MAIN_DIR/tmp/ci-failure.log"' in watcher2_content
    ), "start-system.sh should write CI logs to absolute path"
    assert (
        '--var ci_log_path="$CI_LOG"' in watcher2_content
    ), "start-system.sh should pass absolute path variable to remediation graph"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_ci_log_capture_has_error_guard():
    """AC-03: Command is guarded with || true to prevent set -e crash.

    Current bug: Line 383 has no error guard, so gh CLI failures kill the script under set -euo pipefail.
    Expected fix: Should have '|| true' to prevent script exit on transient failures.

    This test MUST fail because current implementation lacks error guard.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Look for the gh run view command line and check if it has error guard
    # This should FAIL because current line 383 doesn't have || true
    lines = watcher2_content.split("\n")
    gh_run_view_line = None
    for line in lines:
        if "gh run view" in line and "--log-failed" in line:
            gh_run_view_line = line.strip()
            break

    assert gh_run_view_line is not None, "Found gh run view command in start-system.sh"
    assert (
        "|| true" in gh_run_view_line or "2>/dev/null" in gh_run_view_line
    ), "gh run view command should have || true guard or stderr suppression"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_handles_no_failed_run_gracefully():
    """AC-04: When no failed run exists, creates informative placeholder log instead of crashing.

    Current bug: When gh run list returns empty, the script would crash or pass empty run ID.
    Expected fix: Should check if run ID is empty and create placeholder log.

    This test MUST fail because current implementation doesn't handle empty run ID.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Check if there's logic to handle empty run ID case
    # This should FAIL because current code doesn't check for empty RUN_ID
    assert (
        '-n "$RUN_ID"' in watcher2_content
    ), "start-system.sh should check if RUN_ID is not empty"
    assert (
        "No failed run found" in watcher2_content
    ), "start-system.sh should create placeholder message when no failed run exists"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_ci_remediation_section_exists():
    """AC-05: Script continues to remediation graph execution instead of exiting.

    This verifies the CI remediation section exists in the expected location.
    The test should pass - this is testing structure, not the bug.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Verify the CI remediation loop structure exists
    assert "CI failed — remediation attempt" in watcher2_content
    assert "step-ci-remediate.yaml" in watcher2_content
    assert "ci_log_path=" in watcher2_content


@pytest.mark.req("REQ-YG-307")
def test_watcher2_ci_log_content_validation():
    """AC-06: Remediation graph receives actual CI failure logs, not gh usage error text.

    Current bug: Without run ID, gh run view returns usage error instead of logs.
    Expected fix: With proper run ID, should get actual CI logs.

    This test checks that the implementation gets run ID before calling gh run view.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Verify the gh run list call appears before gh run view in the remediation block
    run_list_pos = watcher2_content.find("gh run list --branch")
    run_view_pos = watcher2_content.find('gh run view "$RUN_ID"')

    assert run_list_pos > 0, "Should have gh run list call"
    assert run_view_pos > 0, "Should have gh run view with RUN_ID"
    assert run_list_pos < run_view_pos, "gh run list should appear before gh run view"


@pytest.mark.req("REQ-YG-307")
def test_watcher2_script_survives_gh_api_failures():
    """AC-07: Tests verify CI remediation pathway doesn't crash.

    Current bug: Script exits with code 1 when gh run view fails under set -euo pipefail.
    Expected fix: Script should continue to remediation even if gh commands fail.

    This test verifies the fix: || true guards prevent set -e crash.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Find all gh run commands in the remediation block and verify they have guards
    lines = watcher2_content.split("\n")
    in_remediation = False
    gh_commands = []
    for line in lines:
        if "remediation attempt" in line:
            in_remediation = True
        if in_remediation and "gh run" in line:
            gh_commands.append(line.strip())
        if in_remediation and "CI_REMEDIATED" in line:
            break

    assert (
        len(gh_commands) >= 2
    ), "Should have at least 2 gh run commands in remediation block"
    for cmd in gh_commands:
        assert (
            "|| true" in cmd or "2>/dev/null" in cmd
        ), f"gh command should be guarded: {cmd}"
