# FR-630: loop_exits Target "END" Crashes at Runtime

**Priority:** HIGH
**Type:** Bug
**Status:** Draft
**Effort:** 0.5 day
**Requested:** 2026-07-01
**Surfaced by:** FR-628 wiki-memory demo

## Summary

`loop_exits: gate: END` is accepted by the linter but crashes at runtime with
"unknown target 'END'" because the string `"END"` from YAML is never normalized
to LangGraph's `END` sentinel constant (`"__end__"`).

## Root Cause

In `yamlgraph/edge_compiler.py` (~line 271–285):

1. `loop_exit_target = (loop_exits or {}).get(source_node)` returns string `"END"`
2. `targets.add(loop_exit_target)` adds literal `"END"` to the set
3. The route_mapping loop checks `elif t == END:` where `END = "__end__"`
4. `"END" != "__end__"` so it falls through to `route_mapping["END"] = "END"`
5. Router returns `"END"` but LangGraph has no node named `"END"` → crash

The linter (`checks_semantic.py:86`) explicitly allows it:
```python
if target != "END" and target not in node_names:
```

## Fix

Normalize in `edge_compiler.py` before adding to targets:

```python
loop_exit_target = (loop_exits or {}).get(source_node)
if loop_exit_target == "END":
    loop_exit_target = END  # Normalize YAML string to LangGraph sentinel
```

Same normalization needed in `routing.py:make_expr_router_fn` where
`return loop_exit_target` should return `END` constant, not string `"END"`.

## Acceptance Criteria

- [ ] `loop_exits: node: END` works at runtime (routes to graph end)
- [ ] Existing tests still pass
- [ ] Add unit test: graph with `loop_exits: X: END` completes without error
- [ ] Linter behavior unchanged (already correct)
