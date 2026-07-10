# FR-707: Unblock the sync-bridge — race timeout must return at the deadline

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-10
**Condemned by:** FR-706 witness (`tests/unit/test_fr706_race_timeout_loop_liveness.py`, xfail strict) — measured 5.01 s caller block / 5.01 s host-loop stall for a 0.5 s race timeout
**Incident:** ninchat_voice NC-361 (320–340 s production stall)

## Problem

Two compounding defects in the race timeout path:

1. `_race_async`'s `finally: await asyncio.gather(*cancelled)` waits for
   loser tasks that wrap uncancellable thread work (provider HTTP) — the
   race outcome is known at the deadline, but the coroutine won't return
   until every loser's thread finishes (production: provider socket
   timeouts, minutes).
2. `_run_coro_sync_safe`'s running-loop branch then propagates that wait to
   the **caller's thread** via `t.join()` — when the caller is the host
   event loop (the NC-361 seam), the whole process goes silent.

## Direction (to be judged)

- Deadline authority: after cancellation, bound the loser-drain
  (`asyncio.wait(..., timeout=grace)`) and abandon stragglers to the
  background thread's lifetime — return the verdict at the deadline, let
  cleanup be asynchronous to the caller.
- The bridge (`t.join()`) may keep its blocking semantics only if the coro
  it waits on honors the deadline; alternatively make the bridge
  deadline-aware (`t.join(timeout)` + abandon).
- Removing the FR-706 xfail marker is this FR's GREEN (strict xfail will
  error the moment the fix works — the marker cannot be forgotten).

## Acceptance Criteria

- [ ] FR-706 witness passes with the xfail marker **removed**
- [ ] Race verdict (winner or AllCandidatesFailedError) reaches the caller
      within timeout + bounded grace regardless of loser cancellability
- [ ] No thread/task leak beyond a documented bounded grace (FR-706 thread
      accounting stays green)
- [ ] FR-705 enumeration fidelity preserved (candidates still named)
- [ ] Full race + router-race suites green
