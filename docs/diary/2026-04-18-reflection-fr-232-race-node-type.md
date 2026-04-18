# Diary: FR-232 Race Node Type

**Date:** 2026-04-18
**FR:** FR-232
**Cap:** CAP-91

## Cognitive Process

The FR was anchored by two known pitfalls documented upfront: the "first completed ≠ first successful" race semantics bug, and the sync/async boundary problem with `asyncio.run()` inside an already-running event loop. Both were addressed by using `ThreadPoolExecutor` rather than asyncio — a deliberate choice that sidesteps the event loop boundary entirely while remaining correct under LangGraph's sync execution model.

## Trap Avoided: False Completion

A naive `FIRST_COMPLETED` future strategy cancels all pending tasks the moment *any* future finishes — including failures. The implementation loops over completions until a successful result is found, only then cancelling the rest. This is the correct semantic for "race to the first *winner*".

## Insight

**ThreadPoolExecutor over asyncio for sync-first codebases.** When the surrounding framework is synchronous (LangGraph node functions are sync), `ThreadPoolExecutor` is simpler, avoids event loop conflicts, and achieves the same wall-clock concurrency for I/O-bound LLM calls.

## Heuristic

When adding concurrent execution to a sync-first codebase, prefer `ThreadPoolExecutor` over asyncio unless the framework already owns an event loop. Mixing `asyncio.run()` with an existing loop is a silent failure mode.

## Seed

Could a `race` node optionally stream partial tokens from the first responding model, rather than waiting for its full completion, to further reduce perceived latency?
