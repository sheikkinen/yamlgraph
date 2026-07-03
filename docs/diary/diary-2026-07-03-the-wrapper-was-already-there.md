# Diary: 2026-07-03 — The Wrapper Was Already There

**FR-660, FR-661** | Agent tool unification + import-linter registration

## Observation

FR-658 (graph-as-tool) added a third branch to the agent tool dispatch tree:
`isinstance(ShellToolConfig)` / `isinstance(PythonToolConfig)` / `callable(x) and not hasattr(x, 'invoke')`.
The third branch was the symptom that made the architectural smell visible: every new tool type requires integration in two places (bind path + execute path).

The fix was already sitting in the codebase. `tool_builders.py` (also from FR-658) wraps each tool as a `StructuredTool` with error handling built in. The execute path duplicated that error handling line-for-line. Storing the `StructuredTool` in `tool_lookup` instead of the raw config turned 40 lines of `isinstance` dispatch into one `.invoke()` call.

## Trap: downstream_fix → composition_bug

The `callable(x) and not hasattr(x, 'invoke')` heuristic was a downstream fix for a composition bug. The bind path created StructuredTools; the execute path stored raw configs. The fix should have been at the boundary where tool_lookup is populated, not downstream where tool_config is consumed. Classic `normalize at the boundary`.

## Trap: mock_escape_hatch (minor)

Three tests in `test_conversation_memory.py` patched `yamlgraph.tools.agent.execute_shell_tool` — the old import site. After the refactor removed that import, the tests broke with `AttributeError`. The patch target had to follow the execution path to `yamlgraph.tools.tool_builders.execute_shell_tool`. Lesson: mock at the call site, not the re-export site. When you move execution behind a wrapper, the mock must follow.

## FR-661: The Free Lunch

`loop_detector.py` was extracted from `graph_loader.py` in FR-658 but never registered in `.importlinter`. It passed the three-layer contract only because unlisted modules are unconstrained. One line added to Layer 3. The cost of not doing it: a future `from yamlgraph.executor import ...` inside `loop_detector.py` would silently violate the architecture. Detection without enforcement is advisory.

## Heuristic

When a new tool type requires integration in N places (N > 1), the abstraction boundary is in the wrong place. The wrapper that normalizes external variation (StructuredTool) should also be the execution interface.

**Seed:** The `success = not output.startswith("Error: ")` heuristic is fragile — what if a tool legitimately returns output starting with "Error: "? Should StructuredTool wrappers raise on failure instead of returning error strings, and let the agent loop catch and format?
