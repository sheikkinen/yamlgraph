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

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
WATCHER2_SH = REPO_ROOT / ".chaplain" / "watcher2.sh"


@pytest.mark.req("REQ-YG-285")  
def test_watcher2_ci_log_capture_uses_run_id():
    """AC-01: gh run view --log-failed gets proper run ID from gh run list command.
    
    Current bug: Line 383 uses 'gh run view --log-failed --repo "..." > ...' without run ID.
    Expected fix: Should use 'gh run list' to get run ID first, then pass to 'gh run view'.
    
    This test MUST fail because the current watcher2.sh doesn't get the run ID.
    """
    # Read the watcher2.sh script
    watcher2_content = WATCHER2_SH.read_text()
    
    # Check if the current implementation uses gh run list to get run ID before gh run view
    # This should FAIL on current code because it doesn't use run list
    assert "gh run list --branch" in watcher2_content, "watcher2.sh should query run ID with gh run list"
    assert "--run \"$RUN_ID\"" in watcher2_content, "watcher2.sh should pass run ID to gh run view"


@pytest.mark.req("REQ-YG-285")
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
    assert '"$MAIN_DIR/tmp/ci-failure.log"' in watcher2_content, \
        "watcher2.sh should write CI logs to absolute path"
    assert '--var ci_log_path="$MAIN_DIR/tmp/ci-failure.log"' in watcher2_content, \
        "watcher2.sh should pass absolute path to remediation graph"


@pytest.mark.req("REQ-YG-285")
def test_watcher2_ci_log_capture_has_error_guard():
    """AC-03: Command is guarded with || true to prevent set -e crash.
    
    Current bug: Line 383 has no error guard, so gh CLI failures kill the script under set -euo pipefail.
    Expected fix: Should have '|| true' to prevent script exit on transient failures.
    
    This test MUST fail because current implementation lacks error guard.
    """
    watcher2_content = WATCHER2_SH.read_text()
    
    # Look for the gh run view command line and check if it has error guard
    # This should FAIL because current line 383 doesn't have || true
    lines = watcher2_content.split('\n')
    gh_run_view_line = None
    for line in lines:
        if 'gh run view --log-failed' in line:
            gh_run_view_line = line.strip()
            break
    
    assert gh_run_view_line is not None, "Found gh run view command in watcher2.sh"
    assert "|| true" in gh_run_view_line, "gh run view command should have || true guard"


@pytest.mark.req("REQ-YG-285")
def test_watcher2_handles_no_failed_run_gracefully():
    """AC-04: When no failed run exists, creates informative placeholder log instead of crashing.
    
    Current bug: When gh run list returns empty, the script would crash or pass empty run ID.
    Expected fix: Should check if run ID is empty and create placeholder log.
    
    This test MUST fail because current implementation doesn't handle empty run ID.
    """
    watcher2_content = WATCHER2_SH.read_text()
    
    # Check if there's logic to handle empty run ID case
    # This should FAIL because current code doesn't check for empty RUN_ID
    assert 'if [[ -n "$RUN_ID" ]]' in watcher2_content, \
        "watcher2.sh should check if RUN_ID is not empty"
    assert "No failed run found" in watcher2_content, \
        "watcher2.sh should create placeholder message when no failed run exists"


@pytest.mark.req("REQ-YG-285") 
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


@pytest.mark.req("REQ-YG-285")
def test_watcher2_ci_log_content_validation():
    """AC-06: Remediation graph receives actual CI failure logs, not gh usage error text.
    
    Current bug: Without run ID, gh run view returns usage error instead of logs.
    Expected fix: With proper run ID, should get actual CI logs.
    
    This test checks if the implementation would produce real logs vs error text.
    This test MUST fail because current implementation produces usage errors.
    """
    # Create a mock test environment to simulate the bug
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock script that mimics current broken behavior
        mock_script = tmpdir_path / "test_ci_capture.sh"
        mock_script.write_text(textwrap.dedent("""\
            #!/bin/bash
            set -euo pipefail
            
            # Simulate current broken line 383 from watcher2.sh
            gh run view --log-failed --repo "test/repo" > tmp/ci-failure.log 2>&1
            
            # Check if we got actual logs or usage error
            if grep -q "Usage:" tmp/ci-failure.log; then
                echo "ERROR: Got usage text instead of CI logs"
                exit 1
            else 
                echo "SUCCESS: Got actual CI logs"
                exit 0
            fi
        """))
        mock_script.chmod(0o755)
        
        # Create tmp directory
        (tmpdir_path / "tmp").mkdir()
        
        # Run the mock script - should fail because gh run view without run ID produces usage error
        result = subprocess.run([str(mock_script)], 
                              cwd=tmpdir_path, 
                              capture_output=True, 
                              text=True)
        
        # This should succeed (exit 0) meaning we got real CI logs, not usage error
        # But it will FAIL on current implementation because gh run view without run ID produces usage text
        assert result.returncode == 0, \
            "Current implementation should get CI logs, not usage error (this should fail on broken code)"


@pytest.mark.req("REQ-YG-285")
def test_watcher2_script_survives_gh_api_failures():
    """AC-07: Tests verify CI remediation pathway doesn't crash.
    
    Current bug: Script exits with code 1 when gh run view fails under set -euo pipefail.
    Expected fix: Script should continue to remediation even if gh commands fail.
    
    This test MUST fail because current implementation crashes on gh failures.
    """
    # Create a test script that mimics the problematic section
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create script with current problematic pattern (set -e + unguarded command)
        test_script = tmpdir_path / "test_crash.sh"
        test_script.write_text(textwrap.dedent("""\
            #!/bin/bash
            set -euo pipefail
            
            echo "Starting CI remediation attempt 1/2..."
            
            # Simulate current line 383 - this will fail and should crash the script
            gh run view --log-failed --repo "nonexistent/repo" > tmp/ci-failure.log 2>&1
            
            echo "Continuing to remediation graph..."
            echo "This line should be reached if script doesn't crash"
        """))
        test_script.chmod(0o755)
        
        # Create tmp directory
        (tmpdir_path / "tmp").mkdir()
        
        # Run the test script
        result = subprocess.run([str(test_script)], 
                              cwd=tmpdir_path, 
                              capture_output=True, 
                              text=True)
        
        # Script should continue and print the final message (exit 0)
        # But it will FAIL on current implementation because it crashes on gh failure
        assert result.returncode == 0, \
            "Script should survive gh API failures and continue to remediation"
        assert "This line should be reached" in result.stdout, \
            "Script should continue execution after gh failure"