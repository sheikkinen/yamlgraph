# Feature Request: Enable Ruff C901 Cognitive Complexity Gate

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-11

## Summary

Enable `C901` in ruff's `select` list to gate cognitive complexity at pre-commit and CI, closing the gap where radon CC (grade D ≥ 21) misses deeply-nested functions.

## Value Statement

The pre-commit pipeline catches complexity-driven refactor debt at commit time instead of discovering it in code review or production bugs.

## Problem

The codebase gates cyclomatic complexity via radon at grade D (≥ 21). But radon CC counts branches, not nesting depth. Functions with deep closures and nested conditionals score low on CC but high on cognitive complexity.

### Investigation Results (2026-04-11)

Running `ruff check yamlgraph/ --select C901` found **16 violations** at the default threshold of 10:

| C901 | Function | File |
|------|----------|------|
| **35** | `create_node_function` | `node_factory/llm_nodes.py:51` |
| **26** | `node_fn` (nested) | `node_factory/llm_nodes.py:152` |
| **19** | `create_agent_node` | `tools/agent.py:149` |
| **16** | `check_state_declarations` | `linter/checks.py:106` |
| **15** | `check_edge_coverage` | `linter/checks.py:272` |
| **14** | `compile_node` | `node_compiler.py:33` |
| **14** | `wrap_for_reducer` | `map_compiler.py:91` |
| **14** | `generate_typeddict_code` | `models/state_builder.py:297` |
| **13** | `wrapped` (nested) | `map_compiler.py:112` |
| **13** | `compile_map_node` | `map_compiler.py:182` |
| **13** | `_add_conditional_edges` (implied) | `edge_compiler.py` |
| **12** | `run_graph_streaming_native` | `executor_async.py:324` |
| **12** | `detect_loop_nodes` | `graph_loader.py:31` |
| **12** | `_execute_cli` | `node_factory/copilot_node.py:200` |
| **12** | `node_fn` (agent) | `tools/agent.py:216` |
| **12** | `extract_json` | `utils/json_extract.py:54` |

**Radon CC missed all of these** — its gate fires at grade D (≥ 21), but the worst offender (`create_node_function`) scored only CC=17 (grade C).

### Why C901 catches what radon misses

- **Radon CC**: Counts decision points (if/for/while/except). Flat function with 20 ifs = 20.
- **Ruff C901**: Weights by nesting depth. Nested if-inside-for-inside-closure = exponential penalty.
- `create_node_function` has CC=17 but C901=35 because its complexity comes from **deeply nested closures with inner retry loops**, not flat branching.

## Proposed Solution

### Step 1: Add C901 to ruff select

```toml
# pyproject.toml
[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "SIM", "C901"]
```

### Step 2: Set max-complexity threshold

```toml
[tool.ruff.lint.mccabe]
max-complexity = 15
```

Start at 15 to catch the worst offenders (6 functions above 15) without blocking the 10 functions in the 11–14 range. Tighten to 10 after FR-220 refactors land.

### Step 3: Consider removing radon CC gate

With C901 enabled, the radon CC pre-commit hook (`radon-complexity`) becomes redundant — C901 is strictly more sensitive. Options:
- Remove radon CC hook (radon MI and radon raw remain useful for other metrics)
- Keep both temporarily during transition

## Acceptance Criteria

- [x] `C901` added to ruff `select` in `pyproject.toml`
- [x] `max-complexity` set to 15 in `[tool.ruff.lint.mccabe]`
- [x] `ruff check yamlgraph/` passes (functions above 15 either refactored or granted noqa with confession)
- [x] CI workflow (`workflow.yml`) inherits the rule via existing `ruff check yamlgraph/`
- [x] Any `# noqa: C901` suppressions documented in `docs/confessions.md`
- [x] Decision documented on radon CC gate retention/removal
- [x] Tests pass

### Radon CC Gate Decision

**Keep both temporarily.** Radon CC (grade D ≥ 21) and ruff C901 (threshold 15) measure different dimensions of complexity. Radon CC catches flat branching; C901 catches deep nesting. The radon CC gate remains as a coarser safety net until C901 threshold is tightened to 10 (post-FR-220 refactors). At that point, radon CC becomes redundant and should be removed.

## Alternatives Considered

1. **Keep radon CC only** — Misses nesting-weighted complexity entirely. The investigation proved this gap is real: 16 functions above C901=10 pass radon's gate.
2. **Use flake8-cognitive-complexity** — Separate tool, separate config. Ruff C901 is already available with zero new dependencies.
3. **Set threshold to 10 immediately** — Would require refactoring or suppressing 16 functions. Start at 15, tighten incrementally.

## Related

- FR-220: Refactor `create_node_function` (the worst C901 offender)
- FR-222: Ruff S security rules
- Commandment 8: "Kill all entropy and false idols — sanctify with radon"
- Knowledge Graph process: `detection_without_enforcement` — "Lint without gate = advisory"
