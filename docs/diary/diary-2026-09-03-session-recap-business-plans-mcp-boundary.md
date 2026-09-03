# Diary: Session Recap — Business Plans, MCP, and the yamlgraph Boundary

**Date:** 2026-09-03
**Trigger:** end-of-session request to document research findings and
recommendations in one place. Nine investigations, escalating from general
research review to reading the one real production consumer's actual code.

## What was investigated, and the verdict on each

| # | Investigation | Verdict |
|---|---|---|
| 1 | Business plans / opportunities review | Freshest artifact is the 2026-09-02 brainstorm ranking AuditPack, CodingProof, RegMap, CallCensus top-6; none filed as FRs yet |
| 2 | Voicebot-specific opportunities | Only shipped item is FR-808 (regulated evidence, named Tervola pilot); higher-value wedges (CallCensus, structured intake) still brainstorm-only |
| 3 | Design patterns, general → applicability | Circuit Breaker is the one evidence-backed gap (`race` incident density 5.0, highest in the registry); Decorator/Game-Loop/Saga are precedent- or doctrine-blocked, not novel |
| 4 | Tool-definition census (repo-wide) | 442 declarations / 139 files; manifest reuse (FR-768) works but only ~9% adopted; found live drift — `examples/demos/meta/graph.yaml`'s stale "per the judge/enforcer convention" comment, false since those two migrated to the shared manifest |
| 5 | MCP viability + `session.create_message()` | Both the server direction (FR-910) and the client-shaped precedent (A2A, `contrib/a2a_client.py`) were retired five days ago for zero named consumer; the sampling backend (FR-082) was built and dropped same day as "a solution seeking a problem" |
| 6 | Boundary reflection → corollary of disqualifying signs | Five unrelated audits converged on one sentence: yamlgraph does typed reasoning over a known input, invoked by something owning lifecycle/protocol — enforced reactively (by autopsy), never pre-hoc |
| 7 | csap (real consumer) identity + architecture | Confirmed: package name `ninchat-voice`, yamlgraph 0.5.17 pinned from PyPI (clean package boundary, no fork), FSM-as-conductor doctrine independently re-derived in its own `docs/context/call-lifecycle.md` |
| 8 | csap yamlgraph-usage census | Zero bare `llm` nodes in any callback graph — `race` (34 uses across 7 graphs) is the sole LLM-invocation path in production |
| 9 | csap `yamlgraph_async_action` hardening → graduation candidates | Four candidates clear the boundary test (checkpoint-aware bounded retry, failure classification, interrupt-resume helper, FR-219 reopened with an exemption-class refinement); three correctly stay FSM-owned (re-entrancy guard, failure→dialogue-event routing, deployment telemetry) |

## The throughline

Every investigation, approached with no shared premise, rediscovered the
same boundary: **YAMLGraph does typed reasoning over an input known at
authoring time, invoked by something else that owns discovery, lifecycle,
and protocol.** Five independent measurements of one line is stronger
evidence than any single audit — but every one of the five found the
boundary *after* real effort had already crossed it (FR-082 shipped then
cut same-day; FR-219 approved four months with no consumer; a full evening
of Discord/PSTN design before the self-critique). The boundary is correct
but reactive, enforced by autopsy rather than by a judge-time gate.

Reading the real consumer's code directly (csap) both confirmed and
refined this: the Memento/generation-counter pattern from FR-219 is live in
production, just built at the FSM layer instead of the framework layer
(`bump_generation_action.py`) — and production discovered a design detail
(safety events must survive a stale-generation discard) the framework-side
proposal never had. The consumer solved its own lifecycle-shaped problem
correctly, at the layer that owns lifecycle, without waiting on the
framework — which is exactly why the framework-side FR never got a
consumer to unstick it.

## Recommendations, priority order

1. **File the FR with the strongest evidence: checkpoint-aware bounded
   retry in `executor_async.py`.** csap's NC-352 resume-by-None pattern is
   proven in production (probes logged, verified no double-append), and
   fills a real gap FR-676 (Enforced) doesn't cover — FR-676 retries at the
   provider-call layer (`invoke_async`); NC-352 retries at the whole-graph-
   invocation layer using the checkpoint. Neither covers the other.
2. **Circuit-breaker / retry tuning on `race`** — justified twice over:
   highest incident density in the OSS registry (5.0) *and* the only
   LLM-invocation path in the real consumer's production graphs (34 uses,
   zero bare `llm` nodes). Two independent sources agreeing on the same
   primitive is rare enough to act on directly.
3. **Extract the interrupt-resume helper and failure-classification
   utility** csap hand-rolls today (`_build_graph_input`,
   `classify_graph_failure`) into `executor_async.py` — small, mechanical,
   low risk, proven code.
4. **Reopen FR-219 with the exemption-class refinement**, not the original
   stateless design — production found the missing detail.
5. **Coordinate the AuditPack business wedge with csap's own
   `architecture-claims-pipeline-plan.md`** (mirrored across both repos,
   dated 2026-08-21) rather than treating it as unstarted — csap's
   VBOT-101-A/B are the first real implementation attempt; yamlgraph's own
   FR should learn from that attempt, not duplicate it.
6. **No action on MCP** — correctly parked twice over; revisit only if a
   named external MCP host gets a dated first consumer.
7. **Opportunistic**: fix the `meta` graph's stale manifest-convention
   comment; consider a lint rule for "per X convention" prose lacking a
   `manifest:` reference.

## Seed

Three prior diary entries this session (`diary-tool-census`,
`reflect-boundary`, `csap-hardening-reflect`) each found the same class of
gap independently — the framework learns what its one real consumer needed
*after* someone reads that consumer's code line by line, in a single
session, months after the incidents that proved the need. Is there a
standing mechanical census — an `NC-*`/`VBOT-*` incident scan run on some
cadence, cross-referenced against yamlgraph's own FR corpus — that would
surface "the named consumer already solved this at their layer" before the
next session has to rediscover it by reading five action modules cold?
