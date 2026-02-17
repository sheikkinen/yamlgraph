# Feature Request: Async interrupt_output_mapping

**Priority:** LOW
**Type:** Documentation / Not a bug
**Status:** Closed (No Fix Needed)
**Effort:** 0
**Requested:** 2026-02-17
**Closed:** 2026-02-17

## Summary

~~`interrupt_output_mapping` in `mode=invoke` subgraph nodes silently fails under async execution (`astream()`).~~

**INVESTIGATION RESULT:** This is NOT a bug. The `__pregel_send` mechanism works correctly under async. The perceived "failure" was caused by incorrect stream consumption patterns.

## Investigation (2026-02-17)

### Original Hypothesis (WRONG)

> `__pregel_send` is a sync-only LangGraph internal. Under `astream()`, it is `None`.

### Actual Findings

Tested with LangGraph 1.0.6:

```python
# CONFIG_KEY_SEND is available in ALL execution modes:
send = config.get(CONF, {}).get(CONFIG_KEY_SEND)
# sync invoke:   send is NOT None ✓
# async astream: send is NOT None ✓
# async ainvoke: send is NOT None ✓
```

The `send()` function IS called — the log line `FR-006: Subgraph run_child mapped state: [keys]` confirms this.

### Root Cause: Stream Mode Behavior

The issue is in how `astream()` is consumed, not in `__pregel_send`:

| Stream Mode | Chunks on Interrupt | `child_phase` visible? |
|------------|---------------------|------------------------|
| `updates` (default) | 1 (`__interrupt__`) | ❌ No |
| `values` | 3 (including full state) | ✓ Yes |
| `ainvoke()` | N/A | ✓ Yes (combines updates+values) |

**When using `stream_mode="updates"`:**
- Only node output dicts are yielded
- `send()` writes go to internal state channels
- The writes appear in subsequent `values` emissions, NOT in `updates`
- If consumer breaks on `__interrupt__`, they miss the state

**When using `stream_mode="values"`:**
- Full accumulated state is yielded after each step
- `send()` writes ARE visible in the final chunk
- Pattern: `[initial_state, state_with_interrupt, state_with_mapped_fields]`

### Code Verification

```python
# This WORKS - child_phase IS in the third chunk:
async for chunk in graph.astream(input, config, stream_mode="values"):
    print(chunk)
# Chunk 3: {'child_phase': 'processing', 'child_data': '...', ...}

# This appears broken but isn't - different stream mode:
async for chunk in graph.astream(input, config):  # default: updates
    if "__interrupt__" in chunk:
        break  # Consumer stops here, never sees state
```

## Conclusion

No framework fix needed. The behavior is correct per LangGraph semantics:

1. **`send()` works in async** — verified empirically
2. **`astream(stream_mode="updates")` excludes accumulated state** — by design
3. **`astream(stream_mode="values")` includes all state** — use this for interrupt workflows
4. **`ainvoke()` works correctly** — combines both modes internally

## Recommendations

For consumers needing mapped state during interrupts:

1. Use `astream(stream_mode="values")` and collect the final chunk
2. Or use `ainvoke()` which handles this automatically
3. Or use `get_state()` after stream completes to fetch checkpointed values

The integration tests (`test_subgraph_interrupt.py`) pass because they use `invoke()` which has the correct behavior.

---

## Original Problem Statement (Archived)

~~When a parent graph runs via `astream()` and a `mode=invoke` subgraph hits a `GraphInterrupt`...~~

(Kept for historical reference — see git history for original content)
