# Diary: FR-069 Per-Node Timeout for Map Branches

**Date:** 2026-04-19
**FR:** FR-069

## Cognitive Process

Per-node timeout required intercepting node execution at two distinct boundaries: map branch fan-out (via `ThreadPoolExecutor`) and regular nodes (via `_maybe_wrap_timeout` in node compiler handlers). Both paths needed identical `concurrent.futures.TimeoutError` handling placed before the generic `except Exception` to avoid shadowing.

## Trap Avoided: Partial Remediation

Only adding timeout support to map branches would have left all other node types unguarded. The fix covered all node types uniformly — map and non-map — using a shared `_maybe_wrap_timeout` wrapper.

## Insight

**Timeout is a cross-cutting concern.** It belongs at the execution wrapper level, not inside individual node implementations. Wrapping at compile time (node_compiler) keeps node logic clean and makes timeout transparent to LLM and tool nodes alike.

## Heuristic

When adding a constraint that applies to all node types (timeout, retry, rate-limiting), implement it as a compile-time wrapper, not per-node logic. The node compiler is the correct boundary.

## Seed

Should timeout failures feed into the `race` node's winner-selection logic — allowing a slow-responding candidate to time out and cede victory to the next-fastest, rather than propagating a `TIMEOUT_ERROR`?
