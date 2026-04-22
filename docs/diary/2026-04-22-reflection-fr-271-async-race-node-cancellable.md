# Reflection: FR-271 Async Race Node with Cancellable Candidates

**Date:** 2026-04-22
**FR:** FR-271
**Effort:** ~2 h

## What happened

Rewrote `race_node.py` from `ThreadPoolExecutor` + `as_completed` to an asyncio
core. The key design is three cooperating pieces:

1. `_invoke_candidate_async` — creates LLM synchronously (pure construction), then
   `await llm.ainvoke()` for cooperative cancel at the transport await point.
2. `_race_async` — `asyncio.wait(FIRST_COMPLETED)` loop with a once-computed
   deadline; losers are cancelled and gathered before the function returns.
3. `_run_coro_sync_safe` — detects an existing event loop and falls back to a
   `threading.Thread` bridge (via `concurrent.futures.Future`) to avoid nesting
   `asyncio.run()` inside a running loop.

## Cognitive traps encountered

**Thread-to-async interface blindspot.** I initially reached for `threading.Thread`
with a `list[Any]` to capture exceptions. This works but catches `Exception` broadly,
triggering ruff BLE001. The cure: `concurrent.futures.Future` is the stdlib-blessed
cross-thread exception channel — `set_exception(exc)` accepts `BaseException` and
`future.result()` re-raises it. No noqa needed.

**`asyncio.run()` and executor shutdown.** The rubber duck surfaced the risk that
`asyncio.run()` calls `loop.shutdown_default_executor()`, which blocks if any task
used `loop.run_in_executor()`. Since the mock LLMs use `asyncio.sleep` (native
coroutines, no executor), this never fires in tests. Production LangChain providers
also use their own executor (not the loop's default), so the risk is confined to edge
cases and is documented in the FR as Medium risk.

**Mock async interface.** Pre-existing test mocks only had sync `.invoke`.
After the async rewrite, `await llm.ainvoke()` on a plain `MagicMock` raises
`TypeError: object MagicMock can't be used in 'await' expression`.
Fix: update `_make_mock_llm` to add `async def ainvoke` with `asyncio.sleep`.
Three additional inline mocks in content-normalization tests needed `AsyncMock`.
The rule: **mock at the boundary that the code under test uses**, not the boundary
the old code used.

## Heuristic extracted

> When rewriting a sync concurrency primitive to async, identify every test mock that
> bridges the old primitive and update it to the new one. A `MagicMock` with a sync
> method is a hidden assumption about the execution model.

## Seed

Can `_run_coro_sync_safe` be extracted to a shared utility so that future async
node types (map, pipeline) share the same bridge and its correctness is tested once?
If more than two async node types use the pattern, graduate it to
`yamlgraph/utils/async_bridge.py`.
