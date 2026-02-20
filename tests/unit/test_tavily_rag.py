"""Unit tests for Tavily domain RAG demo (FR-053).

Tests the tavily_retrieve tool function with mocked Tavily API
and validates graph YAML structure.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import yaml

GRAPH_PATH = "examples/demos/tavily_rag/graph.yaml"
GRAPH_DEEP_PATH = "examples/demos/tavily_rag/graph-deep.yaml"


class TestTavilyRetrieveFunction:
    """Test the tavily_retrieve tool function."""

    @pytest.mark.req("REQ-YG-076")
    def test_empty_query_returns_error(self):
        """Empty query should return error string."""
        from examples.demos.tavily_rag.nodes.tavily_retrieve import tavily_retrieve

        result = tavily_retrieve({"question": ""})
        assert "Error" in result
        assert "empty" in result.lower()

    @pytest.mark.req("REQ-YG-076")
    def test_empty_state_returns_error(self):
        """State with no query/question should return error."""
        from examples.demos.tavily_rag.nodes.tavily_retrieve import tavily_retrieve

        result = tavily_retrieve({})
        assert "Error" in result
        assert "empty" in result.lower()

    @pytest.mark.req("REQ-YG-076")
    def test_missing_api_key_returns_error(self):
        """Missing TAVILY_API_KEY should return clear error."""
        from examples.demos.tavily_rag.nodes.tavily_retrieve import tavily_retrieve

        with patch.dict("os.environ", {}, clear=True):
            result = tavily_retrieve({"question": "test query"})
        assert "TAVILY_API_KEY" in result

    @pytest.mark.req("REQ-YG-076")
    def test_missing_package_returns_error(self):
        """Missing tavily-python package should return clear error."""
        from examples.demos.tavily_rag.nodes.tavily_retrieve import tavily_retrieve

        with (
            patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}),
            patch.dict("sys.modules", {"tavily": None}),
        ):
            result = tavily_retrieve({"question": "test query"})
        assert "tavily-python" in result or "not installed" in result.lower()

    @pytest.mark.req("REQ-YG-076")
    def test_successful_retrieval_with_mocked_api(self):
        """Mocked Tavily API should return formatted context."""
        mock_response = {
            "answer": "Tavily summary answer",
            "results": [
                {
                    "title": "Test Page",
                    "url": "https://example.com/page",
                    "content": "Snippet content here",
                    "raw_content": "Full raw content of the page",
                    "score": 0.95,
                },
            ],
        }

        mock_client = MagicMock()
        mock_client.search.return_value = mock_response
        mock_tavily_module = MagicMock()
        mock_tavily_module.TavilyClient.return_value = mock_client

        import sys

        from examples.demos.tavily_rag.nodes.tavily_retrieve import (
            tavily_retrieve,  # noqa: F401
        )

        with (
            patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}),
            patch.dict(sys.modules, {"tavily": mock_tavily_module}),
        ):
            # Need to reimport to pick up the mocked module
            import importlib

            import examples.demos.tavily_rag.nodes.tavily_retrieve as mod

            importlib.reload(mod)
            result = mod.tavily_retrieve({"question": "What services?"})

        assert "Test Page" in result
        assert "https://example.com/page" in result
        assert "Tavily summary answer" in result
        assert "0.95" in result

    @pytest.mark.req("REQ-YG-076")
    def test_reads_query_key_for_map_subnode(self):
        """Map sub-node passes item as state['query'] via as: query."""
        from examples.demos.tavily_rag.nodes.tavily_retrieve import tavily_retrieve

        # When both query and question are present, query takes priority
        with patch.dict("os.environ", {}, clear=True):
            result = tavily_retrieve({"query": "specific", "question": "general"})
        # Should use "query" (not "question") — but will fail on missing API key
        # The important thing is it doesn't error on "empty query"
        assert "TAVILY_API_KEY" in result  # got past empty-check using "query"

    @pytest.mark.req("REQ-YG-076")
    def test_domain_scoping(self):
        """TAVILY_TARGET_DOMAIN should be passed as include_domains."""
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": [], "answer": None}
        mock_tavily_module = MagicMock()
        mock_tavily_module.TavilyClient.return_value = mock_client

        import sys

        from examples.demos.tavily_rag.nodes.tavily_retrieve import (
            tavily_retrieve,  # noqa: F401
        )

        with (
            patch.dict(
                "os.environ",
                {"TAVILY_API_KEY": "key", "TAVILY_TARGET_DOMAIN": "example.com"},
            ),
            patch.dict(sys.modules, {"tavily": mock_tavily_module}),
        ):
            import importlib

            import examples.demos.tavily_rag.nodes.tavily_retrieve as mod

            importlib.reload(mod)
            mod.tavily_retrieve({"question": "test"})

        call_kwargs = mock_client.search.call_args
        assert call_kwargs is not None
        # include_domains should contain the target domain
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        assert kwargs.get("include_domains") == ["example.com"]

    @pytest.mark.req("REQ-YG-076")
    def test_no_domain_scoping_when_unset(self):
        """Without TAVILY_TARGET_DOMAIN, include_domains should not be set."""
        mock_client = MagicMock()
        mock_client.search.return_value = {"results": [], "answer": None}
        mock_tavily_module = MagicMock()
        mock_tavily_module.TavilyClient.return_value = mock_client

        import sys

        from examples.demos.tavily_rag.nodes.tavily_retrieve import (
            tavily_retrieve,  # noqa: F401
        )

        with (
            patch.dict("os.environ", {"TAVILY_API_KEY": "key"}, clear=True),
            patch.dict(sys.modules, {"tavily": mock_tavily_module}),
        ):
            import importlib

            import examples.demos.tavily_rag.nodes.tavily_retrieve as mod

            importlib.reload(mod)
            mod.tavily_retrieve({"question": "test"})

        call_kwargs = mock_client.search.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        assert "include_domains" not in kwargs


class TestTavilyRagGraphYaml:
    """Test graph YAML structure matches conventions."""

    @pytest.mark.req("REQ-YG-076")
    def test_simple_graph_structure(self):
        """Simple graph should have retrieve → answer flow."""
        with open(GRAPH_PATH) as f:
            graph = yaml.safe_load(f)

        assert graph["name"] == "tavily-rag"
        assert "question" in graph.get("state", {})

        nodes = graph["nodes"]
        assert "retrieve" in nodes
        assert nodes["retrieve"]["type"] == "python"
        assert nodes["retrieve"]["tool"] == "tavily_retrieve"

        assert "answer" in nodes
        assert nodes["answer"]["type"] == "llm"

        tools = graph["tools"]
        assert "tavily_retrieve" in tools
        assert tools["tavily_retrieve"]["type"] == "python"

    @pytest.mark.req("REQ-YG-076")
    def test_deep_graph_has_map_node(self):
        """Deep graph should have plan → map(retrieve) → synthesize."""
        with open(GRAPH_DEEP_PATH) as f:
            graph = yaml.safe_load(f)

        assert graph["name"] == "tavily-deep-rag"

        nodes = graph["nodes"]
        assert "plan" in nodes
        assert nodes["plan"]["type"] == "llm"

        assert "retrieve" in nodes
        assert nodes["retrieve"]["type"] == "map"
        assert "over" in nodes["retrieve"]
        assert "as" in nodes["retrieve"]
        assert "collect" in nodes["retrieve"]
        assert nodes["retrieve"]["node"]["type"] == "python"

        assert "synthesize" in nodes
        assert nodes["synthesize"]["type"] == "llm"

    @pytest.mark.req("REQ-YG-076")
    def test_prompts_exist(self):
        """All referenced prompts should exist."""
        import os

        prompts_dir = "examples/demos/tavily_rag/prompts"
        expected = ["answer.yaml", "planner.yaml", "synthesizer.yaml"]
        for name in expected:
            path = os.path.join(prompts_dir, name)
            assert os.path.exists(path), f"Missing prompt: {path}"
