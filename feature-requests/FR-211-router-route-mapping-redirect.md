# Feature Request: Fix Router Conditional Edge Redirect for Interrupt Targets

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-31

## Summary

Router/conditional edges with `to: [list]` targets bypass the FR-060 interrupt redirect logic in `_process_edge`, causing interrupt nodes in router target lists to be routed to their original names instead of the compiler-split `*_prepare` nodes.

## Value Statement

Graph authors using router nodes that target interrupt nodes get correct routing without silent misrouting to non-existent graph nodes or skipping the interrupt prepare phase.

## Problem

`_process_edge` redirects incoming edges to interrupt split nodes via:

```python
if interrupt_nodes and isinstance(to_node, str) and to_node in interrupt_nodes:
    to_node = f"{to_node}_prepare"
```

The `isinstance(to_node, str)` guard means conditional edges with `to: [a, b, c]` are stored as-is into `router_edges[from_node] = to_node` before any redirect can occur. When `_add_conditional_edges` then builds the `route_mapping`:

```python
route_mapping = {target: target for target in target_nodes}
```

the mapping uses unredirected names. The LangGraph node that `make_router_fn` would route to (`node_a_prepare`) doesn't match any graph node registered under `node_a`, causing silent misrouting or a graph build error.

The same failure mode applies to FR-210 subgraph interrupt split targets (`*__run`).

**Root cause:** Redirect logic lives only in `_process_edge` (string-target path). The list-target path stores raw targets and defers to `_add_conditional_edges`, which currently has no knowledge of interrupt nodes.

## Proposed Solution

Two targeted changes in `edge_compiler.py`:

### 1. Do not redirect list targets in `_process_edge`

Leave the conditional list-target path untouched — no rewriting of the list before storage. Keep redirect only on the string path (existing behaviour).

### 2. Build a translated `route_mapping` in `_add_conditional_edges`

Pass both `interrupt_nodes` and `subgraph_interrupt_nodes` to `_add_conditional_edges`. When building the route mapping for router edges, keep the original target name as the **route label** (so `make_router_fn` still matches `_route` correctly) but map it to the **redirected graph node name** as the value:

```python
def _add_conditional_edges(
    graph: StateGraph,
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    loop_exits: dict[str, str] | None = None,
    interrupt_nodes: set[str] | None = None,
    subgraph_interrupt_nodes: set[str] | None = None,
) -> None:
    for source_node, target_nodes in router_edges.items():
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
            make_router_fn(target_nodes),   # still receives original names
            route_mapping,
        )
```

### 3. Update `compile_graph` call site

Pass `interrupt_nodes` (and, when available, `subgraph_interrupt_nodes`) from `compile_nodes` output through to `_add_conditional_edges`.

```python
# graph_loader.py compile_graph()
_add_conditional_edges(
    graph,
    router_edges,
    expression_edges,
    config.loop_exits,
    interrupt_nodes=interrupt_nodes,
)
```

## Acceptance Criteria

- [ ] A unit test proves that a compiled graph with a router node whose `to:` list includes an interrupt node routes to `{name}_prepare` at runtime (not `{name}`)
- [ ] A unit test proves that non-interrupt targets in the same `to:` list are unchanged in the route mapping
- [ ] A unit test proves that `make_router_fn` still receives original target names (route labels unmodified)
- [ ] `_add_conditional_edges` signature accepts `interrupt_nodes` and `subgraph_interrupt_nodes` (both optional, default `None`)
- [ ] `_process_edge` list-target path is not modified (no regression to existing string-redirect logic)
- [ ] All existing router and interrupt tests pass
- [ ] `pytest tests/unit/ -q --no-cov` passes green

## Alternatives Considered

**Rewrite list targets in `_process_edge`:** Mutating the list stored in `router_edges` before `_add_conditional_edges` runs would rewrite both the route labels and the mapping values. This breaks `make_router_fn` because the LLM outputs the original node name as `_route`; if the label is rewritten to `name_prepare` the router would never match.

**Post-processing `router_edges` in `_add_conditional_edges`:** Equivalent to the chosen approach; consolidated into the mapping build loop for clarity.

## Related

- `yamlgraph/edge_compiler.py` — `_process_edge` (line ~84), `_add_conditional_edges` (line ~115)
- `yamlgraph/routing.py` — `make_router_fn`
- `yamlgraph/graph_loader.py` — `compile_graph` call site (line ~291)
- `feature-requests/060-interrupt-set-response-before-pause.md` — FR-060 two-node split (implemented)
- `feature-requests/FR-210-subgraph-interrupt-state-commit.md` — FR-210 judgement J-3/J-14 surface this bug
- `tests/unit/test_router.py` — existing router test patterns
