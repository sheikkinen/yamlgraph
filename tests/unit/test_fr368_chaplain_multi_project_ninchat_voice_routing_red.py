"""Acceptance tests for FR-368 watcher2 multi-project ninchat_voice routing."""

import importlib.util
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

WORKTREE = Path(__file__).resolve().parents[2]
CHAPLAIN = WORKTREE / ".chaplain"

DISPATCHER_CONFIG = CHAPLAIN / "config" / "watcher-dispatcher.yaml"
PIPELINE_CONFIG = CHAPLAIN / "config" / "watcher-pipeline-v2.yaml"
WORKTREE_SETUP = CHAPLAIN / "lib" / "watcher" / "worktree_setup.sh"
DISPATCH_TOPIC = CHAPLAIN / "lib" / "watcher" / "dispatch_topic.py"
PROJECT_CONTRACT = CHAPLAIN / "lib" / "watcher" / "project_contract.py"
VALIDATE_GATE_ACTION = CHAPLAIN / "actions" / "validate_gate_action.py"
PLAN_GRAPH = CHAPLAIN / "graphs" / "watcher-plan" / "step-plan-unified.yaml"
PLAN_PROMPT = CHAPLAIN / "graphs" / "watcher-plan" / "prompts" / "plan-unified.yaml"
NINCHAT_MANIFEST = WORKTREE / "projects" / "ninchat_voice" / "chaplain.yaml"


def _load_yaml(path: Path) -> dict:
    assert path.exists(), f"Missing YAML file: {path}"
    with path.open() as f:
        return yaml.safe_load(f)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.mark.req("REQ-YG-316")
class TestFR368ChaplainMultiProjectNinchatVoiceRouting:
    def test_ac01_dispatcher_scans_yamlgraph_root_and_ninchat_lane(self):
        dispatcher = _load_yaml(DISPATCHER_CONFIG)
        sync_command = dispatcher["actions"]["syncing_inbox"][0]["command"]
        dispatch_topic_text = DISPATCH_TOPIC.read_text()

        assert "dispatch_topic.py" in sync_command
        assert 'inbox_dir.glob("*.md")' in dispatch_topic_text
        assert 'inbox_dir / "ninchat_voice"' in dispatch_topic_text

    def test_ac02_dispatcher_emits_project_contract_context_keys(self):
        dispatcher = _load_yaml(DISPATCHER_CONFIG)
        capture_keys = set(dispatcher["actions"]["syncing_inbox"][0]["capture_keys"])
        expected = {
            "project",
            "branch_prefix",
            "work_dir",
            "test_cmd",
            "precommit_config",
            "fr_template",
            "architecture_doc",
            "topic_file",
        }
        assert expected.issubset(capture_keys)

    def test_ac03_processing_topic_initial_context_propagates_project_keys(self):
        dispatcher = _load_yaml(DISPATCHER_CONFIG)
        command = dispatcher["actions"]["processing_topic"][0]["command"]
        for key in (
            "project",
            "branch_prefix",
            "work_dir",
            "test_cmd",
            "precommit_config",
            "fr_template",
            "architecture_doc",
        ):
            assert key in command

    def test_ac04_worktree_setup_uses_manifest_branch_prefix_and_work_dir(self):
        content = WORKTREE_SETUP.read_text()
        pipeline = _load_yaml(PIPELINE_CONFIG)
        setup_command = pipeline["actions"]["setup"][0]["command"]

        assert "--branch-prefix {branch_prefix}" in setup_command
        assert "--work-dir {work_dir}" in setup_command
        assert "--branch-prefix) BRANCH_PREFIX=" in content
        assert "--work-dir) WORK_DIR=" in content
        assert 'WT_BRANCH="${BRANCH_PREFIX}${topic_basename}"' in content

    def test_ac05a_validate_gate_yamlgraph_checks_unchanged(self):
        action = VALIDATE_GATE_ACTION.read_text()
        assert '["pre-commit", "run", "--all-files"]' in action
        assert '"name": "commit_title"' in action
        assert '"name": "branch_freshness_fetch"' in action
        assert '"name": "diary_parity"' in action

    def test_ac05b_validate_gate_ninchat_uses_project_precommit_config_and_test_cmd(
        self,
    ):
        action = VALIDATE_GATE_ACTION.read_text()
        assert 'context.get("precommit_config"' in action
        assert '--config", precommit_config' in action
        assert 'context.get("test_cmd"' in action
        assert '["bash", "-lc", test_cmd]' in action

    def test_ac06a_plan_unified_passes_project_template_archdoc_and_project_system_text(
        self,
    ):
        graph = _load_yaml(PLAN_GRAPH)
        prompt = _load_yaml(PLAN_PROMPT)
        variables = graph["nodes"]["plan_unified"]["variables"]
        state_fields = graph["state"]

        assert state_fields["project"] == "str"
        assert state_fields["fr_template"] == "str"
        assert state_fields["architecture_doc"] == "str"
        assert variables["project"] == "{state.project}"
        assert variables["fr_template"] == "{state.fr_template}"
        assert variables["architecture_doc"] == "{state.architecture_doc}"
        assert "{{ project }}" in prompt["system"]
        assert "{{ fr_template }}" in prompt["user"]
        assert "{{ architecture_doc }}" in prompt["user"]

    def test_ac06b_capture_fr_searches_project_fr_directory_from_template_path(self):
        pipeline = _load_yaml(PIPELINE_CONFIG)
        command = pipeline["actions"]["capture_fr"][0]["command"]
        assert 'FR_TEMPLATE="{fr_template}"' in command
        assert 'FR_DIR=$(dirname "$FR_TEMPLATE")' in command
        assert 'FR_GLOB="$FR_DIR/FR-*.md"' in command

    def test_ac07_yamlgraph_flat_root_lane_contract_unchanged(self):
        dispatch_topic_text = DISPATCH_TOPIC.read_text()
        root_pick = dispatch_topic_text.find('inbox_dir.glob("*.md")')
        ninchat_pick = dispatch_topic_text.find('inbox_dir / "ninchat_voice"')
        assert root_pick != -1
        assert ninchat_pick != -1
        assert root_pick < ninchat_pick

    def test_ac08_manifest_schema_requires_fields_and_repo_relative_paths_with_red_precondition(
        self,
    ):
        project_contract = _load_module(PROJECT_CONTRACT, "fr368_project_contract")

        loaded = project_contract.load_ninchat_voice_manifest(NINCHAT_MANIFEST)
        assert loaded.project == "ninchat_voice"

        with pytest.raises(FileNotFoundError):
            project_contract.load_ninchat_voice_manifest(
                WORKTREE / "projects" / "ninchat_voice" / "missing.yaml"
            )

        with pytest.raises(ValidationError):
            project_contract.NinchatVoiceManifest.model_validate(
                {"project": "ninchat_voice"}
            )

        with pytest.raises(ValidationError):
            project_contract.NinchatVoiceManifest.model_validate(
                {
                    "project": "ninchat_voice",
                    "branch_prefix": "feat/nv-",
                    "work_dir": "projects/ninchat_voice",
                    "test_cmd": "pytest projects/ninchat_voice/tests/ -q --no-cov",
                    "precommit_config": "/absolute/path.yaml",
                    "fr_template": "projects/ninchat_voice/feature-requests/TEMPLATE.md",
                    "architecture_doc": "projects/ninchat_voice/README.md",
                }
            )
