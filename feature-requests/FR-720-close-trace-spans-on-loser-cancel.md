# Feature Request: FR-720 Close Trace Spans on Race-Loser Cancellation

**Priority:** MEDIUM (observability debt with compounding cost; no runtime defect)
**Type:** Observability fix
**Status:** Completed
**Effort:** 0.5–1 day
**Requested:** 2026-07-13
**Judged:** 2026-07-13 — scope frozen. 7 findings; the proposed "preferred" mechanism was unimplementable on current main and is re-pinned (see Judgement section).
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

## Proposed Solution (as judged — F1/F2/F7 re-pin the mechanism)

At the cancellation seam in `race_node.py` — BOTH cancel sites: winner-found
loser cancel AND the FR-707 cancel-only drain (timeout losers leak spans
identically, F7):

- **Handle (F1):** the wrapper does NOT own any callback handle today —
  `_invoke_candidate_async` passes nothing to `ainvoke`; tracing is ambient.
  Fix: pre-generate a `run_id` per ainvoke attempt and pass
  `config={"run_id": ...}` at all three call sites (structured / retry /
  plain; the retry is a second invocation — own id, last id retained). The
  run_id is the handle.
- **Closure (F2):** on `CancelledError`, enqueue
  `client.update_run(run_id, end_time=now, error=..., extra=...)` via the
  langsmith background queue — enqueue only, no await before re-raise; the
  constraint-3 "fallback" is thereby the primary mechanism, unified.
- **Terminal payloads (F5/F7):** `error="cancelled: lost race to
  {provider}/{model}"` with `extra.metadata.race_outcome=lost` on the
  winner path; `error="cancelled: race timed out"` on the drain path — so
  trace queries compute per-candidate win rates for free (NC-367 seed:
  vertex 0/14 required log archaeology).
- **Scope (F3):** close the run our run_id names; child runs out of scope
  (record if observed).

Normalize at the boundary: the fix lives in the race node's candidate
wrapper (where cancellation is injected), not in provider code and not in
consumer projects.

## Acceptance Criteria

- [ ] AC-01 RED witness (unit, LLM-free, F4): race two mocked candidates,
      cancel the loser; assert via a mocked langsmith client that
      `update_run` fires with the loser's run_id, an end_time, and the
      terminal error/metadata — currently nothing fires. Integration
      variant against real LangSmith: key-guarded, slow, desired not
      required.
- [ ] AC-02 Loser spans carry `race_outcome=lost` and the winning
      candidate's provider/model; drain-path losers carry
      `cancelled: race timed out` (F7); winner spans unaffected.
- [ ] AC-03 `CancelledError` is re-raised after enqueue — cancellation
      semantics (FR-271/FR-707 timing: verdict never waits for losers) are
      unchanged; the FR-709 teardown witness suite stays green.
- [ ] AC-04 No new latency on the verdict path: closure is enqueue-only on
      the loser's own task (assert via existing FR-711 local instrument or
      a timing bound in the witness).
- [ ] AC-05 Works when tracing is disabled (no LangSmith env): closure
      skipped cleanly, no errors, no new module-level imports.
- [ ] AC-06 (F6) New REQ under CAP-13 (LangSmith Tracing), id verified free
      against origin at enforce; `req_coverage --strict` green; fix-type
      changelog fragment; diary entry.

## Judgement (2026-07-13)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | "The wrapper owns the callback handle" is FALSE on current main — ainvoke receives no config; tracing is ambient; the preferred mechanism had no handle to close | Wrapper passes `config={"run_id": uuid}` per ainvoke attempt (3 call sites; retry gets its own id); run_id is the handle |
| F2 | Closing from an except block risks awaiting on the teardown path | Enqueue-only via langsmith background queue; the constraint-3 fallback becomes the primary, unified mechanism |
| F3 | ainvoke may create a run tree | Close the named run only; children recorded if observed, out of scope |
| F4 | AC-01's "recording callback handler" cannot witness this (cancellation is exactly what kills callbacks) | Unit witness mocks the langsmith client and asserts update_run payload; real-LangSmith variant optional |
| F5 | Payload underspecified | error string + extra.metadata.race_outcome + winner identity, exact strings pinned above |
| F6 | Traceability unpinned | New REQ under CAP-13 at enforce |
| F7 | Drain-path (timeout) losers leak identically but were unaddressed | Both cancel sites in scope; distinct terminal message |

**Out of scope (purge list):** child-run closure, provider-specific tracing,
consumer-side LangSmith hygiene jobs, retroactive closure of the 38 deployed
zombie spans (they age out; a one-off script is ops, not framework).

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

## Implementation (2026-07-13)

Enforced as judged. RED commit `1543628d`
(tests/unit/test_fr720_span_closure.py, 3 condemned + 2 invariant
guards), GREEN in `race_node.py`:

- F1 handle: `_invoke_candidate_async` pre-generates `run_id = uuid4()`
  per attempt, passes `config={"run_id": run_id}` at all three ainvoke
  sites (structured / retry-with-own-id / plain); witness asserts the
  invoked id equals the closed id.
- F2 closure: `except asyncio.CancelledError` → `_close_cancelled_run`
  → re-raise; `update_run(run_id, end_time, error, extra)` dispatched
  via `run_in_executor` — enqueue-only, no await on the teardown path.
- F5/F7 payloads: winner path `cancelled: lost race to
  {provider}/{model}` + `race_winner` metadata (winner written into a
  shared `race_ctx` dict BEFORE `loser.cancel()`); drain path
  `cancelled: race timed out`; both carry `race_outcome=lost`.
- AC-03/AC-04: verdict-not-delayed witness green; FR-706/707/709/713
  suites green. AC-05: env check precedes any langsmith import/client;
  lazy singleton `_get_langsmith_client`.
- AC-06: REQ-YG-547 under CAP-13; fragment
  `changelog/unreleased/fr-720-close-loser-trace-spans.md`; diary
  `docs/diary/2026-07-13-fr720-fake-narrower-than-interface.md`.
- Deviation (test-only): eight fake `ainvoke(messages)` doubles across
  six suites declared a narrower signature than the Runnable interface
  and crashed with TypeError when config arrived — rewriting two
  cancellation witnesses' scenarios (loser failed instantly instead of
  hanging). Fixed to `ainvoke(messages, config=None)`; see diary.
- Real-LangSmith integration variant: not added (optional per F4).
