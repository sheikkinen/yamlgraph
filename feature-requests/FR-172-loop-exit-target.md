# Feature Request: FR-172 — Configurable loop exit target for expression router

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Judged:** 2026-03-09
**Requested:** 2026-03-09

## Summary

Add a `loop_exits` graph-level config that maps node names to custom exit targets when loop limits are reached, replacing the hardcoded `END` in `make_expr_router_fn`.

## Value Statement

Graph authors can route to a specific post-loop node when a loop limit is hit, enabling reflexion patterns that continue to downstream stages instead of terminating the entire graph.

## Problem

When a node hits its `loop_limit`, the expression router in `routing.py:68-69` unconditionally returns `END`:

```python
if state.get("_loop_limit_reached"):
    return END
```

This means every loop that exhausts its limit terminates the **entire graph**, not just the loop. In a reflexion pattern like `critique → refine → critique`, hitting the critique loop limit should route to a post-loop node (e.g., `distill_reflection`), not abort the pipeline.

**Concrete impact:** FR-169 (enforce reflexion loop) is blocked because its graph has nodes after the loop (`distill_reflection`, `precommit_check`, `submit_pr`) that would be skipped when the loop limit fires.

## Proposed Solution

### 1. New `loop_exits` field in graph YAML

```yaml
# graph.yaml
loop_limits:
  critique: 3
  refine: 2

loop_exits:
  critique: distill_reflection  # When critique hits limit, go here instead of END
```

### 2. Schema change (`models/graph_schema.py`)

Add `loop_exits` alongside `loop_limits`:

```python
loop_exits: dict[str, str] = Field(
    default_factory=dict,
    description="Map of node name to target node when loop limit is reached",
)
```

### 3. Config loading (`graph_loader.py`)

Store `loop_exits` from config:

```python
self.loop_exits = config.get("loop_exits", {})
```

### 4. Pass `loop_exits` through edge compilation

In `graph_loader.py:compile_graph()`, pass `config.loop_exits` to `_add_conditional_edges()`.

In `edge_compiler.py:_add_conditional_edges()`, accept `loop_exits` and forward to `make_expr_router_fn()`:

```python
def _add_conditional_edges(
    graph: StateGraph,
    router_edges: dict[str, list],
    expression_edges: dict[str, list[tuple[str, str]]],
    loop_exits: dict[str, str] | None = None,
) -> None:
    ...
    for source_node, expr_edges in expression_edges.items():
        loop_exit_target = (loop_exits or {}).get(source_node)
        targets = {target for _, target in expr_edges}
        targets.add(END)
        if loop_exit_target:
            targets.add(loop_exit_target)
        route_mapping = {t: (END if t == END else t) for t in targets}
        graph.add_conditional_edges(
            source_node,
            make_expr_router_fn(expr_edges, source_node, loop_exit_target),
            route_mapping,
        )
```

### 5. Router change (`routing.py`)

```python
def make_expr_router_fn(
    edges: list[tuple[str, str]],
    source_node: str,
    loop_exit_target: str | None = None,
) -> Callable[[GraphState], str]:
    def expr_router_fn(state: GraphState) -> str:
        if state.get("_loop_limit_reached"):
            if loop_exit_target:
                return loop_exit_target
            return END
        ...
```

### 6. Lint validation (`graph_lint.py`)

Add a lint rule: every node in `loop_exits` must (a) exist in `nodes`, (b) appear in `loop_limits`, and (c) the target must be a valid node name or `END`.

## Acceptance Criteria

- [ ] `loop_exits` is a valid top-level graph YAML field (dict[str, str])
- [ ] `GraphConfigSchema` validates `loop_exits` as `dict[str, str]` with default `{}`
- [ ] `GraphConfig` stores `loop_exits` from raw config
- [ ] `make_expr_router_fn` accepts optional `loop_exit_target` parameter
- [ ] When `_loop_limit_reached` is `True` and a `loop_exit_target` is configured, router returns the target instead of `END`
- [ ] When `_loop_limit_reached` is `True` and no `loop_exit_target` is configured, router returns `END` (unchanged behavior)
- [ ] `_add_conditional_edges` passes `loop_exit_target` from `loop_exits` config to the expression router
- [ ] The loop exit target node is included in the route mapping so LangGraph knows it is a valid destination
- [ ] Lint rule warns when `loop_exits` key references a node not in `loop_limits`
- [ ] Lint rule warns when `loop_exits` value references a nonexistent node
- [ ] Reflexion example (`examples/demos/reflexion/graph.yaml`) updated with `loop_exits` demonstrating the pattern
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-093")`
- [ ] Unit test: expression router returns custom target when loop limit reached
- [ ] Unit test: expression router returns `END` when loop limit reached and no exit configured
- [ ] Unit test: end-to-end graph compilation with `loop_exits` config
- [ ] Unit test: lint detects invalid `loop_exits` references
- [ ] Documentation updated in `reference/graph-yaml.md`

## Alternatives Considered

### A. Implicit exit detection from edges

Automatically infer the exit target from the non-loop outgoing edge of a loop node (e.g., the `condition: score >= 0.8` edge target). **Rejected:** ambiguous when a node has multiple non-loop outgoing edges; explicit config is clearer and cheaper to implement.

### B. Per-edge `on_loop_exit` attribute

```yaml
edges:
  - from: critique
    to: refine
    condition: critique.score < 0.8
    on_loop_exit: distill_reflection
```

**Rejected:** the exit target is a property of the loop node, not individual edges. A node-level mapping in `loop_exits` is more intuitive and avoids duplication when multiple edges share the same exit target.

### C. Sentinel target name in edge `to`

```yaml
edges:
  - from: critique
    to: loop_exit
    condition: critique.score >= 0.8
```

Where `loop_exit` is a magic target resolved at compile time. **Rejected:** requires mapping `loop_exit` to an actual node somewhere, reintroducing the same config; also collides if a node is literally named `loop_exit`.

## Related

- **FR-169** (`feature-requests/FR-169-enforce-reflexion-loop.md`): Blocked on this FR. Needs `loop_exits: {critique: distill_reflection}` for reflexion loop.
- **`routing.py:49-84`**: `make_expr_router_fn` — the ~5-line change site.
- **`edge_compiler.py:115-148`**: `_add_conditional_edges` — passes loop exit to router.
- **`models/graph_schema.py:214`**: `loop_limits` field — `loop_exits` goes next to it.
- **`graph_loader.py:150`**: Config loading — add `loop_exits` storage.
- **`examples/demos/reflexion/graph.yaml`**: Existing reflexion pattern to extend.
- **`tests/unit/test_loops.py`**: Existing loop tests to extend.

## Scope Boundary

This FR covers **only** the `loop_exits` routing mechanism. It does **not** cover:
- Resetting `_loop_limit_reached` after exit (the flag is already reset by the next node's return dict)
- Nested loop exit chains (loop within loop) — design separately if needed
- `loop_exits` for router-style (`type: conditional`) edges — only expression edges

## Judgement

**Verdict: APPROVE — Scope frozen. Authority granted to implement.**

**Findings:**

1. **Scope:** Clear, minimal, single-responsibility. Only the `loop_exits` routing mechanism with explicit exclusions.
2. **Feasibility — confirmed.** All change sites verified against source:
   - `routing.py:68-69` — hardcoded `END` confirmed; ~5-line change
   - `edge_compiler.py:115-146` — `_add_conditional_edges` signature and call to `make_expr_router_fn` confirmed
   - `graph_schema.py:214` — `loop_limits` field confirmed; `loop_exits` slots naturally beside it
   - `graph_loader.py:150` — config loading confirmed; `loop_exits` follows same pattern
   - `linter/checks_semantic.py` — existing E008 rule for `loop_limits` provides template for `loop_exits` validation
3. **Acceptance criteria:** 17 criteria, all measurable and testable. Covers schema, config, routing, lint, tests, docs.
4. **Architecture alignment:** Configuration-driven approach is idiomatic YAMLGraph. `loop_exits` beside `loop_limits` is natural.
5. **Alternatives:** Three alternatives considered and rejected with sound reasoning.
6. **Unblocks FR-169** (enforce reflexion loop) which references this capability as a prerequisite.

**Minor notes (non-blocking):**
- FR references `graph_lint.py` in §6 heading — actual file is `linter/checks_semantic.py`. Self-corrects during implementation.
- FR-169 references this feature as "FR-170"; FR-170 was taken by async-action-type, so FR-172 is the correct number. Ensure FR-169 cross-reference is updated during implementation.
