# The Runtime's Own Shutdown Was the Third Blocker (FR-707)

**Date:** 2026-07-10
**Context:** FR-707 enforce — the fix for the FR-706-condemned event-loop stall; the frozen design survived contact with `asyncio.run`'s internals only by escalating to the judged *intent*.

## What happened

The frozen solution was two bounds: `wait_for` around the finally-gather,
`t.join(budget)` on the bridge. Implementing it surfaced a third blocker
neither the incident forensics nor the judgement saw: **`asyncio.run`'s own
shutdown** (`_cancel_all_tasks` + `shutdown_default_executor`) also waits
unboundedly for cancellation-ignoring work. Bounding the gather inside the
coroutine still left the verdict hostage — and worse, made the "nearly
unreachable" RuntimeError belt the *common* path, which would have failed
the witness with the wrong exception type.

The escape was in the judgement's own words: *"return the verdict at the
deadline, let cleanup be asynchronous to the caller."* Mechanism follows
intent: the coroutine's result is handed through a Future the instant it
exists (`verdict.set_result(await coro)`); everything after that line —
bounded drain, WARNING, asyncio.run's shutdown grief — happens inside the
daemon thread, invisible to the caller. The finally becomes cancel-only.
Witness: 5.01 s block → passes at the deadline; 64/64 race tests green.

## Second finding: the fixture taxonomy of "hung"

The drain-WARNING test failed with empty caplog: a `to_thread` loser dies
*as a task* instantly on cancel — the hung thread is invisible to
`asyncio.all_tasks()`, so the drain correctly saw nothing. The NC-361 shape
needed a **cancellation-ignoring coroutine** (swallow CancelledError, keep
sleeping — a hung TLS read). Two kinds of "hung" with different observability:
thread-hidden (blocks shutdown machinery) vs task-visible (blocks gather).
A liveness fix must be tested against both; each catches what the other
cannot see.

## Heuristic

When bounding waits around an async runtime, enumerate EVERY wait between
the verdict and the caller — including the runtime's own teardown
(`asyncio.run` shutdown, executor join, interpreter atexit). Bounding the
waits you wrote while inheriting the ones you didn't is the
`downstream_fix` trap wearing concurrency clothes. The only structure that
survives arbitrary blockers is verdict-first handoff: deliver the result at
the earliest instant it exists; let all cleanup be someone else's lifetime.

**Seed:** FR-706's diary asked for a generic deadline-aware bridge
primitive. This enforce answered its shape: Future-handoff + post-verdict
drain, not bounded joins. If map nodes or future async wrappers grow the
same seam, extract `_run_coro_sync_safe` as that primitive — the race node
is its proof.
