# Reflection: FR-355 Watcher2 Sanity Check

**Date:** 2026-05-08
**FR:** FR-355 — MCP startup schema validation gate (exclude invalid tools before serving)
**Reviewer:** watcher2 post-validate sanity review

## Trap

`downstream_fix` confirmed avoided: rather than patching individual graph YAML files,
the implementation normalized schema quality at the derivation boundary (`discovery.py`)
and added an exclusion gate at the registration boundary (`mcp_server.py`). This is the
canonical "normalize at the boundary" cure.

`partial_remediation` also avoided: both the root-cause derivation fix (`_build_property_schema`
emitting valid `items`/`additionalProperties`) and the defense-in-depth gate
(`_validate_input_schema` + `_partition_graphs_by_schema`) were delivered together.

## What Happened

FR-355 implementation is proportional and complete:

- **534 lines changed** across 11 files, with ~180 in the new acceptance test file and
  ~170 in the two core files (`discovery.py`, `mcp_server.py`). Ancillary artifacts
  (changelog fragment, confessions, docs) account for the remainder. Scope is tight.

- **All 4 acceptance criteria covered by tests:**
  - AC-01 (REQ-YG-311): `test_all_discovered_schemas_valid` — scans default-pattern
    discovery for invalid schemas; passes (meaning all discovered graphs now produce valid schemas).
  - AC-02 (REQ-YG-312): `test_array_without_items_excluded` — asserts invalid tool
    absent from MCP `tools/list`.
  - AC-03 (REQ-YG-312): `test_invalid_schema_exclusion_logs_warning` — asserts
    `logger.warning` called with correct graph name and reason.
  - AC-04 (REQ-YG-310): `test_collect_keys_excluded_from_inputs` — asserts map `collect`
    keys absent from `input_vars`, `properties`, and `required`.

- **Tests pass (4/4)** confirming GREEN state after implementation.

- **No pipeline log evidence** available (no `logs/fsm-pipeline-*.log` found in
  worktree). Assessment based on diff + test run only.

## Root Cause (of original defect)

`_build_input_schema()` in `discovery.py` mapped Python types to JSON Schema types
without appending child keywords (`items` for arrays, `additionalProperties` for
objects). Additionally, `_extract_input_vars()` only excluded `state_key` outputs,
missing `collect` keys produced by map nodes.

## What Worked

- Defense-in-depth: derivation fixed + registration gated. Neither alone would satisfy
  the FR's objectives.
- Exclude-and-warn strategy is consistent with existing YAML-discovery behavior (skip
  bad files with warning, don't crash server).
- `_split_top_level_args` bracket-aware parser replacing `re.split` avoids the
  `regex_fourth_exclusion` trap for nested generics like `dict[str, list[int]]`.
- Test assertions check observable MCP behavior (tool names in `tools/list`, warning
  call args), not internal implementation details.

## Seed

If `_validate_input_schema` in `mcp_server.py` and `_build_property_schema` in
`discovery.py` are independently maintained, their rules could silently diverge — a
graph could pass the gate while still generating a structurally questionable schema.
Should the validation rules be expressed as a shared specification (e.g., a
`SCHEMA_CONSTRAINTS` registry) that both the generator and the gate reference, so
the two layers are mechanically kept in sync?
