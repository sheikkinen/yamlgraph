# Feature Request: Interrupt nodes should set response state before pausing

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-20

## Summary

Interrupt nodes call `interrupt(payload)` which raises `GraphInterrupt`, pausing execution **before** the node function returns. This means the node's return dict (containing `state_key: payload`) is never applied to state. The YAML author's contract says `state_key` holds the payload — the framework must honor that.

## Problem

In `control_nodes.py`, `create_interrupt_node()`:
```python
def interrupt_fn(state: dict) -> dict:
    # ... payload resolution ...
    response = interrupt(payload)       # <-- raises GraphInterrupt, never returns
    return {
        state_key: payload,             # <-- never reached on first call
        resume_key: response,
        "current_step": node_name,
    }
```

`interrupt()` raises `GraphInterrupt` on first invocation, halting the function. The return dict is never applied to the graph state. This means:

1. `state[state_key]` is empty after an interrupt node pauses — violating the YAML author's contract
2. SSE streaming fallback (`_get_state_response`) finds nothing to emit
3. Client receives 0 chars for interrupt turns (greeting, ask_priority, etc.)

## Approach: Two-Node Split (Compiler-Level)

**Rejected:** Setting state before `interrupt()` — local variable assignment is not a state commit; LangGraph only applies state from the node's return dict.

**Rejected:** Consumer-side utility reading `snap.tasks[N].interrupts` — depends on `put_writes()` which `SimpleRedisCheckpointer` does not implement. Checkpointer-dependent = fragile.

**Approved: Two-node split in `create_interrupt_node()`.**

Split one interrupt node into two internal functions, both added by `compile_node()`:

1. **`{name}_prepare`** — computes payload, returns `{state_key: payload, "current_step": node_name}`. State IS committed because the function returns normally.
2. **`{name}`** — reads payload from `state[state_key]` (already committed), calls `interrupt(payload)`, on resume returns `{resume_key: response}`.

`compile_node()` adds both nodes to the graph and inserts an internal edge `{name}_prepare → {name}`. Existing edges targeting `{name}` are redirected to `{name}_prepare` at edge-processing time.

### Why compiler-level, not config-level expansion?

The `interactive_tool` expansion (FR-049) works at config pre-processing. But interrupt is a core node type — every graph with interrupts is affected. Config-level expansion would require edge rewriting in the raw YAML dict. Compiler-level is cleaner: `create_interrupt_node()` returns a `(prepare_fn, interrupt_fn)` tuple, `compile_node()` handles the wiring. No edge rewriting needed — just add an internal edge and redirect incoming edges.

### Design

```python
# control_nodes.py
def create_interrupt_node(...) -> tuple[Callable, Callable]:
    # ... resolve message/prompt/template config ...

    def prepare_fn(state: dict) -> dict:
        # Compute payload (idempotent, prompt, template, or fallback)
        payload = _resolve_payload(state)
        return {state_key: payload, "current_step": node_name}

    def interrupt_fn(state: dict) -> dict:
        payload = state.get(state_key)
        response = interrupt(payload)
        return {resume_key: response, "current_step": node_name}

    return (prepare_fn, interrupt_fn)

# node_compiler.py (compile_node)
elif node_type == NodeType.INTERRUPT:
    prepare_fn, interrupt_fn = create_interrupt_node(...)
    prepare_name = f"{node_name}_prepare"
    graph.add_node(prepare_name, prepare_fn)
    graph.add_node(node_name, interrupt_fn)
    graph.add_edge(prepare_name, node_name)
    # Edge processing redirects incoming edges to prepare_name
```

## Acceptance Criteria

- [x] `create_interrupt_node()` returns `(prepare_fn, interrupt_fn)` tuple
- [x] `compile_node()` adds both nodes with internal edge
- [x] `state[state_key]` contains payload after prepare runs (before interrupt fires)
- [x] Resume path still works (interrupt_fn reads payload from state, returns resume value)
- [x] Idempotency preserved (prepare_fn checks existing payload)
- [x] Template interpolation works (Jinja2, simple {var})
- [x] Prompt-based payloads work (execute_prompt in prepare)
- [x] Dict payloads work (no-message fallback)
- [x] All 15+ existing interrupt tests pass
- [x] Edge redirection: incoming edges to interrupt node → prepare node

## Related

- FR-049 — interactive_tool expansion (precedent for multi-node split)
- FR-058 — agent streaming filter
- FR-059 — agent content normalization
- `SimpleRedisCheckpointer.put_writes()` — no-op, makes snap.interrupts unreliable
