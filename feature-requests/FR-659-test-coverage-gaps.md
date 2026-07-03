# Feature Request: FR-659 Test Coverage Gaps in Guard Evaluator, Subgraph Nodes, and Schema Loader Tool

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 day
**Requested:** 2026-07-03
**Judged:** 2026-07-03
**Enforced:** 2026-07-03

## Summary

Three modules have significant test coverage gaps: `guard_evaluator.py` (73%), `schema_loader_tool.py` (83%), and `subgraph_nodes.py` (81%). Overall coverage is 90% — these three files account for a disproportionate share of uncovered lines.

## Value Statement

Closing coverage gaps on security-relevant and boundary-heavy modules reduces the risk of silent regressions in expression evaluation, subgraph state mapping, and tool schema validation.

## Problem

Coverage audit on 2026-07-03 (4502 passed, 90% total):

| File | Coverage | Missing Lines | Risk |
|------|----------|---------------|------|
| `utils/guard_evaluator.py` | 73% | 35 | **High** — expression evaluator is a security boundary; most comparison operators and evaluator methods untested |
| `tools/schema_loader_tool.py` | 83% | 22 | Medium — validation error branches for malformed config untested |
| `node_factory/subgraph_nodes.py` | 81% | 14 | Medium — `_map_output_state` auto/* untested; GraphInterrupt handler deferred |

Note: `graph_tool.py` was originally scoped but is now at 97% (1 line missing). Dropped.

### Detailed gap analysis

**`guard_evaluator.py` (73%, 35 lines missing: L28, 31, 45-46, 50, 54-56, 59, 64-70, 79, 83, 85, 90-94, 109, 116-118, 124, 128, 146, 148, 152, 183, 191):**
- `_resolve_attribute` with non-dict objects (getattr path) — L28, 31
- `_apply_filter` length TypeError fallback — L45-46
- `_apply_filter` file_exists/dir_exists with non-string — L50, 54-56
- `_apply_filter` type filter — L59
- `_apply_filter` keys filter branches (model_dump, __dict__, empty) — L64-70
- `_compare_values`: NotEq, Lt, Gt, LtE, GtE, NotIn operators — L79, 83, 85, 90-94
- `_GuardEvaluator._eval_name`: output identifier — L109
- `_eval_bool`: Or operator — L116-118
- `_eval_pipe`: non-BitOr error, non-Name filter error — L124, 128
- `UnaryOp` (not) — L146
- `Tuple` literal — L148
- Forbidden node types — L152
- `_parse_guard_expression` empty string — L183, 191

**`schema_loader_tool.py` (83%, 22 lines missing: L49, 55, 62, 68, 75, 119-120, 125, 127, 140, 154, 159, 180, 200, 212, 219, 221, 228, 230, 238, 251, 253):**
- `parse_schema_loader_tools` validation: missing state_key (L49), invalid suffix (L62), invalid deduplicate_by (L68), unsupported merge_mode (L75)
- `_resolve_schema_path` escape detection (L119-120)
- `_load_yaml_schema` not-found, invalid YAML, non-dict content (L125, 127, 140)
- `_coerce_state` kwargs fallback (L154)
- `_deduplicate_fields` non-dict field, missing dedup key (L159, 180)
- `_build_merge_mode` runtime: non-list topics, non-dict existing schema, non-list fields, non-string topic (L200, 212, 219, 221, 228, 230, 238, 251, 253)

**`subgraph_nodes.py` (81%, 14 lines missing: L63, 157, 178-204):**
- `_map_output_state` with "auto"/"*" — L63
- GraphInterrupt handler — L157, 178-204 (deferred — requires checkpointer harness)

## Acceptance Criteria

- [x] AC-1: `guard_evaluator.py` coverage 73% → **95%** — all comparison operators, boolean operators, not/tuple/pipe error branches, filter branches tested
- [x] AC-2: `schema_loader_tool.py` coverage 83% → **97%** — all validation error branches in `parse_schema_loader_tools` tested
- [x] AC-3: `subgraph_nodes.py` — `_map_output_state` auto/* paths tested (81% → 82%; interrupt handler deferred)
- [x] AC-4: All new tests have `@pytest.mark.req()` traceability (REQ-YG-154, REQ-YG-417, REQ-YG-418, REQ-YG-092)
- [x] AC-5: Overall coverage remains ≥ 90% (90.32%)
- [x] AC-6: No production code changes

### Enforcement Results

- **62 new tests** across 3 files, all passing
- `test_fr659_guard_evaluator_coverage.py`: 34 tests (9 classes)
- `test_fr659_schema_loader_tool_coverage.py`: 25 tests (7 classes)
- `test_copilot_subgraph_variables.py::TestMapOutputState`: 3 tests
- **4564 total passed**, 71 skipped, 2 xfailed
- Remaining gaps: guard_evaluator L65-67 (model_dump Pydantic branch), L94/118 (unreachable via public API); schema_loader_tool L180/200/251/253 (deep merge-mode edge cases); subgraph_nodes L157/178-204 (GraphInterrupt — deferred)

## Judgement Notes (2026-07-03)

- **Approved.** `graph_tool.py` dropped (97% already). GraphInterrupt handler in subgraph_nodes.py deferred — testing requires checkpointer harness, separate FR if needed.
- Priority order: guard_evaluator (security boundary) > schema_loader_tool (validation gaps) > subgraph_nodes (trivial `_map_output_state` only).

## Related

- FR-344: `guard_evaluator.py` deterministic guards
- FR-006: `subgraph_nodes.py` interrupt output mapping
- FR-426: `schema_loader_tool.py` type: schema_loader
- CAP-03: Node Execution (REQ-YG-154 for guard evaluator)
- Coverage report: 2026-07-03 — 4502 passed, 90%
