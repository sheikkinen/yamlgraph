"""Tests for impl-agent v4 graph integration.

TDD Phase 5: Wire discovery nodes into impl-agent.yaml.
"""

from pathlib import Path

import pytest
import yaml

GRAPH_PATH = Path(__file__).parent.parent / "impl-agent.yaml"


class TestImplAgentV4Structure:
    """Test the new graph structure."""

    @pytest.fixture
    def graph_config(self) -> dict:
        """Load the graph YAML."""
        with open(GRAPH_PATH) as f:
            return yaml.safe_load(f)

    def test_has_plan_discovery_node(self, graph_config):
        """Should have plan_discovery LLM node."""
        nodes = graph_config.get("nodes", {})
        assert "plan_discovery" in nodes
        node = nodes["plan_discovery"]
        assert node.get("prompt") == "examples/codegen/plan_discovery"
        assert node.get("state_key") == "discovery_plan"

    def test_has_execute_discovery_node(self, graph_config):
        """Should have execute_discovery map node."""
        nodes = graph_config.get("nodes", {})
        assert "execute_discovery" in nodes
        node = nodes["execute_discovery"]
        assert node.get("type") == "map"
        assert "discovery_plan" in node.get("over", "")
        # Sub-node should be tool_call
        sub_node = node.get("node", {})
        assert sub_node.get("type") == "tool_call"

    def test_has_synthesize_node(self, graph_config):
        """Should have synthesize LLM node."""
        nodes = graph_config.get("nodes", {})
        assert "synthesize" in nodes
        node = nodes["synthesize"]
        assert node.get("prompt") == "examples/codegen/synthesize"
        assert node.get("state_key") == "code_analysis"

    def test_edge_flow(self, graph_config):
        """Should have correct edge flow through discovery nodes."""
        edges = graph_config.get("edges", [])

        # Convert to from->to pairs for easier checking
        edge_pairs = [(e["from"], e["to"]) for e in edges]

        # Must have: parse_story -> plan_discovery -> execute_discovery -> synthesize -> plan
        assert ("parse_story", "plan_discovery") in edge_pairs
        assert ("plan_discovery", "execute_discovery") in edge_pairs
        assert ("execute_discovery", "synthesize") in edge_pairs
        assert ("synthesize", "plan") in edge_pairs

    def test_no_agent_nodes(self, graph_config):
        """Should not have old agent nodes (discover, analyze)."""
        nodes = graph_config.get("nodes", {})
        # Old agent-based discovery is replaced
        assert "discover" not in nodes
        assert "analyze" not in nodes


class TestImplAgentV4State:
    """Test state schema includes new fields."""

    @pytest.fixture
    def graph_config(self) -> dict:
        """Load the graph YAML."""
        with open(GRAPH_PATH) as f:
            return yaml.safe_load(f)

    def test_state_has_discovery_plan(self, graph_config):
        """State should include discovery_plan."""
        state = graph_config.get("state", {})
        # Check for discovery_plan in state definition
        assert "discovery_plan" in state or any(
            "discovery_plan" in str(v) for v in state.values()
        )

    def test_state_has_discovery_findings(self, graph_config):
        """State should include discovery_findings for collected results."""
        # The collect key from map node
        nodes = graph_config.get("nodes", {})
        if "execute_discovery" in nodes:
            collect_key = nodes["execute_discovery"].get("collect", "")
            assert collect_key  # Should have a collect key
