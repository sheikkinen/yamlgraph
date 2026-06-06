# Feature Request: Conditional Edge to Map Node Drops the Condition (Dual-Router Non-Termination)

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (2026-06-06)
**Effort:** 1 day
**Requested:** 2026-06-06
**Requirement:** REQ-YG-434 (CAP-168)

## Summary

A conditional edge whose target is a `map` node silently discards its
`condition`. The edge compiler wires the map fan-out as an *unconditional*
`add_conditional_edges` router, while the node's other `condition:` edges are
wired as a *second* expression router. LangGraph runs both routers every
superstep (additive fan-out), so the map branch always fires regardless of the
condition. Graphs that route one branch to a map node and another to `END`
never terminate.

Discovered while building the FR-466 dungeon-master turn loop: resuming the
`dm_window` interrupt with `end` correctly parses `dm_action == 'end'` and the
expression router returns `__end__`, yet the graph re-enters the `plan_all` map
node forever because the `retry` branch (`parse_dm -> plan_all`) registered a
second, unconditional router.

## Value Statement

Graph authors can route conditional branches to map nodes (a natural pattern for
"loop / re-fan-out vs. finish") and trust that exactly one branch fires per
turn — eliminating a silent, hard-to-diagnose infinite loop.

## Problem

In `yamlgraph/edge_compiler.py`, `_process_edge` checks the map handlers
**before** it inspects `condition`:

```python
# Handle map node edges (delegate to handlers that return True if handled)
if _handle_map_to_map_edge(graph, from_node, to_node, map_nodes):
    return
if _handle_to_map_edge(graph, from_node, to_node, map_nodes):   # <-- consumes edge
    return
if _handle_from_map_edge(graph, from_node, to_node, map_nodes):
    return

# (never reached for a conditional edge to a map node)
if condition:
    expression_edges.setdefault(from_node, []).append(...)
```

`_handle_to_map_edge` ignores `condition` entirely:

```python
def _handle_to_map_edge(graph, from_node, to_node, map_nodes) -> bool:
    if isinstance(to_node, str) and to_node in map_nodes:
        map_edge_fn, sub_node_name = map_nodes[to_node]
        graph.add_conditional_edges(from_node, map_edge_fn, [sub_node_name])  # unconditional
        return True
    return False
```

When the source node also has expression edges (e.g. `condition: dm_action ==
'end' -> END`), `_add_conditional_edges` later adds a **second** router on the
same source. Inspecting the compiled graph confirms two coexisting branches:

```text
branches on parse:
  map_edge        -> {'_map_plan_sub': '_map_plan_sub'}   # unconditional
  expr_router_fn  -> {'__end__': '__end__'}               # conditional
```

### Fault isolation (witnesses to keep)

1. `tests/unit/test_interrupt_loop_termination.py` — reproduces the
   non-termination via a minimal interrupt-in-a-cycle graph whose conditional
   branch targets a map node. `test_resume_with_terminating_token_ends_graph`
   asserts `get_state().next == ()` after the terminating token and currently
   **fails** (`next == ('ask',)`).
2. `tests/unit/test_langgraph_dual_router_fault.py` — pure LangGraph (no
   YAMLGraph) proves that two `add_conditional_edges` routers on one node fan
   out to the union of targets every superstep (documented behavior), and that a
   single condition-honoring router terminates. **Exonerates LangGraph**; the
   defect is YAMLGraph emitting two routers.

Fixture: `tests/fixtures/interrupt_loop_end.yaml`.

## Proposed Solution

A conditional edge to a map node must be folded into the **single** expression
router for the source node, which produces the map `Send` fan-out only when its
condition matches (see Judgment J1) — never wired as a separate unconditional
router.

1. **Guard `_handle_to_map_edge` on `condition`.** A conditional edge from a
   non-map source to a map node must NOT be consumed by `_handle_to_map_edge`.
   Pass `condition` into the handler and return `False` (not handled) when it is
   set, so `_process_edge` falls through to the `expression_edges` collection.
   (Per Judgment J2, conditional edges *from* a map node are out of scope;
   `_handle_map_to_map_edge` is left unchanged.)

2. **Resolve map targets in the expression collector AND emit `Send` fan-out at
   runtime.** When collecting an expression edge whose `to` is a map node, the
   edge must carry the map node's `map_edge_fn` so the single router can produce
   the per-item `Send` fan-out — see Judgment defect **J1**: the map sub-node is
   *not* a plain string target. The router's `path_map` lists the sub-node name
   (so LangGraph accepts the destination), but the router's **return value** for
   a matched map condition must be `map_edge_fn(state)` (a `list[Send]`), exactly
   as the existing map-to-map edge does
   (`add_conditional_edges(from_sub, to_map_edge_fn, [to_sub])`).

   Concretely:
   - Thread `map_nodes` into `_add_conditional_edges` and `make_expr_router_fn`.
   - Store the expression edge target as the **map node name** (not the sub-node
     name); resolve to the sub-node name only when building `route_mapping`.
   - In `make_expr_router_fn`, when a condition matches and its target is a map
     node, `return map_edge_fn(state)` (the `Send` list); otherwise return the
     string target as today.

   This keeps a **single** router per source and preserves per-item fan-out with
   item injection. Routing to the bare sub-node string (the original step 2)
   would run the sub-node once over the full state and silently destroy map
   semantics — rejected.

3. **Compiler guard against dual routers (defense in depth).** After edge
   processing, assert no source node has both a map fan-out router and an
   expression router. If detected, raise a clear compile-time error naming
   <!-- Implemented as ValueError; see Implementation Status. -->
   the node — converting a silent infinite loop into a fast, explicit failure.

> Note: the unconditional `prep_turn -> plan_all` map entry edge (no
> `condition`) must keep working unchanged — only *conditional* edges to map
> nodes change behavior.

## Acceptance Criteria

- [x] `test_resume_with_terminating_token_ends_graph` passes (graph terminates
      on the terminating token; `next == ()`).
- [x] `test_resume_with_loop_token_returns_to_interrupt` still passes (loop path
      intact).
- [x] Both `tests/unit/test_langgraph_dual_router_fault.py` witnesses remain
      green (LangGraph behavior unchanged).
- [x] `compile_graph(cfg).branches[<source>]` for a conditional-to-map node
      contains exactly **one** router (the expression router), verified by a new
      unit test on `edge_compiler`
      (`test_conditional_edge_to_map_registers_single_router`).
- [x] Unconditional `node -> map_node` entry edges still compile and run
      (regression test `test_unconditional_edge_to_map_still_compiles`).
- [x] A node configured with a conditional edge to a map node *and* an
      unconditional edge to a map node on the same source raises a clear
      compile-time error (guard test
      `test_unconditional_and_conditional_map_edges_rejected`).
- [x] FR-466 dungeon-master `turn-loop.yaml` runs to completion on the `end`
      action without the example-level workaround (verified live; `retry`
      branch also confirmed to fan out via `Send`).
- [x] `yamlgraph graph lint` clean; `ruff` clean; `lint-imports` clean.
- [x] Diary reflection added.

## Implementation Status (2026-06-06)

Implemented as judged, smallest sufficient change across three files:

- `yamlgraph/edge_compiler.py` — `_handle_to_map_edge` declines to consume an
  edge when a `condition` is present (falls through to the expression router);
  `_process_edge` threads `condition` and records dual-router sources in
  `map_fanout_sources`; `_add_conditional_edges` resolves map-node targets to
  their `_map_<n>_sub` name in the `path_map` and raises on a dual-router
  source.
- `yamlgraph/routing.py` — `make_expr_router_fn` gained a `map_nodes` param and
  returns `map_edge_fn(state)` (the `list[Send]` fan-out) when the matched
  condition's target is a map node, preserving item injection and the `collect`
  reducer (per J1).
- `yamlgraph/graph_loader.py` — `compile_graph` builds `map_fanout_sources` and
  threads `map_nodes` + `map_fanout_sources` into `_add_conditional_edges`.

### Deviation: `ValueError` instead of `GraphCompilationError`

The FR specified raising `GraphCompilationError` for the dual-router guard, but
no such exception class exists in the codebase. The guard raises `ValueError`
with a message naming the offending node and the remedy (make all edges out of
the node conditional, or remove the conditional edges). The guard test asserts
`pytest.raises(ValueError, match="map node")`. Introducing a dedicated
exception type would be out-of-scope speculative API surface; `ValueError` is
the established convention for invalid graph configuration in this module.

### Tests / requirement

New capability `CAP-168` with `REQ-YG-434`. Witness and edge tests retagged
from the FR-466 `REQ-YG-433` to `REQ-YG-434` (the fix is framework-level graph
compilation, not DM-specific). New file
`tests/unit/test_conditional_edge_to_map.py` (3 tests).

## Judgment (2026-06-06)

Verified the proposed solution against the actual compiler and runtime. One
correctness defect found and folded back into the Proposed Solution; scope
frozen.

### J1 — Map fan-out returns `Send`, not a node-name string (BLOCKER, fixed)

The original step 2 proposed routing the matched condition to the map *sub-node*
name as a plain string. This is **wrong**. `map_compiler.create_map_node`
returns a `map_edge` function that yields `list[Send]`:

```python
return [
    Send(sub_node_name, {**state, item_var: item, "_map_index": i})
    for i, item in enumerate(items)
]
```

Returning the bare string `"_map_plan_sub"` from the expression router would run
the sub-node **once over the full state** with no item injection and no
`collect` reducer fan-in — silently destroying map semantics (the loop would
“work” but produce one bogus plan instead of N). The router must return
`map_edge_fn(state)` (the `Send` list) when a map condition matches, with the
sub-node name listed only in the `path_map`. Precedent exists: the map-to-map
edge already does `add_conditional_edges(from_sub, to_map_edge_fn, [to_sub])`
with a `Send`-returning function and the sub-node as `path_map`. Proposed
Solution step 2 rewritten accordingly.

### J2 — Scope: only conditional edges from a NON-map source to a map node

The reproduced and tested fault is `parse -> plan` (plain source, map target)
with a sibling `parse -> END` condition. Conditional edges *from* a map node
(`_handle_map_to_map_edge` / `_handle_from_map_edge` with a `condition`) are a
separate, unreproduced mechanism (routing happens from `_map_<n>_sub`). Frozen
out of scope; if a witness later condemns it, raise a follow-up FR. The fix to
`_handle_to_map_edge` must therefore only decline to consume an edge when
`condition` is present and the **source is not** a map node.

### J3 — Guard wording tightened

The acceptance criterion for the dual-router guard was ambiguous (“if ever
reconstructed”). Restated as a concrete invariant: after edge processing, no
source node may appear in both the map fan-out registration and the
`expression_edges` collection; violation raises `GraphCompilationError` naming
the node. This is the cheap, explicit failure that replaces the silent loop.

### Confirmed correct as written

- Threading `map_nodes` into `make_expr_router_fn` is feasible — the function
  already receives per-edge `(condition, target)` tuples; adding a `map_nodes`
  lookup is local and Layer-3-clean.
- `_loop_limit_reached` / `loop_exit_target` paths in `make_expr_router_fn` are
  unaffected (they return strings before condition evaluation).
- The single-router design avoids the union-fan-out ambiguity that any
  “two routers, one returns `[]`” variant reintroduces (evaluated and rejected).

### Authority

Scope frozen. Implement smallest sufficient change in `edge_compiler.py` +
`routing.py`. Keep all three witnesses. Begin from the existing RED in
`test_interrupt_loop_termination.py`.

## Alternatives Considered

- **Example-level workaround only** (insert a non-map node between the
  conditional source and the map node so the conditional edge targets a plain
  node). Cheap and unblocks FR-466, but leaves the framework trap armed for the
  next author. Rejected as the *sole* fix; may be applied to FR-466 in the
  interim while this FR lands.
- **Reorder `_process_edge` to check `condition` before the map handlers**
  without resolving map targets. Insufficient: the expression router would route
  to the map *node* name, which has no compiled node (only the `_map_<n>_sub`
  exists), producing an unknown-target error. Target resolution (step 2) is
  required.
- **Annotate the `beat`-style channels and let both routers run.** Treats the
  symptom (concurrent updates) not the cause (two routers); the map branch would
  still execute every turn. Rejected.

## Related

- `yamlgraph/edge_compiler.py` — `_process_edge`, `_handle_to_map_edge`,
  `_handle_map_to_map_edge`, `_add_conditional_edges`
- `yamlgraph/routing.py` — `make_expr_router_fn`
- FR-466 (dungeon-master example; discovery context)
- Witnesses: `tests/unit/test_interrupt_loop_termination.py`,
  `tests/unit/test_langgraph_dual_router_fault.py`,
  `tests/fixtures/interrupt_loop_end.yaml`
- Repo memory: `conditional-edge-to-map-node-bug.md`
