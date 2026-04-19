"""Tests for FR-220: Node type registry pattern (REQ-YG-220).

Verifies that compile_node dispatches via NODE_TYPE_HANDLERS registry
instead of an if/elif chain, and that unknown types raise ValueError.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langgraph.graph import StateGraph

from yamlgraph.constants import NodeType
from yamlgraph.graph_loader import GraphConfig
from yamlgraph.node_compiler import compile_node

# ---------------------------------------------------------------------------
# Helpers (reused from test_node_compiler_branches.py)
# ---------------------------------------------------------------------------


def _make_config(
    nodes: dict | None = None,
    source_path: Path | None = None,
    defaults: dict | None = None,
) -> GraphConfig:
    raw = {
        "nodes": nodes or {"dummy": {"prompt": "p", "state_key": "k"}},
        "edges": [{"from": "START", "to": "dummy"}, {"from": "dummy", "to": "END"}],
    }
    if defaults:
        raw["defaults"] = defaults
    return GraphConfig(raw, source_path=source_path)


def _make_graph():
    from typing import TypedDict

    class S(TypedDict):
        x: str

    return StateGraph(S)


# ---------------------------------------------------------------------------
# Registry existence and completeness
# ---------------------------------------------------------------------------


class TestNodeTypeRegistry:
    """NODE_TYPE_HANDLERS registry exists and covers all handled types."""

    @pytest.mark.req("REQ-YG-220")
    def test_registry_exists(self):
        """NODE_TYPE_HANDLERS dict is importable from node_compiler."""
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        assert isinstance(NODE_TYPE_HANDLERS, dict)

    @pytest.mark.req("REQ-YG-220")
    def test_registry_covers_all_compiled_types(self):
        """Every node type that compile_node handles has a registry entry."""
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        expected_types = {
            NodeType.TOOL,
            NodeType.PYTHON,
            NodeType.AGENT,
            NodeType.MAP,
            NodeType.TOOL_CALL,
            NodeType.INTERRUPT,
            NodeType.PASSTHROUGH,
            NodeType.COPILOT,
            NodeType.SUBGRAPH,
            NodeType.LLM,
            NodeType.ROUTER,
            NodeType.RACE,
            NodeType.A2A_CALL,
        }
        registered = set(NODE_TYPE_HANDLERS.keys())
        assert expected_types == registered

    @pytest.mark.req("REQ-YG-220")
    def test_registry_values_are_callable(self):
        """Every handler in the registry is callable."""
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        for node_type, handler in NODE_TYPE_HANDLERS.items():
            assert callable(handler), f"Handler for {node_type} is not callable"


# ---------------------------------------------------------------------------
# NodeCompileContext
# ---------------------------------------------------------------------------


class TestNodeCompileContext:
    """NodeCompileContext dataclass encapsulates compile context."""

    @pytest.mark.req("REQ-YG-220")
    def test_context_is_importable(self):
        """NodeCompileContext is importable from node_compiler."""
        from yamlgraph.node_compiler import NodeCompileContext

        assert NodeCompileContext is not None

    @pytest.mark.req("REQ-YG-220")
    def test_context_construction(self):
        """NodeCompileContext can be constructed with expected fields."""
        from yamlgraph.node_compiler import NodeCompileContext

        config = _make_config()
        graph = _make_graph()
        ctx = NodeCompileContext(
            node_name="test",
            node_config={"prompt": "p", "state_key": "k"},
            graph=graph,
            config=config,
            tools={},
            python_tools={},
            callable_registry={},
            effective_defaults={},
            prompts_dir=None,
            prompts_relative=False,
        )
        assert ctx.node_name == "test"
        assert ctx.prompts_dir is None

    @pytest.mark.req("REQ-YG-220")
    def test_context_is_frozen(self):
        """NodeCompileContext is immutable (frozen dataclass)."""
        from yamlgraph.node_compiler import NodeCompileContext

        config = _make_config()
        graph = _make_graph()
        ctx = NodeCompileContext(
            node_name="test",
            node_config={},
            graph=graph,
            config=config,
            tools={},
            python_tools={},
            callable_registry={},
            effective_defaults={},
            prompts_dir=None,
            prompts_relative=False,
        )
        with pytest.raises(AttributeError):
            ctx.node_name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Unknown type raises ValueError
# ---------------------------------------------------------------------------


class TestUnknownNodeType:
    """Unknown node types raise ValueError instead of silent fallthrough."""

    @pytest.mark.req("REQ-YG-220")
    def test_unknown_type_raises_value_error(self):
        """Passing an unregistered node type raises ValueError."""
        config = _make_config()
        graph = _make_graph()
        node_cfg = {"type": "banana", "state_key": "out"}

        with pytest.raises(ValueError, match="Unknown node type.*banana"):
            compile_node(
                "bad",
                node_cfg,
                graph,
                config,
                tools={},
                python_tools={},
                callable_registry={},
            )


# ---------------------------------------------------------------------------
# Dispatch verification
# ---------------------------------------------------------------------------


class TestRegistryDispatch:
    """compile_node dispatches via registry, not hardcoded if/elif."""

    @pytest.mark.req("REQ-YG-220")
    def test_dispatch_calls_registered_handler(self):
        """compile_node delegates to the handler from NODE_TYPE_HANDLERS."""
        from yamlgraph.node_compiler import NODE_TYPE_HANDLERS

        config = _make_config()
        graph = _make_graph()
        node_cfg = {"type": NodeType.PASSTHROUGH, "state_key": "out", "value": 0}

        # Temporarily replace the handler with a mock
        original = NODE_TYPE_HANDLERS[NodeType.PASSTHROUGH]
        mock_handler = MagicMock(return_value=None)
        NODE_TYPE_HANDLERS[NodeType.PASSTHROUGH] = mock_handler
        try:
            compile_node("pt", node_cfg, graph, config, {}, {}, {})
            mock_handler.assert_called_once()
        finally:
            NODE_TYPE_HANDLERS[NodeType.PASSTHROUGH] = original
