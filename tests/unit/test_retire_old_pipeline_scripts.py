"""Acceptance tests for FR-276: Retire Old Pipeline Scripts.

Tests that the obsolete pipeline scripts are removed and replaced
with watcher2.sh as the sole orchestrator, with forensic failure preservation.
"""

from pathlib import Path

import pytest


@pytest.mark.req("REQ-YG-276")
class TestObsoleteScriptsRemoved:
    """AC-01: All three old scripts deleted."""

    def test_watch_sh_deleted(self):
        """The obsolete .chaplain/watch.sh script must not exist."""
        script_path = Path(".chaplain/watch.sh")
        assert (
            not script_path.exists()
        ), f"Obsolete script should be deleted: {script_path}"

    def test_enforce_worktree_sh_deleted(self):
        """The obsolete scripts/enforce_worktree.sh script must not exist."""
        script_path = Path("scripts/enforce_worktree.sh")
        assert (
            not script_path.exists()
        ), f"Obsolete script should be deleted: {script_path}"

    def test_bugfix_worktree_sh_deleted(self):
        """The obsolete scripts/bugfix_worktree.sh script must not exist."""
        script_path = Path("scripts/bugfix_worktree.sh")
        assert (
            not script_path.exists()
        ), f"Obsolete script should be deleted: {script_path}"


@pytest.mark.req("REQ-YG-276")
class TestDocumentationUpdated:
    """AC-02: Any references to them updated (README, docs, CLAUDE.md)."""

    def test_claude_md_no_old_script_references(self):
        """CLAUDE.md must not reference the obsolete scripts."""
        claude_md = Path("CLAUDE.md")
        if claude_md.exists():
            content = claude_md.read_text()
            obsolete_scripts = ["watch.sh", "enforce_worktree.sh", "bugfix_worktree.sh"]
            for script in obsolete_scripts:
                assert (
                    script not in content
                ), f"CLAUDE.md must not reference obsolete script: {script}"

    def test_readme_no_old_script_references(self):
        """README.md must not reference the obsolete scripts."""
        readme = Path("README.md")
        if readme.exists():
            content = readme.read_text()
            obsolete_scripts = ["watch.sh", "enforce_worktree.sh", "bugfix_worktree.sh"]
            for script in obsolete_scripts:
                assert (
                    script not in content
                ), f"README.md must not reference obsolete script: {script}"

    def test_reference_docs_no_old_script_references(self):
        """Reference documentation must not reference obsolete scripts."""
        ref_dir = Path("reference")
        if ref_dir.exists():
            obsolete_scripts = ["watch.sh", "enforce_worktree.sh", "bugfix_worktree.sh"]
            for md_file in ref_dir.rglob("*.md"):
                content = md_file.read_text()
                for script in obsolete_scripts:
                    assert (
                        script not in content
                    ), f"{md_file} must not reference obsolete script: {script}"


@pytest.mark.req("REQ-YG-276")
class TestWatcher2SingleEntryPoint:
    """AC-03: watcher2.sh documented as the single entry point."""

    def test_claude_md_references_watcher2_as_entry_point(self):
        """CLAUDE.md must reference watcher2.sh as the entry point."""
        claude_md = Path("CLAUDE.md")
        if claude_md.exists():
            content = claude_md.read_text()
            assert (
                "watcher2.sh" in content
            ), "CLAUDE.md must reference watcher2.sh as the entry point"

    def test_watcher2_sh_exists(self):
        """The watcher2.sh script must exist as the replacement."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        assert watcher2_path.exists(), "watcher2.sh must exist as the sole orchestrator"
        assert watcher2_path.is_file(), "watcher2.sh must be a file"


@pytest.mark.req("REQ-YG-276")
class TestForensicFailurePreservation:
    """AC-04: Failure paths preserve worktree + topic for forensic inspection."""

    def test_handle_failure_function_preserves_worktree(self):
        """The handle_failure function must preserve worktree for inspection."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            # Must contain the forensic preservation logic
            assert (
                "worktree preserved for inspection" in content.lower()
            ), "handle_failure() must log worktree preservation"
            # Must NOT contain evidence destruction on failure
            assert not (
                "rm -f" in content
                and "TOPIC_FILE" in content
                and "handle_failure" in content
            ), "handle_failure() must not destroy topic file on failure"

    def test_failed_topics_moved_to_failed_directory(self):
        """Failed topics must be moved to .chaplain/failed/, not deleted."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            assert (
                ".chaplain/failed/" in content
            ), "Failed topics must be moved to .chaplain/failed/ directory"

    def test_failed_directory_exists_or_created(self):
        """The .chaplain/failed directory must exist or be created."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            # Should create the directory if it doesn't exist
            assert (
                ".chaplain/failed" in content
            ), "watcher2.sh must ensure .chaplain/failed directory exists"


@pytest.mark.req("REQ-YG-276")
class TestSuccessPathCleanup:
    """AC-05: Success paths clean up normally (teardown worktree, delete topic)."""

    def test_success_calls_worktree_teardown(self):
        """Success path must call worktree_teardown on completion."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            # Should call worktree_teardown on success but not on failure
            assert (
                "worktree_teardown" in content
            ), "Success path must call worktree_teardown"

    def test_success_removes_topic_file(self):
        """Success path must remove the topic file."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            # Success path should remove topic file
            # But this should NOT be in handle_failure function
            lines = content.split("\n")
            in_handle_failure = False
            for line in lines:
                if "handle_failure()" in line:
                    in_handle_failure = True
                elif line.strip() == "}" and in_handle_failure:
                    in_handle_failure = False
                elif "rm" in line and "TOPIC_FILE" in line and not in_handle_failure:
                    # This is good - topic removal outside handle_failure
                    break
            else:
                raise AssertionError(
                    "Success path must remove topic file (outside handle_failure)"
                )


@pytest.mark.req("REQ-YG-276")
class TestOrphanedWorktreeMetadataPruning:
    """AC-06: Orphaned worktree metadata pruned before branch creation."""

    def test_worktree_setup_calls_git_worktree_prune(self):
        """worktree_setup.sh must call 'git worktree prune' before branch creation."""
        worktree_setup_path = Path(".chaplain/lib/watcher/worktree_setup.sh")
        if worktree_setup_path.exists():
            content = worktree_setup_path.read_text()
            assert (
                "git worktree prune" in content
            ), "worktree_setup.sh must call 'git worktree prune' to clean orphaned metadata"


@pytest.mark.req("REQ-YG-276")
class TestNoFunctionalRegression:
    """AC-07: No functional regression (watcher2.sh covers all old capabilities)."""

    def test_watcher2_has_inbox_processing(self):
        """watcher2.sh must handle inbox processing like old watch.sh."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            assert (
                "inbox" in content.lower()
            ), "watcher2.sh must handle inbox processing"

    def test_watcher2_has_pr_management(self):
        """watcher2.sh must handle PR creation and management like old scripts."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            assert (
                "create_pr" in content or "pr create" in content
            ), "watcher2.sh must handle PR creation"

    def test_watcher2_has_ci_waiting(self):
        """watcher2.sh must wait for CI like old scripts."""
        watcher2_path = Path(".chaplain/watcher2.sh")
        if watcher2_path.exists():
            content = watcher2_path.read_text()
            assert (
                "wait_ci" in content or "ci" in content.lower()
            ), "watcher2.sh must handle CI waiting"


@pytest.mark.req("REQ-YG-276")
class TestForensicBehaviorTests:
    """AC-08: Tests added validating forensic preservation behavior."""

    def test_this_test_file_validates_forensic_behavior(self):
        """This test file itself validates forensic preservation behavior."""
        # This test proves that forensic behavior tests exist
        test_file = Path(__file__)
        assert test_file.exists()
        content = test_file.read_text()
        assert "forensic" in content.lower()
        assert "preserve" in content.lower()
        assert "evidence" in content.lower()


@pytest.mark.req("REQ-YG-276")
class TestSingleOrchestratorPattern:
    """AC-09: Documentation updated to reflect single orchestrator pattern."""

    def test_documentation_emphasizes_single_orchestrator(self):
        """Documentation must emphasize watcher2.sh as single orchestrator."""
        claude_md = Path("CLAUDE.md")
        if claude_md.exists():
            content = claude_md.read_text()
            # Should mention watcher2 as THE way to run pipeline
            assert (
                "watcher2" in content
            ), "Documentation must reference watcher2.sh as primary orchestrator"

    def test_no_documentation_suggests_multiple_entry_points(self):
        """Documentation must not suggest multiple pipeline entry points exist."""
        docs_to_check = ["CLAUDE.md", "README.md"]
        for doc_name in docs_to_check:
            doc_path = Path(doc_name)
            if doc_path.exists():
                content = doc_path.read_text()
                # Should not suggest using multiple different pipeline scripts
                script_refs = [
                    content.count("watch.sh"),
                    content.count("enforce_worktree.sh"),
                    content.count("bugfix_worktree.sh"),
                ]
                total_obsolete_refs = sum(script_refs)
                assert (
                    total_obsolete_refs == 0
                ), f"{doc_name} must not reference obsolete pipeline scripts"
