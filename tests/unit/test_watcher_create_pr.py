"""Unit tests for .chaplain/lib/watcher/create_pr.sh PR reuse behavior (FR-276).

Tests shell function logic for checking existing PRs, reusing them, and
graceful fallback to creation using PATH-based command mocking.
"""

import subprocess
from pathlib import Path

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


def _mock_environment_vars(mock_bin_dir: str):
    """Return dict of environment variables needed by create_pr()."""
    return {
        "WT_BRANCH": "feat/test-branch",
        "PR_TITLE": "feat: test PR title",
        "PATH": f"{mock_bin_dir}:/usr/bin:/bin",  # Mock bin first in PATH
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


def _create_mock_commands(
    mock_bin_dir: Path,
    commands_log: Path,
    gh_behavior: str = "empty",
    jq_available: bool = True,
):
    """Create mock gh and jq commands that log their calls."""

    # Create mock gh command
    gh_script = mock_bin_dir / "gh"
    gh_script.write_text(f"""#!/usr/bin/env bash
# Mock gh command that logs calls and responds based on behavior
echo "gh $@" >> "{commands_log}"

case "$*" in
    "pr list --state open --head feat/test-branch --json number,url")
        case "{gh_behavior}" in
            "empty")
                echo "[]"
                ;;
            "existing")
                echo '[{{"number": 456, "url": "https://github.com/owner/repo/pull/456"}}]'
                ;;
        esac
        ;;
    "pr create --title"*)
        echo "https://github.com/owner/repo/pull/123"
        ;;
    "pr edit"*)
        # Just succeed silently for edits
        exit 0
        ;;
    *)
        echo "Unknown gh command: $*" >&2
        exit 1
        ;;
esac
""")
    gh_script.chmod(0o755)

    if jq_available:
        # Create mock jq command
        jq_script = mock_bin_dir / "jq"
        jq_script.write_text(f"""#!/usr/bin/env bash
# Mock jq command that logs calls and responds based on behavior
echo "jq $@" >> "{commands_log}"

case "$*" in
    "length")
        read input
        if [[ "$input" == "[]" ]]; then
            echo "0"
        else
            echo "1"
        fi
        ;;
    "-r .[0]")
        read input
        echo '{{"number": 456, "url": "https://github.com/owner/repo/pull/456"}}'
        ;;
    "-r .number")
        read input
        echo "456"
        ;;
    "-r .url")
        read input
        echo "https://github.com/owner/repo/pull/456"
        ;;
    *)
        echo "Unknown jq command: $*" >&2
        exit 1
        ;;
esac
""")
        jq_script.chmod(0o755)


@pytest.mark.req("REQ-YG-276")
class TestCreatePrExistenceCheck:
    """AC-01: create_pr() function checks if a PR exists for the current branch before creating."""

    def test_calls_gh_pr_list_with_head_branch(self, tmp_path):
        """Verifies create_pr() calls 'gh pr list --head {branch}' to check for existing PRs."""
        mock_bin_dir = tmp_path / "mock_bin"
        mock_bin_dir.mkdir()
        commands_log = tmp_path / "commands.log"

        _create_mock_commands(mock_bin_dir, commands_log, gh_behavior="empty")
        env = _mock_environment_vars(str(mock_bin_dir))

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        result = subprocess.run(
            ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

        # Check that gh pr list was called with --head parameter
        commands = commands_log.read_text().strip().split("\n")
        list_calls = [cmd for cmd in commands if "pr list" in cmd]
        assert (
            len(list_calls) >= 1
        ), f"Expected 'gh pr list' call, got commands: {commands}"

        list_call = list_calls[0]
        assert "--head" in list_call, f"Expected --head parameter in call: {list_call}"
        assert (
            "feat/test-branch" in list_call
        ), f"Expected branch name in call: {list_call}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrReuseExisting:
    """AC-02: If existing PR found, function reuses it and sets PR_NUMBER, PR_URL variables correctly."""

    def test_reuses_existing_pr_and_sets_variables(self, tmp_path):
        """When gh pr list returns existing PR, variables are set from existing PR data."""
        mock_bin_dir = tmp_path / "mock_bin"
        mock_bin_dir.mkdir()
        commands_log = tmp_path / "commands.log"

        _create_mock_commands(mock_bin_dir, commands_log, gh_behavior="existing")
        env = _mock_environment_vars(str(mock_bin_dir))

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        result = subprocess.run(
            ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
        )

        assert (
            result.returncode == 0
        ), f"Script should succeed when reusing PR. stderr: {result.stderr}"

        # Variables should be set from existing PR
        exported_vars = _extract_exported_vars(result.stdout)
        assert (
            exported_vars.get("PR_NUMBER") == "456"
        ), f"PR_NUMBER should be 456, got: {exported_vars}"
        assert (
            exported_vars.get("PR_URL") == "https://github.com/owner/repo/pull/456"
        ), f"PR_URL incorrect: {exported_vars}"

        # Should NOT call gh pr create when PR exists
        commands = commands_log.read_text().strip().split("\n")
        create_calls = [cmd for cmd in commands if "pr create" in cmd]
        assert (
            len(create_calls) == 0
        ), f"gh pr create should not be called when PR exists, got: {create_calls}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrCreatesNewWhenNoneExists:
    """AC-03: If no existing PR found, function creates new PR as before."""

    def test_creates_new_pr_when_none_exists(self, tmp_path):
        """When gh pr list returns empty, calls gh pr create as before."""
        mock_bin_dir = tmp_path / "mock_bin"
        mock_bin_dir.mkdir()
        commands_log = tmp_path / "commands.log"

        _create_mock_commands(mock_bin_dir, commands_log, gh_behavior="empty")
        env = _mock_environment_vars(str(mock_bin_dir))

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXPORTED_PR_NUMBER=$PR_NUMBER"
        echo "EXPORTED_PR_URL=$PR_URL"
        """

        result = subprocess.run(
            ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
        )

        assert result.returncode == 0, f"Script should succeed. stderr: {result.stderr}"

        # Should call gh pr create
        commands = commands_log.read_text().strip().split("\n")
        create_calls = [cmd for cmd in commands if "pr create" in cmd]
        assert (
            len(create_calls) >= 1
        ), f"Expected 'gh pr create' call, got commands: {commands}"

        # Variables should be set from new PR
        exported_vars = _extract_exported_vars(result.stdout)
        assert (
            exported_vars.get("PR_NUMBER") == "123"
        ), f"PR_NUMBER should be 123, got: {exported_vars}"
        assert (
            exported_vars.get("PR_URL") == "https://github.com/owner/repo/pull/123"
        ), f"PR_URL incorrect: {exported_vars}"


@pytest.mark.req("REQ-YG-276")
class TestCreatePrNoErrorOnExistingPr:
    """AC-04: Function does not exit with error when PR already exists."""

    def test_returns_success_when_pr_already_exists(self, tmp_path):
        """create_pr() returns 0 exit code when reusing existing PR."""
        mock_bin_dir = tmp_path / "mock_bin"
        mock_bin_dir.mkdir()
        commands_log = tmp_path / "commands.log"

        _create_mock_commands(mock_bin_dir, commands_log, gh_behavior="existing")
        env = _mock_environment_vars(str(mock_bin_dir))

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        echo "EXIT_CODE: $?"
        """

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

    def test_calls_gh_pr_edit_to_update_title_and_body(self, tmp_path):
        """When reusing existing PR, calls gh pr edit to update title and body."""
        mock_bin_dir = tmp_path / "mock_bin"
        mock_bin_dir.mkdir()
        commands_log = tmp_path / "commands.log"

        _create_mock_commands(mock_bin_dir, commands_log, gh_behavior="existing")
        env = _mock_environment_vars(str(mock_bin_dir))
        env["PR_TITLE"] = "feat: updated title"

        wrapper_script = f"""
        {_load_create_pr_bash()}
        log_info() {{ echo "INFO: $1"; }}
        log_error() {{ echo "ERROR: $1" >&2; }}
        create_pr
        """

        result = subprocess.run(
            ["bash", "-c", wrapper_script], env=env, capture_output=True, text=True
        )

        assert result.returncode == 0, f"Script should succeed. stderr: {result.stderr}"

        # Should call gh pr edit
        commands = commands_log.read_text().strip().split("\n")
        edit_calls = [cmd for cmd in commands if "pr edit" in cmd]
        assert (
            len(edit_calls) >= 1
        ), f"Expected 'gh pr edit' call, got commands: {commands}"

        edit_call = edit_calls[0]
        assert (
            "--title" in edit_call
        ), f"Expected --title in gh pr edit call: {edit_call}"
        assert (
            "feat: updated title" in edit_call
        ), f"Expected current PR_TITLE in call: {edit_call}"
        assert "--body" in edit_call, f"Expected --body in gh pr edit call: {edit_call}"
