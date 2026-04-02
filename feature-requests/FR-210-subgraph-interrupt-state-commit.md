# FR-210: Subgraph Interrupt State Commit

**Priority:** HIGH
**Type:** Bug Fix
**Status:** Judged (8+5+2 amendments) — monolithic scope rejected, decompose required
**Effort:** 5-7 days for full framework fix (deferred); 0.5-1 day for D-0 standalone bugfix
**Requested:** 2026-03-30
**Judged:** 2026-03-31 (Round 1), 2026-03-31 (Round 2), 2026-03-31 (Round 3)
**Requirement:** REQ-YG-214

## Summary

Fix `interrupt_output_mapping` for `mode=invoke` subgraph nodes so that mapped
child state is committed to the parent graph's checkpointer at each interrupt
boundary. Currently `__pregel_send` writes are discarded when `GraphInterrupt`
propagates.

## Final Judgement Addendum (2026-03-31)

### Verdict

This FR should **not** be enforced as a single implementation. The issue is real,
but the current scope is too coupled and high-risk to ship safely in one pass.

### Decision

1. Reject monolithic FR-210 enforcement as currently scoped.
2. Keep the underlying bug open (do not abandon the problem).
3. Execute D-0 as a standalone bugfix first (router route_mapping redirect).
4. For ninchat_voice delivery, prefer coordinator-level sequential graph switching
     (NV-192 path) instead of nested subgraph interrupt orchestration.
5. Re-open framework work only after D-0 lands and at least one additional
     active consumer confirms need beyond ninchat_voice.

### Rationale

- FR-210 currently bundles multiple concerns: router redirect correctness,
    subgraph resume semantics, outgoing edge transformation, compiler return-type
    changes, and dynamic state augmentation.
- The blast radius is in shared compilation paths (`edge_compiler`,
    `node_compiler`, `graph_loader`, `state_builder`), increasing regression risk.
- ninchat_voice has a lower-complexity architecture alternative already aligned
    with the FSM-as-coordinator model.

### Scope Policy Going Forward

- Phase A (now): D-0 only, independent commit and verification.
- Phase B (optional): Minimal subgraph interrupt commit fix, separated from edge
    language expansion and unrelated compiler refactors.
- Phase C (deferred): advanced outgoing conditional support for subgraph
    interrupt nodes, only if justified by real usage.

## Judgement Amendments

| # | Type | Finding | Resolution |
|---|------|---------|------------|
| J-1 | **Critical: child resume missing** | `__run` function calls `compiled.invoke(child_input, ...)` on every cycle. On turn 2+, child is paused at an interrupt — bare `invoke()` won't resume it. Must use `Command(resume=user_message)` to resume a paused child. | `__run` must detect first-call vs resume: check child state via `compiled.get_state(child_config)`; if `.next` is truthy, invoke with `Command(resume=state[resume_key])` instead of `child_input`. Add `resume_key` config parameter (defaults to first key in `input_mapping` or `"user_message"`). |
| J-2 | **Critical: child has no checkpointer** | `create_subgraph_node` compiles child with `checkpointer=parent_checkpointer` which is always `None` (prototype lesson 3). Without a checkpointer, `compiled.get_state()` raises `ValueError` and multi-turn resume is impossible. The child's own YAML config (e.g., `checkpointer: { type: memory }`) is loaded into `subgraph_config` but never used. | When `interrupt_output_mapping` is non-empty, create child checkpointer from `subgraph_config` via `get_checkpointer_for_graph(subgraph_config)`. Pass to `state_graph.compile(checkpointer=child_checkpointer)`. This is a prerequisite for the split to work. |
| J-3 | **Critical: router edge redirect gap** | `_process_edge` line 84 only redirects `to_node` when `isinstance(to_node, str)`. Router/conditional edges (`to: [run_triage, run_interrai]`) have list targets — redirect never fires. This is a **pre-existing FR-060 bug**: `classify → [store_elderlycare_intent, store_triage_intent, ask_priority]` in the navigator graph also skips `ask_priority_prepare`. | Fix `_process_edge` to iterate list targets and redirect any that are in `interrupt_nodes` or `subgraph_interrupt_nodes`. Apply to BOTH sets. **Separate bugfix commit** for FR-060 router redirect before FR-210 work begins. |
| J-4 | **Critical: outgoing edge transformation** | FR-210 claims "same redirect as FR-060" for edge handling, but FR-060 only redirects incoming `to_node`. FR-210 additionally needs outgoing `from_node` edges transformed: `from: run_triage, to: format_done` must become conditional routing from `{name}__run` (paused → gate, complete → original target). FR-060 doesn't require this because the interrupt node IS the original node name. | New edge compiler logic: when `from_node` is in `subgraph_interrupt_nodes`, rewrite to conditional edges from `{name}__run`. Internal loop edge (`{name}` → `{name}__run`) added by `compile_node`, not edge compiler. |
| J-5 | State key naming inconsistency | Constraint 8 specifies per-node `__{node_name}_paused__` but code sketch uses generic `__subgraph_paused__`. With two subgraph nodes (`run_triage`, `run_interrai`), generic name collides. | All code, routing function, and state builder must use `__{node_name}_paused__`. Update code sketches throughout. |
| J-6 | Interrupt gate over-engineering | Code sketch reads child state in `subgraph_interrupt_fn` via `_build_child_config(state.get("__config__", {}), ...)`. This requires `RunnableConfig` access through state (wrong: config is a separate argument in LangGraph). The `__run` function already commits `response` to parent state — the gate should just read from parent state. | Simplify gate to FR-060 pattern: `payload = state.get(response_key)`, `response = interrupt(payload)`, `return {resume_key: response}`. Two arguments: `(state: dict, config: RunnableConfig)` — config passed through closure, not through state. |
| J-7 | `__interrupt__` marker path scoping | Existing tests and the current `subgraph_node` function handle both `GraphInterrupt` exception AND `__interrupt__` return key. The `__run` sketch only handles exception. Marker path exists for non-checkpointed children. | The split only activates when `interrupt_output_mapping` is non-empty AND child has checkpointer (J-2). Non-checkpointed children can't do multi-turn resume, so `__interrupt__` marker path stays on the legacy single-function code path. Document explicitly: split requires child checkpointer. |
| J-8 | Effort underestimated | Original 3-5 days didn't account for: (a) child checkpointer creation (J-2), (b) router edge redirect bugfix for FR-060 (J-3), (c) outgoing edge transformation (J-4), (d) resume detection logic (J-1). | Revised to 5-7 days. Sequence: J-3 bugfix first (1 day), then J-2 child checkpointer (0.5 day), then split implementation (3-4 days), integration verification (1 day). |
| J-9 | **`response_key` derivation undefined** | The interrupt gate reads `state.get(response_key)` as the payload to show the user, but the FR never specifies how `response_key` is derived. `interrupt_output_mapping` has 3 keys (`response`, `extracted`, `phase`) — which one is the user-visible response? Implicit convention ("always `response`") is brittle. | Add explicit `response_key` field to `SubgraphNodeConfig` (schema `extra="allow"` already accepts it): defaults to `"response"` if present in `interrupt_output_mapping`, else first key. Enforce in factory: if `interrupt_output_mapping` is non-empty and `response_key` not specified, derive from mapping or raise. |
| J-10 | **`resume_key` derivation ambiguous** | J-1 says "defaults to first key in `input_mapping` or `"user_message"`" but dict ordering makes "first key" unreliable in specs. The interrupt gate writes `{resume_key: user_response}` and `__run` reads `state.get(resume_key)` for `Command(resume=...)`. Wrong key → child never gets the message. | Add explicit `resume_key` field to `SubgraphNodeConfig`: defaults to `"user_message"`. Do NOT derive from `input_mapping` ordering. The field must match a key in `input_mapping` so the child receives it. Linter should warn if `resume_key` not in `input_mapping` keys. |
| J-11 | **`compile_nodes` return type change** | `compile_nodes()` currently returns `tuple[dict, set]` (map_nodes, interrupt_nodes). Adding `subgraph_interrupt_nodes` requires a third return value. `graph_loader.py` destructures as `map_nodes, interrupt_nodes = compile_nodes(...)`. Both call sites (`graph_loader.py`, any tests) must update. | `compile_nodes()` returns `tuple[dict, set, set]` → `(map_nodes, interrupt_nodes, subgraph_interrupt_nodes)`. `_process_edge()` accepts both sets. `graph_loader.py` updated to pass `subgraph_interrupt_nodes` through. Alternative: merge into single set with different markers — rejected, the edge rewrite logic differs (incoming-only `_prepare` redirect vs incoming+outgoing `__run` redirect+conditional). |
| J-12 | **D-3 synthetic edge injection mechanics** | D-3 says `_process_edge` rewrites outgoing edges, but the actual mechanism is unclear. When `_process_edge` encounters `from: run_triage, to: format_done`, it must NOT add a simple edge. Instead it injects two entries into `expression_edges["run_triage__run"]`. This is not a redirect — it's a transformation from one edge into two expression edges keyed under a different source node. The YAML `from_node` name disappears entirely. | Specify the exact rewrite: `_process_edge` detects `from_node in subgraph_interrupt_nodes`, collects the target (handling END), then appends to `expression_edges[f"{from_node}__run"]` with conditions `__{from_node}_paused__ == true` → `from_node` and `__{from_node}_paused__ == false` → `original_target`. Returns early — no simple edge added. |
| J-13 | **D-3 + conditional outgoing edges** | D-3 only discusses simple outgoing edges. But what if the outgoing edge has a condition? (E.g., `from: run_triage, to: format_done, condition: "complete == true"`). The condition must be composed with the paused check: `__run_triage_paused__ == false and complete == true`. The FR doesn't address compound conditions. | **Scope constraint:** Phase 1 requires outgoing edges from subgraph interrupt nodes to be simple (no condition). Linter should error if a conditional outgoing edge references a subgraph interrupt node as `from`. Navigator graph has only simple outgoing edges (`run_triage → format_done`), so this doesn't block the current use case. Compound condition support deferred. |
| J-14 | **Critical: D-0 route_mapping — list rewrite breaks `make_router_fn`** | D-0 proposes rewriting list items in `_process_edge`: `["ask_priority"] → ["ask_priority_prepare"]`. These rewritten names flow into `make_router_fn(target_nodes)`, which validates `state["_route"]` against target names. The LLM's router output is the **original** name (`"ask_priority"`), not the redirected name (`"ask_priority_prepare"`). Match fails → defaults to first target. Same issue for FR-210: `run_triage` → `run_triage__run`. Affects both D-0 (FR-060 interrupt nodes) and D-3 (FR-210 subgraph interrupt nodes) in router edges. String redirect for expression/simple/START edges in `_process_edge` is unaffected — only list targets in router edges are wrong. | **Do NOT rewrite list items in `_process_edge`.** Instead, pass `interrupt_nodes` and `subgraph_interrupt_nodes` to `_add_conditional_edges`. Build `route_mapping` with redirected actual targets while keeping original names for `make_router_fn`: `route_mapping = {"ask_priority": "ask_priority_prepare", ...}`. Router LLM outputs original names → mapping translates to actual graph nodes. |
| J-15 | **D-3 `from_node` check position and scope** | D-3's outgoing edge check (`from_node in subgraph_interrupt_nodes`) is described after the conditional/expression edge handling in the FR's pseudo-code. But if it comes after the `type: conditional` check in `_process_edge`, router edges from subgraph interrupt nodes (e.g., `from: run_triage, to: [A, B], type: conditional`) bypass the transformation and go into `router_edges` with the wrong source node. Also, J-13 only rejects `condition` outgoing edges but not `type: conditional` edges. | Place D-3's `from_node in subgraph_interrupt_nodes` check **before** all edge type handling (after incoming redirect, before START/map/router/expression/simple). Reject both `condition` AND `edge_type == "conditional"` outgoing edges from subgraph interrupt nodes in Phase 1. |

## Problem

When a `mode=invoke` subgraph node has `interrupt_output_mapping` and the child
graph hits an interrupt, the mapped child state is never visible in the parent's
`get_state().values`. The parent sees `None` for all mapped keys across every
interrupt cycle.

### Root Cause

[subgraph_nodes.py](yamlgraph/node_factory/subgraph_nodes.py#L178-L200): the
`except GraphInterrupt:` handler reads child state, applies
`interrupt_output_mapping`, pushes updates via `__pregel_send`, then re-raises
`GraphInterrupt`. **LangGraph discards pending writes when GraphInterrupt
propagates** — the `__pregel_send` tuples are never committed to the parent's
checkpointer.

### Evidence Trail

1. **NV-190 condemning test** — `projects/ninchat_voice/tests/integration/
   test_nv190_navigator_triage_walkthrough.py` — 4 passed, 2 failed.
   `extracted` is `{}` and `response` is stale after multiple interrupt/resume
   cycles.

2. **Debug logging** — `__pregel_send` fires with correct values (e.g.
   `extracted = {'chief_complaint': 'Päänsärky', ...}`), but
   `get_state().values` returns `None` for all mapped keys.

3. **FR-039 investigation** — Confirmed `__pregel_send` works in all execution
   modes (sync/async). The issue is specifically the re-raise of
   `GraphInterrupt`, not the send mechanism.

4. **FR-049 workaround** — Interactive tool node type was created specifically
   to avoid this problem by inlining nodes at compile time (no subgraph
   boundary, no `__pregel_send`). Two production cases in questionnaire-api
   had to abandon subgraphs.

### Impact

- **ninchat_voice navigator** — greeting loops because FSM reads parent state
  for phase/response, but they never update during triage interrupt cycles.
- **Any `mode=invoke` subgraph with interrupts** — `interrupt_output_mapping`
  is silently broken for all consumers that read state via `get_state()`.
- Only `stream_mode="values"` on `astream()` accidentally works (FR-039) —
  but `get_state()` never reflects the mapped values.

## Approach: Prepare/Interrupt Node Split

Follow the **FR-060 pattern** (interrupt node split) already proven for regular
interrupt nodes. At compile time, expand each `mode=invoke` subgraph node that
has `interrupt_output_mapping` into two parent-graph nodes:

### Node Split

```
{name}__run   — runs/resumes child graph, catches GraphInterrupt,
                reads child state, returns mapped dict NORMALLY
                (so LangGraph commits state before interrupt fires)

{name}        — checks if child is still paused; if yes, calls
                interrupt() to pause parent; on resume, returns
                resume value for next __run cycle
```

### Edge Wiring

```
                         ┌─────────────────┐
   incoming  ──────────► │  {name}__run     │ ─── child complete ──► outgoing
   edges                 └────────┬────────┘
                                  │ child interrupted
                                  ▼
                         ┌─────────────────┐
                         │  {name}         │ (calls interrupt())
                         └────────┬────────┘
                                  │ resumed
                                  ▼
                         ┌─────────────────┐
                         │  {name}__run     │ ─── (loop)
                         └─────────────────┘
```

1. Incoming edges → `{name}__run` (edge compiler redirect, same as FR-060)
2. `{name}__run` → `{name}` — conditional: when child is paused
3. `{name}__run` → outgoing target — conditional: when child is complete
4. `{name}` → `{name}__run` — unconditional (resume feeds back to run)

### Implementation Detail

#### `{name}__run` function

```python
def subgraph_run_fn(state: dict, config: RunnableConfig | None = None) -> dict:
    """Run or resume child graph, return mapped state normally."""
    from langgraph.errors import GraphInterrupt
    from langgraph.types import Command

    config = config or {}
    child_config = _build_child_config(config, node_name)
    paused_key = f"__{node_name}_paused__"

    # J-1: Detect resume vs first call
    try:
        child_state = compiled.get_state(child_config)
        child_is_paused = bool(child_state and child_state.next)
    except ValueError:
        child_is_paused = False

    try:
        if child_is_paused:
            # Resume paused child with user's response
            resume_value = state.get(resume_key)
            child_output = compiled.invoke(
                Command(resume=resume_value), child_config
            )
        else:
            # Fresh start
            child_input = _map_input_state(state, input_mapping)
            child_output = compiled.invoke(child_input, child_config)
        is_interrupted = "__interrupt__" in child_output
    except GraphInterrupt:
        is_interrupted = True
        child_output = None

    if is_interrupted:
        # Read child state from checkpointer
        child_state = compiled.get_state(child_config)
        child_values = dict(child_state.values) if child_state else {}

        # Apply interrupt_output_mapping — committed because we RETURN normally
        parent_updates = _map_output_state(child_values, interrupt_output_mapping)
        parent_updates["current_step"] = node_name
        parent_updates[paused_key] = True
        return parent_updates

    # Normal completion
    parent_updates = _map_output_state(child_output, output_mapping)
    parent_updates["current_step"] = node_name
    parent_updates[paused_key] = False
    return parent_updates
```

Key insight: the `__run` function **never re-raises GraphInterrupt**. It catches
the exception and returns mapped state normally, which LangGraph commits to the
parent's checkpointer. The interrupt is handled by the separate `{name}` node.

J-1: On turn 2+, detects child is paused via `get_state().next` and uses
`Command(resume=...)` instead of fresh invocation. The `resume_key` parameter
specifies which parent state key contains the user's response.

#### `{name}` (interrupt gate) function

```python
def subgraph_interrupt_fn(state: dict) -> dict:
    """Pause parent if child is still paused; pass-through on resume."""
    from langgraph.types import interrupt

    # J-6: Read response already committed to parent state by __run
    # J-9: response_key is explicit config field (default: "response")
    payload = state.get(response_key)
    response = interrupt(payload)
    # J-10: resume_key is explicit config field (default: "user_message")
    return {
        resume_key: response,
        "current_step": node_name,
    }
```

J-6: Simplified — no child state access needed. The `__run` function already
committed `response` to parent state via `interrupt_output_mapping`.
J-9: `response_key` from explicit config field, not derived from mapping order.
J-10: `resume_key` from explicit config field, not derived from `input_mapping`.

#### Routing condition

```python
def _child_is_paused(state: dict) -> str:
    """Route based on whether child subgraph is still paused."""
    paused_key = f"__{node_name}_paused__"
    if state.get(paused_key):
        return node_name  # → interrupt gate
    return "__exit__"     # → outgoing edges
```

J-5: Uses per-node `__{node_name}_paused__` key to avoid collisions.

### Internal State Key: `__{node_name}_paused__`

A per-node boolean state key tracks whether the child is paused (J-5).

- Set by `{name}__run`: `True` when `GraphInterrupt` caught, `False` on
  normal completion.
- Read by routing condition to decide: interrupt gate or forward to outgoing.
- NOT exposed in YAML schema — internal implementation detail.
- Auto-added to state builder when subgraph has `interrupt_output_mapping`.
- Per-node naming avoids collisions when multiple subgraph nodes exist
  (e.g., `__run_triage_paused__`, `__run_interrai_paused__`).

## Expansion Strategy

### Option 1: Config-level expansion (FR-049 pattern)

Expand at the config dict level before `compile_nodes()` runs, same as
`interactive_tool.py`. The subgraph node entry is replaced with two node
entries and internal edges.

**Pros:** Consistent with existing pattern. No changes to `compile_node()`.
**Cons:** Must duplicate subgraph compilation logic (loading child graph, etc.)
in the expander, or defer it. Edge rewriting is complex for conditional edges.

### Option 2: Node compiler expansion (FR-060 pattern)

Expand during `compile_node()`, same as interrupt nodes. Returns a tuple
marker so the edge compiler knows to redirect incoming edges.

**Pros:** Subgraph compilation happens naturally in `compile_node()`. Edge
redirect already works for interrupt nodes — extend the same mechanism.
**Cons:** Adds another special case to `compile_node()`.

### Recommendation: Option 2 (node compiler expansion)

FR-060 already solved the incoming-edge redirect for interrupt nodes. Extend:

1. `compile_node()` detects subgraph with `interrupt_output_mapping`
2. Creates `{name}__run` and `{name}` functions
3. Registers both with `graph.add_node()`
4. Adds internal loop edge: `graph.add_edge(node_name, run_name)` (resume)
5. Returns `(node_name, "subgraph_interrupt")` marker
6. `compile_nodes()` adds to a `subgraph_interrupt_nodes` set
7. `_process_edge()` redirects incoming `to_node` to `{name}__run`
   (J-3: including list targets in router edges)
8. `_process_edge()` rewrites outgoing `from_node` edges: replaces simple
   edge with conditional routing from `{name}__run` (J-4: paused → `{name}`,
   complete → original target)

**J-3 prerequisite:** Fix the FR-060 router redirect bug first. `_process_edge`
must redirect list items in router/conditional edges for BOTH `interrupt_nodes`
and `subgraph_interrupt_nodes`. This is a separate bugfix that unblocks both
FR-060 and FR-210.

**J-2 prerequisite:** Create child checkpointer from child config when
`interrupt_output_mapping` is non-empty. Without a child checkpointer,
`get_state()` fails and multi-turn resume is impossible.

## Prototype Lessons (from investigation)

Three non-obvious issues discovered during earlier prototype:

1. **`_child_is_paused` needs ValueError guard** — `compiled.get_state()`
   raises `ValueError("No checkpointer set")` when the compiled graph has no
   checkpointer. Must catch and return False.

2. **MagicMock `get_state().next` is truthy** — 24 existing subgraph tests use
   MagicMock for compiled graph. `get_state()` on MagicMock returns MagicMock,
   `.next` is truthy. Any guard that checks child state must handle mocks.
   **Solution:** Use the `__subgraph_paused__` flag in parent state instead
   of querying child state for routing.

3. **`parent_checkpointer` is always None at node creation** —
   `create_subgraph_node` receives `parent_checkpointer` but `node_compiler.py`
   never passes it. Checkpointer is set at `graph.compile()` time. Cannot gate
   behavior at creation time. **Irrelevant for this approach** — we use parent
   state flag instead.

## Constraints

1. **Must not break existing subgraph tests** — 24 tests in `test_subgraph.py`
   use MagicMock compiled graphs with `__interrupt__` in return dict. The split
   only activates when `interrupt_output_mapping` is non-empty AND the node goes
   through `compile_node()` (unit tests call `create_subgraph_node` directly).

2. **Must not break subgraphs without interrupt_output_mapping** — When
   `interrupt_output_mapping` is empty (default), the node compiles as today.
   No split, no routing, no `__subgraph_paused__` key.

3. **Must not break `mode=direct` subgraphs** — Direct mode returns
   `CompiledGraph` directly; LangGraph handles natively. No change.

4. **Multi-turn child interrupts** — The loop edge (`{name}` → `{name}__run`)
   ensures the child graph resumes correctly on each `Command(resume=...)`.
   The parent passes `user_message` back to child via `input_mapping`.

5. **Parent state reflects child progress** — At each interrupt boundary, the
   `{name}__run` function returns mapped state normally, which LangGraph commits.
   `get_state().values` shows current `response`, `extracted`, `phase`, etc.

6. **Stream mode agnostic** — No `__pregel_send`. No reliance on stream mode.
   State committed via normal node return. Works with `messages`, `values`,
   `updates`, and `get_state()`.

7. **Resume value propagation (J-1)** — The interrupt gate captures the resume
   value and writes it to `resume_key`. The `__run` function detects the child
   is paused via `get_state().next` and invokes with `Command(resume=...)`.
   The `resume_key` config parameter specifies which parent state key contains
   the user response (defaults to first key in `input_mapping` or
   `"user_message"`).

8. **`__{node_name}_paused__` state key (J-5)** — Per-subgraph boolean.
   Auto-added to state builder when subgraph has `interrupt_output_mapping`.
   Per-node naming avoids collisions between multiple subgraph nodes.

9. **Loop limits** — The `{name}__run` node inherits the loop limit from the
   subgraph node's YAML config. Each interrupt/resume cycle counts as one
   iteration. If loop limit is reached, the node returns with
   `__{node_name}_paused__ = False` and state as-is.

10. **Linter** — The linter already validates `interrupt_output_mapping` keys.
    No linter changes needed for the split — internal nodes use `__` prefix
    which the linter already warns about (FR-049).

11. **`__interrupt__` marker path preserved (J-7)** — The split only activates
    when `interrupt_output_mapping` is non-empty AND child config has a
    checkpointer. Non-checkpointed children with `interrupt_output_mapping`
    fall back to the existing single-function code path (which handles the
    `__interrupt__` return key marker). This preserves all 24 existing tests.

12. **Implementation sequence (J-8)** — D-0 router bugfix first (separate
    commit, unblocks both FR-060 and FR-210). Then D-1 child checkpointer.
    Then D-2..D-5 split implementation. Finally integration verification.

## Deliverables

### D-0: `edge_compiler.py` — router redirect bugfix (J-3, J-14, separate commit)

Fix pre-existing FR-060 bug: router edges with list targets don't redirect
interrupt node names.

**J-14 correction:** Do NOT rewrite list items in `_process_edge`. The string
redirect there only works for simple, expression, and START edges. For router
edges (`type: conditional`), the redirect must happen in `_add_conditional_edges`
via `route_mapping` — the original names must be preserved for `make_router_fn`
because the LLM's `_route` output uses original node names.

**`_process_edge`**: No change for list targets. Existing string redirect stays.

**`_add_conditional_edges`**: Receives `interrupt_nodes` and
`subgraph_interrupt_nodes` as new parameters. Builds `route_mapping` with
redirected actual targets:

```python
def _add_conditional_edges(
    graph, router_edges, expression_edges, loop_exits=None,
    interrupt_nodes=None, subgraph_interrupt_nodes=None,
) -> None:
    for source_node, target_nodes in router_edges.items():
        # J-14: Redirect via route_mapping, not target list rewrite
        route_mapping = {}
        for target in target_nodes:
            if interrupt_nodes and target in interrupt_nodes:
                route_mapping[target] = f"{target}_prepare"
            elif subgraph_interrupt_nodes and target in subgraph_interrupt_nodes:
                route_mapping[target] = f"{target}__run"
            else:
                route_mapping[target] = target
        graph.add_conditional_edges(
            source_node,
            make_router_fn(target_nodes),  # Original names — matches _route
            route_mapping,                  # Redirected actual node names
        )
```

`graph_loader.py` call site updated:
```python
_add_conditional_edges(
    graph, router_edges, expression_edges, config.loop_exits,
    interrupt_nodes, subgraph_interrupt_nodes,
)
```

Separate commit because this fixes an existing bug affecting FR-060 interrupt
nodes in router edges (e.g., `classify → [store_elderlycare_intent, ...,
ask_priority]` in navigator graph).

### D-1: `subgraph_nodes.py` — child checkpointer + split factory (J-2, J-9, J-10)

Three changes:

**a) Child checkpointer creation (J-2):** When `interrupt_output_mapping` is
non-empty, create child checkpointer from `subgraph_config`:

```python
from yamlgraph.graph_loader import get_checkpointer_for_graph

if interrupt_output_mapping:
    child_checkpointer = get_checkpointer_for_graph(subgraph_config)
    compiled = state_graph.compile(checkpointer=child_checkpointer)
else:
    compiled = state_graph.compile(checkpointer=parent_checkpointer)
```

**b) Config extraction (J-9, J-10):** Extract `response_key` and `resume_key`
from node config with sensible defaults:

```python
response_key = node_config.get("response_key", "response")
resume_key = node_config.get("resume_key", "user_message")
```

Both are closed over by `run_fn` and `interrupt_fn`. `SubgraphNodeConfig`
already accepts extra fields (`extra = "allow"`), so no schema change needed.
Navigator YAML can optionally add `resume_key: user_message` for explicitness.

**c) Split factory:** Return `(run_fn, interrupt_fn)` tuple when
`interrupt_output_mapping` is non-empty AND child has checkpointer.

New function signatures:

```python
def create_subgraph_node(
    node_name, node_config, parent_graph_path, parent_checkpointer=None,
) -> Callable | tuple[Callable, Callable]:
    """Returns single fn (no interrupt mapping) or (run_fn, interrupt_fn) tuple."""
```

The `run_fn` implements J-1 resume detection: checks `compiled.get_state().next`
to determine first-call vs resume, uses `Command(resume=...)` on subsequent calls.

The `interrupt_fn` implements J-6 simplified pattern: reads `response_key` from
parent state, calls `interrupt()`, returns resume value.

### D-2: `node_compiler.py` — subgraph split handling (J-11)

In `compile_node()`, detect when `create_subgraph_node` returns a tuple:

```python
elif node_type == NodeType.SUBGRAPH:
    result = create_subgraph_node(...)
    if isinstance(result, tuple):
        # Has interrupt_output_mapping — split pattern
        run_fn, interrupt_fn = result
        run_name = f"{node_name}__run"
        graph.add_node(run_name, run_fn)
        graph.add_node(node_name, interrupt_fn)
        # Loop-back: gate → run (resume cycle)
        graph.add_edge(node_name, run_name)
        # Internal edges handled by edge compiler
        return (node_name, "subgraph_interrupt")
    else:
        graph.add_node(node_name, result)
```

**J-11: `compile_nodes` return type** changes from `tuple[dict, set]` to
`tuple[dict, set, set]`: `(map_nodes, interrupt_nodes, subgraph_interrupt_nodes)`.
The third set tracks subgraph nodes with interrupt split. Both `graph_loader.py`
and `_process_edge` must accept the new parameter.

### D-3: `edge_compiler.py` — subgraph interrupt routing (J-4, J-12, J-13, J-14, J-15)

Extend `_process_edge()` to handle `subgraph_interrupt_nodes` — significantly
more complex than FR-060 redirect:

**Incoming edges (string `to_node` — same pattern as FR-060):**
- In `_process_edge`, add string redirect alongside FR-060:
  ```python
  if subgraph_interrupt_nodes and isinstance(to_node, str) and to_node in subgraph_interrupt_nodes:
      to_node = f"{to_node}__run"
  ```
- Covers simple, expression, and START edges.
- List `to_node` (router edges) handled by D-0 in `_add_conditional_edges` via
  `route_mapping` (J-14).

**J-15: `from_node` check position — BEFORE all other edge handling:**

```python
def _process_edge(edge, graph, map_nodes, router_edges, expression_edges,
                  interrupt_nodes=None, subgraph_interrupt_nodes=None):
    from_node = edge["from"]
    to_node = edge["to"]
    condition = edge.get("condition")
    edge_type = edge.get("type")

    # FR-060: Redirect incoming string targets to prepare node
    if interrupt_nodes and isinstance(to_node, str) and to_node in interrupt_nodes:
        to_node = f"{to_node}_prepare"

    # FR-210: Redirect incoming string targets to __run node
    if subgraph_interrupt_nodes and isinstance(to_node, str) and to_node in subgraph_interrupt_nodes:
        to_node = f"{to_node}__run"

    # J-15: Outgoing edge from subgraph interrupt node — BEFORE all edge handling
    if subgraph_interrupt_nodes and from_node in subgraph_interrupt_nodes:
        # J-13 + J-15: Reject conditional/router outgoing edges in Phase 1
        if condition or edge_type == "conditional":
            raise ValueError(
                f"Conditional outgoing edge from subgraph interrupt node "
                f"'{from_node}' not supported in Phase 1"
            )
        run_name = f"{from_node}__run"
        paused_key = f"__{from_node}_paused__"
        target = END if to_node == "END" else to_node
        expression_edges.setdefault(run_name, []).append(
            (f"{paused_key} == true", from_node)
        )
        expression_edges.setdefault(run_name, []).append(
            (f"{paused_key} == false", target)
        )
        return  # Do NOT add simple edge

    # Handle START edge
    if from_node == "START":
        ...
```

**Outgoing edges (NEW — J-12 mechanics):**
When `from_node` is in `subgraph_interrupt_nodes`, the YAML edge
`from: run_triage, to: format_done` is transformed into:
- `run_triage__run → run_triage` (condition: `__run_triage_paused__ == true`)
- `run_triage__run → format_done` (condition: `__run_triage_paused__ == false`)

These go into `expression_edges["run_triage__run"]` and are later processed
by `_add_conditional_edges` → `make_expr_router_fn`. The original `from_node`
name disappears from the direct edge wiring.

The loop-back edge (`run_triage → run_triage__run`) is already added by
`compile_node` (D-2), NOT by edge compiler.

**J-13 + J-15 scope constraint:** Both `condition` and `type: conditional`
outgoing edges from subgraph interrupt nodes are rejected in Phase 1 (raise
ValueError). Navigator graph has only simple outgoing edges, so this doesn't
block current use cases. Compound condition support deferred to Phase 2.

This requires `_process_edge` to accept `subgraph_interrupt_nodes` as a
separate parameter (distinct from `interrupt_nodes`) because the rewrite
logic differs: interrupt nodes only redirect incoming `to_node`, while
subgraph interrupt nodes redirect BOTH incoming `to_node` AND transform
outgoing `from_node` into conditional expression edges.

### D-4: `state_builder.py` — auto-add paused flag (J-5)

When building state TypedDict, detect subgraph nodes with
`interrupt_output_mapping` and auto-add `__{node_name}_paused__: bool` to state.
Example: `run_triage` → `__run_triage_paused__`, `run_interrai` →
`__run_interrai_paused__`.

### D-5: Unit tests — `tests/unit/test_subgraph_interrupt_split.py`

New test file focused on the split pattern:

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_split_returns_tuple_with_interrupt_mapping` | `create_subgraph_node` returns `(run_fn, interrupt_fn)` when `interrupt_output_mapping` non-empty |
| 2 | `test_no_split_without_interrupt_mapping` | Returns single callable when `interrupt_output_mapping` is empty |
| 3 | `test_run_fn_catches_graph_interrupt_returns_mapped_state` | `run_fn` catches `GraphInterrupt`, reads child state, returns mapped dict with `__{name}_paused__ = True` |
| 4 | `test_run_fn_returns_output_mapping_on_completion` | `run_fn` returns `output_mapping` with `__{name}_paused__ = False` on normal completion |
| 5 | `test_interrupt_fn_calls_interrupt_with_payload` | `interrupt_fn` reads `response_key` from state, calls `interrupt()` |
| 6 | `test_interrupt_fn_returns_resume_value` | `interrupt_fn` returns `{resume_key: response}` on resume |
| 7 | `test_run_fn_resumes_paused_child_with_command` | J-1: second call detects paused child, uses `Command(resume=...)` |
| 8 | `test_run_fn_fresh_start_when_child_not_paused` | J-1: first call uses `invoke(child_input)`, not `Command(resume=...)` |
| 9 | `test_run_fn_get_state_valueerror_treated_as_fresh` | J-1: `get_state()` raising ValueError → treated as fresh start |
| 10 | `test_child_checkpointer_created_from_config` | J-2: child compiled with checkpointer from own config when `interrupt_output_mapping` present |
| 11 | `test_child_no_checkpointer_without_interrupt_mapping` | J-2: child compiled without checkpointer when `interrupt_output_mapping` empty |
| 12 | `test_multi_turn_state_updates_progressively` | Mock multi-turn: each `run_fn` call returns updated `extracted` |
| 13 | `test_mock_compiled_graph_no_false_pause` | MagicMock compiled graph: `__{name}_paused__` flag routing doesn't depend on mock `.next` |
| 14 | `test_compile_node_creates_split_for_subgraph_interrupt` | `compile_node()` returns `"subgraph_interrupt"` marker |
| 15 | `test_edge_redirect_incoming_to_run_node` | Incoming edge redirected to `{name}__run` |
| 16 | `test_state_builder_adds_per_node_paused_flag` | J-5: State has `__{name}_paused__` key (per-node, not generic) |

**D-5b: `tests/unit/test_edge_router_redirect.py` — D-0 bugfix tests**

| # | Test | Asserts |
|---|------|---------|
| 17 | `test_router_edge_redirects_interrupt_target_in_list` | J-3: list target `ask_priority` → `ask_priority_prepare` |
| 18 | `test_router_edge_leaves_non_interrupt_targets_unchanged` | J-3: non-interrupt targets in same list unchanged |
| 19 | `test_router_edge_redirects_subgraph_interrupt_in_list` | J-3: list target `run_triage` → `run_triage__run` |

**D-5c: Round 2 amendment tests**

| # | Test | Asserts |
|---|------|---------|
| 20 | `test_response_key_defaults_to_response` | J-9: `response_key` defaults to `"response"` |
| 21 | `test_response_key_from_config` | J-9: explicit `response_key` in config overrides default |
| 22 | `test_resume_key_defaults_to_user_message` | J-10: `resume_key` defaults to `"user_message"` |
| 23 | `test_resume_key_from_config` | J-10: explicit `resume_key` in config overrides default |
| 24 | `test_compile_nodes_returns_three_sets` | J-11: `compile_nodes()` returns `(map_nodes, interrupt_nodes, subgraph_interrupt_nodes)` |
| 25 | `test_outgoing_edge_rewritten_to_expression_edges` | J-12: `from: run_triage, to: format_done` → two expression edges from `run_triage__run` |
| 26 | `test_conditional_outgoing_edge_rejected` | J-13+J-15: `from: run_triage, to: X, condition: "..."` raises ValueError |
| 27 | `test_router_outgoing_edge_rejected` | J-15: `from: run_triage, to: [A, B], type: conditional` raises ValueError |

**D-5d: Round 3 amendment tests**

| # | Test | Asserts |
|---|------|---------|
| 28 | `test_router_edge_route_mapping_redirects_interrupt_target` | J-14: `route_mapping["ask_priority"] == "ask_priority_prepare"` while `make_router_fn` receives original names |
| 29 | `test_router_edge_route_mapping_redirects_subgraph_target` | J-14: `route_mapping["run_triage"] == "run_triage__run"` in `_add_conditional_edges` |
| 30 | `test_router_edge_non_interrupt_targets_unchanged_in_mapping` | J-14: non-interrupt items in router edge remain identity-mapped |
| 31 | `test_from_node_check_precedes_router_check` | J-15: `from: run_triage, to: [A, B], type: conditional` caught by from_node check, not stored in router_edges |

All tagged `@pytest.mark.req("REQ-YG-214")`.

### D-6: Existing test migration

- 24 tests in `test_subgraph.py` must continue passing unchanged.
- `TestInterruptOutputMapping` class tests the `__interrupt__` marker path
  which still works for direct `create_subgraph_node` calls (unit test bypass).
- Integration test `test_subgraph_integration.py` must pass with the split.

## Acceptance Criteria

- [ ] D-0: Router/conditional edges redirect list targets for interrupt nodes
      via `route_mapping` in `_add_conditional_edges`, not list rewrite in
      `_process_edge` (J-3, J-14)
- [ ] D-0: `_add_conditional_edges` receives `interrupt_nodes` and
      `subgraph_interrupt_nodes` parameters (J-14)
- [ ] D-1: Child checkpointer created from child config when
      `interrupt_output_mapping` present (J-2)
- [ ] D-1: `response_key` and `resume_key` explicitly configurable with
      sensible defaults (J-9, J-10)
- [ ] Subgraph nodes with `interrupt_output_mapping` are split into `__run` +
      gate at compile time
- [ ] `{name}__run` detects first-call vs resume; uses `Command(resume=...)`
      for paused children (J-1)
- [ ] `{name}__run` returns mapped state normally (no `__pregel_send`, no
      re-raise)
- [ ] Parent `get_state().values` shows mapped keys at each interrupt boundary
- [ ] Multi-turn interrupt/resume cycle works (3+ turns)
- [ ] Existing 24 subgraph tests pass without modification
- [ ] Subgraphs without `interrupt_output_mapping` compile unchanged
- [ ] `mode=direct` subgraphs unaffected
- [ ] Per-node state key `__{node_name}_paused__` avoids collisions (J-5)
- [ ] `compile_nodes` returns three-tuple (J-11)
- [ ] Outgoing edges from subgraph interrupt nodes rewritten to expression
      edges from `{name}__run` (J-12)
- [ ] Conditional outgoing edges from subgraph interrupt nodes rejected in
      Phase 1, including both `condition` and `type: conditional` (J-13, J-15)
- [ ] D-3 `from_node` check precedes all other edge handling in
      `_process_edge` (J-15)
- [ ] Works with all stream modes (`messages`, `values`, `updates`)
- [ ] Works with all checkpointers (`memory`, `sqlite`, `redis`)
- [ ] 31+ unit tests tagged `@pytest.mark.req("REQ-YG-214")`
- [ ] NV-190 integration test passes (6/6)

## Alternatives Considered

### A: Fix `__pregel_send` in LangGraph

The real fix would be for LangGraph to commit `__pregel_send` writes before
discarding on `GraphInterrupt`. This is outside our control — LangGraph treats
`GraphInterrupt` as an abort signal that discards all pending state.

### B: Config-level expansion (inline subgraph)

Expand child graph nodes into parent graph at config pre-processing time.
Theoretically correct but impractically complex for arbitrary subgraphs (state
collisions, tool resolution, edge rewiring). FR-049 handles the common
interactive tool case. A general solution is not justified.

### C: Fix the requirement (concurrent graphs)

For ninchat_voice specifically: don't nest triage inside navigator. Have the FSM
coordinator orchestrate navigator and triage as separate top-level graphs. This
bypasses the framework limitation entirely — no framework changes needed.

**C is the pragmatic choice for ninchat_voice. This FR is the framework-level
fix for the general case.**

## Related

- FR-006: Original `interrupt_output_mapping` feature
- FR-039: Async interrupt_output_mapping investigation (closed, not a bug)
- FR-049: Interactive tool node type (compile-time expansion workaround)
- FR-060: Interrupt node prepare/interrupt split (pattern template)
- NV-190: Navigator → triage happy path test (condemning evidence)
- `.chaplain/inbox/fix-subgraph-interrupt-output-mapping.md`: Investigation log
