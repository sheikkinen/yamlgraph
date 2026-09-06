"""Tests for FR-258: Automate Post-Merge Finalization in watch.sh.

Validates:
1. Shared library `scripts/lib/finalize_lib.sh` functions work correctly (relocated by FR-1011)
2. `scripts/finalize_merge.sh` sources the shared library (no duplication)
3. `watch.sh` contains the post-merge finalization phase
4. Idempotency guards (FR status, existing PR, existing fragment)
5. Timestamp-based filtering via `.chaplain/state/last-finalized-at`
6. `.chaplain/state/` is gitignored

Testing approach:
- Content assertions for watch.sh and finalize_merge.sh (structure)
- Subprocess execution for finalize_lib.sh functions (behavior)
"""

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.process

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
WATCH_SH = os.path.join(REPO_ROOT, ".chaplain", "watch.sh")
FINALIZE_MERGE_SH = os.path.join(REPO_ROOT, "scripts", "finalize_merge.sh")
FINALIZE_LIB_SH = os.path.join(REPO_ROOT, "scripts", "lib", "finalize_lib.sh")
GITIGNORE = os.path.join(REPO_ROOT, ".gitignore")

# Shell snippet that sources finalize_lib.sh and exercises a single function.
# TEST_DIR must contain a feature-requests/ directory with an FR file.
_LIB_TEST_HARNESS = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -euo pipefail
    source "{lib_path}"
    cd "$TEST_DIR"
    "$@"
""")


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_sample_fr(
    test_dir: str,
    filename: str,
    *,
    req_id: str = "",
    status: str = "Approved",
    title: str = "Test Feature",
) -> str:
    """Write a sample FR file and return its path."""
    fr_dir = os.path.join(test_dir, "feature-requests")
    os.makedirs(fr_dir, exist_ok=True)
    fr_path = os.path.join(fr_dir, filename)
    lines = [
        f"# Feature Request: FR-999 {title}",
        "",
        f"**Status:** {status}",
        "",
        "## Summary",
        "",
        "Automate post-merge finalization for FR-999.",
        "",
    ]
    if req_id:
        lines.append(f"Requirement: {req_id}")
        lines.append("")
    with open(fr_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return fr_path


def _run_lib_function(
    test_dir: str, func_name: str, *args: str
) -> subprocess.CompletedProcess:
    """Source finalize_lib.sh and call a function with args."""
    lib_path = os.path.abspath(FINALIZE_LIB_SH)
    script = _LIB_TEST_HARNESS.format(lib_path=lib_path)
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    }
    env["TEST_DIR"] = test_dir
    return subprocess.run(
        ["bash", "-c", script, "--", func_name, *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


# ---------------------------------------------------------------------------
# 1. Shared library exists and is sourceable
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestSharedLibraryExists:
    """`scripts/lib/finalize_lib.sh` must exist and be sourceable."""

    def test_finalize_lib_exists(self):
        assert os.path.isfile(
            FINALIZE_LIB_SH
        ), f"Shared library not found: {FINALIZE_LIB_SH}"

    def test_finalize_lib_is_sourceable(self):
        """Sourcing the library must not produce errors."""
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        result = subprocess.run(
            ["bash", "-c", f"source '{lib_path}'"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Source failed: {result.stderr}"

    def test_finalize_lib_defines_all_functions(self):
        """Library must define extract_fr_metadata, create_changelog_fragment,
        update_fr_status, create_diary_stub."""
        lib_content = _read_file(FINALIZE_LIB_SH)
        for func in [
            "extract_fr_metadata",
            "create_changelog_fragment",
            "update_fr_status",
            "create_diary_stub",
        ]:
            assert f"{func}()" in lib_content, f"Missing function: {func}"


# ---------------------------------------------------------------------------
# 2. extract_fr_metadata
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestExtractFrMetadata:
    """extract_fr_metadata sets FR_NUM, FR_TITLE, REQ_ID, FR_SUMMARY."""

    def test_extracts_fr_num(self, tmp_path):
        test_dir = str(tmp_path)
        fr_path = _write_sample_fr(test_dir, "FR-999-test-feature.md")
        # Call extract_fr_metadata and echo the variables
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            source '{lib_path}'
            extract_fr_metadata '{fr_path}'
            echo "FR_NUM=$FR_NUM"
            echo "FR_TITLE=$FR_TITLE"
            echo "FR_SUMMARY=$FR_SUMMARY"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "FR_NUM=FR-999" in result.stdout

    def test_extracts_title_without_prefix(self, tmp_path):
        test_dir = str(tmp_path)
        fr_path = _write_sample_fr(
            test_dir, "FR-999-test-feature.md", title="Automate Post-Merge"
        )
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            source '{lib_path}'
            extract_fr_metadata '{fr_path}'
            echo "FR_TITLE=$FR_TITLE"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "FR_TITLE=Automate Post-Merge" in result.stdout

    def test_extracts_req_id(self, tmp_path):
        test_dir = str(tmp_path)
        fr_path = _write_sample_fr(
            test_dir, "FR-999-test-feature.md", req_id="REQ-YG-999"
        )
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            source '{lib_path}'
            extract_fr_metadata '{fr_path}'
            echo "REQ_ID=$REQ_ID"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "REQ_ID=REQ-YG-999" in result.stdout

    def test_extracts_summary(self, tmp_path):
        test_dir = str(tmp_path)
        fr_path = _write_sample_fr(test_dir, "FR-999-test-feature.md")
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            source '{lib_path}'
            extract_fr_metadata '{fr_path}'
            echo "FR_SUMMARY=$FR_SUMMARY"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "Automate post-merge finalization" in result.stdout


# ---------------------------------------------------------------------------
# 3. create_changelog_fragment
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestCreateChangelogFragment:
    """create_changelog_fragment creates fragment file with correct format."""

    def test_creates_fragment_file(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "Test Feature" "Some summary." "REQ-YG-999"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Check file was created
        fragments = [
            f
            for f in os.listdir(os.path.join(test_dir, "changelog", "unreleased"))
            if f.startswith("FR-999")
        ]
        assert len(fragments) == 1, f"Expected 1 fragment, found: {fragments}"

    def test_fragment_contains_yaml_frontmatter(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "Test Feature" "Some summary." "REQ-YG-999"
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        frag_dir = Path(test_dir) / "changelog" / "unreleased"
        fragments = [f for f in os.listdir(frag_dir) if f.startswith("FR-999")]
        content = (frag_dir / fragments[0]).read_text(encoding="utf-8")
        assert "---" in content
        assert "type: feat" in content
        assert "req: REQ-YG-999" in content

    def test_fragment_without_req_id_omits_req_line(self, tmp_path):
        """When REQ_ID is empty, no blank req line appears in frontmatter."""
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "Test Feature" "Some summary." ""
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        frag_dir = Path(test_dir) / "changelog" / "unreleased"
        fragments = [f for f in os.listdir(frag_dir) if f.startswith("FR-999")]
        content = (frag_dir / fragments[0]).read_text(encoding="utf-8")
        assert "req:" not in content
        # No blank line between scope and closing ---
        lines = content.strip().split("\n")
        frontmatter_lines = []
        in_fm = False
        for line in lines:
            if line.strip() == "---":
                if in_fm:
                    break
                in_fm = True
                continue
            if in_fm:
                frontmatter_lines.append(line)
        for line in frontmatter_lines:
            assert line.strip() != "", "No blank lines in frontmatter"

    def test_idempotent_skips_existing_fragment(self, tmp_path):
        """Running twice does not overwrite the existing fragment."""
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "Test Feature" "First summary." "REQ-YG-999"
            create_changelog_fragment "FR-999" "Test Feature" "Second summary." "REQ-YG-999"
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        fragments = [
            f
            for f in os.listdir(os.path.join(test_dir, "changelog", "unreleased"))
            if f.startswith("FR-999")
        ]
        assert len(fragments) == 1
        frag_dir = Path(test_dir) / "changelog" / "unreleased"
        content = (frag_dir / fragments[0]).read_text(encoding="utf-8")
        assert "First summary" in content
        assert "Second summary" not in content


# ---------------------------------------------------------------------------
# 4. update_fr_status
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestUpdateFrStatus:
    """update_fr_status changes Status line to ✅ Implemented."""

    def test_updates_approved_to_implemented(self, tmp_path):
        test_dir = str(tmp_path)
        fr_path = _write_sample_fr(test_dir, "FR-999-test.md", status="Approved")
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            source '{lib_path}'
            update_fr_status '{fr_path}'
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        content = Path(fr_path).read_text(encoding="utf-8")
        assert "**Status:** ✅ Implemented" in content
        assert "**Status:** Approved" not in content


# ---------------------------------------------------------------------------
# 5. create_diary_stub
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestCreateDiaryStub:
    """create_diary_stub creates reflection file with placeholders."""

    def test_creates_diary_file(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "docs", "diary"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_diary_stub "FR-999" "Test Feature"
        """)
        result = subprocess.run(
            ["bash", "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        diary_dir = os.path.join(test_dir, "docs", "diary")
        reflections = [f for f in os.listdir(diary_dir) if "FR-999" in f]
        assert len(reflections) == 1, f"Expected 1 reflection, found: {reflections}"

    def test_diary_contains_placeholders(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "docs", "diary"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_diary_stub "FR-999" "Test Feature"
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        diary_dir = os.path.join(test_dir, "docs", "diary")
        reflections = [f for f in os.listdir(diary_dir) if "FR-999" in f]
        content = (Path(diary_dir) / reflections[0]).read_text(encoding="utf-8")
        assert "[What cognitive trap was encountered?]" in content
        assert "[What lesson was learned?]" in content
        assert "[What question remains?]" in content

    def test_idempotent_skips_existing_stub(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "docs", "diary"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_diary_stub "FR-999" "Test Feature"
            create_diary_stub "FR-999" "Test Feature"
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        diary_dir = os.path.join(test_dir, "docs", "diary")
        reflections = [f for f in os.listdir(diary_dir) if "FR-999" in f]
        assert len(reflections) == 1


# ---------------------------------------------------------------------------
# 6. finalize_merge.sh sources the shared library
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestFinalizeMergeSourcesLib:
    """scripts/finalize_merge.sh must source scripts/lib/finalize_lib.sh."""

    def test_sources_finalize_lib(self):
        content = _read_file(FINALIZE_MERGE_SH)
        assert (
            "finalize_lib.sh" in content
        ), "finalize_merge.sh must source finalize_lib.sh"

    def test_calls_extract_fr_metadata(self):
        content = _read_file(FINALIZE_MERGE_SH)
        assert "extract_fr_metadata" in content

    def test_calls_create_changelog_fragment(self):
        content = _read_file(FINALIZE_MERGE_SH)
        assert "create_changelog_fragment" in content

    def test_calls_update_fr_status(self):
        content = _read_file(FINALIZE_MERGE_SH)
        assert "update_fr_status" in content

    def test_calls_create_diary_stub(self):
        content = _read_file(FINALIZE_MERGE_SH)
        assert "create_diary_stub" in content

    def test_no_inline_duplicate_metadata_extraction(self):
        """Metadata extraction logic must be in the library, not inline."""
        content = _read_file(FINALIZE_MERGE_SH)
        # The old inline pattern was: FR_HEADING=$(grep -m1 ...
        # After refactor, this should only appear in the library, not in the script
        # The script should call extract_fr_metadata instead
        assert (
            content.count("FR_HEADING=") == 0
        ), "FR_HEADING= should not be defined inline — use extract_fr_metadata"


# ---------------------------------------------------------------------------
# 8. .gitignore
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestGitignore:
    """.chaplain/state/ must be gitignored."""

    def test_chaplain_state_gitignored(self):
        content = _read_file(GITIGNORE)
        assert ".chaplain/state/" in content


# ---------------------------------------------------------------------------
# 9. Slug generation
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestSlugGeneration:
    """Fragment filename uses correct slug from FR title."""

    def test_slug_lowercased_and_hyphenated(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "My Cool Feature" "Summary." ""
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        fragments = os.listdir(os.path.join(test_dir, "changelog", "unreleased"))
        assert len(fragments) == 1
        assert fragments[0] == "FR-999-my-cool-feature.md"

    def test_slug_strips_special_characters(self, tmp_path):
        test_dir = str(tmp_path)
        os.makedirs(os.path.join(test_dir, "changelog", "unreleased"), exist_ok=True)
        lib_path = os.path.abspath(FINALIZE_LIB_SH)
        script = textwrap.dedent(f"""\
            cd '{test_dir}'
            source '{lib_path}'
            create_changelog_fragment "FR-999" "Feature (v2) & More!" "Summary." ""
        """)
        subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=5
        )
        fragments = os.listdir(os.path.join(test_dir, "changelog", "unreleased"))
        assert len(fragments) == 1
        # Only a-z, 0-9, and hyphens in slug
        slug_part = fragments[0].replace("FR-999-", "").replace(".md", "")
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug_part)


# ---------------------------------------------------------------------------
# 10. Existing finalize_merge.sh still works (behavior unchanged)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-261")
class TestFinalizeMergeStillWorks:
    """Refactored finalize_merge.sh produces identical output."""

    def _make_repo(self, tmp_path):
        """Bootstrap a minimal git repo on branch 'main'."""
        repo = tmp_path / "repo"
        repo.mkdir()
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"GIT_INDEX_FILE", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
        }
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
        (repo / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n\n### Added\n"
        , encoding="utf-8")
        (repo / "changelog" / "unreleased").mkdir(parents=True)
        (repo / "docs" / "diary").mkdir(parents=True)
        (repo / "feature-requests").mkdir()
        (repo / "tmp").mkdir()
        # Copy the shared library into scripts/lib/ for the script to source
        lib_dest = repo / "scripts" / "lib"
        lib_dest.mkdir(parents=True)
        import shutil

        shutil.copy(os.path.abspath(FINALIZE_LIB_SH), str(lib_dest / "finalize_lib.sh"))
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
        return repo, env

    def test_finalize_merge_produces_changelog_fragment(self, tmp_path):
        repo, env = self._make_repo(tmp_path)
        fr_path = repo / "feature-requests" / "FR-300-integration-test.md"
        fr_path.write_text(
            textwrap.dedent("""\
            # Feature Request: FR-300 Integration Test

            **Status:** Approved

            ## Summary

            Integration test for refactored finalize_merge.sh.
        """)
        , encoding="utf-8")
        subprocess.run(
            ["git", "add", "."], cwd=repo, check=True, capture_output=True, env=env
        )
        subprocess.run(
            ["git", "commit", "-m", "add FR"],
            cwd=repo,
            check=True,
            capture_output=True,
            env=env,
        )
        script_abs = os.path.abspath(FINALIZE_MERGE_SH)
        result = subprocess.run(
            ["bash", script_abs, "feature-requests/FR-300-integration-test.md"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        assert result.returncode == 0, f"Failed: {result.stdout}\n{result.stderr}"
        fragments = list((repo / "changelog" / "unreleased").glob("FR-300*.md"))
        assert len(fragments) == 1
        fr_content = fr_path.read_text(encoding="utf-8")
        assert "**Status:** ✅ Implemented" in fr_content
