"""Acceptance tests for FR-276/FR-317 runtime retirement and FSM entrypoint."""

from pathlib import Path

import pytest
import yaml


@pytest.mark.req("REQ-YG-276")
class TestObsoleteScriptsRemoved:
    def test_watch_sh_deleted(self):
        assert not Path(".chaplain/watch.sh").exists()

    def test_enforce_worktree_sh_deleted(self):
        assert not Path("scripts/enforce_worktree.sh").exists()

    def test_bugfix_worktree_sh_deleted(self):
        assert not Path("scripts/bugfix_worktree.sh").exists()

    def test_legacy_start_system_replacement(self):
        assert not Path(".chaplain/watcher2.sh").exists()
        start_script = Path(".chaplain/scripts/start-system.sh")
        assert start_script.exists()
        assert start_script.is_file()


@pytest.mark.req("REQ-YG-276")
class TestFsmRuntimeEntryPoint:
    def test_start_system_references_both_fsm_configs(self):
        content = Path(".chaplain/scripts/start-system.sh").read_text()
        assert "watcher-dispatcher.yaml" in content
        assert "watcher-pipeline-v2.yaml" in content

    def test_readme_points_to_start_system(self):
        content = Path(".chaplain/README.md").read_text()
        assert ".chaplain/scripts/start-system.sh" in content
        assert "watcher2.sh" not in content

    def test_worktree_setup_still_prunes_metadata(self):
        content = Path(".chaplain/lib/watcher/worktree_setup.sh").read_text()
        assert "git worktree prune" in content


@pytest.mark.req("REQ-YG-309")
class TestForensicFailurePreservation:
    def test_pipeline_failed_state_moves_topic_to_failed_dir(self):
        config = yaml.safe_load(
            Path(".chaplain/config/watcher-pipeline-v2.yaml").read_text()
        )
        failed_actions = config["actions"]["failed"]
        command = failed_actions[0]["command"]
        assert "mkdir -p .chaplain/failed" in command
        assert 'mv "{topic_file}" .chaplain/failed/' in command

    def test_forensic_graph_exists(self):
        assert Path(".chaplain/graphs/watcher-forensic/graph.yaml").exists()
