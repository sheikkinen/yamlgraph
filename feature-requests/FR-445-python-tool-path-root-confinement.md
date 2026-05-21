# Feature Request: FR-445 Python Tool Path Root Confinement for File-Based Tools

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 day
**Requested:** 2026-05-21

## Summary

Constrain `type: python` file-path tools (`config.path`) to the graph root directory so tool loading is deterministic and cannot escape the graph boundary via relative traversal or absolute out-of-root paths.

## Value Statement

Graph authors get reproducible, graph-scoped Python tool loading with clear failure messages when a tool path escapes the graph directory.

## Problem

`yamlgraph/tools/python_tool.py` currently resolves file-based tool paths with:

```python
resolved = Path(config.path).resolve()
```

This resolves relative to process CWD, not graph location. Effects:

1. Tool loading depends on where the process is launched from, weakening reproducibility.
2. A path like `../outside.py` can resolve outside graph scope.
3. `graph_root` is already available and passed through call sites (`graph_loader`, `node_compiler`, `map_compiler`, `tools/agent`) but is not enforced for `PythonToolConfig.path`.

## Research

### Existing prior art in this codebase

1. **`schema_loader` already enforces graph-root confinement**
   `yamlgraph/tools/schema_loader_tool.py::_resolve_schema_path()` resolves under `graph_root` and rejects escapes with `resolved.relative_to(graph_root)`.
2. **Python tool loading already has graph context available**
   `load_python_function(..., graph_root=...)` is called with graph-root context from:
   - `yamlgraph/graph_loader.py::_parse_all_tools()`
   - `yamlgraph/node_compiler.py::_compile_python_node()`
   - `yamlgraph/map_compiler.py::compile_map_node()`
   - `yamlgraph/tools/agent.py::build_python_tool()`
3. **Current requirement mismatch**
   `REQ-YG-196` and `tests/unit/test_python_nodes.py` currently describe/verify CWD-relative behavior for file-based Python tool paths.

### Is this already solved?

Partially. Graph-root boundary enforcement exists for `schema_loader` tools, but not for generic file-based Python tools.

## Objectives

1. Enforce graph-root confinement for `PythonToolConfig.path`.
2. Fail fast with explicit error when path escapes root.
3. Preserve existing module-based (`config.module`) loading behavior.
4. Keep scope limited to path resolution/validation semantics.

## Constraints

1. Single responsibility: path resolution and boundary validation only.
2. No silent fallback to CWD when graph-root confinement is expected.
3. Error messages must include path, graph root, and resolved path.
4. Follow existing boundary-normalization pattern used by `schema_loader`.

## Proposed Solution

1. In `yamlgraph/tools/python_tool.py`, apply graph-root-aware resolution for `config.path`:
   - Resolve relative paths against `graph_root`.
   - Validate `resolved.relative_to(graph_root)` to reject escapes.
   - Allow absolute paths only when they remain inside `graph_root`.
2. Raise clear `ValueError` when path escapes root.
3. Keep `FileNotFoundError` for in-root but missing files.
4. Keep `config.module` loading unchanged.
5. Align requirement text for Python file-path loading semantics to graph-root confinement (update `REQ-YG-196` wording in architecture/capability docs).

```yaml
# Example (valid when helper.py is under the graph directory)
tools:
  helper_tool:
    type: python
    path: tools/helper.py
    function: run
```

## Acceptance Criteria

- [x] AC-01: Relative in-root `config.path` loads successfully when resolved from graph root.
- [x] AC-02: Relative escape path (for example `../outside.py`) is rejected with explicit escape error.
- [x] AC-03: Absolute out-of-root path is rejected with explicit escape error.
- [x] AC-04: Absolute in-root path is allowed.
- [x] AC-05: Module-based Python tool loading (`config.module`) behavior is unchanged.
- [x] AC-06: Failure occurs at tool load/compile time, not deferred to node execution.
- [x] AC-07: Tests cover both pass and fail path-boundary cases.
- [x] AC-08: Requirement docs are updated to reflect graph-root semantics (not CWD semantics).

## Failing Acceptance Tests (RED)

RED test file:

- `tests/unit/test_fr445_python_tool_graph_root_confinement_red.py`

RED tests:

1. `test_ac01_relative_in_root_path_loads_from_graph_root`
2. `test_ac02_relative_escape_path_is_rejected`
3. `test_ac03_absolute_out_of_root_path_is_rejected`
4. `test_ac04_absolute_in_root_path_is_allowed`
5. `test_ac05_module_loading_unchanged`

RED command:

```bash
pytest tests/unit/test_fr445_python_tool_graph_root_confinement_red.py -q --no-cov
```

Current RED state:

- `test_ac01_relative_in_root_path_loads_from_graph_root` fails with `FileNotFoundError` because path resolution uses CWD instead of graph root.
- `test_ac02_relative_escape_path_is_rejected` and `test_ac03_absolute_out_of_root_path_is_rejected` fail with `DID NOT RAISE ValueError` because out-of-root paths are currently allowed.

## Alternatives Considered

1. **Keep CWD-relative behavior and document it.** Rejected: does not address boundary safety or reproducibility.
2. **Constrain to repository root instead of graph root.** Rejected: weaker boundary than graph-scoped execution and less aligned with graph portability.
3. **Add an opt-out flag for unsafe paths.** Rejected: increases surface area for a bug fix whose desired behavior is unambiguous.

## Related

- Issue: https://github.com/sheikkinen/yamlgraph/issues/439
- `yamlgraph/tools/python_tool.py`
- `yamlgraph/tools/schema_loader_tool.py`
- `yamlgraph/graph_loader.py`
- `yamlgraph/node_compiler.py`
- `yamlgraph/map_compiler.py`
- `yamlgraph/tools/agent.py`
- `tests/unit/test_python_nodes.py`
