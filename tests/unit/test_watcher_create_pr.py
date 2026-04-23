"""Unit tests for .chaplain/lib/watcher/create_pr.sh PR reuse behavior (FR-276).

Tests shell function logic for checking existing PRs, reusing them, and
graceful fallback to creation using mocked subprocess calls.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_create_pr_bash():
    """Load create_pr.sh as a bash script and return sourcing command."""
    script_path = (
        Path(__file__).resolve().parent.parent.parent
        / ".chaplain"
        / "lib"
        / "watcher"
        / "create_pr.sh"
    )
    return f"source {script_path}"


def _mock_environment_vars():
    """Return dict of environment variables needed by create_pr()."""
    return {
        "WT_BRANCH": "feat/test-branch",
        "PR_TITLE": "feat: test PR title",
        "PATH": "/usr/bin:/bin",  # For gh command
    }


def _extract_exported_vars(output: str) -> dict:
    """Extract PR_NUMBER and PR_URL from bash output."""
    vars_dict = {}
    for line in output.split("\n"):
        if line.startswith("EXPORTED_"):
            # Format: EXPORTED_PR_NUMBER=123
            key, value = line.split("=", 1)
            actual_key = key.replace("EXPORTED_", "")
            vars_dict[actual_key] = value
    return vars_dict


@pytest.mark.req("REQ-YG-276")
class TestCreatePrExistenceCheck:
    """AC-01: create_pr() function checks if a PR exists for the current branch before creating."""

    def test_calls_gh_pr_list_with_head_branch(self):
        """Verifies create_pr() calls 'gh pr list --head {branch}' to check for existing PRs."""
        env = _mock_environment_vars()

        calls_made = []

        def mock_run(cmd, **kwargs):
            calls_made.append(list(cmd) if isinstance(cmd, list) else cmd.split())
            if "gh pr list" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                # Return empty list (no existing PRs)
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="[]", stderr=""
                )
            elif "gh pr create" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout="https://github.com/owner/repo/pull/123",
                    stderr="",
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        # Create a wrapper script that sources create_pr.sh and calls the function with exports
        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        with patch("subprocess.run", side_effect=mock_run):
            subprocess.run(  # noqa: F841
                ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
            )

        # Check that gh pr list was called with --head parameter
        list_calls = [
            call
            for call in calls_made
            if len(call) > 2 and call[:3] == ["gh", "pr", "list"]
        ]
        assert (
            len(list_calls) >= 1
        ), f"Expected at least one 'gh pr list' call, got: {calls_made}"

        list_call = list_calls[0]
        assert (
            "--head" in list_call
        ), f"Expected --head parameter in gh pr list call: {list_call}"
        assert (
            "feat/test-branch" in list_call
        ), f"Expected branch name in call: {list_call}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrReuseExisting:
    """AC-02: If existing PR found, function reuses it and sets PR_NUMBER, PR_URL variables correctly."""

    def test_reuses_existing_pr_and_sets_variables(self):
        """When gh pr list returns existing PR, variables are set from existing PR data."""
        env = _mock_environment_vars()

        def mock_run(cmd, **kwargs):
            if "gh pr list" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                # Return existing PR data
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout='[{"number": 456, "url": "https://github.com/owner/repo/pull/456"}]',
                    stderr="",
                )
            elif "gh pr edit" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                # PR edit succeeds
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
            # Should NOT call gh pr create when PR exists
            elif "gh pr create" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                raise AssertionError(
                    "gh pr create should not be called when PR already exists"
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        with patch("subprocess.run", side_effect=mock_run):
            result = subprocess.run(
                ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
            )

        # Should succeed (returncode 0)
        assert (
            result.returncode == 0
        ), f"create_pr should succeed when reusing PR. stderr: {result.stderr}"

        # Variables should be set from existing PR
        exported_vars = _extract_exported_vars(result.stdout)
        assert (
            exported_vars.get("PR_NUMBER") == "456"
        ), f"PR_NUMBER should be 456, got: {exported_vars}"
        assert (
            exported_vars.get("PR_URL") == "https://github.com/owner/repo/pull/456"
        ), f"PR_URL incorrect: {exported_vars}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrCreatesNewWhenNoneExists:
    """AC-03: If no existing PR found, function creates new PR as before."""

    def test_creates_new_pr_when_none_exists(self):
        """When gh pr list returns empty, calls gh pr create as before."""
        env = _mock_environment_vars()

        calls_made = []

        def mock_run(cmd, **kwargs):
            calls_made.append(list(cmd) if isinstance(cmd, list) else cmd.split())
            if "gh pr list" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                # Return empty list (no existing PRs)
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="[]", stderr=""
                )
            elif "gh pr create" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout="https://github.com/owner/repo/pull/789",
                    stderr="",
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        with patch("subprocess.run", side_effect=mock_run):
            result = subprocess.run(
                ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
            )

        # Should call gh pr create
        create_calls = [
            call
            for call in calls_made
            if len(call) > 2 and call[:3] == ["gh", "pr", "create"]
        ]
        assert (
            len(create_calls) >= 1
        ), f"Expected 'gh pr create' call, got: {calls_made}"

        # Variables should be set from new PR
        exported_vars = _extract_exported_vars(result.stdout)
        assert (
            exported_vars.get("PR_NUMBER") == "789"
        ), f"PR_NUMBER should be 789, got: {exported_vars}"
        assert (
            exported_vars.get("PR_URL") == "https://github.com/owner/repo/pull/789"
        ), f"PR_URL incorrect: {exported_vars}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrNoErrorOnExistingPr:
    """AC-04: Function does not exit with error when PR already exists."""

    def test_returns_success_when_pr_already_exists(self):
        """create_pr() returns 0 exit code when reusing existing PR."""
        env = _mock_environment_vars()

        def mock_run(cmd, **kwargs):
            if "gh pr list" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                # Return existing PR
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout='[{"number": 999, "url": "https://github.com/owner/repo/pull/999"}]',
                    stderr="",
                )
            elif "gh pr edit" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXIT_CODE: $?"
        """

        with patch("subprocess.run", side_effect=mock_run):
            result = subprocess.run(
                ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
            )

        # Overall script should succeed
        assert (
            result.returncode == 0
        ), f"Script should succeed. stdout: {result.stdout}, stderr: {result.stderr}"

        # Function should return success (indicated by successful script completion)
        assert (
            "ERROR:" not in result.stderr
        ), f"Should not log errors when reusing PR: {result.stderr}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrUpdatesExistingPrTitleBody:
    """AC-05: Existing PR title/body are optionally updated to match current PR_TITLE."""

    def test_calls_gh_pr_edit_to_update_title_and_body(self):
        """When reusing existing PR, calls gh pr edit to update title and body."""
        env = _mock_environment_vars()
        env["PR_TITLE"] = "feat: updated title"

        calls_made = []

        def mock_run(cmd, **kwargs):
            calls_made.append(list(cmd) if isinstance(cmd, list) else cmd.split())
            if "gh pr list" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                return subprocess.CompletedProcess(
                    cmd,
                    returncode=0,
                    stdout='[{"number": 555, "url": "https://github.com/owner/repo/pull/555"}]',
                    stderr="",
                )
            elif "gh pr edit" in " ".join(cmd if isinstance(cmd, list) else [cmd]):
                return subprocess.CompletedProcess(
                    cmd, returncode=0, stdout="", stderr=""
                )
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        """

        with patch("subprocess.run", side_effect=mock_run):
            subprocess.run(  # noqa: F841
                ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
            )

        # Should call gh pr edit
        edit_calls = [
            call
            for call in calls_made
            if len(call) > 2 and call[:3] == ["gh", "pr", "edit"]
        ]
        assert len(edit_calls) >= 1, f"Expected 'gh pr edit' call, got: {calls_made}"

        edit_call = edit_calls[0]
        assert (
            "--title" in edit_call
        ), f"Expected --title in gh pr edit call: {edit_call}"
        assert (
            "feat: updated title" in edit_call
        ), f"Expected current PR_TITLE in call: {edit_call}"
        assert "--body" in edit_call, f"Expected --body in gh pr edit call: {edit_call}"
