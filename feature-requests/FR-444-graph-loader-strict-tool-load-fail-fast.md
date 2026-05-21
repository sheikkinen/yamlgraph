# Feature Request: FR-444 Graph Loader Strict Mode for Python Tool Load Failures

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-21

## Summary

Add an explicit strict/fail-fast mode for Python tool loading in `yamlgraph/graph_loader.py` so broken tool imports fail compilation instead of silently degrading runtime behavior.

## Value Statement

Graph authors get compile-time feedback for broken Python tool wiring, preventing late runtime failures that are harder to diagnose.

## Problem

The GH-437 topic identifies a specific gap: `_parse_all_tools()` currently catches Python tool load errors and logs warnings, then continues compilation.

Current behavior in `yamlgraph/graph_loader.py`:

1. Parse Python tool configs.
2. Attempt to load each tool into `callable_registry`.
3. On import/attribute/type errors, log warning and continue.

This is risky for `type: tool_call` flows: runtime then receives `Unknown tool` responses from `create_tool_call_node()` even though the real defect happened earlier during compilation.

## Research Findings

1. **Topic source:** `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-437.md`.
2. **Root behavior:** `yamlgraph/graph_loader.py::_parse_all_tools()` catches load exceptions and warns (`logger.warning("Failed to load tool ...")`) instead of failing.
3. **Runtime symptom:** `yamlgraph/node_factory/tool_nodes.py` returns `success=False, error="Unknown tool: ..."` when tool name is missing from registry.
4. **Prior art for load failures:** `tests/unit/test_python_nodes.py` validates `load_python_function()` raises on invalid module/function, but there is no graph-compilation contract that surfaces those failures early.
5. **Shared loading path:** FR-426 integrated `schema_loader` into the same loader path (`load_python_function`), so the strict-mode decision must be applied at the graph-loader boundary for consistency.

## Objectives

1. Make tool-load failure policy explicit and configurable.
2. Support fail-fast compilation for broken Python tool imports.
3. Preserve an opt-out warn-and-continue mode for graphs that intentionally tolerate partial registries.
4. Keep the change scoped to tool loading behavior in graph compilation.

## Constraints

1. Single responsibility: tool-loading policy only (no node-type redesign).
2. No silent fallback in strict mode: compilation must fail with actionable error context.
3. Non-strict mode must preserve current behavior semantics.
4. Keep architecture boundaries intact (`graph_loader` + tool loader path only).

## Proposed Solution

Introduce graph-level tool-load policy in `config:`:

```yaml
config:
  tool_load_mode: strict  # strict | warn
```

### Policy contract

1. `tool_load_mode: strict` → if any Python tool fails to load, `compile_graph()` raises with a message listing failing tool names and root causes.
2. `tool_load_mode: warn` → keep current behavior (warning + continue) and compile successfully with a partial callable registry.
3. Default policy is explicit and documented as **strict** (fail-fast) unless graph author opts into `warn`.

### Scope details

1. Implement policy evaluation in `GraphConfig` + `_parse_all_tools()`.
2. Accumulate failures across all Python tools before raising so users get one actionable compile error.
3. Keep existing warning logging behavior in `warn` mode.
4. Document configuration and migration guidance for graphs that previously relied on warn-and-continue behavior.

## Acceptance Criteria

- [x] **AC-01:** Default policy fails compilation when a Python tool cannot be imported.
- [x] **AC-02:** Explicit `tool_load_mode: strict` fails compilation and the error message includes every failed tool name.
- [x] **AC-03:** Explicit `tool_load_mode: warn` preserves compile success and unresolved tools remain runtime `Unknown tool` responses in `tool_call` nodes.
- [x] **AC-04:** `warn` mode still emits warning logs for each failed tool load.
- [x] **AC-05:** User-facing docs describe `tool_load_mode` and strict-vs-warn behavior.

## Failing Acceptance Tests (RED)

RED tests are defined in:

- `tests/unit/test_fr444_graph_loader_tool_load_mode_red.py`

RED test cases:

1. `test_ac01_default_mode_is_strict_and_fails_on_broken_python_tool`
2. `test_ac02_strict_mode_reports_all_failed_tools`
3. `test_ac03_warn_mode_compiles_and_returns_runtime_unknown_tool_error`

RED command:

```bash
pytest tests/unit/test_fr444_graph_loader_tool_load_mode_red.py -q --no-cov
```

Expected RED state in this planning cycle: strict-mode expectations fail because current graph-loader behavior still warns and continues.

## Requirement Traceability Plan

Reserve and implement:

1. **REQ-YG-420** — Graph compilation enforces strict tool-load failure policy (default strict).
2. **REQ-YG-421** — Graph compilation supports explicit warn mode for legacy/non-strict tool-load behavior.

During enforcement:

1. Add capability file for the new contract.
2. Add REQ-YG-420 and REQ-YG-421 entries to `ARCHITECTURE.md`.
3. Keep RED/GREEN tests tagged to the new requirement IDs.

## Alternatives Considered

1. **Keep warn-and-continue only (status quo).** Rejected: defers defects to runtime.
2. **Always strict with no warn mode.** Rejected: larger migration blast radius than required for this bug fix.
3. **Linter-only detection of bad tool modules.** Rejected: lint cannot fully replace runtime import checks and does not guarantee compile-time failure semantics.

## Judge Notes

**2026-05-21 — APPROVED**

- RED tests verified: `test_ac01` and `test_ac02` fail with `DID NOT RAISE ValueError` (correct symptom — missing implementation, not fixture issues). `test_ac03` passes because warn-and-continue is current behavior.
- Classification: **Framework primitive** — compile-time contract enforcement for tool loading affects every graph using Python tools.
- Minor gap: AC-04 (warn mode emits warning logs) has no dedicated `caplog` test. Implementation can add one during GREEN; not a blocker.
- Scope is frozen. Authority to implement is granted.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-437.md`
- `yamlgraph/graph_loader.py`
- `yamlgraph/tools/python_tool.py`
- `yamlgraph/node_factory/tool_nodes.py`
- `tests/unit/test_python_nodes.py`
- `feature-requests/FR-426-schema-loader-tool-type.md`
