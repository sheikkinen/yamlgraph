"""Checkpointer factory for YAML-configured persistence.

Creates checkpointer instances from YAML configuration with support for:
- Multiple backends (memory, sqlite, redis)
- Environment variable expansion for secrets
- Sync and async modes for Redis
"""

import os
import re
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver


def expand_env_vars(value: Any) -> Any:
    """Expand ${VAR} patterns in string.

    Args:
        value: Value to expand. Non-strings pass through unchanged.

    Returns:
        String with ${VAR} patterns replaced by environment values.
        Missing vars keep original ${VAR} pattern.
    """
    if not isinstance(value, str):
        return value

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replacer, value)


def get_checkpointer(
    config: dict | None,
    *,
    async_mode: bool = False,
) -> BaseCheckpointSaver | None:
    """Create checkpointer from config.

    Args:
        config: Checkpointer configuration dict with keys:
            - type: "memory" | "sqlite" | "redis" (default: "memory")
            - url: Redis connection URL (for redis type)
            - path: SQLite file path (for sqlite type)
            - ttl: TTL in minutes (for redis type, default: 60)
        async_mode: If True, return async-compatible saver for FastAPI/async usage

    Returns:
        Configured checkpointer or None if config is None

    Raises:
        ValueError: If unknown checkpointer type
        ImportError: If redis type used without yamlgraph[redis] installed
    """
    if not config:
        return None

    cp_type = config.get("type", "memory")

    if cp_type == "redis":
        url = expand_env_vars(config.get("url", ""))
        ttl = config.get("ttl", 60)

        try:
            if async_mode:
                from langgraph.checkpoint.redis.aio import (
                    AsyncRedisSaver,
                )

                saver = AsyncRedisSaver.from_conn_string(
                    url,
                    ttl={"default_ttl": ttl},
                )
                # For async, caller must await saver.asetup()
            else:
                from langgraph.checkpoint.redis import RedisSaver

                saver = RedisSaver.from_conn_string(
                    url,
                    ttl={"default_ttl": ttl},
                )
                saver.setup()

            return saver
        except ImportError as e:
            raise ImportError(
                "Install redis support: pip install yamlgraph[redis]"
            ) from e

    elif cp_type == "sqlite":
        import sqlite3

        from langgraph.checkpoint.sqlite import SqliteSaver

        path = expand_env_vars(config.get("path", ":memory:"))
        conn = sqlite3.connect(path, check_same_thread=False)
        return SqliteSaver(conn)

    elif cp_type == "memory":
        from langgraph.checkpoint.memory import InMemorySaver

        return InMemorySaver()

    raise ValueError(f"Unknown checkpointer type: {cp_type}")
