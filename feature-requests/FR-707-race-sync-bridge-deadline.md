# FR-707: Race sync bridge must not block the caller's event loop unboundedly

**Priority:** HIGH
**Type:** Bug
**Status:** Judged
**Effort:** 1 day
**Requested:** 2026-07-10
**Judged:** 2026-07-10 — scope frozen. Consolidates the parallel session's fix spec (filed as a duplicate FR-706, renumbered here per first-on-origin precedent) with this FR's original stub; 6 findings resolved (see Judgement section).
**Condemned by:** FR-706 witness (`tests/unit/test_fr706_race_timeout_loop_liveness.py`, xfail strict) — measured 5.01 s caller block / 5.01 s host-loop stall for a 0.5 s race timeout
**Incident:** ninchat_voice NC-361 (320–340 s production stall; H2 verdict: event-loop blockage)

## Problem

Two compounding defects in the race timeout path (source-verified; witness-reproduced):

1. `_race_async`'s `finally: await asyncio.gather(*cancelled)` waits for
   loser tasks that wrap uncancellable work (hung TLS read, provider HTTP
   thread) — the race outcome is known at the deadline, but the coroutine
   won't return until every loser finishes (production: provider socket
   timeouts, minutes). The race's own `timeout` fires *before* the finally;
   the hang is in the cleanup after it.
2. `_run_coro_sync_safe`'s running-loop branch then propagates that wait to
   the **caller's thread** via an unbounded `t.join()` — when the caller is
   the host event loop (the NC-361 seam), the whole process goes silent. In
   a voice worker that loop also services audio, STT callbacks, and FSM
   events: one hung provider connection silences a live call.

## Solution (frozen)

Bound both waits; abandon what cannot be reclaimed (the bridge thread is
already a daemon — no interpreter hang):

1. **Bound the cleanup gather:** wrap the `finally` gather in
   `asyncio.wait_for(..., timeout=CLEANUP_GRACE)` — module constant 5.0 s,
   **no YAML knob** (F5). On expiry, log a WARNING naming the still-pending
   candidates by `provider/model` (FR-705 fidelity applies to logs too, F6)
   and proceed — losers are cancelled and daemon-side; waiting longer buys
   nothing. This fixes BOTH entry paths: plain `asyncio.run` hangs
   identically today (F6).
2. **Bound the join (bridge path, only when the race has a timeout, F3):**
   `t.join(timeout=race_timeout + CLEANUP_GRACE + 1.0)`. On expiry raise
   `RuntimeError("race sync bridge abandoned after Xs — bg loop failed to
   exit within its guaranteed budget")` — an invariant breach, deliberately
   **not** a `TimeoutError` (F4: FR-705 deleted that except-branch; a bridge
   TimeoutError would bypass the on_error:skip contract anonymously). With
   the gather bounded this path is nearly unreachable — it is the second
   belt. When `timeout` is None the race may legitimately run forever; the
   join stays unbounded (no deadline authority exists).

## Acceptance Criteria

- [ ] **GREEN = the FR-706 witness passes with its xfail marker removed**
      (strict xfail already errors on pass — the marker cannot be forgotten)
- [ ] Race verdict (winner or AllCandidatesFailedError) reaches the caller
      within `race_timeout + CLEANUP_GRACE + margin` regardless of loser
      cancellability; witness heartbeat-gap threshold (2 s) holds
- [ ] Cleanup-gather expiry logs WARNING naming pending candidates
      (`provider/model`) — caplog unit test (F6)
- [ ] `timeout: null` race: join remains unbounded; no arithmetic on None
      (unit test) (F3)
- [ ] Bridge abandon (forced via monkeypatched budget) raises RuntimeError,
      not TimeoutError (F4)
- [ ] FR-705 enumeration fidelity preserved (candidates named in the error);
      FR-706 thread accounting stays green
- [ ] No behavior change on happy path and plain-timeout path: full race +
      router-race suites green unmodified
- [ ] Tests tagged `@pytest.mark.req("REQ-YG-269")`; `req_coverage --strict`
      green; `fix`-type changelog fragment + diary entry

## Judgement (2026-07-10)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Fix spec filed by a parallel session as duplicate FR-706 (number held by the completed witness, first on origin) | Consolidated here; duplicate file removed — cap-req-id-allocation-race precedent, now recurring at FR level (second id-class strike this week) |
| F2 | Spec re-invented a condemning test the FR-706 witness already provides | Witness xfail removal is the GREEN; only the WARNING-content caplog test is new |
| F3 | Join bound `race_timeout + …` is arithmetic on None for `timeout: null` races | Bound only when a race timeout exists |
| F4 | Bridge abandon raising TimeoutError resurrects the branch FR-705 deleted and bypasses the skip contract anonymously | RuntimeError with invariant-breach semantics, fail-fast |
| F5 | `cleanup_timeout` node-config knob is speculative configurability | Module constant CLEANUP_GRACE=5.0; config only when a real workload demands it |
| F6 | Both entry paths hang today; WARNING must carry candidate names | Bounded gather fixes both; caplog test pins the names |

**Out of scope (purge list):** per-candidate timeout budgets, generic
deadline-aware bridge primitive for other node types (diary seed — separate
FR if the shape recurs), LangGraph executor-shielding variants, retry
semantics.

## Related

- FR-706 (witness + CONDEMNED verdict), FR-705 (error fidelity — same
  incident, message layer), FR-271 (async race origin)
- ninchat_voice NC-361 (H2 verdict: event-loop blockage, reproducible
  without load)
- Doctrine: `composition_bug` (timeout fired as configured; cleanup hung
  after it) — a recovery path with an unbounded wait is a second outage
