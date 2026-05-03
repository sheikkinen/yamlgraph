"""Acceptance tests for FR-275: Watcher2 should reuse existing PRs.

Tests the enhanced create_pr.sh functionality to check for existing PRs
before creating new ones, following the TDD RED-GREEN-REFACTOR pattern.

Testing approach:
- Mock bash subprocess calls to simulate `gh pr list` and `gh pr create` responses
- Test both code paths: existing PR found and new PR creation
- Verify environment variable setting (PR_NUMBER, PR_URL)
- Assert proper logging behavior
- Test error handling for network failures

All tests target the unmodified code and MUST fail (RED phase).
"""

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")

pytestmark = pytest.mark.slow

REPO_ROOT = Path(__file__).parent.parent.parent
CREATE_PR_SH = REPO_ROOT / ".chaplain" / "lib" / "watcher" / "create_pr.sh"

# Shell test harness that sources create_pr.sh and executes function
_TEST_HARNESS = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail

    # Source the create_pr.sh library (also sources common.sh)
    source "{create_pr_path}"

    # Override log functions AFTER sourcing (common.sh defines them with emoji to stderr)
    log_info() {{ echo "INFO: $1"; }}
    log_error() {{ echo "ERROR: $1" >&2; }}

    # Set required environment variables
    export WT_BRANCH="$1"
    export PR_TITLE="$2"

    # Run create_pr function and capture results
    if create_pr; then
        echo "CREATE_PR_SUCCESS=true"
        echo "PR_NUMBER=$PR_NUMBER"
        echo "PR_URL=$PR_URL"
        exit 0
    else
        echo "CREATE_PR_SUCCESS=false"
        exit 1
    fi
""")


def _run_create_pr_test(
    wt_branch: str,
    pr_title: str,
    gh_list_response: str = "",
    gh_list_returncode: int = 0,
    gh_create_response: str = "",
    gh_create_returncode: int = 0,
    gh_edit_returncode: int = 0,
) -> subprocess.CompletedProcess:
    """
    Run create_pr() function with mocked gh CLI responses.

    Returns the subprocess result with stdout containing:
    - CREATE_PR_SUCCESS=true|false
    - PR_NUMBER=<number>
    - PR_URL=<url>
    """

    # Write test script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(_TEST_HARNESS.format(create_pr_path=CREATE_PR_SH))
        test_script = f.name

    try:
        # Mock the gh CLI commands in the subprocess environment
        env = os.environ.copy()

        # Create a mock gh script that responds appropriately
        gh_mock_dir = Path(tempfile.mkdtemp())
        gh_mock_script = gh_mock_dir / "gh"

        gh_mock_content = textwrap.dedent(f"""\
            #!/usr/bin/env bash
            if [[ "$1 $2 $3" == "pr list --state" ]]; then
                echo '{gh_list_response}'
                exit {gh_list_returncode}
            elif [[ "$1 $2 $3" == "pr create --title" ]]; then
                echo '{gh_create_response}'
                exit {gh_create_returncode}
            elif [[ "$1 $2 $3" == "pr edit" ]]; then
                exit {gh_edit_returncode}
            else
                echo "Mock gh: Unknown command: $*" >&2
                exit 1
            fi
        """)

        gh_mock_script.write_text(gh_mock_content)
        gh_mock_script.chmod(0o755)

        # Put mock gh in PATH
        env["PATH"] = f"{gh_mock_dir}:{env['PATH']}"

        # Run the test
        result = subprocess.run(
            ["bash", test_script, wt_branch, pr_title],
            capture_output=True,
            text=True,
            env=env,
        )
        return result
    finally:
        os.unlink(test_script)
        # Clean up mock gh
        if "gh_mock_dir" in locals():
            import shutil

            shutil.rmtree(gh_mock_dir)


@pytest.mark.req("REQ-YG-272")
class TestCreatePrExistingCheck:
    """AC-01: create_pr.sh checks if a PR exists for $WT_BRANCH before attempting to create one."""

    def test_checks_existing_pr_before_create(self):
        """Should call 'gh pr list --state open --head $WT_BRANCH' before 'gh pr create'."""
        # This test MUST fail on current implementation - it doesn't check for existing PRs
        result = _run_create_pr_test(
            wt_branch="feat/test-branch",
            pr_title="Test PR Title",
            gh_list_response="",  # No existing PR
            gh_create_response="https://github.com/owner/repo/pull/42",
        )

        # Current code should fail because it doesn't check for existing PRs
        # We expect this test to FAIL until implementation is added
        assert (
            "INFO: Checking for existing PR on branch: feat/test-branch"
            in result.stdout
        )


@pytest.mark.req("REQ-YG-272")
class TestCreatePrReuseExisting:
    """AC-02: If an existing open PR is found, it reuses the PR number and URL instead of creating a new one."""

    def test_reuses_existing_pr_when_found(self):
        """Should reuse existing PR without calling gh pr create."""
        existing_pr_json = '{"number": 123, "url": "https://github.com/owner/repo/pull/123", "title": "Existing PR"}'

        result = _run_create_pr_test(
            wt_branch="feat/test-branch",
            pr_title="Test PR Title",
            gh_list_response=existing_pr_json,
            gh_create_returncode=1,  # Should not be called
        )

        # Current code should fail - it always calls gh pr create
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert "PR_NUMBER=123" in result.stdout
        assert "PR_URL=https://github.com/owner/repo/pull/123" in result.stdout
        assert "INFO: Reusing existing PR:" in result.stdout


@pytest.mark.req("REQ-YG-272")
class TestCreatePrNewWhenNoneExists:
    """AC-03: If no existing PR is found, it creates a new PR as before."""

    def test_creates_new_pr_when_none_exists(self):
        """Should create new PR when gh pr list returns empty result."""
        result = _run_create_pr_test(
            wt_branch="feat/new-branch",
            pr_title="New PR Title",
            gh_list_response="",  # No existing PRs
            gh_create_response="https://github.com/owner/repo/pull/456",
        )

        # This might pass on current code, but we need proper checking logic
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert "PR_NUMBER=456" in result.stdout
        assert "PR_URL=https://github.com/owner/repo/pull/456" in result.stdout
        assert "INFO: Creating new PR:" in result.stdout


@pytest.mark.req("REQ-YG-272")
class TestCreatePrVariablesSetting:
    """AC-04: The function sets PR_NUMBER and PR_URL variables correctly in both cases."""

    def test_sets_variables_for_existing_pr(self):
        """Should set PR_NUMBER and PR_URL from existing PR JSON."""
        existing_pr_json = '{"number": 789, "url": "https://github.com/owner/repo/pull/789", "title": "Old PR"}'

        result = _run_create_pr_test(
            wt_branch="feat/existing-branch",
            pr_title="Updated Title",
            gh_list_response=existing_pr_json,
        )

        # Current code should fail - no logic to parse existing PR JSON
        assert "PR_NUMBER=789" in result.stdout
        assert "PR_URL=https://github.com/owner/repo/pull/789" in result.stdout

    def test_sets_variables_for_new_pr(self):
        """Should set PR_NUMBER and PR_URL from gh pr create output."""
        result = _run_create_pr_test(
            wt_branch="feat/new-branch",
            pr_title="New PR",
            gh_list_response="",
            gh_create_response="https://github.com/owner/repo/pull/999",
        )

        # This tests current behavior - should pass if existing logic works
        assert "PR_NUMBER=999" in result.stdout
        assert "PR_URL=https://github.com/owner/repo/pull/999" in result.stdout


@pytest.mark.req("REQ-YG-272")
class TestCreatePrGhListPattern:
    """AC-05: Existing PR detection uses gh pr list --state open --head pattern (consistent with watch.sh)."""

    @pytest.mark.xfail(
        reason="Test design flaw: mocks subprocess.run for bash script behavior"
    )
    def test_uses_correct_gh_list_pattern(self):
        """Should call exactly: gh pr list --state open --head $WT_BRANCH --json number,url,title."""
        # This test verifies the specific command pattern used
        # Current code should fail - no such command exists

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                [],
                0,
                '{"number": 100, "url": "https://github.com/test/test/pull/100", "title": "Test"}',
                "",
            )

            _run_create_pr_test(
                wt_branch="feat/pattern-test",
                pr_title="Pattern Test PR",
                gh_list_response='{"number": 100, "url": "https://github.com/test/test/pull/100", "title": "Test"}',
            )

            # Verify the exact command was called
            expected_cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--head",
                "feat/pattern-test",
                "--json",
                "number,url,title",
                "--jq",
                ".[0] | select(.number != null)",
            ]

            # Should fail - current code doesn't make this call
            mock_run.assert_any_call(expected_cmd, capture_output=True, text=True)


@pytest.mark.req("REQ-YG-272")
class TestCreatePrLogging:
    """AC-06: Function logs clearly whether it's reusing an existing PR or creating a new one."""

    def test_logs_reusing_existing_pr(self):
        """Should log when reusing existing PR with PR details."""
        existing_pr_json = '{"number": 555, "url": "https://github.com/owner/repo/pull/555", "title": "Existing"}'

        result = _run_create_pr_test(
            wt_branch="feat/log-test",
            pr_title="Log Test",
            gh_list_response=existing_pr_json,
        )

        # Current code should fail - no such logging exists
        assert (
            "INFO: Reusing existing PR: https://github.com/owner/repo/pull/555 (#555)"
            in result.stdout
        )

    def test_logs_creating_new_pr(self):
        """Should log when creating new PR."""
        result = _run_create_pr_test(
            wt_branch="feat/new-log-test",
            pr_title="New Log Test",
            gh_list_response="",
            gh_create_response="https://github.com/owner/repo/pull/777",
        )

        # This might work with current logging
        assert "INFO: Creating new PR: New Log Test" in result.stdout


@pytest.mark.req("REQ-YG-272")
class TestCreatePrErrorHandling:
    """AC-07: Error handling remains robust — network failures don't crash the pipeline."""

    def test_handles_gh_list_failure_gracefully(self):
        """Should handle network failure in gh pr list and proceed to create."""
        result = _run_create_pr_test(
            wt_branch="feat/error-test",
            pr_title="Error Test",
            gh_list_returncode=1,  # gh pr list fails
            gh_create_response="https://github.com/owner/repo/pull/888",
        )

        # Should gracefully fall back to creating new PR
        # Current code should fail - no error handling for gh pr list
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert "PR_NUMBER=888" in result.stdout

    def test_handles_gh_create_failure(self):
        """Should handle failure in gh pr create with proper error."""
        result = _run_create_pr_test(
            wt_branch="feat/create-fail",
            pr_title="Create Fail Test",
            gh_list_response="",
            gh_create_returncode=1,
            gh_create_response="Error: PR already exists",
        )

        # Should fail and return error - current behavior should work
        assert "CREATE_PR_SUCCESS=false" in result.stdout
        assert "ERROR: Failed to create PR:" in result.stderr


@pytest.mark.req("REQ-YG-272")
class TestCreatePrTitleUpdate:
    """AC-08: Optional feature to update PR title if different (nice-to-have)."""

    def test_updates_pr_title_when_different(self):
        """Should update PR title when existing title differs from new title."""
        existing_pr_json = '{"number": 666, "url": "https://github.com/owner/repo/pull/666", "title": "Old Title"}'

        result = _run_create_pr_test(
            wt_branch="feat/title-update",
            pr_title="New Different Title",
            gh_list_response=existing_pr_json,
            gh_edit_returncode=0,
        )

        # Current code should fail - no title update logic
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert (
            "INFO: Updating PR title from 'Old Title' to 'New Different Title'"
            in result.stdout
        )

    def test_skips_title_update_when_same(self):
        """Should not call gh pr edit when titles are identical."""
        existing_pr_json = '{"number": 777, "url": "https://github.com/owner/repo/pull/777", "title": "Same Title"}'

        result = _run_create_pr_test(
            wt_branch="feat/same-title",
            pr_title="Same Title",
            gh_list_response=existing_pr_json,
            gh_edit_returncode=1,  # Should not be called
        )

        # Should not attempt to update title when same
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert "Updating PR title" not in result.stdout


@pytest.mark.req("REQ-YG-272")
class TestCreatePrIntegration:
    """AC-09: Manual testing confirms watcher2 handles pre-existing PRs gracefully."""

    def test_integration_with_watcher2_environment_variables(self):
        """Should work with environment variables as set by start-system.sh."""
        # Test that the function integrates properly with watcher2 expectations
        # This validates the interface contract

        result = _run_create_pr_test(
            wt_branch="feat/watcher2-integration",
            pr_title="feat: watcher2 enforce — FR-275",  # Typical watcher2 PR title format
            gh_list_response="",
            gh_create_response="https://github.com/sheikkinen/yamlgraph/pull/185",
        )

        # Should work with watcher2's expected variables and title format
        assert "CREATE_PR_SUCCESS=true" in result.stdout
        assert "PR_NUMBER=185" in result.stdout
        assert (
            "PR_URL=https://github.com/sheikkinen/yamlgraph/pull/185" in result.stdout
        )
