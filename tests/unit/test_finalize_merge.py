"""Unit tests for scripts/finalize_merge.sh (FR-125).

Tests the post-merge finalization script that automates three obligations
after a PR from the enforce pipeline is merged: CHANGELOG entry, FR status
update, and diary reflection stub.

The script is pure shell (deterministic text transforms), so tests exercise
it via subprocess with temporary directory structures — matching the pattern
established in test_watch_enforce_spawn.py.
"""

import os
import subprocess
import textwrap

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Path to the real finalize_merge.sh script (relative to repo root)
_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "scripts", "finalize_merge.sh"
)


def _make_repo(tmp_path):
    """Bootstrap a minimal git repo on branch 'main' with required files."""
    repo = tmp_path / "repo"
    repo.mkdir()

    # Init git repo on main
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create CHANGELOG.md with [Unreleased] / ### Added section
    changelog = repo / "CHANGELOG.md"
    changelog.write_text(
        textwrap.dedent("""\
        # Changelog

        ## [Unreleased]

        ### Added
        - **FR-100 Existing Feature**: Some existing entry (REQ-YG-100)

        ### Fixed
        - **FR-099 Bug Fix**: Fixed something

        ## [0.4.60] — 2026-03-06

        ### Added
        - Old entry
    """)
    )

    # Create docs/diary.md
    docs = repo / "docs"
    docs.mkdir()
    diary = docs / "diary.md"
    diary.write_text(
        textwrap.dedent("""\
        # Diary

        ## 2026-03-06: Previous Entry

        Some previous reflection.

        **Seed:** What comes next?
    """)
    )

    # Create feature-requests/ with a sample FR
    fr_dir = repo / "feature-requests"
    fr_dir.mkdir()

    # Create tmp/ for commit message
    (repo / "tmp").mkdir()

    # Initial commit so we have a clean state
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


def _write_fr(repo, filename, *, status="Approved", req_id=None, title=None):
    """Write a feature request file and return its relative path."""
    fr_path = repo / "feature-requests" / filename
    fr_num = (
        filename.replace(".md", "").split("-")[0]
        + "-"
        + filename.replace(".md", "").split("-")[1]
    )
    if title is None:
        title = "Test Feature Title"

    lines = [
        f"# Feature Request: {fr_num.upper()} {title}",
        "",
        f"**Status:** {status}",
        "",
        "## Summary",
        "",
        f"Add a post-merge finalization script for {fr_num.upper()}.",
        "",
    ]
    if req_id:
        lines.append(f"Requirement: {req_id}")
        lines.append("")

    fr_path.write_text("\n".join(lines) + "\n")

    # Stage and commit the FR
    subprocess.run(
        ["git", "add", str(fr_path)],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"add {filename}"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return f"feature-requests/{filename}"


def _run_finalize(repo, fr_rel_path, *, expect_fail=False):
    """Run finalize_merge.sh in the test repo. Returns (stdout, stderr, returncode)."""
    script_abs = os.path.abspath(_SCRIPT_PATH)
    result = subprocess.run(
        ["bash", script_abs, fr_rel_path],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
        env={
            **os.environ,
            # Prevent git pull from hitting a remote
            "GIT_TERMINAL_PROMPT": "0",
        },
    )
    if not expect_fail:
        assert result.returncode == 0, (
            f"finalize_merge.sh failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# Fail-Fast Guards
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestFailFastGuards:
    """Script must exit non-zero when preconditions are not met."""

    def test_missing_fr_file(self, tmp_path):
        """Exit 1 when FR file does not exist."""
        repo = _make_repo(tmp_path)
        _, stderr, rc = _run_finalize(
            repo, "feature-requests/nonexistent.md", expect_fail=True
        )
        assert rc != 0
        assert "not found" in stderr.lower() or "not found" in _.lower()

    def test_dirty_working_tree(self, tmp_path):
        """Exit 1 when working tree has uncommitted changes."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-200-dirty-test.md")
        # Dirty the tree
        (repo / "CHANGELOG.md").write_text("dirty\n")
        stdout, stderr, rc = _run_finalize(repo, fr_rel, expect_fail=True)
        assert rc != 0
        assert "dirty" in (stdout + stderr).lower()

    def test_not_on_main_branch(self, tmp_path):
        """Exit 1 when not on main branch."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-201-branch-test.md")
        # Switch to a different branch
        subprocess.run(
            ["git", "checkout", "-b", "feature-branch"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        stdout, stderr, rc = _run_finalize(repo, fr_rel, expect_fail=True)
        assert rc != 0
        assert "main" in (stdout + stderr).lower()


# ---------------------------------------------------------------------------
# CHANGELOG Entry
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestChangelogEntry:
    """CHANGELOG.md is updated with a properly formatted entry."""

    def test_entry_inserted_under_added(self, tmp_path):
        """New entry appears immediately after ### Added header."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-210-changelog-test.md", req_id="REQ-YG-210")
        _run_finalize(repo, fr_rel)

        changelog = (repo / "CHANGELOG.md").read_text()
        lines = changelog.splitlines()
        # Find ### Added line
        added_idx = next(
            i for i, line in enumerate(lines) if line.strip() == "### Added"
        )
        # Next non-empty line should be our new entry
        entry_line = lines[added_idx + 1]
        assert "FR-210" in entry_line
        assert entry_line.startswith("- **FR-210")

    def test_entry_format_with_req_id(self, tmp_path):
        """Entry format: - **FR-NNN Title**: Summary (REQ-YG-XXX)."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(
            repo,
            "FR-211-format-test.md",
            title="Format Test",
            req_id="REQ-YG-211",
        )
        _run_finalize(repo, fr_rel)

        changelog = (repo / "CHANGELOG.md").read_text()
        assert "- **FR-211 Format Test**:" in changelog
        assert "(REQ-YG-211)" in changelog

    def test_entry_format_without_req_id(self, tmp_path):
        """Entry omits (REQ-YG-XXX) when FR has no requirement ID."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-212-no-req.md", title="No Req Feature")
        _run_finalize(repo, fr_rel)

        changelog = (repo / "CHANGELOG.md").read_text()
        assert "- **FR-212 No Req Feature**:" in changelog
        assert "REQ-YG" not in changelog.split("FR-212")[1].split("\n")[0]

    def test_summary_extracted_from_fr(self, tmp_path):
        """CHANGELOG description comes from FR's ## Summary section."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-213-summary-test.md")
        _run_finalize(repo, fr_rel)

        changelog = (repo / "CHANGELOG.md").read_text()
        # The summary from _write_fr is "Add a post-merge finalization script for FR-213."
        assert "post-merge finalization script" in changelog

    def test_duplicate_entry_guard(self, tmp_path):
        """Running script twice does not insert duplicate CHANGELOG entry."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-214-dup-test.md", req_id="REQ-YG-214")
        _run_finalize(repo, fr_rel)

        # Reset status back to Approved so the script can run status update again
        fr_path = repo / fr_rel
        fr_path.write_text(fr_path.read_text().replace("✅ Implemented", "Approved"))
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "reset"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        stdout, _, _ = _run_finalize(repo, fr_rel)
        assert "already in CHANGELOG" in stdout.lower() or "skipping" in stdout.lower()

        changelog = (repo / "CHANGELOG.md").read_text()
        assert changelog.count("**FR-214") == 1

    def test_creates_added_section_when_missing(self, tmp_path):
        """When ### Added doesn't exist under [Unreleased], it is created."""
        repo = _make_repo(tmp_path)

        # Rewrite CHANGELOG without ### Added section
        (repo / "CHANGELOG.md").write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Fixed
            - **FR-099 Bug Fix**: Fixed something

            ## [0.4.60] — 2026-03-06
        """)
        )
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "remove added section"],
            cwd=repo,
            check=True,
            capture_output=True,
        )

        fr_rel = _write_fr(repo, "FR-215-no-added.md", title="No Added Section")
        _run_finalize(repo, fr_rel)

        changelog = (repo / "CHANGELOG.md").read_text()
        assert "### Added" in changelog
        assert "FR-215" in changelog


# ---------------------------------------------------------------------------
# FR Status Update
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestFRStatusUpdate:
    """FR file's **Status:** line is updated to ✅ Implemented."""

    def test_status_updated(self, tmp_path):
        """Status line changes from Approved to ✅ Implemented."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-220-status-test.md", status="Approved")
        _run_finalize(repo, fr_rel)

        content = (repo / fr_rel).read_text()
        assert "**Status:** ✅ Implemented" in content
        assert "**Status:** Approved" not in content


# ---------------------------------------------------------------------------
# Diary Reflection Stub
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestDiaryStub:
    """docs/diary.md gets a reflection stub with placeholders."""

    def test_diary_stub_appended(self, tmp_path):
        """Diary entry has date, FR number, and Trap/Heuristic/Seed placeholders."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-230-diary-test.md", title="Diary Test")
        _run_finalize(repo, fr_rel)

        diary = (repo / "docs" / "diary.md").read_text()
        assert "FR-230" in diary
        assert "Implementation Reflection" in diary
        assert "[What cognitive trap was encountered?]" in diary
        assert "[What lesson was learned?]" in diary
        assert "[What question remains?]" in diary


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestCommit:
    """Finalization changes are committed with correct message format."""

    def test_commit_message_format(self, tmp_path):
        """Commit message follows chore: FR-XXX post-merge finalization."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-240-commit-test.md")
        _run_finalize(repo, fr_rel)

        result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert "chore: FR-240 post-merge finalization" in result.stdout

    def test_commit_includes_co_author(self, tmp_path):
        """Commit includes Co-authored-by trailer."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-241-coauthor-test.md")
        _run_finalize(repo, fr_rel)

        result = subprocess.run(
            ["git", "log", "-1", "--format=%b"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        assert "Co-authored-by: Copilot" in result.stdout


# ---------------------------------------------------------------------------
# enforce_worktree.sh Integration
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestEnforceNextSteps:
    """enforce_worktree.sh NEXT STEPS block includes finalize command."""

    def test_finalize_command_in_next_steps(self):
        """enforce_worktree.sh mentions finalize_merge.sh in output."""
        enforce_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "scripts",
            "enforce_worktree.sh",
        )
        with open(enforce_path) as f:
            content = f.read()
        assert "finalize_merge.sh" in content
        assert "After merging" in content or "after merging" in content.lower()


# ---------------------------------------------------------------------------
# Script Header
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestScriptHeader:
    """finalize_merge.sh has proper header comments."""

    def test_script_has_usage_comment(self):
        """Script header includes usage instructions."""
        with open(os.path.abspath(_SCRIPT_PATH)) as f:
            content = f.read()
        assert "Usage:" in content
        assert "finalize_merge.sh" in content

    def test_script_uses_portable_sed(self):
        """Script uses temp file pattern, not sed -i."""
        with open(os.path.abspath(_SCRIPT_PATH)) as f:
            content = f.read()
        assert "sed -i" not in content
