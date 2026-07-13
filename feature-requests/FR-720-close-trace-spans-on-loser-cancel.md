# Feature Request: FR-720 Close Trace Spans on Race-Loser Cancellation

**Priority:** MEDIUM (observability debt with compounding cost; no runtime defect)
**Type:** Observability fix
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-07-13
**Spawned by:** ninchat_voice NC-367 census verdict (BOUNDED — pending-forever
spans are zombie SPANS, not zombie work); NC-366 finding 2/3 (38/38 deployed
vertex spans pending-forever); FR-713 Related seed ("close the LangSmith span
when a race loser is cancelled")
**Related:** FR-713 (persistent bridge loop), FR-711 (latency witness — its
deployed A/B was blinded by this artifact), FR-271 (loser cancellation),
FR-707 (cancel-only verdict)

## Problem

When a race node cancels a losing candidate (`race_node.py` — winner found →
`loser.cancel()`), the loser's LangChain LLM invocation is torn down at an
await point and its LangSmith span is **never closed**: the run stays
`pending` forever, with no error and no end_time.

Measured cost on the deployed fleet (NC-367, project pr-fly-ninchat-voice,
2026-07-13 window): **38 azure spans ok / 38 vertex spans pending** over 14
races — every loser span leaks. Consequences:

1. **False alarms:** the pending-forever population is indistinguishable from
   hung work in any trace query. NC-366 flagged it as a possible leak;
   NC-367 needed a full deployed census (7 live phone calls, on-box log
   taps) to prove it harmless. That disambiguation tax is paid again on
   every future trace-based investigation until the spans close.
2. **Blinded instruments:** FR-711's deployed transport A/B returned
   "0 completions" for google in both arms partly because completion state
   is unreadable for cancelled losers — the artifact corrupted a verdict
   instrument.
3. **Commandment 9:** operational truth requires traces that reflect
   execution. A span state that means "cancelled by design" must not render
   as "pending".

## Proposed Solution

At the cancellation seam in `race_node.py` (both the winner-found loser
cancel and the FR-707 cancel-only drain), close the loser's trace before or
upon cancelling:

- Preferred: catch `asyncio.CancelledError` inside the per-candidate wrapper
  coroutine and end the run-tree/callback with a terminal state (e.g.
  `end(error="cancelled: lost race to <winner>")` or metadata tag
  `race_outcome=lost`), then re-raise. The wrapper owns the callback handle;
  no global LangSmith client work needed.
- The span must record which candidate won, so trace queries can compute
  per-candidate win rates for free (NC-367 seed: vertex 0/14 — today this
  requires log archaeology).

Normalize at the boundary: the fix lives in the race node's candidate
wrapper (where cancellation is injected), not in provider code and not in
consumer projects.

## Acceptance Criteria

- [ ] AC-01 RED witness: integration test races two candidates, cancels the
      loser, then asserts via the LangSmith client (or a recording callback
      handler for unit scope) that the loser's run has an end_time and a
      terminal state — currently fails (run stays pending).
- [ ] AC-02 Loser spans carry `race_outcome=lost` and the winning
      candidate's provider/model; winner spans unaffected.
- [ ] AC-03 `CancelledError` is re-raised after span closure — cancellation
      semantics (FR-271/FR-707 timing: verdict never waits for losers) are
      unchanged; the FR-709 teardown witness suite stays green.
- [ ] AC-04 No new latency on the verdict path: span closure happens on the
      loser's own task, not the winner's return path (assert via existing
      FR-711 local instrument or a timing bound in the witness).
- [ ] AC-05 Works when tracing is disabled (no LangSmith env): no errors, no
      new dependencies imported at module level.

## Constraints

1. Cancel-only discipline (FR-707) is frozen: closing the span must not
   reintroduce awaiting losers on the verdict path.
2. No provider-specific code — the fix is at the race-node seam, uniform
   for all candidates.
3. If the LangChain callback API cannot close a span from inside a
   cancelled coroutine (known limitation risk), the fallback is a
   post-verdict fire-and-forget task on the bridge loop that patches the
   run via the LangSmith client — must still satisfy AC-04 and drain within
   CLEANUP_GRACE (NC-367 proved the loop censuses clean; keep it that way).

## Evidence

- `projects/ninchat_voice/docs/analysis/nc367-census-2026-07-13.md`
  (38 pending spans / 14 races, R-4 disambiguation)
- `projects/ninchat_voice/logs/nc367-langsmith-census.txt` (raw span census)
- `yamlgraph/node_factory/race_node.py` L188–206 (the two cancel sites)
