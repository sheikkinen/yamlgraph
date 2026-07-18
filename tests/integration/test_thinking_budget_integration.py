"""
Integration test for FR-071: Graph-Level Thinking Budget (REQ-YG-083)

Tests extended thinking with real Anthropic API.
"""

import os

import pytest

from yamlgraph.compile.graph_loader import GraphConfig, compile_graph


@pytest.mark.req("REQ-YG-083")
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_thinking_budget_runs_successfully():
    """Integration test: graph with thinking_budget executes successfully."""
    # Simple graph with thinking enabled
    graph_config_dict = {
        "defaults": {
            "provider": "anthropic",
            "model": "claude-haiku-4-5",
            "thinking_budget": 1024,  # minimum valid budget
        },
        "state": {
            "name": "str",
            "style": "str",
        },
        "nodes": {
            "greet": {
                "prompt": "greet",
                "state_key": "greeting",
            }
        },
        "edges": [{"from": "START", "to": "greet"}, {"from": "greet", "to": "END"}],
    }

    # Load and compile graph
    config = GraphConfig(graph_config_dict)
    state_graph = compile_graph(config)
    compiled = state_graph.compile()

    # Run with a simple input
    result = compiled.invoke(
        {"name": "World", "style": "casual", "iterations": []},
        {"configurable": {"thread_id": "test-thinking"}},
    )

    # Should complete successfully (actual response doesn't matter for this test)
    assert "greeting" in result
    assert result["greeting"]  # Non-empty response


@pytest.mark.req("REQ-YG-230")
@pytest.mark.skipif(
    not os.getenv("VERTEX_API_KEY"),
    reason="VERTEX_API_KEY not set",
)
def test_vertex_thinking_budget_runs_successfully():
    """Integration test: graph with thinking_budget on vertex/gemini-2.5-flash executes successfully."""
    graph_config_dict = {
        "defaults": {
            "provider": "vertex",
            "model": "gemini-2.5-flash",
            "thinking_budget": 1024,
        },
        "state": {
            "name": "str",
            "style": "str",
        },
        "nodes": {
            "greet": {
                "prompt": "greet",
                "state_key": "greeting",
            }
        },
        "edges": [{"from": "START", "to": "greet"}, {"from": "greet", "to": "END"}],
    }

    config = GraphConfig(graph_config_dict)
    state_graph = compile_graph(config)
    compiled = state_graph.compile()

    result = compiled.invoke(
        {"name": "World", "style": "casual", "iterations": []},
        {"configurable": {"thread_id": "test-vertex-thinking"}},
    )

    assert "greeting" in result
    assert result["greeting"]
