# Feature Request: FR-204 Fix E102 false positives for `output_schema:` and `route_field`

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-30

## Summary

The E102 linter check in `check_router_schema_fields()` produces false positives on valid router configurations that use `output_schema:` (JSON Schema format) or `route_field` (explicit routing field override).

## Value Statement

Graph authors get accurate lint feedback — valid router configurations pass E102 without suppression — reducing confusion when building routers with `output_schema:` or non-default routing fields.

## Problem

`check_router_schema_fields()` in `yamlgraph/linter/patterns/router.py` has two defects:

### 1. Only reads `schema:` format; ignores `output_schema:`

The linter reads schema exclusively via `prompt_data.get("schema", {})`. The runtime (`yamlgraph/schema_loader.py` lines 253–265) supports both:

- `schema:` — native YAMLGraph format with `fields:` dict
- `output_schema:` — JSON Schema format with `properties:` dict

Prompts that use `output_schema:` appear to have no schema fields, so E102 always fires — even when the prompt is valid and the graph compiles and runs correctly.

### 2. Hardcodes `intent`/`tone`; ignores `route_field`

The linter requires `intent` or `tone` in schema fields. The runtime (`yamlgraph/node_factory/llm_nodes.py` lines 128, 264–269) supports `route_field` — an explicit node config key naming which schema field to route on (e.g. `route_field: priority`). When set, the runtime extracts the route from that field, not from `intent`/`tone`. The linter should validate that the named `route_field` exists in the schema instead of checking hardcoded names.

**Affected nodes in `projects/ninchat_voice/graphs/navigator/graph.yaml`:**

| Node | Prompt schema format | Route field | Current E102 result |
|------|---------------------|-------------|---------------------|
| `classify` | `output_schema:` with `intent` | `route_field: intent` | FALSE POSITIVE |
| `classify_priority` | `output_schema:` with `priority` | `route_field: priority` | FALSE POSITIVE |
| `route_by_intent` | `output_schema:` with `route` | `route_field: route` | FALSE POSITIVE |

All three compile and run correctly at runtime.

## Proposed Solution

Modify `check_router_schema_fields()` in `yamlgraph/linter/patterns/router.py`:

### Step 1 — Read fields from both schema formats

```python
schema = prompt_data.get("schema", {})
output_schema = prompt_data.get("output_schema", {})

if schema:
    fields = schema.get("fields", {})
elif output_schema:
    fields = output_schema.get("properties", {})
else:
    fields = {}
```

### Step 2 — When `route_field` is set, validate it exists in fields

```python
route_field = node_config.get("route_field")

if route_field:
    # Validate route_field names an actual schema field
    if route_field not in fields:
        available_fields = list(fields.keys())
        issues.append(LintIssue(
            severity="error",
            code="E102",
            message=f"Router node '{node_name}' route_field '{route_field}' not found in prompt schema",
            fix=f"Add '{route_field}' field to schema (available: {available_fields}).",
        ))
else:
    # Fallback: require 'intent' or 'tone'
    if "intent" not in fields and "tone" not in fields:
        available_fields = list(fields.keys())
        issues.append(LintIssue(
            severity="error",
            code="E102",
            message=f"Router node '{node_name}' prompt schema missing 'intent' or 'tone' field",
            fix=f"Add 'intent' field to schema or set route_field (available: {available_fields}).",
        ))
```

Update the docstring to reflect the expanded semantics.

## Acceptance Criteria

- [ ] `yamlgraph graph lint` passes (no E102) on a router node whose prompt uses `output_schema:` with `intent` field
- [ ] `yamlgraph graph lint` passes (no E102) on a router node with `route_field: priority` whose prompt `output_schema:` contains `priority`
- [ ] `yamlgraph graph lint` passes (no E102) on a router node with `route_field: route` whose prompt `output_schema:` contains `route`
- [ ] `yamlgraph graph lint` still reports E102 when `route_field` names a field absent from the schema
- [ ] `yamlgraph graph lint` still reports E102 when no `route_field` and neither `intent` nor `tone` appears in the schema (both `schema:` and `output_schema:` formats)
- [ ] All existing router linter tests pass unchanged
- [ ] New unit tests added covering: `output_schema:` format, `route_field` valid, `route_field` invalid, no schema at all
- [ ] `req_coverage.py` passes (new tests tagged with appropriate REQ-YG-XXX)

## Alternatives Considered

**Suppress E102 with `# noqa`** — rejected; suppression hides real errors and violates confession policy (CONF-XXX burden without real sin).

**Update graph YAML to use `schema:` format** — rejected; `output_schema:` (JSON Schema) is a first-class supported format at runtime and the linter must honour it.

## Related

- `yamlgraph/linter/patterns/router.py` — `check_router_schema_fields()` (lines 66–128)
- `yamlgraph/schema_loader.py` (lines 253–265) — dual-format schema loading at runtime
- `yamlgraph/node_factory/llm_nodes.py` (lines 128, 264–269) — `route_field` runtime handling
- `projects/ninchat_voice/graphs/navigator/graph.yaml` — three affected router nodes
- `tests/unit/test_router_linter.py` — existing router linter tests (extend here)
