"""Tests for changelog release sync gate (FR-192).

Validates:
  - check_changelog_release_sync.py blocks version bump when unreleased/ has fragments
  - check_changelog_release_sync.py allows version bump when unreleased/ is empty
  - check_changelog_release_sync.py allows normal commits (no version change)
  - release.sh performs atomic freeze → bump → aggregate → commit → tag
  - release.sh fails when no fragments exist in unreleased/
  - CI release-hygiene job validates tag-to-changelog alignment
  - Pre-commit hook changelog-release-sync registered in .pre-commit-config.yaml
  - reference/release-checklist.md references scripts/release.sh
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest

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
# Gate 1: check_changelog_release_sync.py
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-189")
class TestChangelogReleaseSync:
    """Pre-commit gate: version bump requires empty unreleased/."""

    def test_blocks_version_bump_with_fragments(self, tmp_path: Path) -> None:
        """Commit blocked when version bumped and unreleased/ has .md files."""
        mod = _load_module(
            "check_changelog_release_sync",
            REPO_ROOT / "scripts" / "check_changelog_release_sync.py",
        )
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True)
        (unreleased / "FR-100-feature.md").write_text("fragment")
        (unreleased / ".gitkeep").write_text("")

        # Simulate: git diff --cached shows version change
        diff_output = textwrap.dedent("""\
            -version = "0.4.62"
            +version = "0.4.63"
        """)
        result = mod.check(diff_output=diff_output, unreleased_dir=unreleased)
        assert result != 0, "Should block when version bumped with fragments"

    def test_allows_version_bump_with_empty_unreleased(self, tmp_path: Path) -> None:
        """Commit allowed when version bumped and unreleased/ has no .md files."""
        mod = _load_module(
            "check_changelog_release_sync",
            REPO_ROOT / "scripts" / "check_changelog_release_sync.py",
        )
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True)
        (unreleased / ".gitkeep").write_text("")

        diff_output = textwrap.dedent("""\
            -version = "0.4.62"
            +version = "0.4.63"
        """)
        result = mod.check(diff_output=diff_output, unreleased_dir=unreleased)
        assert result == 0, "Should allow when version bumped with empty unreleased/"

    def test_allows_normal_commit_no_version_change(self, tmp_path: Path) -> None:
        """Commit allowed when pyproject.toml version is NOT changed."""
        mod = _load_module(
            "check_changelog_release_sync",
            REPO_ROOT / "scripts" / "check_changelog_release_sync.py",
        )
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True)
        (unreleased / "FR-100-feature.md").write_text("fragment")

        # No version change in diff
        diff_output = ""
        result = mod.check(diff_output=diff_output, unreleased_dir=unreleased)
        assert result == 0, "Should allow when no version change"

    def test_allows_normal_commit_with_unrelated_changes(self, tmp_path: Path) -> None:
        """Commit allowed when pyproject.toml has changes but not version."""
        mod = _load_module(
            "check_changelog_release_sync",
            REPO_ROOT / "scripts" / "check_changelog_release_sync.py",
        )
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True)
        (unreleased / "FR-100-feature.md").write_text("fragment")

        # pyproject.toml changed but not the version line
        diff_output = textwrap.dedent("""\
            -description = "old"
            +description = "new"
        """)
        result = mod.check(diff_output=diff_output, unreleased_dir=unreleased)
        assert result == 0, "Should allow when version not changed"

    def test_lists_orphaned_fragments_in_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Error output lists the specific orphaned fragment files."""
        mod = _load_module(
            "check_changelog_release_sync",
            REPO_ROOT / "scripts" / "check_changelog_release_sync.py",
        )
        unreleased = tmp_path / "changelog" / "unreleased"
        unreleased.mkdir(parents=True)
        (unreleased / "FR-100-feature.md").write_text("fragment")
        (unreleased / "FR-101-bugfix.md").write_text("fragment")

        diff_output = '+version = "0.4.63"'
        mod.check(diff_output=diff_output, unreleased_dir=unreleased)
        captured = capsys.readouterr()
        assert "FR-100-feature.md" in captured.out
        assert "FR-101-bugfix.md" in captured.out


# ---------------------------------------------------------------------------
# Gate 2: release.sh (structural tests)
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-190")
class TestReleaseScript:
    """Atomic release script structural validation."""

    def test_release_script_exists(self) -> None:
        """scripts/release.sh must exist and be executable."""
        script = REPO_ROOT / "scripts" / "release.sh"
        assert script.exists(), "scripts/release.sh must exist"
        assert script.stat().st_mode & 0o111, "release.sh must be executable"

    def test_release_script_validates_empty_unreleased(self) -> None:
        """release.sh must check for fragments before proceeding."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "changelog/unreleased" in content, "release.sh must check unreleased dir"
        assert (
            "No fragments" in content
            or "no fragments" in content.lower()
            or "No fragment" in content.lower()
        ), "release.sh must fail when no fragments exist"

    def test_release_script_freezes_changelog(self) -> None:
        """release.sh must move fragments to versioned directory."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "mv " in content and "changelog/" in content, (
            "release.sh must move fragments"
        )

    def test_release_script_bumps_version(self) -> None:
        """release.sh must update pyproject.toml version."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "pyproject.toml" in content, "release.sh must update pyproject.toml"

    def test_release_script_aggregates_changelog(self) -> None:
        """release.sh must run aggregate_changelog.py."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "aggregate_changelog" in content, (
            "release.sh must run aggregate_changelog.py"
        )

    def test_release_script_commits_and_tags(self) -> None:
        """release.sh must create commit and tag."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "git commit" in content, "release.sh must commit"
        assert "git tag" in content, "release.sh must create tag"

    def test_release_script_uses_file_for_commit_msg(self) -> None:
        """release.sh must use -F for commit message (avoid dquote trap)."""
        script = REPO_ROOT / "scripts" / "release.sh"
        content = script.read_text()
        assert "commit -F" in content or "commit --file" in content, (
            "release.sh must use -F for commit message"
        )


# ---------------------------------------------------------------------------
# Gate 3: CI release-hygiene job
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-191")
class TestCIReleaseHygiene:
    """CI tag-push validation job in commitlint.yml."""

    def test_release_hygiene_job_exists(self) -> None:
        """commitlint.yml must have a release-hygiene job."""
        import yaml

        workflow_path = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)
        assert "release-hygiene" in workflow.get("jobs", {}), (
            "commitlint.yml must have release-hygiene job"
        )

    def test_workflow_triggers_on_tag_push(self) -> None:
        """commitlint.yml must trigger on tag pushes (v*)."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
        content = workflow_path.read_text()
        # Must have push trigger with tags
        assert "tags:" in content, "Workflow must trigger on tag pushes"
        assert "v*" in content or "'v*'" in content or '"v*"' in content, (
            "Tag trigger must match v* pattern"
        )

    def test_release_hygiene_checks_changelog_folder(self) -> None:
        """release-hygiene job must verify changelog/{VERSION}/ exists."""
        import yaml

        workflow_path = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)
        job = workflow["jobs"]["release-hygiene"]
        # Job steps must reference changelog directory check
        steps_text = str(job.get("steps", []))
        assert "changelog/" in steps_text, (
            "release-hygiene must check for changelog version folder"
        )

    def test_release_hygiene_checks_orphaned_fragments(self) -> None:
        """release-hygiene job must check for orphaned unreleased fragments."""
        import yaml

        workflow_path = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)
        job = workflow["jobs"]["release-hygiene"]
        steps_text = str(job.get("steps", []))
        assert "unreleased" in steps_text, (
            "release-hygiene must check for orphaned fragments"
        )

    def test_release_hygiene_only_runs_on_tags(self) -> None:
        """release-hygiene job must have if condition for tag pushes."""
        import yaml

        workflow_path = REPO_ROOT / ".github" / "workflows" / "commitlint.yml"
        content = workflow_path.read_text()
        workflow = yaml.safe_load(content)
        job = workflow["jobs"]["release-hygiene"]
        job_if = job.get("if", "")
        assert "refs/tags/v" in job_if, "release-hygiene must only run on tag pushes"


# ---------------------------------------------------------------------------
# Pre-commit Hook Registration
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-189")
class TestPrecommitRegistration:
    """Pre-commit hook changelog-release-sync registered."""

    def test_hook_registered(self) -> None:
        """changelog-release-sync hook must exist in .pre-commit-config.yaml."""
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
        assert "changelog-release-sync" in config, (
            "changelog-release-sync hook must be registered"
        )

    def test_hook_runs_script(self) -> None:
        """Hook must run check_changelog_release_sync.py."""
        config = (REPO_ROOT / ".pre-commit-config.yaml").read_text()
        assert "check_changelog_release_sync" in config, (
            "Hook must reference check_changelog_release_sync script"
        )


# ---------------------------------------------------------------------------
# Documentation Updates
# ---------------------------------------------------------------------------


@pytest.mark.req("REQ-YG-190")
class TestDocumentation:
    """Release checklist references scripts/release.sh."""

    def test_release_checklist_references_release_sh(self) -> None:
        """release-checklist.md must reference scripts/release.sh."""
        checklist = (REPO_ROOT / "reference" / "release-checklist.md").read_text()
        assert "scripts/release.sh" in checklist or "release.sh" in checklist, (
            "release-checklist.md must reference release.sh"
        )

    def test_release_checklist_shows_release_sh_as_canonical(self) -> None:
        """release-checklist.md must present release.sh as the canonical command."""
        checklist = (REPO_ROOT / "reference" / "release-checklist.md").read_text()
        assert "release.sh" in checklist, (
            "release-checklist.md must show release.sh as canonical"
        )
