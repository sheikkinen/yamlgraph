"""Tests for node-level caching via LangGraph CachePolicy (FR-032).

REQ-YG-235: Per-node `cache` field in YAML config → CachePolicy on add_node().
"""

from typing import TypedDict
from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph import StateGraph
from langgraph.types import CachePolicy

from yamlgraph.models.graph_schema import CacheConfig, NodeConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_graph():
    """Create a StateGraph with a simple state schema."""

    class S(TypedDict):
        x: str

    return StateGraph(S)


def _make_config(nodes=None, source_path=None):
    """Build a minimal valid GraphConfig."""
    from pathlib import Path

    from yamlgraph.graph_loader import GraphConfig

    raw = {
        "nodes": nodes or {"dummy": {"prompt": "p", "state_key": "k"}},
        "edges": [{"from": "START", "to": "dummy"}, {"from": "dummy", "to": "END"}],
    }
    return GraphConfig(raw, source_path=source_path or Path("/fake"))


# ===========================================================================
# Schema tests — CacheConfig and NodeConfig.cache field
# ===========================================================================


class TestCacheConfigSchema:
    """CacheConfig Pydantic model validates cache settings."""

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_default_ttl_none(self):
        """CacheConfig() has ttl=None by default."""
        cfg = CacheConfig()
        assert cfg.ttl is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_with_ttl(self):
        """CacheConfig(ttl=3600) stores TTL."""
        cfg = CacheConfig(ttl=3600)
        assert cfg.ttl == 3600

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_rejects_negative_ttl(self):
        """Negative TTL is invalid."""
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            CacheConfig(ttl=-1)

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_rejects_zero_ttl(self):
        """Zero TTL is invalid (use cache: false instead)."""
        with pytest.raises(ValueError, match="greater than or equal to 1"):
            CacheConfig(ttl=0)


class TestNodeConfigCacheField:
    """NodeConfig.cache field parses YAML cache shorthand."""

    @pytest.mark.req("REQ-YG-235")
    def test_cache_default_none(self):
        """No cache field → None."""
        node = NodeConfig(prompt="p", state_key="k")
        assert node.cache is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_true_becomes_cache_config(self):
        """cache: true → CacheConfig()."""
        node = NodeConfig(prompt="p", state_key="k", cache=True)
        assert isinstance(node.cache, CacheConfig)
        assert node.cache.ttl is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_false_becomes_none(self):
        """cache: false → None."""
        node = NodeConfig(prompt="p", state_key="k", cache=False)
        assert node.cache is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_dict_with_ttl(self):
        """cache: {ttl: 3600} → CacheConfig(ttl=3600)."""
        node = NodeConfig(prompt="p", state_key="k", cache={"ttl": 3600})
        assert isinstance(node.cache, CacheConfig)
        assert node.cache.ttl == 3600

    @pytest.mark.req("REQ-YG-235")
    def test_cache_dict_empty(self):
        """cache: {} → CacheConfig() (no TTL)."""
        node = NodeConfig(prompt="p", state_key="k", cache={})
        assert isinstance(node.cache, CacheConfig)
        assert node.cache.ttl is None


# ===========================================================================
# Node compiler tests — cache_policy passed to add_node()
# ===========================================================================


class TestNodeCompilerCachePolicy:
    """compile_node passes CachePolicy to graph.add_node()."""

    @pytest.mark.req("REQ-YG-235")
    @patch("yamlgraph.node_compiler.create_node_function", return_value=lambda s: {})
    def test_llm_node_with_cache_true(self, mock_factory):
        """cache: true → add_node called with cache_policy=CachePolicy()."""
        from yamlgraph.node_compiler import compile_node

        config = _make_config()
        graph = _make_graph()
        node_cfg = {"type": "llm", "prompt": "p", "state_key": "k", "cache": True}

        with patch.object(graph, "add_node", wraps=graph.add_node) as spy:
            compile_node(
                "cached_node",
                node_cfg,
                graph,
                config,
                tools={},
                python_tools={},
                callable_registry={},
            )
            spy.assert_called_once()
            call_kwargs = spy.call_args
            assert call_kwargs.kwargs.get("cache_policy") is not None
            policy = call_kwargs.kwargs["cache_policy"]
            assert isinstance(policy, CachePolicy)
            assert policy.ttl is None

    @pytest.mark.req("REQ-YG-235")
    @patch("yamlgraph.node_compiler.create_node_function", return_value=lambda s: {})
    def test_llm_node_with_cache_ttl(self, mock_factory):
        """cache: {ttl: 3600} → add_node called with CachePolicy(ttl=3600)."""
        from yamlgraph.node_compiler import compile_node

        config = _make_config()
        graph = _make_graph()
        node_cfg = {
            "type": "llm",
            "prompt": "p",
            "state_key": "k",
            "cache": {"ttl": 3600},
        }

        with patch.object(graph, "add_node", wraps=graph.add_node) as spy:
            compile_node(
                "cached_node",
                node_cfg,
                graph,
                config,
                tools={},
                python_tools={},
                callable_registry={},
            )
            spy.assert_called_once()
            policy = spy.call_args.kwargs["cache_policy"]
            assert isinstance(policy, CachePolicy)
            assert policy.ttl == 3600

    @pytest.mark.req("REQ-YG-235")
    @patch("yamlgraph.node_compiler.create_node_function", return_value=lambda s: {})
    def test_llm_node_without_cache(self, mock_factory):
        """No cache field → add_node called without cache_policy."""
        from yamlgraph.node_compiler import compile_node

        config = _make_config()
        graph = _make_graph()
        node_cfg = {"type": "llm", "prompt": "p", "state_key": "k"}

        with patch.object(graph, "add_node", wraps=graph.add_node) as spy:
            compile_node(
                "uncached_node",
                node_cfg,
                graph,
                config,
                tools={},
                python_tools={},
                callable_registry={},
            )
            spy.assert_called_once()
            # No cache_policy kwarg or None
            policy = spy.call_args.kwargs.get("cache_policy")
            assert policy is None

    @pytest.mark.req("REQ-YG-235")
    @patch("yamlgraph.node_compiler.create_tool_node", return_value=lambda s: {})
    def test_tool_node_with_cache(self, mock_factory):
        """Tool nodes also support cache policy."""
        from yamlgraph.constants import NodeType
        from yamlgraph.node_compiler import compile_node

        config = _make_config()
        graph = _make_graph()
        node_cfg = {
            "type": NodeType.TOOL,
            "tool": "my_tool",
            "state_key": "out",
            "cache": True,
        }

        with patch.object(graph, "add_node", wraps=graph.add_node) as spy:
            compile_node(
                "cached_tool",
                node_cfg,
                graph,
                config,
                tools={"my_tool": MagicMock()},
                python_tools={},
                callable_registry={},
            )
            spy.assert_called_once()
            policy = spy.call_args.kwargs.get("cache_policy")
            assert isinstance(policy, CachePolicy)


# ===========================================================================
# resolve_cache_policy unit test
# ===========================================================================


class TestResolveCachePolicy:
    """resolve_cache_policy converts CacheConfig → CachePolicy."""

    @pytest.mark.req("REQ-YG-235")
    def test_none_returns_none(self):
        from yamlgraph.node_compiler import resolve_cache_policy

        assert resolve_cache_policy(None) is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_no_ttl(self):
        from yamlgraph.node_compiler import resolve_cache_policy

        policy = resolve_cache_policy(CacheConfig())
        assert isinstance(policy, CachePolicy)
        assert policy.ttl is None

    @pytest.mark.req("REQ-YG-235")
    def test_cache_config_with_ttl(self):
        from yamlgraph.node_compiler import resolve_cache_policy

        policy = resolve_cache_policy(CacheConfig(ttl=600))
        assert isinstance(policy, CachePolicy)
        assert policy.ttl == 600
