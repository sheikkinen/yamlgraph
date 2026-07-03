# Feature Request: Unify Agent Tool Bind and Execute Paths

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-07-03
**Judged:** 2026-07-03

## Summary

`tools/agent.py` has two distinct tool execution mechanisms that duplicate logic. The bind path wraps tools as `StructuredTool` for `bind_tools()`, then the execute path ignores those wrappers and calls raw functions via `tool_lookup`.

## Value Statement

Agent node maintenance cost drops by removing the dual-path pattern that forces every new tool type (shell, python, graph) to be integrated in two places.

## Problem

The agent node currently:

1. **Binding** (lines 147-168): Uses `build_langchain_tool`, `build_python_tool`, `build_graph_tool` to create `StructuredTool` wrappers for LLM `bind_tools()` — so the LLM knows the tool schemas.
2. **Execution** (lines 288-327): Re-imports `execute_shell_tool` and `load_python_function` to execute the same tools natively, dispatching on `isinstance(tool_config, ShellToolConfig)` / `PythonToolConfig | SchemaLoaderToolConfig` / callable.

Both `agent.py` and `tool_builders.py` import `execute_shell_tool` and `load_python_function`. The bind path wraps them; the execute path ignores the wrappers.

The graph tool fix in FR-658 (`callable(tool_config) and not hasattr(tool_config, 'invoke')`) is a symptom: `tool_lookup` stores raw configs for shell/python but raw callables for graph tools. The `isinstance` dispatch tree grows with every new tool type.

## Proposed Solution

Store the `StructuredTool` instances (already created for binding) in `tool_lookup` instead of the raw configs. The execution path then becomes a single `tool.invoke(tool_args)` call for all tool types — shell, python, graph, websearch.

```python
# Current: dual path
for name in tool_names:
    if name in tools:
        lc_tools.append(build_langchain_tool(name, tools[name]))
        tool_lookup[name] = tools[name]  # raw config
    elif name in python_tools:
        lc_tools.append(build_python_tool(...))
        tool_lookup[name] = python_tools[name]  # raw config
    ...

# Proposed: single path
for name in tool_names:
    if name in tools:
        st = build_langchain_tool(name, tools[name])
        lc_tools.append(st)
        tool_lookup[name] = st  # StructuredTool
    elif name in python_tools:
        st = build_python_tool(...)
        lc_tools.append(st)
        tool_lookup[name] = st  # StructuredTool
    ...

# Execution: one line for all types
output = tool_lookup[tool_name].invoke(tool_args)
```

This eliminates:
- The `isinstance` dispatch tree in the execution loop
- The duplicate imports of `execute_shell_tool` and `load_python_function`
- The `callable(x) and not hasattr(x, 'invoke')` heuristic for graph tools

## Acceptance Criteria

- [ ] AC-1: `tool_lookup` stores `StructuredTool` instances, not raw configs/callables
- [ ] AC-2: Execution loop uses `tool.invoke()` for all tool types (no isinstance dispatch)
- [ ] AC-3: `execute_shell_tool` and `load_python_function` imports removed from `agent.py`
- [ ] AC-4: All existing agent tests pass. Add one test verifying `tool_lookup` stores `StructuredTool` instances (not raw configs)
- [ ] AC-5: Error output format to the LLM is preserved (same `Error: ...` prefix). Add a test for error paths.

## Judgement

**Verdict: Approved with amendments.**

The dual-path pattern is real and verified. `agent.py` (367 lines) imports `execute_shell_tool` and `load_python_function` for the execution loop (lines 292-327) while also wrapping them as StructuredTools for binding (lines 147-168, via `tool_builders.py`). FR-658 added a third branch with the `callable(x) and not hasattr(x, 'invoke')` heuristic — a clear code smell signalling the dispatch tree is wrong.

**Amendments:**

1. **AC-4 strengthened.** Original "All existing agent tests pass without modification" was too weak. Amended to require a test proving `tool_lookup` stores `StructuredTool` instances.

2. **AC-5 added (error format).** The current execution path formats errors as `f"Error: {result.error}"` for shell tools and `f"Error: {e}"` for python tools. `StructuredTool.invoke()` wraps exceptions differently (may return `ToolException` or re-raise). Must preserve error format and add a test.

3. **`tool_builders.py` extraction is prerequisite, not assumed.** The FR references `tool_builders.py` as existing — it exists in the committed codebase (FR-658). The extraction is already done.

4. **Original AC-5 (line count decrease) dropped.** Line count is a side-effect, not a criterion. The file-size gate enforces the limit independently.

**Scope freeze:** One concern — unify the execution dispatch. No new tool types, no refactoring of the binding loop structure.

## Alternatives Considered

- **Keep dual path**: Works but grows linearly with new tool types. FR-658 already added a third branch.
- **Use `lc_tools` list directly**: The LLM returns tool names, and we could look up by name in the `lc_tools` list. Slightly slower lookup but eliminates `tool_lookup` entirely.

## Related

- FR-658: Graph-as-tool (added the third tool type that exposed the duplication)
- `yamlgraph/tools/tool_builders.py`: `build_langchain_tool`, `build_python_tool`
- `yamlgraph/tools/agent.py`: Lines 147-168 (bind loop), 288-327 (execute dispatch)
