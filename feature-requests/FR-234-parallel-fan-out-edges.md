# Feature Request: Parallel Fan-Out Edges

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-18

## Summary

Add support for parallel fan-out edges where a single node fans out to multiple target nodes that execute concurrently, expressed as `to: [node_a, node_b, node_c]` without `type: conditional`.

## Value Statement

Graph authors can express concurrent execution of independent branches with a single edge declaration, enabling natural DAG patterns without resorting to map nodes or workarounds.

## Problem

Currently, `to: [list]` in YAML edges only works with `type: conditional` (router-based conditional routing that picks ONE target). There is no way to express "after this node completes, run all these targets in parallel" — a fundamental DAG pattern.

Users who need parallel branches must either:
- Use map nodes (designed for iterating over a list with the SAME sub-node)
- Write multiple sequential edges (which LangGraph would still run in parallel, but the YAML intent is unclear)

Neither pattern clearly expresses fan-out to distinct, independent nodes.

## Proposed Solution

When `to` is a list and there is no `type: conditional` or `condition`, treat it as parallel fan-out. The edge compiler adds multiple `graph.add_edge()` calls — one per target. LangGraph natively runs these in parallel.

```yaml
# Parallel fan-out: all three run concurrently after generate completes
edges:
  - from: generate
    to: [analyze, summarize, translate]

# Fan-in: all three must complete before final runs
  - from: analyze
    to: final
  - from: summarize
    to: final
  - from: translate
    to: final
  - from: final
    to: END
```

Contrast with existing conditional routing (unchanged):

```yaml
# Conditional: picks ONE target based on router output
edges:
  - from: classify
    to: [positive, negative, neutral]
    type: conditional
```

### Implementation Details

**Edge compiler** (`edge_compiler.py`):
- In `_process_edge()`, when `to` is a list and `edge_type != "conditional"` and no `condition`, add `graph.add_edge(from_node, target)` for each target.
- Handle interrupt node redirect: replace targets in interrupt_nodes with `{name}_prepare`.
- Handle map node targets: use `_handle_to_map_edge()` for map targets.
- Handle START fan-out: set first target as entry point, add edges to rest.

**No model changes needed**: `EdgeConfig.to` already accepts `str | list[str]`.

**Linter**: `check_edge_coverage()` already handles list targets correctly.

## Acceptance Criteria

- [x] `to: [a, b, c]` without `type: conditional` compiles as parallel fan-out (multiple `add_edge` calls)
- [x] Fan-out targets in `interrupt_nodes` are redirected to `{name}_prepare`
- [x] Fan-out from START uses conditional entry point
- [x] Fan-out to map nodes dispatches via map edge function
- [x] Linter reachability (W002/W003) works correctly with fan-out edges
- [x] Graph with parallel fan-out compiles and produces a valid CompiledGraph
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-235")`
- [x] `reference/graph-yaml.md` updated with parallel fan-out section
- [x] REQ-YG-235 added to ARCHITECTURE.md
- [x] Changelog fragment added

## Alternatives Considered

1. **Explicit `type: parallel`** — Adds a new type keyword. Rejected because the implicit behavior (list without conditional = parallel) is more natural and consistent with how LangGraph works.
2. **Reuse map nodes** — Map nodes iterate the SAME sub-node over a list. Fan-out sends to DIFFERENT nodes. Different semantics.
3. **Multiple simple edges** — Writing separate `from: A, to: B` edges for each target already works in LangGraph. But a single edge with `to: [list]` is more declarative and the YAML intent is clearer.

## Related

- `yamlgraph/edge_compiler.py` — Main implementation target
- FR-067: Edge compiler extraction (module structure)
- FR-232: Race node type (parallel provider execution, different pattern)
- `yamlgraph/map_compiler.py` — Map node fan-out via Send() (different mechanism)
