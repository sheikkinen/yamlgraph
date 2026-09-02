"""Tests for FR-257: Chaplain research guidance in watcher-plan runtime."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_GRAPH = (
    REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-plan-unified.yaml"
)
JUDGE_GRAPH = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "step-judge-v2.yaml"
PIPELINE_CONFIG = REPO_ROOT / ".chaplain" / "config" / "watcher-pipeline-v2.yaml"
PROMPTS_DIR = REPO_ROOT / ".chaplain" / "graphs" / "watcher-plan" / "prompts"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.req("REQ-YG-260")
class TestResearchGuidanceInUnifiedPlan:
    def test_plan_graph_exists(self):
        assert PLAN_GRAPH.exists()

    def test_plan_unified_node_exists(self):
        graph = _load_yaml(PLAN_GRAPH)
        assert "plan_unified" in graph["nodes"]
        node = graph["nodes"]["plan_unified"]
        assert node["type"] == "copilot"
        assert node["prompt"] == "plan-unified"
        assert node["state_key"] == "plan_result"

    def test_plan_prompt_mentions_research(self):
        prompt = _load_yaml(PROMPTS_DIR / "plan-unified.yaml")
        user = prompt["user"].lower()
        assert "research" in user
        assert "existing patterns" in user or "existing" in user

    def test_pipeline_plan_phase_mentions_research(self):
        config = _load_yaml(PIPELINE_CONFIG)
        action = config["actions"]["plan"][0]
        assert "research" in action.get("description", "").lower()


@pytest.mark.req("REQ-YG-260")
class TestResearchPromptArtifact:
    def test_research_prompt_file_exists(self):
        assert (PROMPTS_DIR / "research.yaml").exists()

    def test_research_prompt_has_system_and_user(self):
        prompt = _load_yaml(PROMPTS_DIR / "research.yaml")
        assert "system" in prompt
        assert "user" in prompt

    def test_research_prompt_required_signals(self):
        user = _load_yaml(PROMPTS_DIR / "research.yaml")["user"].lower()
        assert "existing abstraction" in user or "overlapping" in user
        assert "diary" in user
        assert "classification" in user or "classify" in user
        assert "usage" in user
        assert "feature-requests/" in user


@pytest.mark.req("REQ-YG-260")
class TestJudgePromptClassification:
    def test_judge_graph_uses_local_prompt_dir(self):
        graph = _load_yaml(JUDGE_GRAPH)
        assert graph["prompts_dir"] == "prompts"

    def test_judge_prompt_mentions_research_brief(self):
        user = _load_yaml(PROMPTS_DIR / "judge.yaml")["user"].lower()
        assert "research brief" in user or "research" in user

    def test_judge_prompt_has_classification_options(self):
        user = _load_yaml(PROMPTS_DIR / "judge.yaml")["user"].lower()
        assert "framework primitive" in user or "primitive" in user
        assert "pattern documentation" in user or "pattern doc" in user
        assert "contrib" in user


@pytest.mark.req("REQ-YG-260")
class TestWatcherPlanGraphValidity:
    def test_plan_graph_yaml_valid(self):
        graph = _load_yaml(PLAN_GRAPH)
        assert graph["version"] == "1.0"
        assert "nodes" in graph
        assert "edges" in graph

    def test_plan_graph_edges_reference_known_nodes(self):
        graph = _load_yaml(PLAN_GRAPH)
        node_names = set(graph["nodes"].keys()) | {"START", "END"}
        for edge in graph["edges"]:
            assert edge["from"] in node_names
            assert edge["to"] in node_names
