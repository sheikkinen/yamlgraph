"""Tests for yamlgraph.tools.websearch module."""

from unittest.mock import MagicMock, patch


class TestWebSearchToolConfig:
    """Tests for WebSearchToolConfig dataclass."""

    def test_config_defaults(self):
        """Config should have sensible defaults."""
        from yamlgraph.tools.websearch import WebSearchToolConfig

        config = WebSearchToolConfig()
        assert config.provider == "duckduckgo"
        assert config.max_results == 5
        assert config.description == ""
        assert config.timeout == 30

    def test_config_custom_values(self):
        """Config should accept custom values."""
        from yamlgraph.tools.websearch import WebSearchToolConfig

        config = WebSearchToolConfig(
            provider="duckduckgo",
            max_results=10,
            description="Search the web",
            timeout=60,
        )
        assert config.max_results == 10
        assert config.description == "Search the web"
        assert config.timeout == 60


class TestWebSearchResult:
    """Tests for WebSearchResult dataclass."""

    def test_result_success(self):
        """Result should store successful search data."""
        from yamlgraph.tools.websearch import WebSearchResult

        result = WebSearchResult(
            success=True,
            results=[{"title": "Test", "url": "https://test.com", "body": "Content"}],
            query="test query",
        )
        assert result.success is True
        assert len(result.results) == 1
        assert result.error is None

    def test_result_failure(self):
        """Result should store error information."""
        from yamlgraph.tools.websearch import WebSearchResult

        result = WebSearchResult(
            success=False,
            results=[],
            query="test query",
            error="Search failed",
        )
        assert result.success is False
        assert result.error == "Search failed"


class TestExecuteWebSearch:
    """Tests for execute_web_search function."""

    @patch("yamlgraph.tools.websearch.DUCKDUCKGO_AVAILABLE", True)
    @patch("yamlgraph.tools.websearch.DDGS")
    def test_successful_search(self, mock_ddgs_class):
        """Should return results from DuckDuckGo."""
        from yamlgraph.tools.websearch import WebSearchToolConfig, execute_web_search

        # Mock the DDGS context manager
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "https://example.com", "body": "Content 1"},
            {"title": "Result 2", "href": "https://example2.com", "body": "Content 2"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        config = WebSearchToolConfig(max_results=5)
        result = execute_web_search("python programming", config)

        assert result.success is True
        assert len(result.results) == 2
        assert result.results[0]["title"] == "Result 1"
        mock_ddgs.text.assert_called_once_with("python programming", max_results=5)

    @patch("yamlgraph.tools.websearch.DUCKDUCKGO_AVAILABLE", True)
    @patch("yamlgraph.tools.websearch.DDGS")
    def test_empty_results(self, mock_ddgs_class):
        """Should handle empty search results."""
        from yamlgraph.tools.websearch import WebSearchToolConfig, execute_web_search

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        config = WebSearchToolConfig()
        result = execute_web_search("obscure query xyz123", config)

        assert result.success is True
        assert result.results == []

    @patch("yamlgraph.tools.websearch.DUCKDUCKGO_AVAILABLE", True)
    @patch("yamlgraph.tools.websearch.DDGS")
    def test_search_error(self, mock_ddgs_class):
        """Should handle search errors gracefully."""
        from yamlgraph.tools.websearch import WebSearchToolConfig, execute_web_search

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.side_effect = Exception("Network error")
        mock_ddgs_class.return_value = mock_ddgs

        config = WebSearchToolConfig()
        result = execute_web_search("test query", config)

        assert result.success is False
        assert "Network error" in result.error

    def test_empty_query(self):
        """Should handle empty query."""
        from yamlgraph.tools.websearch import WebSearchToolConfig, execute_web_search

        config = WebSearchToolConfig()
        result = execute_web_search("", config)

        assert result.success is False
        assert "empty" in result.error.lower()


class TestFormatSearchResults:
    """Tests for format_search_results function."""

    def test_format_results_as_text(self):
        """Should format results as readable text."""
        from yamlgraph.tools.websearch import WebSearchResult, format_search_results

        result = WebSearchResult(
            success=True,
            query="python",
            results=[
                {
                    "title": "Python.org",
                    "href": "https://python.org",
                    "body": "Official site",
                },
                {
                    "title": "Python Wiki",
                    "href": "https://wiki.python.org",
                    "body": "Wiki",
                },
            ],
        )

        formatted = format_search_results(result)

        assert "Python.org" in formatted
        assert "https://python.org" in formatted
        assert "Official site" in formatted

    def test_format_empty_results(self):
        """Should handle empty results."""
        from yamlgraph.tools.websearch import WebSearchResult, format_search_results

        result = WebSearchResult(success=True, query="xyz", results=[])

        formatted = format_search_results(result)

        assert "no results" in formatted.lower()

    def test_format_error_result(self):
        """Should format error message."""
        from yamlgraph.tools.websearch import WebSearchResult, format_search_results

        result = WebSearchResult(
            success=False,
            query="test",
            results=[],
            error="Search failed",
        )

        formatted = format_search_results(result)

        assert "error" in formatted.lower()
        assert "Search failed" in formatted


class TestCreateWebSearchTool:
    """Tests for create_web_search_tool function."""

    def test_create_langchain_tool(self):
        """Should create a LangChain-compatible tool."""
        from yamlgraph.tools.websearch import (
            WebSearchToolConfig,
            create_web_search_tool,
        )

        config = WebSearchToolConfig(description="Search the web for information")
        tool = create_web_search_tool("search_web", config)

        assert tool.name == "search_web"
        assert tool.description == "Search the web for information"

    @patch("yamlgraph.tools.websearch.DUCKDUCKGO_AVAILABLE", True)
    @patch("yamlgraph.tools.websearch.DDGS")
    def test_tool_invocation(self, mock_ddgs_class):
        """Created tool should be invocable."""
        from yamlgraph.tools.websearch import (
            WebSearchToolConfig,
            create_web_search_tool,
        )

        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {"title": "Test", "href": "https://test.com", "body": "Test content"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        config = WebSearchToolConfig()
        tool = create_web_search_tool("search_web", config)

        result = tool.invoke({"query": "test"})

        assert "Test" in result
        assert "https://test.com" in result
