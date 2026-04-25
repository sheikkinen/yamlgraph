"""Tests for FR-251: Harden GitHub Issues Remote Inbox.

Validates that watch.sh:
1. Checks issue author against .chaplain/allowed-authors.txt before import
2. Truncates issue body at 10,000 characters
3. Prepends <!-- author: @username --> audit header to imported files
4. Gracefully accepts all authors when allowed-authors.txt is missing
5. Leaves the chaplain label on skipped (untrusted) issues
"""

import os
import stat
import subprocess
import textwrap

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
WATCH_SH = os.path.join(REPO_ROOT, ".chaplain", "watcher2.sh")
WATCHER_LIB = os.path.join(REPO_ROOT, ".chaplain", "lib", "watcher")


def _read_watch_sh() -> str:
    """Read watcher2.sh + all library scripts."""
    with open(WATCH_SH) as fh:
        parts = [fh.read()]
    for f in sorted(os.listdir(WATCHER_LIB)):
        if f.endswith(".sh"):
            with open(os.path.join(WATCHER_LIB, f)) as fh:
                parts.append(fh.read())
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1. watch.sh content assertions — Author allowlist
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestWatchShAuthorAllowlist:
    """watch.sh must gate imports on allowed-authors.txt."""

    def test_allowed_authors_file_referenced(self):
        """watch.sh references allowed-authors.txt."""
        watch_sh = _read_watch_sh()
        assert "allowed-authors.txt" in watch_sh

    def test_author_login_fetched(self):
        """watch.sh fetches author login via gh issue view."""
        watch_sh = _read_watch_sh()
        assert "author" in watch_sh
        assert ".login" in watch_sh or "author.login" in watch_sh

    def test_grep_allowlist_check(self):
        """watch.sh uses grep to check author against allowlist."""
        watch_sh = _read_watch_sh()
        assert "grep" in watch_sh
        assert "allowed-authors" in watch_sh

    def test_untrusted_author_warning(self):
        """watch.sh logs a warning for untrusted authors."""
        watch_sh = _read_watch_sh()
        assert "untrusted author" in watch_sh.lower() or "Skipped issue" in watch_sh


# ---------------------------------------------------------------------------
# 2. watch.sh content assertions — Body size cap
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestWatchShBodySizeCap:
    """watch.sh must truncate oversized issue bodies."""

    def test_body_size_cap_defined(self):
        """watch.sh defines BODY_SIZE_CAP."""
        watch_sh = _read_watch_sh()
        assert "BODY_SIZE_CAP" in watch_sh

    def test_body_size_cap_is_10000(self):
        """BODY_SIZE_CAP is set to 10000."""
        watch_sh = _read_watch_sh()
        assert "BODY_SIZE_CAP=10000" in watch_sh

    def test_body_truncation_logic(self):
        """watch.sh truncates body when exceeding cap."""
        watch_sh = _read_watch_sh()
        assert "BODY_SIZE_CAP" in watch_sh
        assert "truncat" in watch_sh.lower()


# ---------------------------------------------------------------------------
# 3. watch.sh content assertions — Audit header
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestWatchShAuditHeader:
    """watch.sh must prepend author audit header to imported files."""

    def test_audit_header_in_printf(self):
        """watch.sh printf includes <!-- author: @... --> header."""
        watch_sh = _read_watch_sh()
        assert "<!-- author:" in watch_sh


# ---------------------------------------------------------------------------
# 4. Functional tests — Author allowlist
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestAuthorAllowlistLogic:
    """Functional tests for author allowlist filtering."""

    def _make_mock_gh(self, tmp_path, *, author: str = "trusteduser"):
        """Create a mock gh script that returns a configurable author."""
        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent(f"""\
            #!/usr/bin/env bash
            case "$1" in
                auth) exit 0 ;;
                issue)
                    case "$2" in
                        list)  echo '42' ;;
                        view)
                            num="$3"
                            for arg in "$@"; do
                                if [[ "$arg" == *author* ]]; then echo "{author}"; exit 0; fi
                                if [[ "$arg" == *title* ]]; then echo "Test Title"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then echo "Test body"; exit 0; fi
                            done
                            ;;
                        edit)  exit 0 ;;
                    esac
                    ;;
            esac
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)
        return mock_gh

    def _sync_script(self):
        """Return the sync script snippet with FR-251 hardening."""
        return textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            export PATH="$MOCK_DIR:$PATH"
            ln -sf "$MOCK_DIR/mock_gh" "$MOCK_DIR/gh" 2>/dev/null || true
            INBOX="$TEST_INBOX"
            SCRIPT_DIR="$TEST_SCRIPT_DIR"
            ALLOWED_AUTHORS="$SCRIPT_DIR/allowed-authors.txt"
            BODY_SIZE_CAP=10000

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue

                    author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
                    if [[ -f "$ALLOWED_AUTHORS" ]] && ! grep -qxF "$author" "$ALLOWED_AUTHORS"; then
                        echo "SKIPPED_UNTRUSTED:$num:$author"
                        continue
                    fi

                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

                    if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
                        echo "TRUNCATED:$num:${#body}:$BODY_SIZE_CAP"
                        body="${body:0:$BODY_SIZE_CAP}"
                    fi

                    printf "<!-- author: @%s -->\\n# %s\\n\\n%s\\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
                    gh issue edit "$num" --remove-label chaplain 2>/dev/null || true
                    echo "IMPORTED:$num"
                done
            fi
        """)

    def test_allowed_author_imported(self, tmp_path):
        """Issue from an allowed author is imported."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()
        (script_dir / "allowed-authors.txt").write_text("trusteduser\n")

        self._make_mock_gh(tmp_path, author="trusteduser")
        result = subprocess.run(
            ["bash", "-c", self._sync_script()],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
                "TEST_SCRIPT_DIR": str(script_dir),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IMPORTED:42" in result.stdout
        assert (inbox / "gh-42.md").exists()

    def test_untrusted_author_skipped(self, tmp_path):
        """Issue from an unlisted author is skipped."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()
        (script_dir / "allowed-authors.txt").write_text("trusteduser\n")

        self._make_mock_gh(tmp_path, author="untrusteduser")
        result = subprocess.run(
            ["bash", "-c", self._sync_script()],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
                "TEST_SCRIPT_DIR": str(script_dir),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "SKIPPED_UNTRUSTED:42:untrusteduser" in result.stdout
        assert not (inbox / "gh-42.md").exists()

    def test_label_not_removed_on_skip(self, tmp_path):
        """The chaplain label is NOT removed from skipped issues."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()
        (script_dir / "allowed-authors.txt").write_text("trusteduser\n")

        # Mock gh that logs edit calls
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
                            for arg in "$@"; do
                                if [[ "$arg" == *author* ]]; then echo "eviluser"; exit 0; fi
                                if [[ "$arg" == *title* ]]; then echo "T"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then echo "B"; exit 0; fi
                            done
                            ;;
                        edit)  echo "EDIT_CALLED"; exit 0 ;;
                    esac
                    ;;
            esac
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)

        result = subprocess.run(
            ["bash", "-c", self._sync_script()],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
                "TEST_SCRIPT_DIR": str(script_dir),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "SKIPPED_UNTRUSTED" in result.stdout
        # edit is never called (label not removed)
        assert "EDIT_CALLED" not in result.stdout

    def test_no_allowlist_accepts_all(self, tmp_path):
        """When allowed-authors.txt is absent, all authors are accepted."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()
        # No allowed-authors.txt file

        self._make_mock_gh(tmp_path, author="anyuser")
        result = subprocess.run(
            ["bash", "-c", self._sync_script()],
            env={
                **os.environ,
                "MOCK_DIR": str(tmp_path),
                "TEST_INBOX": str(inbox),
                "TEST_SCRIPT_DIR": str(script_dir),
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IMPORTED:42" in result.stdout
        assert (inbox / "gh-42.md").exists()


# ---------------------------------------------------------------------------
# 5. Functional tests — Body size cap
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestBodySizeCapLogic:
    """Functional tests for body size truncation."""

    def test_body_truncated_at_cap(self, tmp_path):
        """Body exceeding BODY_SIZE_CAP is truncated."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()

        # Create a body larger than 100 chars (use small cap for testing)
        large_body = "A" * 200

        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent(f"""\
            #!/usr/bin/env bash
            case "$1" in
                auth) exit 0 ;;
                issue)
                    case "$2" in
                        list)  echo '42' ;;
                        view)
                            for arg in "$@"; do
                                if [[ "$arg" == *author* ]]; then echo "user"; exit 0; fi
                                if [[ "$arg" == *title* ]]; then echo "Title"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then printf "%s" "{large_body}"; exit 0; fi
                            done
                            ;;
                        edit)  exit 0 ;;
                    esac
                    ;;
            esac
        """)
        )
        mock_gh.chmod(mock_gh.stat().st_mode | stat.S_IEXEC)

        # Use a smaller cap (100) for testing
        sync_script = textwrap.dedent("""\
            #!/usr/bin/env bash
            set -euo pipefail
            export PATH="$MOCK_DIR:$PATH"
            ln -sf "$MOCK_DIR/mock_gh" "$MOCK_DIR/gh" 2>/dev/null || true
            INBOX="$TEST_INBOX"
            BODY_SIZE_CAP=100

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue
                    author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

                    if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
                        echo "TRUNCATED:$num:${#body}:$BODY_SIZE_CAP"
                        body="${body:0:$BODY_SIZE_CAP}"
                    fi

                    printf "<!-- author: @%s -->\\n# %s\\n\\n%s\\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
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
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "TRUNCATED:42:200:100" in result.stdout
        assert "IMPORTED:42" in result.stdout

        content = (inbox / "gh-42.md").read_text()
        # Body portion should be exactly 100 A's, not 200
        body_line = content.split("\n\n", 1)[1].rstrip("\n")
        assert len(body_line) == 100

    def test_body_under_cap_not_truncated(self, tmp_path):
        """Body under BODY_SIZE_CAP is imported without truncation."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()

        small_body = "Short body"

        mock_gh = tmp_path / "mock_gh"
        mock_gh.write_text(
            textwrap.dedent(f"""\
            #!/usr/bin/env bash
            case "$1" in
                auth) exit 0 ;;
                issue)
                    case "$2" in
                        list)  echo '42' ;;
                        view)
                            for arg in "$@"; do
                                if [[ "$arg" == *author* ]]; then echo "user"; exit 0; fi
                                if [[ "$arg" == *title* ]]; then echo "Title"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then echo "{small_body}"; exit 0; fi
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
            BODY_SIZE_CAP=10000

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue
                    author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

                    if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
                        echo "TRUNCATED:$num:${#body}:$BODY_SIZE_CAP"
                        body="${body:0:$BODY_SIZE_CAP}"
                    fi

                    printf "<!-- author: @%s -->\\n# %s\\n\\n%s\\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
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
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "TRUNCATED" not in result.stdout
        assert "IMPORTED:42" in result.stdout
        content = (inbox / "gh-42.md").read_text()
        assert "Short body" in content


# ---------------------------------------------------------------------------
# 6. Functional tests — Audit header
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestAuditHeaderLogic:
    """Functional tests for author audit header in imported files."""

    def test_audit_header_present(self, tmp_path):
        """Imported file starts with <!-- author: @username --> header."""
        inbox = tmp_path / "inbox"
        inbox.mkdir()
        script_dir = tmp_path / "chaplain"
        script_dir.mkdir()

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
                            for arg in "$@"; do
                                if [[ "$arg" == *author* ]]; then echo "testuser"; exit 0; fi
                                if [[ "$arg" == *title* ]]; then echo "My Title"; exit 0; fi
                                if [[ "$arg" == *body* ]]; then echo "Body content"; exit 0; fi
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
            BODY_SIZE_CAP=10000

            if command -v gh &>/dev/null && gh auth status &>/dev/null 2>&1; then
                gh issue list --state open --label chaplain --json number --jq '.[].number' 2>/dev/null \\
                | while read -r num; do
                    [[ -f "$INBOX/gh-$num.md" ]] && continue
                    author=$(gh issue view "$num" --json author --jq '.author.login' 2>/dev/null) || continue
                    title=$(gh issue view "$num" --json title --jq '.title' 2>/dev/null) || continue
                    body=$(gh issue view "$num" --json body --jq '.body' 2>/dev/null) || continue

                    if [[ ${#body} -gt $BODY_SIZE_CAP ]]; then
                        body="${body:0:$BODY_SIZE_CAP}"
                    fi

                    printf "<!-- author: @%s -->\\n# %s\\n\\n%s\\n" "$author" "$title" "$body" > "$INBOX/gh-$num.md"
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
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "IMPORTED:42" in result.stdout

        content = (inbox / "gh-42.md").read_text()
        first_line = content.split("\n")[0]
        assert first_line == "<!-- author: @testuser -->"
        assert "# My Title" in content
        assert "Body content" in content


# ---------------------------------------------------------------------------
# 7. watch.sh integration — all three mitigations present
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestWatchShIntegration:
    """Integration assertions on watch.sh containing FR-251 changes."""

    def test_author_fetched_before_title_body(self):
        """Author login is fetched before title/body in the import block."""
        watch_sh = _read_watch_sh()
        # Inside the gh issue sync block, author fetch should come before title
        sync_block_start = watch_sh.find("gh issue list")
        sync_block_end = watch_sh.find("done", sync_block_start)
        sync_block = watch_sh[sync_block_start:sync_block_end]

        author_pos = sync_block.find("author")
        title_pos = sync_block.find("title")
        assert author_pos != -1, "author fetch not found in sync block"
        assert title_pos != -1, "title fetch not found in sync block"
        assert author_pos < title_pos, (
            "author must be fetched before title for early rejection"
        )


# ---------------------------------------------------------------------------
# 8. Allowed-authors.txt file exists
# ---------------------------------------------------------------------------
@pytest.mark.req("REQ-YG-256")
class TestAllowedAuthorsFileExists:
    """The .chaplain/allowed-authors.txt file must exist with default entry."""

    def test_allowed_authors_file_exists(self):
        """allowed-authors.txt exists in .chaplain/."""
        allowed_path = os.path.join(REPO_ROOT, ".chaplain", "allowed-authors.txt")
        assert os.path.isfile(allowed_path), ".chaplain/allowed-authors.txt must exist"

    def test_allowed_authors_contains_default(self):
        """allowed-authors.txt contains the repo owner as default."""
        allowed_path = os.path.join(REPO_ROOT, ".chaplain", "allowed-authors.txt")
        with open(allowed_path) as f:
            content = f.read()
        assert "sheikkinen" in content
