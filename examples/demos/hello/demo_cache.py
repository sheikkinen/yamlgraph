"""FR-111 Graph Cache Demo — shows cache hit/miss behavior.

Compiles the hello-world graph twice to demonstrate:
1. First call: compiles and caches (INFO log)
2. Second call: cache hit (DEBUG log)
3. clear_cache() forces recompilation
4. cache=None bypasses cache entirely

Run:
    python examples/demos/hello/demo_cache.py
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(name)s: %(message)s")


async def main() -> None:
    """Demonstrate graph cache behavior."""
    from yamlgraph.executor_async import load_and_compile_async
    from yamlgraph.graph_cache import GRAPH_CACHE, clear_cache

    graph_path = str(Path(__file__).parent / "graph.yaml")

    # 1. First call — cache miss, compiles the graph
    print("\n=== Call 1: Cache miss (compiles) ===")
    app1 = await load_and_compile_async(graph_path)
    print(f"  Cached graphs: {len(GRAPH_CACHE)}")

    # 2. Second call — cache hit, instant
    print("\n=== Call 2: Cache hit (instant) ===")
    app2 = await load_and_compile_async(graph_path)
    print(f"  Same object? {app1 is app2}")

    # 3. clear_cache() forces recompile
    print("\n=== Call 3: After clear_cache() ===")
    clear_cache()
    print(f"  Cached graphs after clear: {len(GRAPH_CACHE)}")
    app3 = await load_and_compile_async(graph_path)
    print(f"  Same as original? {app1 is app3}")

    # 4. cache=None bypasses cache entirely
    print("\n=== Call 4: cache=None (no caching) ===")
    clear_cache()
    _app4 = await load_and_compile_async(graph_path, cache=None)
    print(f"  Cached graphs: {len(GRAPH_CACHE)} (still empty — bypassed)")

    print("\n✅ Graph cache demo complete")


if __name__ == "__main__":
    asyncio.run(main())
