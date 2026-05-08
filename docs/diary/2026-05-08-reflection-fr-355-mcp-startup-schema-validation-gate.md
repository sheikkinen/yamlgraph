# Reflection: FR-355 MCP Startup Schema Validation Gate

**Date:** 2026-05-08
**FR:** FR-355 — MCP startup schema validation gate (exclude invalid tools before serving)
**Reviewer:** watcher2 post-implement reflection

## Trap

`downstream_fix`: the previous behavior registered every discovered graph as an MCP tool
without validating the schema shape. When Copilot encountered an invalid `input_schema`
(array property without `items`), it rejected the entire server — not just the bad graph.
Adding a startup gate at the registration boundary (in `create_server()`) instead of
patching individual graph YAML files is the canonical normalize-at-the-boundary cure.

`partial_remediation`: fixing only the MCP registration path without also fixing the root
cause in `discovery.py` would have left the schema derivation silently generating invalid
schemas. Both layers required attention: derive valid schemas in discovery and gate
invalid ones at registration.

## What Happened

FR-355 added two coordinated changes:

1. **`yamlgraph/discovery.py`**: `_extract_input_vars()` now treats map-node `collect`
   keys as output keys (excluded from `input_vars`). `_build_input_schema()` now
   generates valid JSON Schema shapes — array properties include `"items": {}`, object
   properties include `"additionalProperties": {}`.

2. **`yamlgraph/mcp_server.py`**: `_validate_input_schema()` runs lightweight structural
   checks (array→items, object→properties/additionalProperties, required→properties
   membership). `create_server()` skips graphs that fail validation and logs one WARNING
   per exclusion with graph name and reasons.

Four acceptance tests pass, each tagged with the relevant REQ-YG-3xx and covering:
schema validity scan, array-without-items exclusion, collect-key exclusion from inputs,
and startup warning emission.

## Root Cause (of the original defect)

`_build_input_schema()` in discovery used a simple type-mapping table
(`list → array`, `dict → object`) without appending required child keywords. JSON Schema
mandates `items` for `type: array` and at minimum `additionalProperties` for
`type: object` to be structurally valid under strict validators. The fix adds these
defaults at the derivation boundary, not as post-hoc patches in callers.

## What Worked

- Defense-in-depth: schema quality fixed in derivation AND gated at registration ensures
  existing broken schemas in example graphs are excluded without crashing startup.
- Exclude-and-warn strategy (not fail-fast) preserves server availability when one graph
  is invalid — consistent with the existing pattern for malformed YAML discovery.
- No new dependencies: validation logic is ~15 lines of structural dict inspection.
- `collect` key exclusion is backward-compatible: map nodes that produce `collect`
  outputs were already being misclassified; correcting this only removes false positives
  from `input_vars`.

## Seed

If the schema validation rules in `_validate_input_schema()` diverge from the schema
derivation rules in `_build_input_schema()` over time (e.g., one is updated without the
other), invalid schemas could slip through. Should validation be driven by the same
derivation spec — perhaps a shared `SCHEMA_SHAPE_RULES` dict — so the gate and the
generator stay in sync without manual coordination?
