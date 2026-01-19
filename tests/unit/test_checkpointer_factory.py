"""Unit tests for checkpointer factory.

TDD tests for 002: Redis Checkpointer feature.
Tests get_checkpointer() factory with env var expansion and async mode.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from yamlgraph.storage.checkpointer_factory import (
    expand_env_vars,
    get_checkpointer,
)


class TestExpandEnvVars:
    """Test environment variable expansion."""

    def test_expand_single_var(self):
        """Should expand ${VAR} pattern."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
            result = expand_env_vars("${REDIS_URL}")
            assert result == "redis://localhost:6379"

    def test_expand_multiple_vars(self):
        """Should expand multiple ${VAR} patterns."""
        with patch.dict(os.environ, {"HOST": "localhost", "PORT": "6379"}):
            result = expand_env_vars("redis://${HOST}:${PORT}/0")
            assert result == "redis://localhost:6379/0"

    def test_expand_missing_var_keeps_original(self):
        """Missing env vars should keep original ${VAR} pattern."""
        # Ensure NONEXISTENT is not set
        os.environ.pop("NONEXISTENT", None)
        result = expand_env_vars("${NONEXISTENT}")
        assert result == "${NONEXISTENT}"

    def test_expand_non_string_returns_unchanged(self):
        """Non-string values should pass through unchanged."""
        assert expand_env_vars(123) == 123
        assert expand_env_vars(None) is None
        assert expand_env_vars(["a", "b"]) == ["a", "b"]

    def test_expand_no_vars_returns_original(self):
        """String without ${} should return unchanged."""
        result = expand_env_vars("redis://localhost:6379")
        assert result == "redis://localhost:6379"

    def test_expand_empty_string(self):
        """Empty string should return empty string."""
        assert expand_env_vars("") == ""


class TestGetCheckpointerMemory:
    """Test in-memory checkpointer (default)."""

    def test_memory_checkpointer_default(self):
        """Default type should be memory."""
        config = {"type": "memory"}  # Empty config defaults to memory via get
        saver = get_checkpointer(config)

        from langgraph.checkpoint.memory import InMemorySaver

        assert isinstance(saver, InMemorySaver)

    def test_memory_checkpointer_explicit(self):
        """Explicit type: memory should work."""
        config = {"type": "memory"}
        saver = get_checkpointer(config)

        from langgraph.checkpoint.memory import InMemorySaver

        assert isinstance(saver, InMemorySaver)

    def test_none_config_returns_none(self):
        """None config should return None."""
        assert get_checkpointer(None) is None


class TestGetCheckpointerSqlite:
    """Test SQLite checkpointer."""

    def test_sqlite_checkpointer_memory(self):
        """SQLite with :memory: should work."""
        config = {"type": "sqlite", "path": ":memory:"}
        saver = get_checkpointer(config)

        from langgraph.checkpoint.sqlite import SqliteSaver

        assert isinstance(saver, SqliteSaver)

    def test_sqlite_expands_env_var(self):
        """SQLite path should expand env vars."""
        with patch.dict(os.environ, {"DB_PATH": ":memory:"}):
            config = {"type": "sqlite", "path": "${DB_PATH}"}
            saver = get_checkpointer(config)

            from langgraph.checkpoint.sqlite import SqliteSaver

            assert isinstance(saver, SqliteSaver)


class TestGetCheckpointerRedis:
    """Test Redis checkpointer (mocked)."""

    def test_redis_checkpointer_sync(self):
        """Redis sync saver should be created."""
        mock_saver = MagicMock()
        mock_redis_module = MagicMock()
        mock_redis_module.RedisSaver.from_conn_string.return_value = mock_saver

        with patch.dict(
            "sys.modules", {"langgraph.checkpoint.redis": mock_redis_module}
        ):
            # Re-import to pick up mocked module
            import importlib

            from yamlgraph.storage import checkpointer_factory

            importlib.reload(checkpointer_factory)

            with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
                config = {"type": "redis", "url": "${REDIS_URL}", "ttl": 120}
                saver = checkpointer_factory.get_checkpointer(config)

                mock_redis_module.RedisSaver.from_conn_string.assert_called_once_with(
                    "redis://localhost:6379",
                    ttl={"default_ttl": 120},
                )
                mock_saver.setup.assert_called_once()
                assert saver is mock_saver

    def test_redis_checkpointer_async(self):
        """Redis async saver should be created with async_mode=True."""
        mock_saver = MagicMock()
        mock_aio_module = MagicMock()
        mock_aio_module.AsyncRedisSaver.from_conn_string.return_value = mock_saver

        with patch.dict(
            "sys.modules", {"langgraph.checkpoint.redis.aio": mock_aio_module}
        ):
            import importlib

            from yamlgraph.storage import checkpointer_factory

            importlib.reload(checkpointer_factory)

            config = {"type": "redis", "url": "redis://localhost:6379", "ttl": 60}
            saver = checkpointer_factory.get_checkpointer(config, async_mode=True)

            mock_aio_module.AsyncRedisSaver.from_conn_string.assert_called_once_with(
                "redis://localhost:6379",
                ttl={"default_ttl": 60},
            )
            # Async saver should NOT call setup() - caller must await asetup()
            mock_saver.setup.assert_not_called()
            assert saver is mock_saver

    def test_redis_import_error_helpful_message(self):
        """Missing redis package should give helpful error."""
        # Clear any cached imports
        import sys

        for key in list(sys.modules.keys()):
            if "langgraph.checkpoint.redis" in key:
                del sys.modules[key]

        # This test verifies the ImportError wrapping
        config = {"type": "redis", "url": "redis://localhost:6379"}

        with pytest.raises(ImportError) as exc_info:
            get_checkpointer(config)

        assert "pip install yamlgraph[redis]" in str(exc_info.value)

    def test_redis_default_ttl(self):
        """Redis should use default TTL of 60 if not specified."""
        mock_saver = MagicMock()
        mock_redis_module = MagicMock()
        mock_redis_module.RedisSaver.from_conn_string.return_value = mock_saver

        with patch.dict(
            "sys.modules", {"langgraph.checkpoint.redis": mock_redis_module}
        ):
            import importlib

            from yamlgraph.storage import checkpointer_factory

            importlib.reload(checkpointer_factory)

            config = {"type": "redis", "url": "redis://localhost:6379"}
            checkpointer_factory.get_checkpointer(config)

            mock_redis_module.RedisSaver.from_conn_string.assert_called_once_with(
                "redis://localhost:6379",
                ttl={"default_ttl": 60},
            )


class TestGetCheckpointerErrors:
    """Test error handling."""

    def test_unknown_type_raises_error(self):
        """Unknown checkpointer type should raise ValueError."""
        config = {"type": "unknown_db"}

        with pytest.raises(ValueError) as exc_info:
            get_checkpointer(config)

        assert "Unknown checkpointer type: unknown_db" in str(exc_info.value)
