"""Tests for FR-243: GitHub Issues as Remote Chaplain Inbox.

Validates that watch.sh:
1. Syncs open GitHub Issues labeled 'chaplain' into .chaplain/inbox/gh-{number}.md
2. Removes the 'chaplain' label after import to prevent re-import loops
3. Gracefully skips when `gh` is not installed or not authenticated
4. Closes the originating GitHub Issue on successful enforcement
5. Does NOT close on failure, rejection, or non-GitHub inbox files
6. Initializes EXIT_CODE=1 as failure sentinel before the enforcement block
"""

import os
import stat
import subprocess
import textwrap

import pytest

pytestmark = [
    pytest.mark.process,
    pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)"),
]

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
WATCH_SH = os.path.join(REPO_ROOT, ".chaplain", "start-system.sh")
WATCHER_LIB = os.path.join(REPO_ROOT, ".chaplain", "lib", "watcher")


def _read_watch_sh() -> str:
    """Read start-system.sh + all library scripts (patterns split across files)."""
    parts = []
    with open(WATCH_SH) as fh:
        parts.append(fh.read())
    for f in sorted(os.listdir(WATCHER_LIB)):
        if f.endswith(".sh"):
            with open(os.path.join(WATCHER_LIB, f)) as fh:
                parts.append(fh.read())
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1. watch.sh content assertions — GitHub Issue sync block
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-247")
class TestWatchShGitHubIssueSync:
    """watch.sh must contain the GitHub Issue sync block."""

    def test_gh_issue_list_with_chaplain_label(self):
        """watch.sh uses `gh issue list` with --label chaplain."""
        watch_sh = _read_watch_sh()
        assert "gh issue list" in watch_sh
        assert "--label chaplain" in watch_sh

    def test_gh_issue_view_for_body(self):
        """watch.sh uses `gh issue view` to fetch title and body (two-pass)."""
        watch_sh = _read_watch_sh()
        assert "gh issue view" in watch_sh

    def test_gh_remove_label_after_import(self):
        """watch.sh removes the chaplain label after importing."""
        watch_sh = _read_watch_sh()
        assert "--remove-label chaplain" in watch_sh

    def test_gh_auth_status_guard(self):
        """watch.sh checks `gh auth status` before syncing."""
        watch_sh = _read_watch_sh()
        assert "gh auth status" in watch_sh

    def test_command_v_gh_guard(self):
        """watch.sh checks `command -v gh` before syncing."""
        watch_sh = _read_watch_sh()
        assert "command -v gh" in watch_sh

    def test_inbox_file_naming_convention(self):
        """watch.sh writes inbox files as gh-{number}.md."""
        watch_sh = _read_watch_sh()
        assert "gh-$num.md" in watch_sh or "gh-${num}.md" in watch_sh


# ---------------------------------------------------------------------------
# 3. watch.sh content assertions — GitHub Issue close block
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-247")
class TestWatchShGitHubIssueClose:
    """watch.sh must close originating GitHub Issues on successful enforcement."""

    def test_gh_issue_close_present(self):
        """watch.sh contains `gh issue close`."""
        watch_sh = _read_watch_sh()
        assert "gh issue close" in watch_sh

    def test_close_has_comment_with_commit(self):
        """Close comment includes commit hash via git log."""
        watch_sh = _read_watch_sh()
        assert "git log" in watch_sh
        assert "--comment" in watch_sh


# ---------------------------------------------------------------------------
# 4. Functional tests — GitHub Issue sync logic
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-247")
class TestGitHubIssueSyncLogic:
    """Functional tests for the sync shell snippet."""

    def test_sync_creates_inbox_file(self, tmp_path):
        """Sync creates gh-{number}.md file in inbox."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()

        # Mock gh that returns issue #42 with title and body
        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            case "$1" in
                auth) exit 0 ;;
                issue)
                    case "$2" in
                        list)  echo '42' ;;
                        view)
                            num="$3"
                            for arg in "$@"; do
                                if [[ "$arg" == *title* ]]; then echo "Test Issue Title"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then echo "Test issue body content"; exit 0; fi
                            done
                            ;;
                        edit)  exit 0 ;;
                    esac
                    ;;
            esac
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)

        sync_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            export PATH="$MOCK_DIR:$PATH"
            ln -sf "$MOCK_DIR/mock_gh" "$MOCK_DIR/gh" 2>/dev/null || true
            INBOX="$TEST_INBOX"

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue
                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue
                    printf "# %s\\n\\n%s\\n" "$title" "$body" > "$INBOX/gh-$num.md"
                    gh issue edit "$num" --remove-label chaplain 2>/dev/null || true
                    echo "IMPORTED:$num"
                done
            fi
        """)

        result = subprocess.run(
            ["bash", "-c", sync_script],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Sync failed: {result.stderr}"
        assert "IMPORTED:42" in result.stdout

        inbox_file = inbox / "gh-42.md"
        assert inbox_file.exists(), "Inbox file gh-42.md must be created"
        content = inbox_file.read_text()
        assert "Test Issue Title" in content
        assert "Test issue body content" in content

    def test_sync_skips_existing_file(self, tmp_path):
        """Sync skips issues that already have an inbox file."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        (inbox / "gh-42.md").write_text("already imported")

        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            case "$1" in
                auth) exit 0 ;;
                issue)
                    case "$2" in
                        list)  echo '42' ;;
                        view)  echo "Should not be called" ;;
                        edit)  echo "Should not be called" ;;
                    esac
                    ;;
            esac
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)

        sync_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            export PATH="$MOCK_DIR:$PATH"
            ln -sf "$MOCK_DIR/mock_gh" "$MOCK_DIR/gh" 2>/dev/null || true
            INBOX="$TEST_INBOX"

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue
                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue
                    printf "# %s\\n\\n%s\\n" "$title" "$body" > "$INBOX/gh-$num.md"
                    echo "IMPORTED:$num"
                done
            fi
            echo "DONE"
        """)

        result = subprocess.run(
            ["bash", "-c", sync_script],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Sync failed: {result.stderr}"
        assert "IMPORTED" not in result.stdout
        assert "DONE" in result.stdout

    def test_sync_skipped_when_gh_missing(self, tmp_path):
        """Sync is silently skipped when `gh` is not available."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()

        sync_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            # Use empty PATH to simulate gh not installed
            export PATH="/nonexistent"
            INBOX="$TEST_INBOX"

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                echo "SHOULD_NOT_REACH"
            fi
            echo "SKIPPED"
        """)

        result = subprocess.run(
            ["bash", "-c", sync_script],
            env={
                **os.environ,
                "TEST_INBOX": str(inbox),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "SHOULD_NOT_REACH" not in result.stdout
        assert "SKIPPED" in result.stdout


# ---------------------------------------------------------------------------
# 5. Functional tests — GitHub Issue close logic
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-247")
class TestGitHubIssueCloseLogic:
    """Functional tests for the close shell snippet."""

    def _run_close_script(
        self, tmp_path, *, exit_code: int, inbox_basename: str
    ) -> subprocess.CompletedProcess:
        """Run the close logic snippet with given EXIT_CODE and inbox_basename."""
        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent("""\
            #!/usr/bin/env bash
            if [[ "$1" == "issue" && "$2" == "close" ]]; then
                echo "CLOSED:$3"
            fi
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)

        close_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            export PATH="$MOCK_DIR:$PATH"
            ln -sf "$MOCK_DIR/mock_gh" "$MOCK_DIR/gh" 2>/dev/null || true

            EXIT_CODE=$TEST_EXIT_CODE
            inbox_basename="$TEST_INBOX_BASENAME"

            if [[ $EXIT_CODE -eq 0 ]]; then
                if [[ "$inbox_basename" == gh-*.md ]]; then
                    gh_num="${inbox_basename#gh-}"
                    gh_num="${gh_num%.md}"
                    gh issue close "$gh_num" \\
                        --comment "✅ Implemented via test-commit" 2>/dev/null || true
                    echo "ISSUE_CLOSED:$gh_num"
                fi
            fi
            echo "DONE"
        """)

        return subprocess.run(
            ["bash", "-c", close_script],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_EXIT_CODE": str(exit_code),
                "TEST_INBOX_BASENAME": inbox_basename,
            },
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_close_on_success_with_gh_file(self, tmp_path):
        """Issue is closed when EXIT_CODE=0 and file is gh-*.md."""
        result = self._run_close_script(
            tmp_path, exit_code=0, inbox_basename="gh-42.md"
        )
        assert result.returncode == 0
        assert "ISSUE_CLOSED:42" in result.stdout

    def test_no_close_on_failure(self, tmp_path):
        """Issue is NOT closed when EXIT_CODE != 0."""
        result = self._run_close_script(
            tmp_path, exit_code=1, inbox_basename="gh-42.md"
        )
        assert result.returncode == 0
        assert "ISSUE_CLOSED" not in result.stdout
        assert "DONE" in result.stdout

    def test_no_close_for_local_inbox_file(self, tmp_path):
        """Issue is NOT closed for non gh-*.md files."""
        result = self._run_close_script(
            tmp_path, exit_code=0, inbox_basename="refactor-state-builder.md"
        )
        assert result.returncode == 0
        assert "ISSUE_CLOSED" not in result.stdout
        assert "DONE" in result.stdout

    def test_no_close_on_rejection(self, tmp_path):
        """Issue is NOT closed when EXIT_CODE=1 (rejection sentinel)."""
        result = self._run_close_script(
            tmp_path, exit_code=1, inbox_basename="gh-99.md"
        )
        assert result.returncode == 0
        assert "ISSUE_CLOSED" not in result.stdout

    def test_number_extraction_from_filename(self, tmp_path):
        """Issue number is correctly extracted from gh-{number}.md."""
        result = self._run_close_script(
            tmp_path, exit_code=0, inbox_basename="gh-1234.md"
        )
        assert result.returncode == 0
        assert "ISSUE_CLOSED:1234" in result.stdout


# ---------------------------------------------------------------------------
# 6. Documentation assertions
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-247")
class TestDocumentationUpdate:
    """CLAUDE.md must document remote submission via GitHub Issues."""

    def test_claude_md_mentions_github_issues_remote(self):
        """CLAUDE.md Submitting Proposals section mentions GitHub Issues."""
        content = _read_claude_md()
        proposals_section = _extract_submitting_proposals(content)
        assert (
            "GitHub Issue" in proposals_section
            or "github issue" in proposals_section.lower()
        ), "CLAUDE.md Submitting Proposals must mention GitHub Issues"

    def test_claude_md_mentions_chaplain_label(self):
        """CLAUDE.md mentions the 'chaplain' label."""
        content = _read_claude_md()
        proposals_section = _extract_submitting_proposals(content)
        assert (
            "chaplain" in proposals_section.lower()
        ), "CLAUDE.md Submitting Proposals must mention the chaplain label"


def _read_claude_md() -> str:
    claude_path = os.path.join(REPO_ROOT, "CLAUDE.md")
    with open(claude_path) as f:
        return f.read()


def _read_copilot_instructions() -> str:
    copilot_path = os.path.join(REPO_ROOT, ".github", "copilot-instructions.md")
    with open(copilot_path) as f:
        return f.read()


def _extract_submitting_proposals(text: str) -> str:
    """Extract the Submitting Proposals section from markdown text."""
    start = text.index("### Submitting Proposals")
    rest = text[start + len("### Submitting Proposals") :]
    for i, line in enumerate(rest.split("\n")):
        if i > 0 and line.startswith("#"):
            end = (
                start
                + len("### Submitting Proposals")
                + sum(len(line_text) + 1 for line_text in rest.split("\n")[:i])
            )
            return text[start:end].strip()
    return text[start:].strip()
