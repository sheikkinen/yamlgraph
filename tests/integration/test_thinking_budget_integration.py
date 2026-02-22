"""
Integration test for FR-071: Graph-Level Thinking Budget (REQ-YG-083)

Tests extended thinking with real Anthropic API.
"""

import os

import pytest

from yamlgraph.graph_loader import load_graph_config_from_dict


@pytest.mark.req("REQ-YG-083")
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_thinking_budget_runs_successfully():
    """Integration test: graph with thinking_budget executes successfully."""
    # Simple graph with thinking enabled
    graph_config = {
        "defaults": {
            "provider": "anthropic",
            "model": "claude-3-7-sonnet-20250219",
            "thinking_budget": 1024,  # minimum valid budget
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
    graph = load_graph_config_from_dict(graph_config)
    compiled = graph.compile()

    # Run with a simple input
    result = compiled.invoke(
        {"name": "World", "style": "casual", "iterations": []},
        {"configurable": {"thread_id": "test-thinking"}},
    )

    # Should complete successfully (actual response doesn't matter for this test)
    assert "greeting" in result
    assert result["greeting"]  # Non-empty response
