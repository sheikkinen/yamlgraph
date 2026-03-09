# 2026-03-09: FR-176 Concurrency Safety Map — Reflection

## Context

FR-175 (Sequential Enforcement Mode) exposed "parallelism theatre" — concurrent execution that appeared efficient but silently created race conditions on shared state (ARCHITECTURE.md, CHANGELOG.md). This prompted a systematic audit of all concurrency patterns in YAMLGraph.

## Trap

**Plausible parallelism.** Code that runs concurrently can appear to work correctly in testing while harboring subtle race conditions. The map node fan-out, graph cache, and checkpoint writes all use shared state — but their safety properties weren't documented until now.

## Heuristic

*Before adding concurrent execution, document the safety invariant.* For each concurrency pattern, answer:
- What state is shared?
- What serialization mechanism protects it?
- Under what conditions does the safety invariant hold?

## Findings

Six concurrency areas audited:
1. **Map node fan-out**: Safe — items are independent, state merge is atomic
2. **Checkpoint writes**: Safe — LangGraph's Checkpoint protocol serializes writes per thread_id
3. **Graph cache**: Conditional — safe with GIL, requires lock for async
4. **Inquisitor diary writes**: Conditional — single writer expected
5. **MCP server**: Safe — FastAPI handles concurrent requests, state is per-invocation
6. **Async executor**: Safe — asyncio event loop serializes coroutines

## Seed

Should each concurrency pattern have a documented "safety card" in ARCHITECTURE.md, similar to how capabilities have requirement tables?
