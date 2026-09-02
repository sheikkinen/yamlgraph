"""Tests for active watcher enforce session graph."""

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.process

_GRAPH_PATH = Path(".chaplain/graphs/watcher-enforce/enforce-session.yaml")
_PROMPTS_DIR = Path(".chaplain/graphs/watcher-enforce/prompts")


def _load_graph() -> dict:
    with open(_GRAPH_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.req("REQ-YG-001")
class TestWatcherEnforceSessionGraph:
    def test_graph_exists(self):
        assert _GRAPH_PATH.exists()

    def test_graph_has_context_planner_assembler_and_enforce_nodes(self):
        graph = _load_graph()
        assert set(graph["nodes"].keys()) == {
            "load_module_map",
            "plan_context",
            "assemble_context",
            "enforce",
        }

        load_map_node = graph["nodes"]["load_module_map"]
        assert load_map_node["type"] == "python"

        plan_node = graph["nodes"]["plan_context"]
        assert plan_node["type"] == "llm"
        assert plan_node["prompt"] == "context-planner"

        assemble_node = graph["nodes"]["assemble_context"]
        assert assemble_node["type"] == "python"
        assert assemble_node["tool"] == "assemble_context_tool"

        enforce_node = graph["nodes"]["enforce"]
        assert enforce_node["type"] == "copilot"
        assert enforce_node["prompt"] == "enforce-session"
        assert enforce_node["state_key"] == "enforce_result"

    def test_graph_edges_are_linear(self):
        graph = _load_graph()
        assert graph["edges"] == [
            {"from": "START", "to": "load_module_map"},
            {"from": "load_module_map", "to": "plan_context"},
            {"from": "plan_context", "to": "assemble_context"},
            {"from": "assemble_context", "to": "enforce"},
            {"from": "enforce", "to": "END"},
        ]

    def test_no_loop_configuration(self):
        graph = _load_graph()
        assert "loop_limits" not in graph
        assert "loop_exits" not in graph


@pytest.mark.req("REQ-YG-012")
class TestWatcherEnforcePrompts:
    def test_active_session_prompts_exist(self):
        expected = {
            "context-planner.yaml",
            "enforce-session.yaml",
            "validate-session.yaml",
            "sanity-check-session.yaml",
        }
        found = {p.name for p in _PROMPTS_DIR.glob("*.yaml")}
        assert expected.issubset(found)
