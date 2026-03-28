"""FR-205 .fi Domain Crawler — Unit tests (RED phase).

Tests for crawl_page and seed_discovery tool nodes with mocked HTTP/search.
"""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock, patch

import pytest

# Directory uses hyphens; importlib handles it, ``from`` syntax cannot.
_crawl_mod = importlib.import_module("examples.demos.fi-domain-crawl.nodes.crawl_page")
crawl_page = _crawl_mod.crawl_page

_seed_mod = importlib.import_module(
    "examples.demos.fi-domain-crawl.nodes.seed_discovery"
)
discover_seeds = _seed_mod.discover_seeds


# ---------------------------------------------------------------------------
# crawl_page tests
# ---------------------------------------------------------------------------


class TestCrawlPage:
    """Unit tests for crawl_page tool node."""

    @pytest.mark.req("REQ-YG-199")
    def test_returns_structured_dict_with_title(self) -> None:
        """crawl_page returns dict with title extracted from HTML."""

        html = "<html><head><title>Helsinki Libraries</title></head><body><p>Content</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/libraries"})

        assert isinstance(result, dict)
        assert result["title"] == "Helsinki Libraries"

    @pytest.mark.req("REQ-YG-199")
    def test_extracts_internal_links(self) -> None:
        """crawl_page extracts internal links from the same domain."""

        html = """<html><head><title>Test</title></head><body>
        <a href="/about">About</a>
        <a href="https://example.fi/contact">Contact</a>
        <a href="https://other.com/ext">External</a>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/"})

        assert "https://example.fi/about" in result["internal_links"]
        assert "https://example.fi/contact" in result["internal_links"]
        assert "https://other.com/ext" not in result["internal_links"]

    @pytest.mark.req("REQ-YG-199")
    def test_extracts_external_links(self) -> None:
        """crawl_page identifies external links separately."""

        html = """<html><head><title>Test</title></head><body>
        <a href="https://other.com/page">Other</a>
        <a href="/local">Local</a>
        </body></html>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/"})

        assert "https://other.com/page" in result["external_links"]

    @pytest.mark.req("REQ-YG-199")
    def test_extracts_meta_description(self) -> None:
        """crawl_page extracts meta description tag."""

        html = """<html><head>
        <title>Test</title>
        <meta name="description" content="A page about Helsinki">
        </head><body><p>Body text</p></body></html>"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/"})

        assert result["meta_description"] == "A page about Helsinki"

    @pytest.mark.req("REQ-YG-199")
    def test_extracts_text_snippet_capped_at_500(self) -> None:
        """crawl_page returns text snippet capped at 500 chars."""

        long_text = "A" * 1000
        html = f"<html><head><title>Test</title></head><body><p>{long_text}</p></body></html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/"})

        assert len(result["snippet"]) <= 500

    @pytest.mark.req("REQ-YG-199")
    def test_handles_http_error_gracefully(self) -> None:
        """crawl_page returns error dict on HTTP failure, does not raise."""

        import httpx

        with patch("httpx.get", side_effect=httpx.TimeoutException("timeout")):
            result = crawl_page({"url": "https://example.fi/broken"})

        assert isinstance(result, dict)
        assert result["error"] is not None
        assert "timeout" in result["error"].lower()

    @pytest.mark.req("REQ-YG-199")
    def test_respects_timeout_parameter(self) -> None:
        """crawl_page passes timeout=10 to httpx.get by default."""

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><head><title>T</title></head><body></body></html>"

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            crawl_page({"url": "https://example.fi/"})

        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs.get("timeout") == 10

    @pytest.mark.req("REQ-YG-199")
    def test_returns_url_in_result(self) -> None:
        """crawl_page includes the original URL in the result dict."""

        html = "<html><head><title>T</title></head><body></body></html>"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html

        with patch("httpx.get", return_value=mock_resp):
            result = crawl_page({"url": "https://example.fi/page"})

        assert result["url"] == "https://example.fi/page"


# ---------------------------------------------------------------------------
# seed_discovery tests
# ---------------------------------------------------------------------------


class TestSeedDiscovery:
    """Unit tests for seed_discovery tool node."""

    @pytest.mark.req("REQ-YG-199")
    def test_filters_results_to_fi_tld_only(self) -> None:
        """discover_seeds returns only .fi domain URLs."""

        mock_results = [
            {"title": "A", "href": "https://helsinki.fi/page", "body": "desc"},
            {"title": "B", "href": "https://example.com/page", "body": "desc"},
            {"title": "C", "href": "https://turku.fi/info", "body": "desc"},
        ]

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = mock_results

        with patch.object(
            _seed_mod,
            "DDGS",
            return_value=mock_ddgs,
        ):
            result = discover_seeds({"search_queries": ["Helsinki libraries"]})

        assert isinstance(result, dict)
        urls = result["discovered_urls"]
        assert "https://helsinki.fi/page" in urls
        assert "https://turku.fi/info" in urls
        assert "https://example.com/page" not in urls

    @pytest.mark.req("REQ-YG-199")
    def test_deduplicates_urls(self) -> None:
        """discover_seeds returns deduplicated URLs."""

        mock_results = [
            {"title": "A", "href": "https://helsinki.fi/page", "body": "desc"},
            {"title": "B", "href": "https://helsinki.fi/page", "body": "desc"},
        ]

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = mock_results

        with patch.object(
            _seed_mod,
            "DDGS",
            return_value=mock_ddgs,
        ):
            result = discover_seeds({"search_queries": ["Helsinki libraries"]})

        urls = result["discovered_urls"]
        assert len(urls) == len(set(urls))

    @pytest.mark.req("REQ-YG-199")
    def test_reads_search_queries_from_state(self) -> None:
        """discover_seeds reads search_queries from state and executes each."""

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "A", "href": "https://example.fi/a", "body": "desc"},
        ]

        with patch.object(
            _seed_mod,
            "DDGS",
            return_value=mock_ddgs,
        ):
            discover_seeds({"search_queries": ["query one", "query two"]})

        # Should call text() once per query
        assert mock_ddgs.text.call_count == 2

    @pytest.mark.req("REQ-YG-199")
    def test_handles_empty_search_queries(self) -> None:
        """discover_seeds handles empty search_queries gracefully."""

        result = discover_seeds({"search_queries": []})

        assert isinstance(result, dict)
        assert result["discovered_urls"] == []

    @pytest.mark.req("REQ-YG-199")
    def test_handles_search_api_error(self) -> None:
        """discover_seeds handles search API errors without raising."""

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.side_effect = Exception("API error")

        with patch.object(
            _seed_mod,
            "DDGS",
            return_value=mock_ddgs,
        ):
            result = discover_seeds({"search_queries": ["Helsinki libraries"]})

        assert isinstance(result, dict)
        assert result["discovered_urls"] == []


# ---------------------------------------------------------------------------
# Graph structure tests
# ---------------------------------------------------------------------------


class TestFiDomainCrawlGraph:
    """Test the graph.yaml configuration loads correctly."""

    GRAPH_PATH = "examples/demos/fi-domain-crawl/graph.yaml"

    @pytest.mark.req("REQ-YG-199")
    def test_graph_config_loads(self) -> None:
        """Graph config loads successfully."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(self.GRAPH_PATH)
        assert config.name == "fi-domain-crawl"

    @pytest.mark.req("REQ-YG-199")
    def test_plan_node_uses_parse_json(self) -> None:
        """Plan node outputs search queries via parse_json."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(self.GRAPH_PATH)
        plan = config.nodes["plan"]
        assert plan.get("parse_json") is True
        assert plan.get("state_key") == "search_queries"

    @pytest.mark.req("REQ-YG-199")
    def test_crawl_node_is_map_with_collect(self) -> None:
        """Crawl node is a map node that collects into crawl_results."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(self.GRAPH_PATH)
        crawl = config.nodes["crawl"]
        assert crawl["type"] == "map"
        assert crawl["collect"] == "crawl_results"
        assert crawl.get("max_items") == 10

    @pytest.mark.req("REQ-YG-199")
    def test_pipeline_flow_start_to_end(self) -> None:
        """Edges define START → plan → discover → crawl → summarise → END."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(self.GRAPH_PATH)
        edges = config.edges
        edge_pairs = [(e["from"], e["to"]) for e in edges]
        assert ("START", "plan") in edge_pairs
        assert ("plan", "discover") in edge_pairs
        assert ("discover", "crawl") in edge_pairs
        assert ("crawl", "summarise") in edge_pairs
        assert ("summarise", "END") in edge_pairs

    @pytest.mark.req("REQ-YG-199")
    def test_no_max_pages_in_state(self) -> None:
        """State should NOT contain max_pages — cap is via map max_items."""
        from yamlgraph.graph_loader import load_graph_config

        config = load_graph_config(self.GRAPH_PATH)
        state = config.raw_config.get("state", {})
        assert "max_pages" not in state

    @pytest.mark.req("REQ-YG-199")
    def test_graph_lint_passes(self) -> None:
        """Graph passes yamlgraph lint."""
        from yamlgraph.linter.graph_linter import lint_graph

        result = lint_graph(self.GRAPH_PATH)
        errors = [i for i in result.issues if i.severity == "error"]
        assert errors == [], f"Lint errors: {errors}"
