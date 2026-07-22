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

pytestmark = [pytest.mark.process, pytest.mark.slow]

# Strip git env vars that pre-commit injects (GIT_INDEX_FILE from stashing).
_GIT_ENV_POISON = {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}


def _clean_git_env(**extra: str) -> dict[str, str]:
    """Return os.environ minus git vars that pollute temp-repo subprocess calls."""
    env = {k: v for k, v in os.environ.items() if k not in _GIT_ENV_POISON}
    env.update(extra)
    return env


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

    env = _clean_git_env()

    # Init git repo on main
    subprocess.run(
        ["git", "init", "-b", "main"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
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

    # Create changelog/unreleased/ for fragment files (FR-179)
    changelog_dir = repo / "changelog" / "unreleased"
    changelog_dir.mkdir(parents=True)

    # Create docs/diary/ folder
    docs = repo / "docs"
    docs.mkdir()
    diary_dir = docs / "diary"
    diary_dir.mkdir()

    # Create feature-requests/ with a sample FR
    fr_dir = repo / "feature-requests"
    fr_dir.mkdir()

    # Create tmp/ for commit message
    (repo / "tmp").mkdir()

    # Initial commit so we have a clean state
    subprocess.run(
        ["git", "add", "."], cwd=repo, check=True, capture_output=True, env=env
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=env,
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
        env=_clean_git_env(),
    )
    subprocess.run(
        ["git", "commit", "-m", f"add {filename}"],
        cwd=repo,
        check=True,
        capture_output=True,
        env=_clean_git_env(),
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
        env=_clean_git_env(
            # Prevent git pull from hitting a remote
            GIT_TERMINAL_PROMPT="0",
        ),
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
            env=_clean_git_env(),
        )
        stdout, stderr, rc = _run_finalize(repo, fr_rel, expect_fail=True)
        assert rc != 0
        assert "main" in (stdout + stderr).lower()


# ---------------------------------------------------------------------------
# CHANGELOG Entry
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-125")
class TestChangelogEntry:
    """Changelog fragment is created in changelog/unreleased/ (FR-179)."""

    def test_fragment_created_in_unreleased(self, tmp_path):
        """New fragment file appears in changelog/unreleased/."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-210-changelog-test.md", req_id="REQ-YG-210")
        _run_finalize(repo, fr_rel)

        fragments = list((repo / "changelog" / "unreleased").glob("FR-210*.md"))
        assert len(fragments) == 1, f"Expected 1 fragment, found: {fragments}"
        content = fragments[0].read_text()
        assert "FR-210" in content

    def test_fragment_format_with_req_id(self, tmp_path):
        """Fragment contains YAML front matter with req field."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(
            repo,
            "FR-211-format-test.md",
            title="Format Test",
            req_id="REQ-YG-211",
        )
        _run_finalize(repo, fr_rel)

        fragments = list((repo / "changelog" / "unreleased").glob("FR-211*.md"))
        assert len(fragments) == 1
        content = fragments[0].read_text()
        assert "- **FR-211 Format Test**:" in content
        assert "REQ-YG-211" in content

    def test_fragment_format_without_req_id(self, tmp_path):
        """Fragment omits req line when FR has no requirement ID."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-212-no-req.md", title="No Req Feature")
        _run_finalize(repo, fr_rel)

        fragments = list((repo / "changelog" / "unreleased").glob("FR-212*.md"))
        assert len(fragments) == 1
        content = fragments[0].read_text()
        assert "- **FR-212 No Req Feature**:" in content

    def test_summary_extracted_from_fr(self, tmp_path):
        """Fragment description comes from FR's ## Summary section."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-213-summary-test.md")
        _run_finalize(repo, fr_rel)

        fragments = list((repo / "changelog" / "unreleased").glob("FR-213*.md"))
        assert len(fragments) == 1
        content = fragments[0].read_text()
        assert "post-merge finalization script" in content

    def test_duplicate_fragment_guard(self, tmp_path):
        """Running script twice does not create duplicate fragment."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-214-dup-test.md", req_id="REQ-YG-214")
        _run_finalize(repo, fr_rel)

        # Reset status back to Approved so the script can run status update again
        fr_path = repo / fr_rel
        fr_path.write_text(fr_path.read_text().replace("✅ Implemented", "Approved"))
        subprocess.run(
            ["git", "add", "."],
            cwd=repo,
            check=True,
            capture_output=True,
            env=_clean_git_env(),
        )
        subprocess.run(
            ["git", "commit", "-m", "reset"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=_clean_git_env(),
        )

        stdout, _, _ = _run_finalize(repo, fr_rel)
        assert "already exists" in stdout.lower() or "skipping" in stdout.lower()

        fragments = list((repo / "changelog" / "unreleased").glob("FR-214*.md"))
        assert len(fragments) == 1

    def test_creates_fragment_without_added_section(self, tmp_path):
        """Fragment created even when CHANGELOG has no ### Added section."""
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
        subprocess.run(
            ["git", "add", "."],
            cwd=repo,
            check=True,
            capture_output=True,
            env=_clean_git_env(),
        )
        subprocess.run(
            ["git", "commit", "-m", "remove added section"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=_clean_git_env(),
        )

        fr_rel = _write_fr(repo, "FR-215-no-added.md", title="No Added Section")
        _run_finalize(repo, fr_rel)

        fragments = list((repo / "changelog" / "unreleased").glob("FR-215*.md"))
        assert len(fragments) == 1
        content = fragments[0].read_text()
        assert "FR-215" in content


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
    """docs/diary/ gets a reflection stub file with placeholders."""

    def test_diary_stub_written_as_file(self, tmp_path):
        """Diary entry is written as individual file in docs/diary/."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-230-diary-test.md", title="Diary Test")
        _run_finalize(repo, fr_rel)

        diary_dir = repo / "docs" / "diary"
        assert diary_dir.exists(), "docs/diary/ folder should exist"
        reflection_files = list(diary_dir.glob("*-reflection-FR-230.md"))
        assert (
            len(reflection_files) == 1
        ), f"Expected 1 reflection file, found: {list(diary_dir.iterdir())}"
        content = reflection_files[0].read_text()
        assert "FR-230" in content
        assert "Implementation Reflection" in content
        assert "[What cognitive trap was encountered?]" in content
        assert "[What lesson was learned?]" in content
        assert "[What question remains?]" in content


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
            env=_clean_git_env(),
        )
        assert "chore: FR-240 post-merge finalization" in result.stdout

    def test_commit_excludes_co_author_trailer(self, tmp_path):
        """FR-167: Commit must NOT contain Co-authored-by Copilot trailer."""
        repo = _make_repo(tmp_path)
        fr_rel = _write_fr(repo, "FR-242-no-trailer-test.md")
        _run_finalize(repo, fr_rel)

        result = subprocess.run(
            ["git", "log", "-1", "--format=%b"],
            cwd=repo,
            capture_output=True,
            text=True,
            env=_clean_git_env(),
        )
        assert "Co-authored-by: Copilot" not in result.stdout


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
