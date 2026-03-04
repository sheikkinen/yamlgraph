# FR-111: Compiled Graph Cache

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Requirement:** REQ-YG-107
**Effort:** 0.5 days
**Requested:** 2026-03-04
**Judged:** 2026-03-04

## Summary

Provide a process-global compiled graph cache in the `yamlgraph` package so that `load_and_compile_async()` results survive module reloads and are shared across all callers within the same Python process.

## Value Statement

Embeddings hosts and engine action loaders that reload action modules on every invocation currently recompile the LangGraph graph on every LLM call (1.5–4s). A process-global cache eliminates this cost after the first compilation, enabling sub-50ms graph access on all subsequent calls within the same process.

**Implicit beneficiaries:** `run_graph_streaming_native()` also calls `load_and_compile_async()` — streaming callers get the same cache benefit transparently without code changes.

## Problem

`yamlgraph_action.py` declares:

```python
_GRAPH_CACHE: dict[str, Any] = {}
```

This initializes to `{}` every time the engine's action loader reimports the module. In the ninchat_voice engine, the loader reimports on every FSM transition. The result:

- Preload (`warming_up` state) compiles graphs into one incarnation of `_GRAPH_CACHE`.
- Classify (`classifying` state) gets a fresh incarnation — cache miss, recompiles.
- Every turn pays the full 1.5–4s graph compilation cost.

**Observed log evidence (2026-03-04):**
```
14:38:03.149  🔥 Preloading 2 graph(s)        ← warming_up, action_loader reload #1
14:38:15.703  📊 Loading YAMLGraph: intent-classifier  ← classifying, reload #2 → MISS
14:38:22.500  📊 Loading YAMLGraph: rewrite-response   ← rewriting, reload #3 → MISS
14:39:08.213  🔥 Preloading 2 graph(s)        ← call 2 warming_up, reload #N → MISS again
14:39:20.655  📊 Loading YAMLGraph: intent-classifier  ← call 2 classifying → MISS
```

Classify latency: 1.26–2.24s. With a true cache hit, graph compilation (0.8–1.5s of that) is eliminated.

## Proposed Solution

Add `yamlgraph/graph_cache.py` to the installed package:

```python
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
```

Update `load_and_compile_async()` in `executor_async.py` to accept an optional `cache` parameter, defaulting to `GRAPH_CACHE`:

```python
from yamlgraph.graph_cache import GRAPH_CACHE as _DEFAULT_CACHE

async def load_and_compile_async(
    graph_path: str,
    *,
    cache: dict[str, Any] | None = _DEFAULT_CACHE,
) -> CompiledStateGraph:
    """Load and compile a graph, using the process-global cache by default.

    Cache invalidation: In development, pass ``cache=None`` or call
    ``clear_cache()`` to force recompilation after YAML changes.
    In production, YAML changes require a process restart.
    """
    if cache is not None and graph_path in cache:
        logger.debug("Cache hit: %s", graph_path)
        return cache[graph_path]

    logger.info("Compiling graph: %s", graph_path)
    compiled = await _compile(graph_path)

    if cache is not None:
        cache[graph_path] = compiled

    return compiled
```

Both `yamlgraph_action.py` and `yamlgraph_preload_action.py` then simply call `load_and_compile_async()` — the cache is handled transparently. No action-level cache dict required.

### Migration path for ninchat_voice

1. Remove `_GRAPH_CACHE` module variable from `yamlgraph_action.py`.
2. Remove deferred-import workaround from `yamlgraph_preload_action.py` (including both `# noqa: PLC0415` suppressions — no confessions to retire as they were in project code, not the yamlgraph package).
3. Both actions call `load_and_compile_async(path)` — caching automatic.
4. Remove local cache-hit/miss logging — `load_and_compile_async()` now logs at debug/info level.

## Acceptance Criteria

- [x] `yamlgraph/graph_cache.py` exists with `GRAPH_CACHE` dict and `clear_cache()` function
- [x] `load_and_compile_async()` uses `GRAPH_CACHE` by default
- [x] `cache=None` disables caching (for tests that require isolation)
- [x] Second call to `load_and_compile_async(same_path)` does not call `_compile()` again
- [x] Calling from two different action modules in the same process returns the same compiled object (`cache_a is cache_b`)
- [x] `load_and_compile_async()` logs `debug("Cache hit: %s")` on hit, `info("Compiling graph: %s")` on miss
- [x] `yamlgraph_action.py` and `yamlgraph_preload_action.py` in ninchat_voice migrated to use the new cache (no local `_GRAPH_CACHE`, no `noqa: PLC0415`)
- [ ] Log confirms cache hit on classifying turn 1 of call 2
- [ ] Classify latency on warm call ≤ 900ms (NC-121 acceptance criterion)
- [x] Unit tests with `@pytest.mark.req("REQ-YG-107")`: cache hit, cache miss, `cache=None` bypass, `clear_cache()` reset
- [x] REQ-YG-107 added to ARCHITECTURE.md capability table
- [x] CHANGELOG updated

## Alternatives Considered

**A — `sys.modules` sentinel (current workaround)**
Store `{}` under a sentinel key in `sys.modules`. Works because `sys.modules` is process-global. But uses `sys.modules` as a general-purpose namespace, which is unconventional and opaque. The deferred-import pattern in `yamlgraph_preload_action` is a symptom of this fragility.

**B — FSM context variable (`context["graph_cache"]`)**
Compiled graphs are Python objects and not JSON-serializable. Breaks any checkpoint or database-logging path. Also per-call: no cross-call benefit.

**C — Sidecar / separate process**
Compiled graphs cannot be pickled across processes without re-implementing the entire LLM invocation in the sidecar. Major architectural change for marginal benefit.

**D — Thread-local / class variable**
Depends on whether the engine reuses action instances. Fragile against undocumented engine internals.

The installed-package approach (this FR) is the canonical solution: installed packages are never reloaded by Python's import system, making them the natural home for process-global state.

## Scope Fence (out of scope)

- **No LRU / TTL / size-bounded cache.** The dict holds 2–5 compiled graphs per process. Bounded eviction is over-engineering.
- **No `asyncio.Lock`.** Single-threaded event loop. If multi-threaded use emerges, it's a separate FR.
- **No file watcher.** Cache invalidation by filesystem watcher is a different feature. Development invalidation: `cache=None` or `clear_cache()`. Production: process restart.

## Related

- NC-121 FR: `projects/ninchat_voice/feature-requests/NC-121-warmup-graph-preload.md`
- `yamlgraph/executor_async.py` — `load_and_compile_async()`
- `projects/ninchat_voice/actions/real/yamlgraph_action.py` — current `_GRAPH_CACHE`
- `projects/ninchat_voice/actions/real/yamlgraph_preload_action.py` — deferred-import workaround
- Diary entry 80: "Three Wrong Hypotheses and a 490ms Gap"
