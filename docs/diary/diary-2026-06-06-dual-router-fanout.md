# Diary: One Source, Two Routers — The Additive Fan-Out Trap

**Date:** 2026-06-06
**FR:** FR-467 (Conditional Edge to Map Node)
**Trap:** `downstream_fix` → `symptom_patch` averted by two-level condemnation

## Observation

The dungeon-master turn loop (FR-466) refused to terminate. Resuming the
`dm_window` interrupt with `end` parsed `dm_action == 'end'` correctly, the
expression router returned `__end__` — and yet the graph re-entered the
`plan_all` map node forever.

The first instinct was a *downstream fix*: the `beat` channel was raising
`InvalidUpdateError`, so split it into `draft_beat`/`beat`. That removed a
symptom but not the loop. The loop was a different boundary entirely.

The root cause sat at the **edge-compilation boundary**. `_handle_to_map_edge`
consumed the `parse_dm -> plan_all` edge and registered an *unconditional*
`add_conditional_edges` map router — silently discarding the edge's
`condition`. The node's sibling `parse_dm -> END` condition was wired as a
*second* expression router. LangGraph runs every router on a node each
superstep and unions their targets (documented, as-designed). So the map branch
fired every turn no matter what the condition said.

## The two-level condemnation

The decisive move was refusing to fix until the fault was *attributed*. Two
condemning tests, written before any fix:

1. `test_interrupt_loop_termination.py` — a minimal YAMLGraph repro proving the
   loop never terminates (RED).
2. `test_langgraph_dual_router_fault.py` — *pure LangGraph*, no YAMLGraph,
   proving that two `add_conditional_edges` on one node fan out to the union and
   that a single router terminates (GREEN).

The second test exonerated LangGraph. The bug was ours: emitting two routers
for one source. Without it, the easy story — "LangGraph mishandles conditional
map edges" — would have sent the fix in the wrong direction.

## The Send subtlety (judgment caught it)

The judge caught a would-be `symptom_patch`: routing the matched condition to
the map *sub-node name as a string* would have made the loop "work" while
silently destroying map semantics — one bogus plan over the whole state instead
of N parallel per-item plans. The router must return `map_edge_fn(state)` (the
`list[Send]`), with the sub-node name appearing only in the `path_map`. A green
loop that produces wrong output is harder to catch than a crash.

## Heuristic

**Two routers on one source is never what you want.** When a node has both an
unconditional fan-out edge and conditional edges, LangGraph's additive union
makes the condition a no-op. Normalize at the *compilation* boundary: a
conditional edge to a map node must fold the map's `Send` fan-out *into* the
single expression router, and a dual-router source must fail loudly at compile
time — not loop silently at runtime.

## Seed

The guard raises `ValueError` because no `GraphCompilationError` type exists.
Graph-configuration faults (unknown target, dual router, missing state key) are
all `ValueError` today, indistinguishable from runtime value errors. Should
graph compilation own a dedicated exception hierarchy so authors can catch
"my graph is malformed" separately from "my data is wrong" — and so the
compiler can attach the offending node/edge as structured context?
