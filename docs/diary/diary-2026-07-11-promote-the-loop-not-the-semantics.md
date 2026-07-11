# Promote the Loop, Not the Semantics

**Date:** 2026-07-11
**Context:** Design reflection — should `type: race` be promoted from node level to graph level? Examined along two axes: semantics and threading.

## What happened

The question "promote race to graph level?" arrived as one question but
decomposed into two with **opposite answers**. Semantically, promotion is
wrong: race's restriction to *same prompt, N pure LLM candidates* is not
an accident of scope but the invariant that makes cancellation safe.
Racing arbitrary subgraphs inherits side effects with no rollback,
winner-only state merge with no transactional primitive, and undefined
interrupt/resume semantics for cancelled losers — all while fighting a
substrate (LangGraph `Send`) that only knows join-all.

Threading-wise, promotion is exactly right — but of the **execution
substrate**, not the node. The entire bridge apparatus
(`_run_coro_sync_safe`, `CLEANUP_GRACE`, `_BRIDGE_MARGIN`, daemon thread
per invocation) exists because an async race is embedded in a sync node
inside a sync graph. The FR scar trail proves the point: NC-361 (stall),
FR-707 (verdict/cleanup split), FR-709/711 (google loop-affinity defect)
are not race bugs — they are *layer-mismatch* bugs. A graph-owned
long-lived event loop dissolves the bridge entirely: race collapses to
`asyncio.wait(FIRST_COMPLETED)`, cancellation propagates natively, and
the FR-711 defect class becomes unreachable by construction.

## The trap

**Scar tissue mislocated.** Race accumulated six FRs of concurrency
fixes, so it *looks* like the complex component — the natural reading is
"race is hard, generalize it carefully." But every scar sits on the
sync/async boundary the node straddles, not in the race logic itself
(~60 lines, boringly correct). When a component collects incident after
incident, ask: do the scars belong to the component, or to the boundary
it is forced to straddle? Fixing the component again is `downstream_fix`;
moving the boundary is the cure.

A second, quieter trap: **"promote X" questions conflate axes.** What is
raced (semantics) and where the concurrency lives (substrate) are
independent decisions that arrived fused in one word. Decomposing before
answering flipped one axis to *no, the restriction is load-bearing* and
the other to *yes, and it deletes three FRs' worth of machinery*.

## Heuristic

When asked to generalize a component, split the question into
**contract** and **substrate**. A restriction in the contract that makes
correctness hold by construction (purity of raced units) should be kept;
complexity in the substrate that exists only to bridge layers (sync↔async)
should be promoted upward until it dissolves. The test: after promotion,
does code get deleted? Loop promotion deletes the bridge; semantic
promotion adds a purity-contract validator YAML cannot even express.

**Seed:** If the graph runtime owned one event loop, race is merely the
first beneficiary — map fan-out, A2A calls, and copilot nodes all pay
thread-bridge tax today. What would an async-first `run_graph` migration
cost, and could the sync CLI become the thin wrapper instead of the
other way around?
