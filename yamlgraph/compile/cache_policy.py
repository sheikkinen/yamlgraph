"""Cache policy resolution for compiled nodes (FR-032).

Split out of node_compiler.py when the FR-1155 decision handler pushed it
over the 450-line split gate. Converts the YAML ``cache`` field into a
LangGraph ``CachePolicy``.
"""

from typing import Any

from langgraph.types import CachePolicy

from yamlgraph.models.guard_schema import CacheConfig


def resolve_cache_policy(cache_config: CacheConfig | None) -> CachePolicy | None:
    """Convert CacheConfig → LangGraph CachePolicy.

    Args:
        cache_config: Parsed cache configuration from YAML, or None.

    Returns:
        CachePolicy instance, or None if caching not configured.
    """
    if cache_config is None:
        return None
    return CachePolicy(ttl=cache_config.ttl)


def parse_cache_field(raw: Any) -> CacheConfig | None:
    """Parse raw cache field value from YAML node config.

    Handles: True → CacheConfig(), False/None → None, dict → CacheConfig(**dict).
    """
    if raw is True:
        return CacheConfig()
    if raw is False or raw is None:
        return None
    if isinstance(raw, dict):
        return CacheConfig(**raw)
    if isinstance(raw, CacheConfig):
        return raw
    return None
