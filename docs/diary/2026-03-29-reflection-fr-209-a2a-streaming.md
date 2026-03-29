# Reflection: FR-209 — A2A Demo Streaming Response

**Date:** 2026-03-29
**FR:** FR-209

## Cognitive Process

Started with what appeared to be a simple demo-only change: add a Part 3 to
`demo.sh` exercising `message/stream`. The FR explicitly stated "No production
code changes required."

### Trap: Unchallenged Premise

The FR assumed the A2A SDK's `message/stream` endpoint "just worked." TDD
discipline (Commandment 7) required running the demo to verify — which revealed
only the `working` event reached the SSE client. The `artifact` and `completed`
events were silently dropped.

### Root Cause

`event_queue.close(immediate=True)` in the `execute()` method's `finally` block
invoked the A2A SDK's `EventQueue.clear_events()`, destroying any pending events
the SSE consumer hadn't yet drained. The original comment ("SDK handles consumer
drain") was a **plausible wrong answer** — it sounded correct but wasn't.

### Second Trap: Working System Inertia

The existing unit tests all passed because they used mock queues that collected
events synchronously. The real `EventQueue` with asyncio scheduling exposed the
timing-dependent bug only under actual SSE consumption.

### Third Trap: Venv Worktree Isolation

Edits to `a2a_server.py` in the worktree weren't picked up because `pip install
-e .` pointed to the main repo, not the worktree. Several debugging iterations
were wasted before noticing the installed package location didn't match the
worktree.

### Fix

Changed `close(immediate=True)` to `close(immediate=False)` in the `finally`
block. This calls `queue.join()` which waits for the SSE consumer to drain all
enqueued events before closing. The interrupt handler's redundant `close` call
was also removed.

## Heuristic

**"Test the demo, not just the unit."** Unit tests with mocks prove the contract
but hide asyncio scheduling and I/O timing bugs. Integration-level verification
(running the actual server + client) is the only way to validate SSE streams.

## Seed

Should the `YAMLGraphAgentExecutor.execute()` method even call
`event_queue.close()` at all? The A2A SDK's `_run_event_stream` wrapper already
calls `queue.close()` after `execute()` returns. Double-closing is redundant at
best and subtly dangerous (as this FR proved). Consider removing the close from
`execute()` entirely, leaving lifecycle management to the SDK wrapper.
