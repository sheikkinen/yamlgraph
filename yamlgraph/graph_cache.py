"""Process-global compiled graph cache.

Lives in the installed yamlgraph package, which Python never reloads once
imported. Any code that imports from here shares the same dict object for
the lifetime of the process.

Usage:
    from yamlgraph.graph_cache import GRAPH_CACHE

    if path not in GRAPH_CACHE:
        GRAPH_CACHE[path] = await load_and_compile_async(path)

    app = GRAPH_CACHE[path]
"""

from __future__ import annotations

from typing import Any

# Keyed by absolute resolved graph path string → CompiledStateGraph.
# CompiledStateGraph is stateless (thread state lives in the checkpointer,
# not in the graph object) — safe to share across concurrent invocations.
GRAPH_CACHE: dict[str, Any] = {}


def clear_cache() -> None:
    """Clear all cached compiled graphs.

    Use in test teardown, hot-reload scenarios, or operational diagnostics.
    """
    GRAPH_CACHE.clear()
