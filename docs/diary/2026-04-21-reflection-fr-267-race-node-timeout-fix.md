# Reflection: FR-267 Race Node Timeout Double-Wrap Fix

**Date:** 2026-04-21
**FR:** FR-267
**Branch:** feat/fr-267-race-node-timeout-double-wrap

## What Was Done

Fixed silent state loss in race nodes with `timeout:` config. The root cause: `_compile_race_node` in `node_compiler.py` called `_maybe_wrap_timeout`, which wrapped the race node in an outer `ThreadPoolExecutor(max_workers=1)`. The race node already owns its timeout internally via `as_completed(timeout=...)` with its own thread pool. The double-wrap meant the outer executor submitted the race function, but when the outer future completed, its return value was discarded — the state dict never propagated. No exception, no log, just silent `None`.

Fix: remove the `_maybe_wrap_timeout` call from `_compile_race_node`. Race nodes handle their own timeout. Also added `TimeoutError` handling inside the race node to emit `PipelineError(TIMEOUT_ERROR)` respecting `on_error` config.

## Cognitive Trap: Plausible Wrong Answer

The symptoms — winner logged, state empty, no exception — were easy to misread as an LLM provider issue or a state merge bug. The double-wrap was invisible in logs. This is the **plausible_wrong_answer** trap: the system appeared to work (winner selected, no crash) but produced semantically wrong output (empty state).

The condemning test was the key: a race node with `timeout: 5` must return its winner's state keys. Once that test was red, the double-wrap became the obvious suspect.

## Heuristic

**Timeout ownership must be singular**: When a component declares its own timeout contract (race node's `as_completed(timeout=...)`), no outer layer should impose a second timeout mechanism. Double-wrapping creates a silent discard path where the outer wrapper returns before the inner result is captured. Audit every `_maybe_wrap_*` call to verify the wrapped function doesn't already own that concern.

## Seed

Are there other node types that call `_maybe_wrap_timeout` but already implement their own timeout internally? A static analysis pass over `node_compiler.py` cross-referenced with each node factory's internal timeout usage would catch this class of bug at PR time rather than in production.
