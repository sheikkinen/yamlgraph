# Feature Request: Async interrupt_output_mapping

**Priority:** MEDIUM
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-02-17

## Summary

`interrupt_output_mapping` in `mode=invoke` subgraph nodes silently fails under async execution (`astream()`). Parent state is never updated when a child graph hits an interrupt.

## Problem

When a parent graph runs via `astream()` and a `mode=invoke` subgraph hits a `GraphInterrupt`, the interrupt handler in `subgraph_nodes.py` attempts to propagate child state to the parent using `__pregel_send`:

```python
send = config.get("configurable", {}).get("__pregel_send")
if send:
    updates = [(k, v) for k, v in parent_updates.items()]
    send(updates)
```

`__pregel_send` is a **sync-only** LangGraph internal. Under `astream()`, it is `None`. The `if send:` guard silently skips the state update — no error, no warning. The parent never receives the mapped fields (e.g. `response`, `phase`).

This was discovered in a voice call scenario where a subgraph sets `response` via `interrupt_output_mapping` and the streaming layer falls back to `state.values["response"]` — which is always empty in the parent because the mapping never fired.

### Debug evidence

```
state.tasks[0].interrupts = ()     # always empty after aget_state()
state.values["response"] = ""      # never populated by interrupt_output_mapping
```

The log line `FR-006: Subgraph {node_name} mapped state: [keys]` **does** fire, confirming the code reaches the mapping logic — but `send` is `None` so no state is written.

## Proposed Solution

Replace `__pregel_send` with `aget_state()`/checkpoint-based approach, or use LangGraph's async equivalent.

Option A — Read child state via checkpointer (most robust):

```python
except GraphInterrupt:
    if interrupt_output_mapping:
        child_state = compiled.get_state(child_config)
        child_output = dict(child_state.values) if child_state else {}
        parent_updates = _map_output_state(child_output, interrupt_output_mapping)
        parent_updates["current_step"] = node_name
        # Return updates instead of using __pregel_send
        # Let LangGraph merge them into parent state before re-raising
        return parent_updates  # <-- this won't work with GraphInterrupt re-raise
```

Option B — Log a warning when `send` is `None` (minimal fix):

```python
if send:
    send(updates)
else:
    logger.warning(
        f"FR-006: __pregel_send unavailable (async context). "
        f"interrupt_output_mapping for {node_name} will not propagate. "
        f"Consider using mode=direct or inlining nodes."
    )
```

Option C — Make the subgraph node async-aware:

Create an async variant of `subgraph_node` that uses `await compiled.ainvoke()` and the async equivalent of `__pregel_send`. This aligns with FR-030 Phase 2 (async mode=invoke).

## Acceptance Criteria

- [ ] `interrupt_output_mapping` propagates state under `astream()` OR emits a clear warning
- [ ] Tests added for async subgraph interrupt propagation
- [ ] Documentation updated to note async limitation (if warning-only fix)

## Alternatives Considered

**Inline subgraph nodes into parent graph** — This is the workaround used in questionnaire-api. The auth flow nodes were moved from a separate subgraph into the navigator graph directly. This eliminates the need for `interrupt_output_mapping` entirely since `response` is set in parent state directly. Works but defeats the purpose of subgraph modularity.

## Related

- FR-030: Subgraph Token Streaming (Phase 2 — async mode=invoke)
- `yamlgraph/node_factory/subgraph_nodes.py` lines 186-201
- LangGraph `__pregel_send` internals
