"""Tests for FR-260: acceptance tests are authored before enforce execution."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_CONFIG = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml"
PLAN_GRAPH = (
    REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml"
)
PLAN_PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "prompts"
ENFORCE_GRAPH = (
    REPO_ROOT / ".chaplain" / "graphs" / "watcher-enforce" / "enforce-session.yaml"
)
ENFORCE_PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "watcher-enforce" / "prompts"
WORKTREE_TOOL = REPO_ROOT / ".chaplain" / "lib" / "worktree.py"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-263")
class TestPipelineFlow:
    def test_setup_creates_worktree_before_plan(self):
        config = _load_yaml(PIPELINE_CONFIG)
        setup_cmd = config["actions"]["setup"][0]["command"]
        assert "worktree_setup.sh" in setup_cmd

    def test_plan_runs_before_judge_and_enforce(self):
        transitions = _load_yaml(PIPELINE_CONFIG)["transitions"]
        pairs = {(t["from"], t["to"]) for t in transitions}
        assert ("setup", "plan") in pairs
        assert ("plan", "capture_fr") in pairs
        assert ("capture_fr", "judge") in pairs
        assert ("judge", "enforce_session") in pairs

    def test_plan_uses_unified_planning_graph(self):
        config = _load_yaml(PIPELINE_CONFIG)
        plan_action = config["actions"]["plan"][0]
        assert (
            plan_action["graph"]
            == ".chaplain/graphs/watcher-plan/step-plan-unified.yaml"
        )
        description = plan_action["description"].lower()
        assert "tests" in description and "research" in description


@pytest.mark.req("REQ-YG-263")
class TestPlanArtifacts:
    def test_plan_graph_exists_and_has_plan_unified_node(self):
        graph = _load_yaml(PLAN_GRAPH)
        assert "plan_unified" in graph["nodes"]
        node = graph["nodes"]["plan_unified"]
        assert node["type"] == "copilot"
        assert node["prompt"] == "plan-unified"
        assert node["state_key"] == "plan_result"

    def test_write_acceptance_tests_prompt_exists_in_active_path(self):
        path = PLAN_PROMPTS_DIR / "write-acceptance-tests.yaml"
        assert path.exists(), f"Missing {path}"

    def test_write_acceptance_tests_prompt_instructions(self):
        prompt = _load_yaml(PLAN_PROMPTS_DIR / "write-acceptance-tests.yaml")
        user = prompt["user"]
        user_lower = user.lower()
        assert "acceptance criteria" in user_lower
        assert "pytest.mark.req" in user
        assert "SKIP=pytest" in user
        assert "{worktree_dir}" in user
        assert (
            "{branch}" in (PLAN_PROMPTS_DIR / "write-acceptance-tests.yaml").read_text(encoding="utf-8")
        )

    def test_judge_prompt_criterion_8_still_present(self):
        judge = (PLAN_PROMPTS_DIR / "judge.yaml").read_text(encoding="utf-8").lower()
        assert "8." in judge
        assert "acceptance test" in judge or "test evidence" in judge
        assert "amend" in judge


@pytest.mark.req("REQ-YG-263")
class TestEnforceSessionContract:
    def test_enforce_graph_exists(self):
        assert ENFORCE_GRAPH.exists()

    def test_enforce_session_prompt_references_existing_tests(self):
        prompt = (ENFORCE_PROMPTS_DIR / "enforce-session.yaml").read_text(encoding="utf-8").lower()
        assert "acceptance tests" in prompt or "acceptance test" in prompt
        assert "do not modify acceptance test assertions" in prompt


@pytest.mark.req("REQ-YG-263")
class TestCreateWorktreeTool:
    def test_worktree_tool_file_exists(self):
        assert WORKTREE_TOOL.exists()

    def test_worktree_tool_has_create_worktree_function(self):
        content = WORKTREE_TOOL.read_text(encoding="utf-8")
        assert "def create_worktree(" in content
        assert "worktree_dir" in content
        assert "branch" in content

    def test_worktree_tool_uses_worktree_helpers(self):
        content = WORKTREE_TOOL.read_text(encoding="utf-8")
        assert "derive_branch_name" in content
        assert "construct_worktree_path" in content
