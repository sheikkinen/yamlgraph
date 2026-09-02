"""FR-423: enforce stable FR identity and durable judge rationale persistence."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml"
PLAN_GRAPH = (
    REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml"
)
PLAN_PROMPT = (
    REPO_ROOT
    / ".chaplain"
    / "graphs"
    / "watcher-plan"
    / "prompts"
    / "plan-unified.yaml"
)
JUDGE_PROMPT = (
    REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "prompts" / "judge.yaml"
)
CHAPLAIN_YAMLGRAPH_ACTION = (
    REPO_ROOT / ".chaplain" / "actions" / "yamlgraph_async_action.py"
)


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-316")
class TestFR423IdentityConvergence:
    def test_plan_graph_accepts_fr_path_variable(self):
        graph = _yaml(PLAN_GRAPH)
        assert "fr_path" in graph["state"]
        node = graph["nodes"]["plan_unified"]
        assert node["variables"]["fr_path"] == "{state.fr_path}"

    def test_pipeline_plan_passes_fr_path(self):
        config = _yaml(PIPELINE)
        plan_vars = config["actions"]["plan"][0]["vars"]
        assert plan_vars["fr_path"] == "{fr_path}"

    def test_capture_fr_reuses_existing_fr_path_before_discovery(self):
        config = _yaml(PIPELINE)
        cmd = config["actions"]["capture_fr"][0]["command"]
        assert "{fr_path}" in cmd
        assert '-f "$FR"' in cmd

    def test_capture_fr_emits_absolute_fr_path(self):
        config = _yaml(PIPELINE)
        cmd = config["actions"]["capture_fr"][0]["command"]
        assert 'OUT="$PWD/$FR"' in cmd
        assert "fr_path" in cmd
        assert "$OUT" in cmd


@pytest.mark.req("REQ-YG-316")
class TestFR423PromptContracts:
    def test_plan_prompt_requires_in_place_edit_when_fr_path_present(self):
        prompt = _yaml(PLAN_PROMPT)["user"].lower()
        assert "if fr_path is provided" in prompt
        assert "edit that file in place" in prompt
        assert "do not create a new fr number" in prompt

    def test_judge_prompt_requires_persisted_judge_notes(self):
        user = _yaml(JUDGE_PROMPT)["user"].lower()
        assert "judge notes" in user
        assert "amend" in user and "reject" in user


@pytest.mark.req("REQ-YG-316")
class TestFR423WritebackGuard:
    def test_judge_writeback_guard_hook_present(self):
        content = CHAPLAIN_YAMLGRAPH_ACTION.read_text(encoding="utf-8")
        assert "_judge_writeback" in content
        assert 'context.get("current_state") != "judge"' in content
        assert 'event not in {"revise", "reject"}' in content
