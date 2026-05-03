"""Acceptance tests for FR-279: Watcher2 CI Resilience.

Tests the CI wait logic fixes and CI remediation loop functionality.
These tests target the unmodified code and MUST fail (RED phase).

AC-01: wait_ci.sh waits for all IN_PROGRESS checks before evaluating FAILURE
AC-02: CI remediation loop invokes copilot node on first CI failure
AC-03: Copilot node can read gh run view --log-failed output and apply fixes
AC-04: Maximum 2 remediation attempts before giving up
AC-05: Remediation covers syntax errors, missing changelog fragments, missing diary entries
AC-06: Existing passing pipelines are unaffected (no behavioral change when CI passes)
AC-07: Tests added for wait_ci.sh check ordering
AC-08: step-ci-remediate.yaml graph created and tested
AC-09: step-ci-remediate prompt template created in enforce/prompts/
"""

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")

REPO_ROOT = Path(__file__).parent.parent.parent
WAIT_CI_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "wait_ci.sh"
WATCHER2_SH = REPO_ROOT / ".chaplain" / "start-system.sh"
ENFORCE_DIR = REPO_ROOT / ".chaplain" / "graphs" / "watcher-enforce"
ENFORCE_PROMPTS = REPO_ROOT / ".chaplain" / "graphs" / "enforce" / "prompts"


@pytest.mark.req("REQ-YG-294")
def test_wait_ci_checks_in_progress_before_failure():
    """AC-01: wait_ci.sh waits for all IN_PROGRESS checks to complete before evaluating FAILURE.

    Current bug: FAILURE is checked before IN_PROGRESS, causing premature exits.
    Expected fix: IN_PROGRESS check should come first.

    This test MUST fail because the current wait_ci.sh has the wrong check order.
    """
    # Create test script that simulates the current wait_ci.sh logic with a progressive status
    test_script = textwrap.dedent("""\
        #!/usr/bin/env bash
        source '{wait_ci_path}'

        # Mock functions to avoid log_info errors
        log_info() {{ echo "INFO: $*"; }}
        log_error() {{ echo "ERROR: $*"; }}
        log_warn() {{ echo "WARN: $*"; }}
        export -f log_info log_error log_warn

        # Create a status file that changes over time to simulate CI progression
        status_file="/tmp/ci_status_$$"
        echo "FAILURE,IN_PROGRESS,SUCCESS" > "$status_file"

        # Mock gh pr checks that reads from the status file
        gh() {{
            if [[ "$1" == "pr" && "$2" == "checks" ]]; then
                if [[ -f "$status_file" ]]; then
                    cat "$status_file"
                    # On second call, simulate completion
                    echo "SUCCESS,SUCCESS,SUCCESS" > "$status_file"
                else
                    echo "SUCCESS,SUCCESS,SUCCESS"
                fi
            else
                echo "Mock gh command not supported"
                return 1
            fi
        }}
        export -f gh

        export PR_NUMBER=123
        CI_POLL_INTERVAL=1
        CI_TIMEOUT=10

        wait_ci
        exit_code=$?
        echo "wait_ci_exit_code:$exit_code"
        echo "CI_RESULT:$CI_RESULT"

        # Cleanup
        rm -f "$status_file"
    """).format(wait_ci_path=WAIT_CI_SH)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(test_script)
        test_script_path = f.name

    try:
        result = subprocess.run(
            ["bash", test_script_path], capture_output=True, text=True, timeout=15
        )

        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        print(f"RETURN CODE: {result.returncode}")

        # With the fix, wait_ci should wait for IN_PROGRESS to complete and then succeed
        assert (
            "wait_ci_exit_code:0" in result.stdout
        ), "FIXED: wait_ci should wait for IN_PROGRESS checks to complete before evaluating FAILURE"
        assert (
            "CI_RESULT:success" in result.stdout
        ), "FIXED: CI_RESULT should be 'success' when IN_PROGRESS completes successfully"

    finally:
        os.unlink(test_script_path)


# AC-02 (step-ci-remediate references), AC-08, AC-09 tests removed:
# step-ci-remediate.yaml and its prompt are retired (FR-305).
# CI remediation is now handled inside enforce-session.yaml.


@pytest.mark.req("REQ-YG-298")
def test_ci_remediation_max_attempts():
    """AC-04: Maximum 2 remediation attempts before giving up.

    The remediation loop should try exactly 2 times before calling handle_failure.

    This test MUST fail because the remediation loop doesn't exist yet.
    """
    with patch.dict(os.environ, {"MAIN_DIR": str(REPO_ROOT)}):
        watcher2_content = WATCHER2_SH.read_text()

        # Look for the remediation attempt counter
        # This will fail because the loop doesn't exist
        assert (
            "ci_attempt in 1 2" in watcher2_content
        ), "FIXED: start-system.sh should limit CI remediation to exactly 2 attempts"

        # Look for proper failure handling after max attempts
        assert (
            'handle_failure "CI (after remediation)"' in watcher2_content
        ), "FIXED: start-system.sh should call handle_failure with specific message after remediation fails"


@pytest.mark.req("REQ-YG-299")
def test_ci_remediation_covers_required_failure_types():
    """AC-05: Remediation covers syntax errors, missing changelog fragments, missing diary entries.

    The CI remediation should handle specific, mechanical failure types.

    This test MUST fail because the prompt and logic don't exist yet.
    """
    # Test that the prompt template covers all required failure types
    ci_remediate_prompt = ENFORCE_PROMPTS / "enforce-ci-remediate.yaml"

    if ci_remediate_prompt.exists():  # pragma: no cover
        content = ci_remediate_prompt.read_text().lower()

        failure_types = [
            "indentationerror",
            "syntax error",
            "missing changelog fragment",
            "missing diary entry",
            "changelog/unreleased/",
        ]

        for failure_type in failure_types:
            assert (
                failure_type in content
            ), f"FIXED: CI remediation prompt should handle {failure_type}"
    else:
        # This will fail because the prompt doesn't exist
        raise AssertionError("FIXED: enforce-ci-remediate.yaml prompt should exist")


@pytest.mark.req("REQ-YG-300")
def test_existing_passing_pipelines_unaffected():
    """AC-06: Existing passing pipelines are unaffected (no behavioral change when CI passes).

    When CI passes on first try, the new remediation logic should not be invoked.

    This test MUST fail because we can't verify non-regression without the implementation.
    """
    watcher2_content = WATCHER2_SH.read_text()

    # Look for conditional remediation that only triggers on CI failure
    ci_wait_section = None
    lines = watcher2_content.split("\n")
    for i, line in enumerate(lines):
        if "wait_ci" in line and "if" in line:
            ci_wait_section = "\n".join(lines[i : i + 20])
            break

    assert ci_wait_section is not None, "Should find wait_ci conditional logic"

    # The remediation should only trigger if wait_ci fails
    # This will fail because the remediation logic doesn't exist
    assert (
        "if ! wait_ci; then" in watcher2_content
    ), "FIXED: CI remediation should only trigger when wait_ci fails"
    assert (
        "CI_REMEDIATED=false" in watcher2_content
    ), "FIXED: start-system.sh should track remediation state to avoid affecting passing pipelines"


@pytest.mark.req("REQ-YG-301")
def test_wait_ci_check_ordering_structure():
    """AC-07: Tests added for wait_ci.sh check ordering.

    The wait_ci.sh logic should be structured to check IN_PROGRESS before FAILURE.

    This test MUST fail because the current check order is wrong.
    """
    wait_ci_content = WAIT_CI_SH.read_text()

    # Find the position of IN_PROGRESS and FAILURE checks
    lines = wait_ci_content.split("\n")
    in_progress_line = None
    failure_line = None

    for i, line in enumerate(lines):
        if "IN_PROGRESS" in line and "grep" in line:
            in_progress_line = i
        if (
            "FAILURE" in line
            and "grep" in line
            and 'CI_RESULT="failure"'
            in wait_ci_content[
                wait_ci_content.find(line) : wait_ci_content.find(line) + 100
            ]
        ):
            failure_line = i

    assert in_progress_line is not None, "Should find IN_PROGRESS check in wait_ci.sh"
    assert failure_line is not None, "Should find FAILURE check in wait_ci.sh"

    # This assertion will fail because currently FAILURE is checked before IN_PROGRESS
    assert (
        in_progress_line < failure_line
    ), "FIXED: IN_PROGRESS check should come before FAILURE check in wait_ci.sh"
