"""Tests for FR-211: Router route mapping redirect for interrupt targets.

Router conditional edges with `to: [list]` targets must redirect
interrupt node names to their `*_prepare` split equivalents in the
route mapping, while keeping original names as route labels for
make_router_fn matching.
"""

from unittest.mock import MagicMock

import pytest

from yamlgraph.edge_compiler import _add_conditional_edges


class TestRouterInterruptRedirect:
    """FR-211: _add_conditional_edges redirects interrupt targets."""

    @pytest.mark.req("REQ-YG-214")
    def test_interrupt_target_redirected_to_prepare(self):
        """Router target in interrupt_nodes maps to {name}_prepare."""
        graph = MagicMock()
        router_edges = {"classify": ["normal_node", "ask_priority"]}
        interrupt_nodes = {"ask_priority"}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            interrupt_nodes=interrupt_nodes,
        )

        # Verify add_conditional_edges was called
        graph.add_conditional_edges.assert_called_once()
        args = graph.add_conditional_edges.call_args
        source = args[0][0]
        route_mapping = args[0][2]

        assert source == "classify"
        # Non-interrupt target unchanged
        assert route_mapping["normal_node"] == "normal_node"
        # Interrupt target redirected to prepare
        assert route_mapping["ask_priority"] == "ask_priority_prepare"

    @pytest.mark.req("REQ-YG-214")
    def test_non_interrupt_targets_unchanged(self):
        """Router targets not in interrupt_nodes remain identity-mapped."""
        graph = MagicMock()
        router_edges = {"router": ["node_a", "node_b", "node_c"]}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            interrupt_nodes=set(),
        )

        args = graph.add_conditional_edges.call_args
        route_mapping = args[0][2]

        assert route_mapping == {
            "node_a": "node_a",
            "node_b": "node_b",
            "node_c": "node_c",
        }

    @pytest.mark.req("REQ-YG-214")
    def test_router_fn_receives_original_target_names(self):
        """make_router_fn gets original names, not redirected ones."""
        graph = MagicMock()
        router_edges = {"classify": ["store_intent", "ask_priority"]}
        interrupt_nodes = {"ask_priority"}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            interrupt_nodes=interrupt_nodes,
        )

        args = graph.add_conditional_edges.call_args
        router_fn = args[0][1]

        # Router function should match original names
        assert router_fn({"_route": "ask_priority"}) == "ask_priority"
        assert router_fn({"_route": "store_intent"}) == "store_intent"

    @pytest.mark.req("REQ-YG-214")
    def test_interrupt_nodes_none_leaves_identity_mapping(self):
        """When interrupt_nodes is None, all targets identity-mapped."""
        graph = MagicMock()
        router_edges = {"router": ["a", "b"]}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            interrupt_nodes=None,
        )

        args = graph.add_conditional_edges.call_args
        route_mapping = args[0][2]
        assert route_mapping == {"a": "a", "b": "b"}

    @pytest.mark.req("REQ-YG-214")
    def test_subgraph_interrupt_target_redirected_to_run(self):
        """Router target in subgraph_interrupt_nodes maps to {name}__run."""
        graph = MagicMock()
        router_edges = {"classify": ["normal", "sub_interrupt"]}
        subgraph_interrupt_nodes = {"sub_interrupt"}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            subgraph_interrupt_nodes=subgraph_interrupt_nodes,
        )

        args = graph.add_conditional_edges.call_args
        route_mapping = args[0][2]

        assert route_mapping["normal"] == "normal"
        assert route_mapping["sub_interrupt"] == "sub_interrupt__run"

    @pytest.mark.req("REQ-YG-214")
    def test_mixed_interrupt_and_subgraph_interrupt_targets(self):
        """Router with both interrupt and subgraph interrupt targets."""
        graph = MagicMock()
        router_edges = {"classify": ["normal", "interrupt_node", "subgraph_int"]}
        interrupt_nodes = {"interrupt_node"}
        subgraph_interrupt_nodes = {"subgraph_int"}

        _add_conditional_edges(
            graph,
            router_edges,
            expression_edges={},
            interrupt_nodes=interrupt_nodes,
            subgraph_interrupt_nodes=subgraph_interrupt_nodes,
        )

        args = graph.add_conditional_edges.call_args
        route_mapping = args[0][2]

        assert route_mapping["normal"] == "normal"
        assert route_mapping["interrupt_node"] == "interrupt_node_prepare"
        assert route_mapping["subgraph_int"] == "subgraph_int__run"
