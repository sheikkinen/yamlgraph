# Feature Request: FR-426 Declarative `schema_loader` Tool Type

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1.5 days
**Requested:** 2026-05-20

## Summary

Add a built-in `type: schema_loader` tool that loads questionnaire/data-collection YAML schemas into graph state, replacing repeated custom Python loader functions.

## Value Statement

Graph authors get one deterministic, secure schema-loading primitive instead of copying near-identical loaders across projects.

## Problem

Issue `.chaplain/processing/gh-420.md` describes repeated `load_schema` / `load_and_merge` patterns for schema-driven questionnaires. Core primitives currently do not cover this pattern end-to-end:

1. `data_files` (`yamlgraph/data_loader.py`) loads static files at graph load time, but not state-driven topic lists.
2. `type: python` tooling (`yamlgraph/tools/python_tool.py`) requires project-local function code for every schema-loading graph.
3. Tool parsing only recognizes `type: python` (`parse_python_tools`) and shell-style tools (`tools.shell.parse_tools`), so schema-loader config has no typed registry path.

Result: duplicated code and behavior drift in merge order, deduplication, and path safety.

## Research Findings

1. Topic source read from `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-420.md`.
2. `yamlgraph/graph_loader.py::_parse_all_tools` currently composes shell + python registries only.
3. `yamlgraph/data_loader.py` already defines the required security invariant: graph-relative path resolution with traversal rejection via `relative_to`.
4. `tests/unit/test_data_loader.py` provides prior-art test shape for traversal, missing-file, and graph-relative semantics.
5. No existing built-in `schema_loader` tool type exists in core.

## Objectives

1. Support single-schema loading from `path` into `state[state_key]`.
2. Support merge loading from state-driven topics (`paths_from_state` + `schema_dir` + `suffix`).
3. Guarantee deterministic deduplication by `deduplicate_by` (default `id`) and additive merge semantics.
4. Preserve graph-relative path safety independent of process CWD.

## Constraints

1. Single responsibility: tool primitive only (no new node type).
2. Keep deterministic Python behavior; no LLM or fuzzy merge logic.
3. Keep existing shell tools and `type: python` tool contracts unchanged for non-schema-loader tools.
4. Fail loudly on invalid config and missing files (no silent empty fallbacks).

## Proposed Solution

Introduce `type: schema_loader` under `tools:` and implement a dedicated parser + typed config path.

### YAML usage (single-file mode)

```yaml
tools:
  load_fields:
    type: schema_loader
    path: schemas/symptom.yaml
    state_key: schema
```

### YAML usage (state-driven merge mode)

```yaml
tools:
  load_merged:
    type: schema_loader
    paths_from_state: active_topics
    schema_dir: schemas
    suffix: ".yaml"
    state_key: schema
    deduplicate_by: id
    merge_mode: additive
```

### Implementation contract

1. Add `yamlgraph/tools/schema_loader_tool.py` with:
   - `SchemaLoaderToolConfig` dataclass:
     - `state_key: str`
     - `path: str | None = None`
     - `paths_from_state: str | None = None`
     - `schema_dir: str | None = None`
     - `suffix: str = ".yaml"`
     - `deduplicate_by: str = "id"`
     - `merge_mode: str = "additive"`
   - `parse_schema_loader_tools(tools_config) -> dict[str, SchemaLoaderToolConfig]`
   - runtime callable builder for schema-loader tools.
2. Validation rule: exactly one of `path` or `paths_from_state` must be configured.
3. `graph_root` is captured at compile time (closure) from `config.source_path.parent.resolve()`, matching `data_loader` graph-relative behavior.
4. In merge mode, field order is deterministic: existing `state[state_key]["fields"]` first (additive), then newly loaded topic fields in input topic order, deduplicated by `deduplicate_by`.
5. File loading errors and traversal violations raise explicit exceptions with actionable messages.

## Acceptance Criteria

- [x] **AC-01:** `parse_schema_loader_tools()` recognizes `type: schema_loader` and returns typed `SchemaLoaderToolConfig` entries.
- [x] **AC-02:** Single-file mode loads graph-relative YAML path and writes schema to configured `state_key`.
- [x] **AC-03:** Merge mode loads all files from `paths_from_state` + `schema_dir` + `suffix`.
- [x] **AC-04:** Merge mode deduplicates by `deduplicate_by` and preserves additive order with pre-existing fields first.
- [x] **AC-05:** Missing schema files raise explicit errors (no silent fallback).
- [x] **AC-06:** Path traversal outside graph root is rejected.
- [x] **AC-07:** Schema paths resolve relative to graph file location, not process CWD.
- [x] **AC-08:** Invalid schema-loader config using both `path` and `paths_from_state` raises validation error.

## Failing Acceptance Tests (RED)

RED tests are defined in:

- `tests/unit/test_fr426_schema_loader_tool_type_red.py`

RED test cases:

1. `test_ac01_parse_schema_loader_tool_type_returns_typed_config`
2. `test_ac02_single_path_loads_schema_into_state_key`
3. `test_ac03_merge_paths_from_state_with_dedup_and_additive`
4. `test_ac04_missing_schema_file_raises_explicit_error`
5. `test_ac05_path_traversal_is_rejected`
6. `test_ac06_paths_resolve_relative_to_graph_root_not_cwd`
7. `test_ac07_rejects_configs_with_both_path_and_paths_from_state`

RED command:

```bash
pytest tests/unit/test_fr426_schema_loader_tool_type_red.py -q --no-cov
```

Observed RED state in this planning cycle: parser/type support is missing and schema-loader tools are not present in python tool registry, so the acceptance suite fails.

## Requirement Traceability Plan

Reserve and implement:

1. **REQ-YG-417** — Schema-loader typed config parsing, validation, and single-file loading contract.
2. **REQ-YG-418** — Merge-mode semantics (`paths_from_state`, deduplication, additive ordering, graph-root safety).

During enforcement:

1. Add capability file `capabilities/CAP-155-schema-loader-tool-type.yaml`.
2. Add REQ-YG-417 and REQ-YG-418 rows to `ARCHITECTURE.md`.
3. Keep RED/GREEN tests tagged with the new requirement IDs.

## Alternatives Considered

1. **Keep project-local Python loader functions (status quo).**
   Rejected: continues duplication and drift.
2. **Use only `data_files`.**
   Rejected: cannot support state-driven topic-based schema selection.
3. **Add a dedicated node type (`type: schema_loader_node`).**
   Rejected: unnecessary surface expansion; this is a tool concern.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-420.md`
- `yamlgraph/graph_loader.py`
- `yamlgraph/tools/python_tool.py`
- `yamlgraph/data_loader.py`
- `tests/unit/test_data_loader.py`

## Judge Notes

**Date:** 2026-05-20
**Verdict:** APPROVE

**Assessment:**

1. **Scope — clear and minimal.** Single responsibility: one new tool type, no new node type, no changes to existing tool contracts. The `_parse_all_tools` integration point in `graph_loader.py` is the only composition site that needs updating.

2. **No contradictions.** The validation invariant (exactly one of `path` or `paths_from_state`) is explicit and directly tested. Path safety delegates to the `data_loader` prior-art pattern.

3. **Acceptance criteria are measurable.** Eight AC items with concrete, deterministic observable outcomes. The merge-order assertion (`["existing_field", "subject_person", "symptom", "appointment_time"]`) is unambiguous.

4. **Feasibility confirmed.** `data_loader.py` already carries the graph-relative path safety primitives; `parse_python_tools` provides a template for the new `parse_schema_loader_tools` function. Estimated 1.5 days is credible.

5. **Architecture-aligned.** Tool primitive only; stays within Layer 3. Three-layer boundary is not crossed. Import-linter constraints are not threatened.

6. **Classification: Framework primitive.** Schema-driven questionnaire loading is a recurring pattern (gh-420). Neither `data_files` (static, not state-driven) nor `type: python` (requires project-local code) covers the full contract. This closes a genuine gap without over-engineering.

7. **RED tests fail for the correct reason.** All 7 tests fail with `ModuleNotFoundError: No module named 'yamlgraph.tools.schema_loader_tool'` — missing implementation, not missing fixtures or infrastructure. Canonical RED.

**Minor observation (cosmetic, no amendment required):** FR lists 8 acceptance criteria (AC-01–AC-08) but the RED test cases section lists 7 functions (ac01–ac07). AC-03 and AC-04 of the FR are both exercised by `test_ac03_merge_paths_from_state_with_dedup_and_additive`. The test file numbering and the AC list are both internally consistent; the off-by-one is cosmetic.

**Authority granted.** Proceed to enforce.

## Implementation Notes (Enforce)

1. Added `yamlgraph/tools/schema_loader_tool.py` with:
   - `SchemaLoaderToolConfig`
   - `parse_schema_loader_tools()`
   - `build_schema_loader_tool()` runtime callable builder
2. Integrated schema-loader tools into compilation/runtime flow:
   - `yamlgraph/graph_loader.py` now parses schema_loader tools and merges them into the python tool registry.
   - `yamlgraph/tools/python_tool.py` now resolves both `PythonToolConfig` and `SchemaLoaderToolConfig`.
   - `yamlgraph/node_compiler.py`, `yamlgraph/map_compiler.py`, and `yamlgraph/tools/agent.py` now pass graph-root context for graph-relative schema path resolution.
3. Traceability artifacts added:
   - `capabilities/CAP-155-schema-loader-tool-type.yaml`
   - `ARCHITECTURE.md` entries for `REQ-YG-417` and `REQ-YG-418`
   - `changelog/unreleased/fr-426-schema-loader-tool-type.md`
