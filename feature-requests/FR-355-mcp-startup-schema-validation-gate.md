# Feature Request: FR-355 MCP startup schema validation gate (exclude invalid tools before serving)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-08

## Summary

Add a startup validation gate in `yamlgraph/mcp_server.py` so discovered graphs with invalid `input_schema` are excluded (with warnings) instead of being exposed as MCP tools and causing Copilot to reject the whole server.

## Value Statement

Copilot users keep access to valid YAMLGraph MCP tools even when one graph generates a broken schema.

## Problem

`create_server()` currently registers every discovered graph tool without validating `input_schema`. If any graph emits invalid JSON Schema (notably arrays without `items`), Copilot fails MCP initialization for the entire server, not just that graph.

Additionally, `_extract_input_vars()` in `yamlgraph/discovery.py` only treats `state_key` as output and misses map-node `collect` outputs, so `collect` keys can be exposed as required user inputs.

## Research: Existing Patterns, Evidence, and Gaps

1. **Current MCP registration path has no schema gate.**
   - `yamlgraph/mcp_server.py:create_server()` appends all discovered per-graph tools directly from `g["input_schema"]`.
2. **Schema derivation is centralized and currently permissive.**
   - `yamlgraph/discovery.py` builds `input_schema` from `input_vars` and type mapping (`list -> array`, `dict -> object`) with no schema-shape validation step.
3. **Output-key extraction misses map `collect`.**
   - `_extract_input_vars()` excludes only top-level `state_key` targets.
4. **Repository evidence confirms this is not already solved in this worktree.**
   - No startup schema validation helper exists in MCP server or discovery.
   - Local discovery scan on default graph patterns found multiple invalid schemas (including `animated-character-storyboard` exposing `animated_panels` as array input without `items`).
5. **Prior-art behavior supports exclude-and-warn strategy.**
   - Discovery already skips malformed YAML with warnings instead of crashing startup.

## Objectives

1. Prevent invalid `input_schema` tools from being served through MCP `tools/list`.
2. Preserve server availability by excluding invalid tools with explicit startup warnings.
3. Ensure map `collect` targets are classified as outputs, not user inputs.

## Constraints

1. **Single responsibility:** startup MCP tool-schema hardening only.
2. **No runtime invocation changes:** graph execution flow remains unchanged.
3. **No new dependencies:** implement schema checks with lightweight in-repo validation logic.
4. **Explicit visibility:** each exclusion must produce a warning with graph name and validation reason.

## Proposed Solution

### In scope

1. Add MCP startup schema validation before per-graph tool registration.
2. Validate each graph `input_schema` with at least these rules:
   - Array properties (`"type": "array"`) must include `"items"`.
   - Object properties (`"type": "object"`) should include `"properties"` or `"additionalProperties"`.
   - Every entry in `"required"` must exist in `"properties"`.
3. Exclude invalid graphs from MCP typed-tool lookup and `tools/list` output.
4. Log one WARNING per excluded graph with graph name and validation errors.
5. Fix `_extract_input_vars()` to treat map-node `collect` keys as output keys.
6. Add acceptance tests for schema validity scan, startup exclusion, and collect-key handling.

### Out of scope

1. Refactoring all graph state type annotations across examples.
2. New CLI flags or configuration toggles for schema validation behavior.
3. Changes to A2A protocol behavior in this FR.

## Requirement Mapping (existing capability extension)

This FR extends existing MCP typed-tool requirements:

- **REQ-YG-310**: input/output separation in discovery (expand to include map `collect`)
- **REQ-YG-311**: JSON Schema quality for derived input properties
- **REQ-YG-312**: per-graph MCP tool registration behavior (register only valid schemas)

## Acceptance Criteria

- [x] **AC-01 (REQ-YG-311):** Discovered graph `input_schema` values satisfy startup validation rules used by MCP registration.
- [x] **AC-02 (REQ-YG-312):** MCP `tools/list` excludes graphs whose `input_schema` fails validation.
- [x] **AC-03 (REQ-YG-312):** Startup logs one WARNING per excluded graph with graph name and validation reason(s).
- [x] **AC-04 (REQ-YG-310):** Map-node `collect` keys are excluded from `input_vars`, `input_schema.properties`, and `required`.
- [x] **AC-05:** RED acceptance tests are present and fail before implementation for the intended reasons.

## Failing Acceptance Tests (RED)

RED artifact added in this planning change:

- `tests/unit/test_fr355_mcp_schema_validation_gate_red.py`

Planned RED tests:

1. `test_all_discovered_schemas_valid`
2. `test_array_without_items_excluded`
3. `test_collect_keys_excluded_from_inputs`

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr355_mcp_schema_validation_gate_red.py -q --no-cov
```

## Alternatives Considered

1. **Fail-fast startup (raise on first invalid graph)**
   - Rejected: one invalid graph would still take down all MCP tools.
2. **Rely solely on root-cause fixes (e.g., #354)**
   - Rejected: does not provide defense-in-depth for future schema regressions.
3. **Add external JSON Schema validator dependency**
   - Rejected for this scope: startup gate can be implemented with minimal built-in checks and no dependency churn.

## Related

- Issue #355: <https://github.com/sheikkinen/yamlgraph/issues/355>
- Issue #354: <https://github.com/sheikkinen/yamlgraph/issues/354>
- `yamlgraph/mcp_server.py`
- `yamlgraph/discovery.py`
- `tests/unit/test_mcp_typed_tools.py`
- `tests/unit/test_mcp_server.py`
