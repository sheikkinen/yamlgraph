# Feature Request: FR-267 Fix race node timeout: silent state loss from double ThreadPoolExecutor wrap

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-21

## Summary

Race nodes with `timeout:` in YAML silently lose their entire return value. The race node logs a winner, but all state updates (`state_key`, `_race_winner`, `current_step`, `_loop_counts`) are lost — downstream nodes see `None` or default values. No exception is raised.

## Value Statement

Graph authors using race nodes with `timeout:` get correct state propagation instead of silent data loss that masquerades as LLM/provider issues.

## Problem

`_compile_race_node` in `node_compiler.py` (line 277) wraps the race node function in `_maybe_wrap_timeout`, which creates an outer `ThreadPoolExecutor(max_workers=1)`. The race node _already_ uses its own `ThreadPoolExecutor` with `as_completed(timeout=...)` internally (lines 148–156 in `race_node.py`). This creates nested thread pools.

The nested-pool interaction silently discards the return value: the race node executes correctly, logs its winner, but LangGraph never receives the state update dict.

The `timeout` config key has **two distinct meanings** for race nodes:
1. **Intended (race-internal):** total race deadline via `as_completed(timeout=...)` — bounds how long to wait for candidates.
2. **Accidental (outer wrap):** wall-clock guard via `_maybe_wrap_timeout` — redundant because the race already bounds its own time.

Additionally, `race_node.py` does not catch `TimeoutError` from `as_completed`. The `for future in as_completed(futures, timeout=timeout)` loop raises `TimeoutError` when the deadline expires before all futures complete. This exception propagates _outside_ the `try/except Exception` block (which only wraps `future.result()`). Currently masked by the outer wrapper (which itself is broken for race nodes), this gap must be fixed when the outer wrapper is removed.

### Verification matrix

| `timeout:` on race node | Race logs winner | Downstream sees state | Result |
|--------------------------|:----------------:|:---------------------:|:------:|
| Present (current)        | ✓                | ✗ (`None`)            | **BUG** |
| Removed                  | ✓                | ✓                     | PASS   |

## Proposed Solution

Two changes, both in service of race-node timeout correctness:

### Change 1: Remove outer wrapper (`node_compiler.py`)

Remove the `_maybe_wrap_timeout` call from `_compile_race_node`. The race node's native `as_completed(timeout=...)` already enforces the timeout contract.

**Before (buggy):**

```python
def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(...)
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)  # ← bug
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
```

**After:**

```python
def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(...)
    # Race owns `timeout` natively via as_completed(timeout=...);
    # do NOT wrap in _maybe_wrap_timeout (nested pools drop return value).
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
```

### Change 2: Handle TimeoutError in race node (`race_node.py`)

Wrap the `for future in as_completed(...)` loop in a `try/except TimeoutError` block. On timeout expiry, cancel remaining futures and fall through to the all-failed handler:

```python
try:
    for future in as_completed(futures, timeout=timeout):
        candidate = futures[future]
        try:
            result = future.result()
            # ... existing winner logic ...
        except Exception as e:
            errors.append((candidate, e))
except TimeoutError:
    for f in futures:
        f.cancel()
    errors.append(({}, TimeoutError(f"Race {node_name} timed out after {timeout}s")))
```

This ensures timeout expiry produces a structured `PipelineError(TIMEOUT_ERROR)` via the existing `on_error` path, not a raw exception.

### Timeout semantics clarification

The race node `timeout` is a **total race deadline** — it bounds the maximum wall-clock time waiting for any candidate to succeed. This matches the `as_completed(timeout=...)` behavior. It is NOT a per-candidate timeout.

## Acceptance Criteria

- [x] `_compile_race_node` does not call `_maybe_wrap_timeout`
- [x] `race_node.py` catches `TimeoutError` from `as_completed` and returns structured error via `on_error` path
- [x] Condemning test via **compile path**: race node with `timeout: N` where a candidate succeeds returns full state dict (`state_key`, `_race_winner`, `current_step`, `_loop_counts` all non-None)
- [x] Condemning test: race node with `timeout: N` and `parse_json: true` returns parsed dict in state
- [x] Test: race node with `timeout` where all candidates exceed deadline returns `PipelineError(TIMEOUT_ERROR)` when `on_error: skip`, raises when no `on_error`
- [x] Regression test: race node **without** `timeout:` continues to work unchanged
- [x] Existing race node tests pass (`tests/unit/test_race_node.py`)
- [x] Linter tests pass (`tests/unit/test_linter_patterns_race.py`)
- [x] `@pytest.mark.req("REQ-YG-266")` on new tests; REQ-YG-266 added to ARCHITECTURE.md, REQ-YG-233 amended
- [x] CAP-119 capability YAML created in `capabilities/`
- [x] `req_coverage.py` passes with `--strict`

## Requirement

**REQ-YG-266:** Race node applies exactly one timeout mechanism — its native `as_completed(timeout=...)`. The node compiler must not apply `_maybe_wrap_timeout` to race nodes. On timeout expiry (no candidate succeeds within deadline), the race node must produce a structured `PipelineError(TIMEOUT_ERROR)` and respect `on_error` configuration, not raise a raw exception.

**Amends REQ-YG-233:** Add: "Race node `timeout` is a total race deadline (not per-candidate). Timeout enforcement is internal to the race node; `_maybe_wrap_timeout` must not be applied."

**Amends REQ-YG-078 (CAP-96):** Narrow scope: "`_maybe_wrap_timeout` applies to non-map node types **except race**, which owns timeout natively."

## Alternatives Considered

1. **Fix `_maybe_wrap_timeout` to detect nested pools** — rejected. The outer wrapper is genuinely redundant for race nodes; adding detection complexity buys nothing. Other node types that lack native timeout handling still benefit from the wrapper.

2. **Add a `skip_timeout_wrap: true` flag to NodeCompileContext** — rejected. Over-engineering a one-off exclusion. A simple code-path skip is clearer than a metadata flag.

3. **Unwrap the race node's internal timeout and rely solely on `_maybe_wrap_timeout`** — rejected. The race node's `as_completed(timeout=...)` is semantically correct (it bounds the _race_, not the node). Replacing it with the outer wrapper would change timeout semantics and break `on_error` handling within the race.

4. **Separate FR for TimeoutError handling** — rejected. The gap is exposed directly by removing the outer wrapper. Shipping one without the other would regress timeout-expired behavior from "silently broken" to "raw exception". Both changes serve the same invariant: race node owns its timeout contract end-to-end.

## Related

- **Upstream issue:** [#152](https://github.com/sheikkinen/yamlgraph/issues/152)
- **Downstream project FR:** NV-240 in `sheikkinen/ninchat-voice`
- **Race node FR:** FR-264 (`parse_json` content normalization) — independent, already merged
- **Timeout FR:** FR-069 (per-node timeout bounding via `_maybe_wrap_timeout`, CAP-96)
- **Race node CAP:** CAP-91 (race node type, REQ-YG-233)
- **Key files:** `yamlgraph/node_compiler.py:270–279`, `yamlgraph/node_factory/race_node.py:90,148–156`

## Research Brief

### Competitive Landscape

No competing framework suffers from this bug because none layer a generic timeout wrapper on top of a node that already owns its timeout:

| Framework | Race Primitive | Timeout Method | Double-Wrap Risk |
|-----------|---------------|----------------|-----------------|
| **LangGraph** (upstream) | Implicit via `concurrent.futures.wait(FIRST_COMPLETED)` | Single shared `BackgroundExecutor` with deadline recalculation per loop iteration ([_runner.py:227-232](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/pregel/_runner.py)) | ✅ None — one executor per graph, no per-node wrapping |
| **OpenAI Agents SDK** | Multi-phase settlement with `asyncio.wait(FIRST_COMPLETED)` + grace periods | Pure async — deadline tracking on event loop, no thread pools at all ([tool_execution.py](https://github.com/openai/openai-agents-python/blob/main/src/agents/run_internal/tool_execution.py)) | ✅ None — no thread pools |
| **CrewAI** | ❌ No race primitive | Sequential task execution; relies on provider timeouts | N/A |
| **AutoGen** | ❌ No race primitive | Agent message-passing loop; no parallel execution | N/A |
| **Google ADK** | Not publicly documented for this pattern | — | — |

**Key insight:** LangGraph upstream avoids the problem by managing a single executor at the graph runner level. YAMLGraph's `_maybe_wrap_timeout` creates a _new_ `ThreadPoolExecutor(max_workers=1)` per node — correct for nodes without native timeout, but redundant and destructive for race nodes which already own a pool. The fix (removing the outer wrap) aligns with upstream's single-executor philosophy.

**Could documenting solve this?** No — this is a runtime bug causing silent data loss. Documentation cannot prevent the double-wrap; only a code fix can.

### Existing Abstractions

| Abstraction | File | Overlap |
|-------------|------|---------|
| Race node (native `as_completed(timeout=...)`) | `yamlgraph/node_factory/race_node.py:148-156` | **Direct conflict** — owns timeout internally but gets wrapped again |
| Generic timeout wrapper | `yamlgraph/node_compiler.py:102-148` (`_maybe_wrap_timeout`) | Applied to race at line 277 — **root cause of bug** |
| Map node timeout | `yamlgraph/map_compiler.py:93-197` (`wrap_for_reducer`) | Correct pattern — catches `TimeoutError` before `Exception`, returns structured `PipelineError` |
| Content normalization | `yamlgraph/utils/content.py` (`normalize_content`) | Independent (FR-264), already integrated into race node |
| PipelineError model | `yamlgraph/models/schemas.py` (`ErrorType.TIMEOUT_ERROR`) | Reusable — race node should use this for timeout expiry |

**Node compiler timeout application matrix:**

| Node Type | `_maybe_wrap_timeout` applied? | Own timeout? | Correct? |
|-----------|-------------------------------|--------------|----------|
| llm, router, tool, python, agent, tool_call | ✅ Yes | ❌ No | ✅ Correct |
| map | ❌ No (uses `wrap_for_reducer`) | ✅ Yes | ✅ Correct |
| race | ✅ Yes (line 277) | ✅ Yes | ❌ **BUG** |
| interrupt, passthrough, copilot, subgraph | ❌ No | ❌ No | ✅ Correct |

### Diary Precedents

Three diary entries directly inform this fix:

1. **`2026-04-18-reflection-fr-232-race-node-type.md`** — Race node deliberately chose `ThreadPoolExecutor` over asyncio to avoid event loop conflicts in LangGraph's sync-first model. Heuristic: "First completed ≠ first successful." The race node _must_ own its pool to implement this correctly.

2. **`2026-04-19-reflection-fr-069-map-node-timeout.md`** — FR-069 (timeout) required intercepting at TWO boundaries: map fan-out and regular nodes. Trap: `partial_remediation` — only adding timeout to map would leave other nodes unguarded. **The fix correctly added `_maybe_wrap_timeout` to regular nodes, but over-applied it to race nodes which already had native timeout.**

3. **`2026-04-21-reflection-fr-264-race-node-content-normalization.md`** — Trap: `downstream_fix` — symptom manifested in race consumers, root cause was at provider boundary. **The One Law: normalize at the boundary where external data enters.** Directly applicable: timeout ownership belongs inside `race_node.py`, not at the compiler layer.

**Recurring traps activated:**
- `downstream_fix` → timeout applied at compiler (downstream) instead of race node (boundary)
- `partial_remediation` → FR-069 fixed map+regular nodes correctly but didn't exclude race
- `infrastructure_self_exempt` → `_maybe_wrap_timeout` guards all nodes uniformly but doesn't account for nodes that already self-guard

### Usage Evidence

- **Existing graphs using race nodes:** 1 (`examples/demos/race/graph.yaml` — uses `timeout: 15`)
- **Existing graphs using timeout:** 16 total (across examples/ebook, examples/demos/map-timeout, etc.)
- **Test files:** `tests/unit/test_race_node.py` (741 lines), `tests/unit/test_linter_patterns_race.py` (133 lines), `tests/unit/test_map_node_timeout.py` (313 lines)
- **Downstream project:** NV-240 in `sheikkinen/ninchat-voice` (race node for multi-provider LLM racing)
- **Real-world use cases beyond the proposal:** Any graph using `type: race` with `timeout:` is affected. The race demo (`examples/demos/race/graph.yaml`) is broken when timeout triggers the outer wrapper.

### Classification Signal

- **Abstraction level:** primitive — race node is a core node type (CAP-91) and timeout is a core feature (CAP-96); this bug affects any graph combining both
- **Recommended approach:** build — this is a runtime bug causing silent data loss; a 1-line removal + 5-line TimeoutError handler is the minimum viable fix
- **Key risk:** Removing `_maybe_wrap_timeout` from race nodes exposes the uncaught `TimeoutError` from `as_completed`; both changes must ship together (as FR-267 proposes) or timeout-expired races will raise raw exceptions instead of structured `PipelineError`
