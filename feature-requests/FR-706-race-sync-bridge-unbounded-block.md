# FR-706: Race sync bridge must not block the caller's event loop unboundedly

**Status:** Proposed
**Type:** Bug
**Effort:** 1 day
**Requested:** 2026-07-10
**Spawned by:** ninchat_voice NC-361 H2 verdict (2026-07-10) — production
stall forensics; sibling of FR-705 (error fidelity, same incident)

## Problem

In the NC-361 incident, each worker hard-stalled for 320–340 s after one race
timeout: zero transcript writes, zero FSM events, then ~5 minutes of queued
STT utterances flushed in <2 s at teardown — proving the CPU was fine and the
**event loop was blocked**. The traceback passes through
`race_node.py _run_coro_sync_safe`.

## Root Cause (current main, verified 2026-07-10)

`_run_coro_sync_safe` (race_node.py:169), on the already-inside-a-loop path:

```python
t = threading.Thread(target=_run, daemon=True)
t.start()
t.join()          # ← unbounded block on the CALLER'S event-loop thread
```

and inside the coroutine it runs, `_race_candidates_async`'s `finally` does:

```python
for task in tasks: task.cancel()
await asyncio.gather(*tasks.keys(), return_exceptions=True)  # ← unbounded
```

Composition: a provider HTTP connection that ignores cancellation (hung TLS
read, unresponsive endpoint — exactly the NC-361 "both candidates pending"
state) makes the `finally` gather wait indefinitely → the dedicated thread
never finishes → `t.join()` never returns → **the caller's event loop is dead
for the duration**. In a voice worker that loop also services audio, STT
callbacks, and FSM events: one hung provider connection silences a live call.
The race's own `timeout` does not protect this path — it fires *before* the
finally; the hang is in the cleanup after it.

## Proposed Solution

Bound both waits; abandon what cannot be reclaimed (daemon thread already
guarantees no interpreter hang):

1. **Bound the cleanup gather:** wrap the `finally` gather in
   `asyncio.wait_for(..., timeout=CLEANUP_TIMEOUT)` (default 5 s), log a
   WARNING naming the still-pending candidates on expiry (FR-705 fidelity
   applies here too), and proceed — losers are daemon-side and cancelled;
   waiting longer buys nothing.
2. **Bound the join:** `t.join(timeout=race_timeout + CLEANUP_TIMEOUT + margin)`;
   on expiry raise `TimeoutError("race sync bridge abandoned after Xs")` —
   loud, and the caller's loop lives. The abandoned daemon thread cannot be
   reclaimed, but a leaked thread is strictly better than a dead event loop.
3. Timeouts configurable via node config (`cleanup_timeout`), defaulted.

## Acceptance Criteria

- [ ] RED: candidate whose coroutine ignores cancellation (shields a sleep) →
      current `_run_coro_sync_safe` blocks past race timeout (assert with an
      outer watchdog); condemns the unbounded join
- [ ] GREEN: same scenario returns/raises within `race_timeout +
      cleanup_timeout + margin`; caller's event loop demonstrably serviceable
      (a concurrent task on the same loop keeps ticking)
- [ ] Cleanup-gather expiry logs WARNING with pending candidate names
- [ ] No behavior change on the happy path and the plain-timeout path
      (existing race tests green)
- [ ] Works on both entry paths: no-loop (`asyncio.run`) and
      inside-loop (thread bridge)

## Related

- FR-705 (race timeout error fidelity — same incident, message layer)
- FR-271 (async race origin), ninchat_voice NC-361 (H2 verdict:
  event-loop blockage, reproducible without load via injected race timeout)
- Doctrine: `composition_bug` (timeout fired as configured, cleanup hung
  after it); a recovery path with an unbounded wait is a second outage
