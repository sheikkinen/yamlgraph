"""Acceptance tests for FR-339: watcher2 post-merge processing cleanup.

These tests define the RED contract for consuming stale processing topics
after a successful merge.
They MUST fail on the unmodified codebase.
"""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"
PIPELINE_V2 = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
POST_MERGE_SH = CHAPLAIN / "lib" / "watcher" / "post_merge.sh"
CHAPLAIN_README = CHAPLAIN / "README.md"


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _action_for(config: dict, state: str) -> dict:
    action = config["actions"][state]
    if isinstance(action, list):
        assert len(action) == 1, f"Expected one action for {state}, got {len(action)}"
        return action[0]
    return action


@pytest.mark.req("REQ-YG-276")
class TestFR339PostMergeProcessingCleanup:
    """AC-01..AC-09."""

    def test_ac01_ac02_done_action_exports_post_merge_context_and_owns_cleanup(self):
        """AC-01, AC-02: done exports post-merge context; no direct topic rm there."""
        config = _load_yaml(PIPELINE_V2)
        done_action = _action_for(config, "done")
        command = done_action["command"]

        assert 'PR_NUMBER="$PR_NUM"' in command
        assert 'PR_TITLE="$PR_TITLE"' in command
        assert 'TOPIC_FILE="{main_dir}/{topic_file}"' in command
        assert "bash {main_dir}/.chaplain/lib/watcher/post_merge.sh" in command
        assert "rm -f {topic_file}" not in command

    def test_ac03_post_merge_verifies_merged_state_before_processing_cleanup(self):
        """AC-03: post_merge queries PR merge state before moving processing topic."""
        content = POST_MERGE_SH.read_text(encoding="utf-8")

        assert "gh pr view" in content
        assert "--json state" in content
        assert ".state" in content
        assert "MERGED" in content

    def test_ac04_ac05_processing_topic_moves_to_done_with_idempotent_missing_path(
        self,
    ):
        """AC-04, AC-05: processing topic moved to done; missing source is explicit no-op."""
        content = POST_MERGE_SH.read_text(encoding="utf-8")
        lower = content.lower()

        assert ".chaplain/processing" in content
        assert ".chaplain/done" in content
        assert "mv " in content
        assert "processing topic" in lower
        assert "missing" in lower and "processing" in lower

    def test_ac06_unmerged_pr_state_skips_processing_move_explicitly(self):
        """AC-06: unmerged/unknown PR state path is explicit and skip-logged."""
        content = POST_MERGE_SH.read_text(encoding="utf-8").lower()

        assert "not merged" in content or "unmerged" in content
        assert "skip" in content and "processing" in content

    def test_ac07_existing_post_merge_behaviors_still_present(self):
        """AC-07: issue close, inbox consumption, and main sync are preserved."""
        content = POST_MERGE_SH.read_text(encoding="utf-8")

        assert "gh issue close" in content
        assert "consume_matching_inbox_items" in content
        assert "sync_main_after_merge" in content

    def test_ac09_readme_documents_processing_cleanup_contract(self):
        """AC-09: README documents merged-state-gated processing cleanup."""
        content = CHAPLAIN_README.read_text(encoding="utf-8").lower()

        assert "post_merge" in content or "post-merge" in content
        assert "gh pr view" in content and "state" in content
        assert (
            "moves merged topics from .chaplain/processing/ to .chaplain/done/"
            in content
        )
