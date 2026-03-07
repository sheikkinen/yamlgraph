# Feature Request: Lint W015 — skip_if_exists in cycle

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

Add lint warning W015 when a node inside a cycle has `skip_if_exists: true` (explicit or default). The node will execute once, cache its output, and return stale results on every subsequent iteration — the graph loops but produces identical results.

## Value Statement

Graph authors get immediate lint-time feedback on the skip_if_exists loop trap, catching a subtle infinite-staleness bug before runtime.

## Problem

`skip_if_exists: true` is the default for LLM nodes. When such a node participates in a cycle, it writes to its `state_key` on the first iteration. On every subsequent iteration the cached value triggers skip, replaying the same output forever. The graph appears to loop but produces no new work.

This trap is documented in diary 2026-02-22 ("The skip_if_exists Loop Trap") where it caused a production bug in OC-005 probe-recap: the greeting node replayed the same utterance on every loop iteration.

**Runtime mitigation exists** — `apply_loop_node_defaults()` in `graph_loader.py` auto-sets `skip_if_exists: false` on detected loop nodes. However:

1. The runtime fix is silent; authors don't learn the graph was misconfigured.
2. If someone explicitly sets `skip_if_exists: true` on a cycle node, the runtime default won't override it — the intent is respected but the behavior is almost certainly wrong.
3. Lint-time feedback is faster and more educational than runtime fixups.

## Proposed Solution

Add `check_skip_if_exists_in_cycle()` to `yamlgraph/linter/checks_semantic.py`, following the pattern of `check_unguarded_cycles()` (W012).

### Logic

```python
def check_skip_if_exists_in_cycle(graph_path: Path) -> list[LintIssue]:
    """W015 — skip_if_exists: true on a node in a cycle.

    Warns when a node participating in a cycle has skip_if_exists
    explicitly set to true. This causes the node to cache its first
    output and return stale results on every subsequent iteration.
    """
    from yamlgraph.graph_loader import detect_loop_nodes

    issues: list[LintIssue] = []
    graph = load_graph(graph_path)

    edges = graph.get("edges", [])
    loop_nodes = detect_loop_nodes(edges)
    nodes = graph.get("nodes", {})

    for node_name in sorted(loop_nodes):
        node_config = nodes.get(node_name, {})
        if node_config.get("skip_if_exists") is True:
            issues.append(
                LintIssue(
                    severity="warning",
                    code="W015",
                    message=(
                        f"Node '{node_name}' is in a cycle with "
                        f"skip_if_exists: true — it will return "
                        f"cached output on every iteration"
                    ),
                    fix=(
                        f"Set 'skip_if_exists: false' on node "
                        f"'{node_name}' or remove the explicit setting"
                    ),
                )
            )

    return issues
```

### Scope: only explicit `skip_if_exists: true`

The check only fires when the author has written `skip_if_exists: true` explicitly in the YAML. It does **not** warn on nodes that merely inherit the default, because:

- `apply_loop_node_defaults()` already silently corrects the default at runtime.
- Warning on every cycle node that doesn't mention `skip_if_exists` would be noisy and redundant with the runtime fix.
- The real danger is the explicit override — the author thought about it and got it wrong.

### Wiring

1. Add function to `checks_semantic.py` and `__all__`.
2. Import and call in `graph_linter.py` alongside `check_unguarded_cycles`.

## Acceptance Criteria

- [x] W015 fires when a node in a cycle has explicit `skip_if_exists: true`
- [x] W015 does **not** fire when `skip_if_exists` is absent (runtime handles default)
- [x] W015 does **not** fire when `skip_if_exists: false` is set (correct config)
- [x] W015 does **not** fire on nodes outside cycles regardless of `skip_if_exists`
- [x] Unit test with inline YAML covering all four cases above
- [x] All existing example graphs pass lint without false positives (`yamlgraph graph lint examples/**/*.yaml`)
- [x] REQ-YG-113 added to `ARCHITECTURE.md` and tagged on tests

## Alternatives Considered

1. **Promote to error (E-code).** Rejected — `apply_loop_node_defaults()` silently corrects the default case, so the graph still runs correctly. A warning is appropriate for the explicit-override case.
2. **Warn on implicit default too.** Rejected — would generate noise on every cycle node; the runtime already handles it. The value is catching the explicit misconfig.
3. **Remove `apply_loop_node_defaults()` and rely solely on lint.** Rejected — the runtime fix is a safety net; lint and runtime serve complementary roles.

## Related

- **Diary 2026-02-22**: "The skip_if_exists Loop Trap" — origin of this insight
- **FR-050**: `skip_if_exists` truthiness (related but distinct concern)
- **W012**: `check_unguarded_cycles()` — same detection infrastructure, same file
- **W021**: `check_skip_if_exists_add_reducer()` — related skip_if_exists lint in `checks_contracts.py`
- **`apply_loop_node_defaults()`** in `graph_loader.py` — the runtime complement to this lint
