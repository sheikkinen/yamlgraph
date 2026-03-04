"""Unit tests for graph_cache module (FR-111, REQ-YG-107).

Tests the process-global compiled graph cache: hit, miss, bypass, and clear.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.req("REQ-YG-107")
class TestGraphCacheModule:
    """Tests for yamlgraph.graph_cache module."""

    def test_graph_cache_is_dict(self):
        """GRAPH_CACHE should be a plain dict."""
        from yamlgraph.graph_cache import GRAPH_CACHE

        assert isinstance(GRAPH_CACHE, dict)

    def test_clear_cache_empties_dict(self):
        """clear_cache() should empty the GRAPH_CACHE dict."""
        from yamlgraph.graph_cache import GRAPH_CACHE, clear_cache

        GRAPH_CACHE["test_key"] = "test_value"
        clear_cache()
        assert GRAPH_CACHE == {}

    def test_cache_identity_survives_reimport(self):
        """Importing from two different places returns the same dict object."""
        from yamlgraph.graph_cache import GRAPH_CACHE as cache_a
        from yamlgraph.graph_cache import GRAPH_CACHE as cache_b

        assert cache_a is cache_b


@pytest.mark.req("REQ-YG-107")
class TestLoadAndCompileAsyncCache:
    """Tests for cache integration in load_and_compile_async."""

    def setup_method(self):
        """Clear cache before each test."""
        from yamlgraph.graph_cache import clear_cache

        clear_cache()

    def teardown_method(self):
        """Clear cache after each test."""
        from yamlgraph.graph_cache import clear_cache

        clear_cache()

    @pytest.mark.asyncio
    async def test_cache_miss_compiles_graph(self):
        """First call should compile the graph (cache miss)."""
        mock_compiled = MagicMock(name="CompiledStateGraph")

        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = mock_compiled

            from yamlgraph.executor_async import load_and_compile_async

            result = await load_and_compile_async("graphs/test.yaml", cache=None)

            assert result is mock_compiled
            mock_load.assert_called_once_with("graphs/test.yaml")

    @pytest.mark.asyncio
    async def test_cache_hit_skips_compile(self):
        """Second call with same path should return cached graph, no recompile."""
        mock_compiled = MagicMock(name="CompiledStateGraph")

        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = mock_compiled

            from yamlgraph.executor_async import load_and_compile_async

            result1 = await load_and_compile_async("graphs/test.yaml")
            result2 = await load_and_compile_async("graphs/test.yaml")

            # Same object returned
            assert result1 is result2
            # Compile called only once
            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_none_disables_caching(self):
        """cache=None should compile every time, never store."""
        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = MagicMock()

            from yamlgraph.executor_async import load_and_compile_async

            await load_and_compile_async("graphs/test.yaml", cache=None)
            await load_and_compile_async("graphs/test.yaml", cache=None)

            # Compiled twice — no caching
            assert mock_load.call_count == 2

            # GRAPH_CACHE should be empty
            from yamlgraph.graph_cache import GRAPH_CACHE

            assert "graphs/test.yaml" not in GRAPH_CACHE

    @pytest.mark.asyncio
    async def test_clear_cache_forces_recompile(self):
        """After clear_cache(), next call should recompile."""
        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = MagicMock()

            from yamlgraph.executor_async import load_and_compile_async
            from yamlgraph.graph_cache import clear_cache

            await load_and_compile_async("graphs/test.yaml")
            clear_cache()
            await load_and_compile_async("graphs/test.yaml")

            # Compiled twice — cache was cleared
            assert mock_load.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_hit_logs_debug(self, caplog):
        """Cache hit should log at DEBUG level."""
        import logging

        mock_compiled = MagicMock(name="CompiledStateGraph")

        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = mock_compiled

            from yamlgraph.executor_async import load_and_compile_async

            # yamlgraph logger has propagate=False; temporarily enable for caplog
            parent_logger = logging.getLogger("yamlgraph")
            original_propagate = parent_logger.propagate
            parent_logger.propagate = True

            try:
                await load_and_compile_async("graphs/test.yaml")

                with caplog.at_level(logging.DEBUG, logger="yamlgraph.executor_async"):
                    await load_and_compile_async("graphs/test.yaml")

                assert any("Cache hit" in msg for msg in caplog.messages)
            finally:
                parent_logger.propagate = original_propagate

    @pytest.mark.asyncio
    async def test_cache_miss_logs_info(self, caplog):
        """Cache miss should log at INFO level."""
        import logging

        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            mock_async_compile.return_value = MagicMock()

            from yamlgraph.executor_async import load_and_compile_async

            # yamlgraph logger has propagate=False; temporarily enable for caplog
            parent_logger = logging.getLogger("yamlgraph")
            original_propagate = parent_logger.propagate
            parent_logger.propagate = True

            try:
                with caplog.at_level(logging.INFO, logger="yamlgraph.executor_async"):
                    await load_and_compile_async("graphs/test.yaml", cache=None)

                assert any("Compiling graph" in msg for msg in caplog.messages)
            finally:
                parent_logger.propagate = original_propagate

    @pytest.mark.asyncio
    async def test_different_paths_cached_separately(self):
        """Different graph paths should be cached as separate entries."""
        with (
            patch("yamlgraph.graph_loader.load_graph_config") as mock_load,
            patch("yamlgraph.graph_loader.compile_graph") as mock_compile,
            patch(
                "yamlgraph.executor_async.compile_graph_async",
                new_callable=AsyncMock,
            ) as mock_async_compile,
        ):
            mock_config = MagicMock()
            mock_config.name = "test"
            mock_config.version = "1.0"
            mock_load.return_value = mock_config
            mock_compile.return_value = MagicMock()
            # Return different objects for each compile
            mock_async_compile.side_effect = [
                MagicMock(name="graph_a"),
                MagicMock(name="graph_b"),
            ]

            from yamlgraph.executor_async import load_and_compile_async

            result_a = await load_and_compile_async("graphs/a.yaml")
            result_b = await load_and_compile_async("graphs/b.yaml")

            assert result_a is not result_b
            assert mock_load.call_count == 2
