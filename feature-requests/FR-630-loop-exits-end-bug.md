# FR-630: loop_exits Target "END" Crashes at Runtime

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented (2026-07-01) — commit `4742576d` (three boundary fixes from the FR-628 wiki-memory demo).
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

## Judgement

**Verdict: GRANTED — enforce immediately.**

This is a clear bug with linter/runtime disagreement — the most dangerous class
of defect (user gets false confidence from lint passing). The fix is mechanical:
two lines of normalization following the exact pattern already used 4 times in
the same file (lines 99, 175, 180, 206).

**Scope freeze:**
- Fix `edge_compiler.py` line ~271: normalize `loop_exit_target`
- Fix `routing.py` line ~82: normalize return value in `expr_router_fn`
- One unit test proving `loop_exits: X: END` compiles and routes correctly
- No other changes

**Enforcement order:**
1. RED: Test that compiles a graph with `loop_exits: node: END` + condition edges, invokes it, asserts it reaches END
2. GREEN: Two-line fix in edge_compiler + routing
3. Verify existing test suite still passes
4. Commit
