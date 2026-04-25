"""Tests for append-only changelog fragments (FR-179).

Validates:
  - Fragment files use YAML front matter (type, scope, optional req) + body
  - aggregate_changelog.py generates CHANGELOG.md from fragment files
  - migrate_changelog.py splits existing CHANGELOG.md into fragment files
  - Round-trip: migrate → aggregate reproduces original content
  - finalize_merge.sh creates fragment file instead of editing CHANGELOG.md
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_module(name: str, script_path: Path):
    """Import a script module by file path."""
    import sys as _sys

    spec = importlib.util.spec_from_file_location(name, script_path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fragment Format
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestFragmentFormat:
    """Changelog fragments must use YAML front matter + markdown body."""

    def test_parse_fragment_with_all_fields(self, tmp_path: Path) -> None:
        """Fragment with type, scope, and req parses correctly."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        fragment = tmp_path / "FR-100-test.md"
        fragment.write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: graph
            req: REQ-YG-100
            ---
            **FR-100 Test Feature**: Add a test feature for validation.
        """)
        )
        entry = aggregate.parse_fragment(fragment)
        assert entry.fr_num == "FR-100"
        assert entry.entry_type == "feat"
        assert entry.scope == "graph"
        assert entry.req == "REQ-YG-100"
        assert "Test Feature" in entry.body

    def test_parse_fragment_without_req(self, tmp_path: Path) -> None:
        """Fragment without req field parses with req=None."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        fragment = tmp_path / "FR-101-no-req.md"
        fragment.write_text(
            textwrap.dedent("""\
            ---
            type: fix
            scope: cli
            ---
            **FR-101 Bug Fix**: Fix a bug in the CLI.
        """)
        )
        entry = aggregate.parse_fragment(fragment)
        assert entry.entry_type == "fix"
        assert entry.req is None

    def test_parse_fragment_removal_type(self, tmp_path: Path) -> None:
        """Fragment with type: removal maps to Removed section."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        fragment = tmp_path / "FR-102-remove.md"
        fragment.write_text(
            textwrap.dedent("""\
            ---
            type: removal
            scope: utils
            ---
            **FR-102 Dead Code**: Remove dead module.
        """)
        )
        entry = aggregate.parse_fragment(fragment)
        assert entry.entry_type == "removal"

    def test_parse_fragment_rejects_missing_type(self, tmp_path: Path) -> None:
        """Fragment without type field raises ValueError."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        fragment = tmp_path / "FR-103-bad.md"
        fragment.write_text(
            textwrap.dedent("""\
            ---
            scope: graph
            ---
            Missing type field.
        """)
        )
        with pytest.raises(ValueError, match="type"):
            aggregate.parse_fragment(fragment)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestAggregateChangelog:
    """aggregate_changelog.py generates CHANGELOG.md from fragment files."""

    def test_groups_by_type(self, tmp_path: Path) -> None:
        """Entries grouped into Added/Fixed/Removed sections."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog_dir = tmp_path / "changelog"
        unreleased = changelog_dir / "unreleased"
        unreleased.mkdir(parents=True)
        version_dir = changelog_dir / "0.5.0"
        version_dir.mkdir()

        # Unreleased fragments
        (unreleased / "FR-200-feat.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: graph
            req: REQ-YG-200
            ---
            - **FR-200 New Feature**: Add something new. (REQ-YG-200)
        """)
        )
        (unreleased / "FR-201-fix.md").write_text(
            textwrap.dedent("""\
            ---
            type: fix
            scope: cli
            ---
            - **FR-201 Bug Fix**: Fix a bug.
        """)
        )

        # Versioned fragment
        (version_dir / "FR-199-old.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: core
            req: REQ-YG-199
            ---
            - **FR-199 Old Feature**: An older feature. (REQ-YG-199)
        """)
        )

        output = aggregate.aggregate(changelog_dir)
        assert "## [Unreleased]" in output
        assert "### Added" in output
        assert "### Fixed" in output
        assert "FR-200" in output
        assert "FR-201" in output
        assert "## [0.5.0]" in output
        assert "FR-199" in output

    def test_sorted_by_fr_number(self, tmp_path: Path) -> None:
        """Within a section, entries sorted by FR number descending (newest first)."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog_dir = tmp_path / "changelog"
        unreleased = changelog_dir / "unreleased"
        unreleased.mkdir(parents=True)

        (unreleased / "FR-300-second.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: graph
            ---
            - **FR-300 Second**: Second feature.
        """)
        )
        (unreleased / "FR-200-first.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: graph
            ---
            - **FR-200 First**: First feature.
        """)
        )

        output = aggregate.aggregate(changelog_dir)
        pos_200 = output.index("FR-200")
        pos_300 = output.index("FR-300")
        assert pos_300 < pos_200, (
            "FR-300 should appear before FR-200 (descending order)"
        )

    def test_empty_unreleased(self, tmp_path: Path) -> None:
        """Empty unreleased directory emits section with no entries."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog_dir = tmp_path / "changelog"
        unreleased = changelog_dir / "unreleased"
        unreleased.mkdir(parents=True)

        output = aggregate.aggregate(changelog_dir)
        assert "## [Unreleased]" in output

    def test_generated_header_comment(self, tmp_path: Path) -> None:
        """Output starts with generation comment."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog_dir = tmp_path / "changelog"
        (changelog_dir / "unreleased").mkdir(parents=True)

        output = aggregate.aggregate(changelog_dir)
        assert output.startswith("<!-- Generated by")

    def test_version_ordering(self, tmp_path: Path) -> None:
        """Versions appear in descending order (newest first)."""
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog_dir = tmp_path / "changelog"
        (changelog_dir / "unreleased").mkdir(parents=True)
        v1 = changelog_dir / "0.4.59"
        v1.mkdir()
        v2 = changelog_dir / "0.4.61"
        v2.mkdir()

        (v1 / "FR-100-old.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: core
            ---
            - **FR-100 Old**: Old entry.
        """)
        )
        (v2 / "FR-150-new.md").write_text(
            textwrap.dedent("""\
            ---
            type: feat
            scope: core
            ---
            - **FR-150 New**: New entry.
        """)
        )

        output = aggregate.aggregate(changelog_dir)
        pos_61 = output.index("0.4.61")
        pos_59 = output.index("0.4.59")
        assert pos_61 < pos_59, "0.4.61 should appear before 0.4.59"


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestMigrateChangelog:
    """migrate_changelog.py splits CHANGELOG.md into fragment files."""

    def test_extracts_unreleased_entries(self, tmp_path: Path) -> None:
        """Entries under [Unreleased] go to changelog/unreleased/."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added
            - **FR-200 New Feature**: Add a new feature. (REQ-YG-200)

            ## [0.5.0] — 2026-03-01

            ### Added
            - **FR-100 Old Feature**: An old feature. (REQ-YG-100)
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        unreleased_files = list((output_dir / "unreleased").glob("*.md"))
        assert len(unreleased_files) >= 1
        assert any("FR-200" in f.name for f in unreleased_files)

    def test_extracts_versioned_entries(self, tmp_path: Path) -> None:
        """Entries under versioned sections go to changelog/{version}/."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ## [0.5.0] — 2026-03-01

            ### Added
            - **FR-100 Old Feature**: An old feature. (REQ-YG-100)

            ### Fixed
            - **FR-101 Bug Fix**: Fixed a bug.
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        version_files = list((output_dir / "0.5.0").glob("*.md"))
        assert len(version_files) >= 2
        assert any("FR-100" in f.name for f in version_files)
        assert any("FR-101" in f.name for f in version_files)

    def test_fragment_has_yaml_front_matter(self, tmp_path: Path) -> None:
        """Generated fragments have proper YAML front matter."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added
            - **FR-200 Test Feature**: Description here. (REQ-YG-200)
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        fragment = next((output_dir / "unreleased").glob("FR-200*.md"))
        content = fragment.read_text()
        assert content.startswith("---\n")
        # Parse YAML front matter
        parts = content.split("---", 2)
        front_matter = yaml.safe_load(parts[1])
        assert front_matter["type"] == "feat"
        assert front_matter["req"] == "REQ-YG-200"

    def test_fix_type_mapping(self, tmp_path: Path) -> None:
        """Entries under ### Fixed get type: fix."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Fixed
            - **FR-300 Bug**: Fixed a bug.
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        fragment = next((output_dir / "unreleased").glob("FR-300*.md"))
        content = fragment.read_text()
        parts = content.split("---", 2)
        front_matter = yaml.safe_load(parts[1])
        assert front_matter["type"] == "fix"

    def test_removal_type_mapping(self, tmp_path: Path) -> None:
        """Entries under ### Removed get type: removal."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Removed
            - **FR-400 Dead Code**: Remove dead module.
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        fragment = next((output_dir / "unreleased").glob("FR-400*.md"))
        content = fragment.read_text()
        parts = content.split("---", 2)
        front_matter = yaml.safe_load(parts[1])
        assert front_matter["type"] == "removal"

    def test_non_fr_entries_preserved(self, tmp_path: Path) -> None:
        """Entries without FR-XXX pattern are preserved with slug filename."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text(
            textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Fixed
            - **Lint Test Assertions**: Fix severity.value in tests.
        """)
        )

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)

        files = list((output_dir / "unreleased").glob("*.md"))
        assert len(files) >= 1
        content = files[0].read_text()
        assert "Lint Test Assertions" in content


# ---------------------------------------------------------------------------
# Round-Trip
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestRoundTrip:
    """Migrate → aggregate reproduces original content (modulo whitespace)."""

    def test_round_trip_simple(self, tmp_path: Path) -> None:
        """Simple changelog round-trips through migrate+aggregate."""
        migrate = _load_module(
            "migrate_changelog",
            REPO_ROOT / "scripts" / "migrate_changelog.py",
        )
        aggregate = _load_module(
            "aggregate_changelog",
            REPO_ROOT / "scripts" / "aggregate_changelog.py",
        )
        changelog = tmp_path / "CHANGELOG.md"
        original = textwrap.dedent("""\
            # Changelog

            ## [Unreleased]

            ### Added
            - **FR-200 Feature A**: Description A. (REQ-YG-200)
            - **FR-201 Feature B**: Description B.

            ### Fixed
            - **FR-202 Bug Fix**: Fixed something.

            ## [0.5.0] — 2026-03-01

            ### Added
            - **FR-100 Old Feature**: Old description. (REQ-YG-100)
        """)
        changelog.write_text(original)

        output_dir = tmp_path / "changelog"
        migrate.migrate(changelog, output_dir)
        result = aggregate.aggregate(output_dir)

        # Verify all FR entries are present in the aggregated output
        for fr in ["FR-200", "FR-201", "FR-202", "FR-100"]:
            assert fr in result, f"{fr} missing from round-trip output"

        # Verify section structure
        assert "## [Unreleased]" in result
        assert "## [0.5.0]" in result
        assert "### Added" in result
        assert "### Fixed" in result


# ---------------------------------------------------------------------------
# Directory Structure
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestDirectoryStructure:
    """changelog/ directory structure exists with .gitkeep."""

    def test_unreleased_directory_exists(self) -> None:
        """changelog/unreleased/ directory must exist."""
        assert (REPO_ROOT / "changelog" / "unreleased").is_dir()

    def test_gitkeep_exists(self) -> None:
        """changelog/unreleased/.gitkeep must exist."""
        assert (REPO_ROOT / "changelog" / "unreleased" / ".gitkeep").exists()

    def test_changelog_in_gitignore(self) -> None:
        """CHANGELOG.md must be listed in .gitignore."""
        gitignore = (REPO_ROOT / ".gitignore").read_text()
        assert "CHANGELOG.md" in gitignore


# ---------------------------------------------------------------------------
# finalize_merge.sh Fragment Creation
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestFinalizeMergeFragments:
    """finalize_merge.sh creates fragment files instead of editing CHANGELOG."""

    def test_script_creates_fragment_file(self) -> None:
        """finalize_merge.sh must reference changelog/unreleased/ for fragments."""
        script_path = REPO_ROOT / "scripts" / "finalize_merge.sh"
        content = script_path.read_text()
        assert "changelog/unreleased/" in content, (
            "finalize_merge.sh should create fragments in changelog/unreleased/"
        )

    def test_script_does_not_edit_changelog(self) -> None:
        """finalize_merge.sh must not directly edit CHANGELOG.md."""
        script_path = REPO_ROOT / "scripts" / "finalize_merge.sh"
        content = script_path.read_text()
        # Should not contain sed operations on CHANGELOG.md
        assert "CHANGELOG.md.tmp" not in content, (
            "finalize_merge.sh should not create CHANGELOG.md.tmp (old edit pattern)"
        )


# ---------------------------------------------------------------------------
# Gate Updates
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-162")
class TestGateUpdates:
    """Pre-commit and CI gates check for changelog fragments."""

    def test_precommit_checks_fragments(self) -> None:
        """Pre-commit hook checks changelog/unreleased/ not CHANGELOG.md."""
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
        # Find the changelog-required hook
        assert "changelog/unreleased/" in config, (
            "Pre-commit hook should check for changelog/unreleased/ fragments"
        )

    def test_ci_gate_checks_fragments(self) -> None:
        """CI changelog-gate checks changelog/unreleased/ not CHANGELOG.md."""
        workflow = (REPO_ROOT / ".github" / "workflows" / "commitlint.yml").read_text()
        assert "changelog/unreleased/" in workflow, (
            "CI changelog-gate should check for changelog/unreleased/ fragments"
        )
