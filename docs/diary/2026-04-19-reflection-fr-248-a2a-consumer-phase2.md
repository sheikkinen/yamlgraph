# Reflection: FR-248 A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming

**Date:** 2026-04-19
**FR:** FR-248
**Author:** Copilot

## Cognitive Process

The task combined three independent capabilities (Agent Card discovery, skill selection, SSE streaming) into a single feature. The risk was treating them as a monolith rather than composable layers.

## Trap: Quick Confidence on Cache Scope

Initial instinct was to use a module-level dict for Agent Card caching. This would leak state across graph invocations in long-running processes (FastAPI, MCP server). The cure: ContextVar isolates the cache per invocation context — each call starts fresh, no TTL complexity needed.

## Trap: Framework Costume for Streaming

SSE streaming could have been implemented as a full FR-030 graph-level streaming integration. But the requirement is transport-only — the A2A call node collects the complete response and writes it to state_key as a string. Recognizing this distinction avoided pulling in the subgraph streaming machinery. The `streaming` field on NodeConfig is explicitly documented as "transport-only, not FR-030."

## Insight: Boundary Normalization at Agent Card

The Agent Card is an external boundary where untrusted data enters. Parsing via the SDK's `AgentCard` model normalizes the shape at entry. Skill validation then operates on trusted, typed data — no downstream string comparisons against raw JSON.

## Heuristic

**Cache scope follows invocation scope.** When caching external data in a library that may run in long-lived processes, use ContextVar (or equivalent per-request scoping) rather than module globals. The cache lifetime should match the logical operation lifetime, not the process lifetime.

## Seed

Could Agent Card capabilities be used at graph compile time (not just runtime) to statically validate that a requested skill exists before the graph ever runs? This would shift validation left — from runtime ValueError to linter error — similar to how E904 catches streaming on wrong node types.
