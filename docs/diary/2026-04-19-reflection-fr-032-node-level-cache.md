# Diary: FR-032 Node-Level Cache Policy

**Date:** 2026-04-19
**FR:** FR-032

## Cognitive Process

LangGraph's `graph.add_node()` accepts a `cache_policy` parameter. The boundary where this enters YAMLGraph is `NodeConfig` parsing and `compile_graph()`. Adding an optional `cache:` field to the YAML node config, validating it as a `CacheConfig`, and resolving it to a `CachePolicy` before passing to `add_node()` keeps the LangGraph integration isolated at one callsite.

## Trap Avoided: Leaking Abstractions

Passing LangGraph's `CachePolicy` objects directly through the YAML layer would leak an internal abstraction. The `resolve_cache_policy()` intermediary translates the user-facing YAML config to the LangGraph type at the boundary, keeping graph YAML independent of provider internals.

## Heuristic

When integrating framework-specific types (LangGraph `CachePolicy`), always translate at the compilation boundary. YAML config should express user intent; the compiler converts to framework objects.

## Seed

Should the cache config support per-model cache keys — so that the same prompt to different providers can be cached independently, enabling A/B comparison without cache poisoning?
