# Diary: The Five Modules Under yamlgraph_async_action.py

**Date:** 2026-09-03
**Trigger:** "reflect on csap yamlgraph_async_action hardening... what
learnings and features to graduate to the shared core" — reading
`customer-service-agent-platform/actions/real/yamlgraph_async_action.py`
and its four sibling modules in full, not just grepping for names.

## What's actually there

`yamlgraph_async_action.py` is the one FSM action that calls into yamlgraph
(`load_and_compile_async` + `run_graph_async`) from the real production
consumer. Around that single call site, csap built:

- `_yamlgraph_async_helpers.py` — `classify_graph_failure` (timeout / infra
  / content_filter / mixed), `_extract_event`, `_json_safe`
- `_yamlgraph_async_retry.py` — `_invoke_with_retry` (NC-352): on a
  transient-kind failure, retry exactly once via `run_graph_async(app,
  None, config=run_config)` — LangGraph's checkpoint resume-by-None re-runs
  only the failed node, verified (R-2, logged probes) to not double-append
  messages or lose interrupt-resume values. `content_filter` never retries
  — safety beats liveness, by explicit rule.
- `_yamlgraph_async_snapshot.py` — `SnapshotParams`, collapsing what NC-243
  says was once 16 loose parameters into one dataclass
- `_race_metadata.py` — `_pop_race_winner`, reading structured winner
  metadata the race node already emits
- `bump_generation_action.py` + `_GEN_EXEMPT_EVENTS` — a live generation
  counter that discards stale fire-and-forget results, *except* for a named
  exemption class (`graph_switch`, `crisis_detected`) that must dispatch
  even when stale, because safety-relevant events must never be silently
  dropped by a staleness check built for convenience

Plus `_build_graph_input` inline in the action file: `aget_state()` →
`prior_state.next` set → `Command(resume=user_input)`, else fresh state —
hand-rolled interrupt-resume detection every consumer of an async
checkpointed graph has to write for itself today.

## The correction this reading forced

Two turns ago I told the operator FR-219 (the Memento/generation-counter
speculative node) was "stalled, zero consumer" — evidence of a boundary
enforced reactively. That was half right and half wrong. The *pattern* FR-219
proposed is live in production, just not through FR-219: csap built its own
generation counter at the FSM layer (`bump_generation_action.py`) instead of
waiting on the framework's stateless `speculative` node type. That is not a
framework failure to notice a need — it is the consumer correctly solving a
lifecycle-shaped problem at the layer that owns lifecycle, per this
session's own boundary finding. But it also improves on FR-219's original
design: FR-219 had no exemption class. NC-205 D-3 / FR-372 D-1 discovered,
under real safety pressure, that "discard everything stale" is wrong — some
events must survive a generation mismatch. That refinement doesn't exist
anywhere in the framework-side proposal.

## What clears the graduation bar and what doesn't

The test from this session's boundary work applies directly: does the
candidate make yamlgraph own something it doesn't already own (lifecycle,
FSM re-entrancy, dialogue policy), or does it make yamlgraph's own execution
boundary (`run_graph_async`, checkpointer, `race`) more correct for a need
already proven by production incidents (NC-352, NC-347, NC-183, NC-186)?

**Clears it — graph-execution-boundary concerns, dated production incidents:**
1. Checkpoint-aware bounded retry (NC-352's resume-by-None-on-transient-
   kind) at the whole-invocation level in `executor_async.py`. FR-676
   already added retry to `invoke_async` (the provider-call layer) — this
   is a different, uncovered layer: the graph-invocation layer, gated by a
   coarser failure taxonomy, using the checkpoint instead of a bare retry.
2. A `classify_error()`-shaped utility distinguishing transient/infra vs.
   safety/content-policy failures, so `on_error:` can discriminate by kind
   instead of one policy for every exception.
3. An interrupt-resume helper (`run_or_resume_graph_async` or equivalent)
   wrapping the `aget_state → Command(resume=...) vs fresh state` decision
   that `_build_graph_input` hand-rolls today — every interrupt + async
   checkpointer consumer needs this exact fifteen lines.
4. FR-219, reopened with the exemption-class refinement NC-205/FR-372
   proved necessary — not the original stateless design as filed.

**Does not clear it — stays FSM-owned:**
- Guard-key dedup for fire-and-forget re-entrancy (`_GUARD_PREFIX`) — FSM
  state-entry concern, not graph-execution concern.
- Failure-kind → FSM event routing (crisis line vs. apology line) —
  dialogue policy, explicitly the graph/FSM's content decision, not the
  framework's.
- UI activity emission, Prometheus labels — deployment-specific
  observability wiring.

## The trap, named

I almost graduated candidates 1–4 into one undifferentiated "csap built
retry logic, yamlgraph should have retry logic" recommendation on the first
read. The five-module split only became legible by reading the actual code,
not the file names — `_yamlgraph_async_retry.py` and
`bump_generation_action.py` look like the same kind of thing from a
directory listing and are not: one is a graph-execution concern
(checkpoint resume), the other is FSM lifecycle policy (which events survive
staleness). Naming candidates by directory proximity instead of by which
layer's problem they actually solve would have proposed graduating FSM
policy into the framework — exactly the crossing this whole session's
boundary work argues against.

## Seed

FR-676 fixed retry at the provider-call layer four months before NC-352
independently fixed it at the graph-invocation layer, in a different repo,
without citing FR-676. Is there a standing gap in how yamlgraph's own FR
corpus surfaces "this incident happened in the named production consumer"
back into yamlgraph's own backlog — not as a diary curiosity to be
discovered five investigations deep in one session, but as a mechanical
census (an `NC-*`/`VBOT-*` → yamlgraph-FR cross-reference, run on some
cadence) so the framework doesn't have to wait for someone to read the
sibling repo's action modules line by line to learn what its only real
consumer already had to build around it?
