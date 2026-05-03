"""Tests for active watcher enforce session graph."""

from pathlib import Path

import pytest
import yaml

_GRAPH_PATH = Path(".chaplain/graphs/watcher-enforce/enforce-session.yaml")
_PROMPTS_DIR = Path(".chaplain/graphs/watcher-enforce/prompts")


def _load_graph() -> dict:
    with open(_GRAPH_PATH) as f:
        return yaml.safe_load(f)


@pytest.mark.req("REQ-YG-001")
class TestWatcherEnforceSessionGraph:
    def test_graph_exists(self):
        assert _GRAPH_PATH.exists()

    def test_graph_has_single_enforce_node(self):
        graph = _load_graph()
        assert set(graph["nodes"].keys()) == {"enforce"}
        node = graph["nodes"]["enforce"]
        assert node["type"] == "copilot"
        assert node["prompt"] == "enforce-session"
        assert node["state_key"] == "enforce_result"

    def test_graph_edges_are_linear(self):
        graph = _load_graph()
        assert graph["edges"] == [
            {"from": "START", "to": "enforce"},
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
            "enforce-session.yaml",
            "validate-session.yaml",
            "sanity-check-session.yaml",
        }
        found = {p.name for p in _PROMPTS_DIR.glob("*.yaml")}
        assert expected.issubset(found)
