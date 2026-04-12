# Feature Request: FR-225 A2A Module Unit-Test Coverage

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 2–3 days
**Requested:** 2026-04-12
**Judged:** 2026-04-12

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

### Verification of Claims

All factual claims verified against the codebase:

| Claim | Verified |
|-------|----------|
| Module line counts (241, 330, 89 = 660) | ✅ Exact match |
| Function counts (6, 7, 4) | ✅ Exact match |
| All functions exist in stated modules | ✅ Confirmed |
| 32 existing tests in `test_a2a_server.py` | ✅ Confirmed |
| `pytest.importorskip("a2a")` at module level | ✅ Confirmed |
| CI installs `.[dev,digest,websearch]` (no `a2a`) | ✅ Confirmed |
| `a2a` optional dep in `pyproject.toml` | ✅ Confirmed |
| REQ-YG-206–213 exist in ARCHITECTURE.md | ✅ Confirmed |
| FR-225 is next available FR number | ✅ Confirmed |

### Strengths

1. **Correctly identifies the real problem**: CI skips ≠ CI coverage. The "detection without enforcement" trap citation is apt.
2. **Per-module thresholds**: Superior to global coverage for accountability.
3. **Test inventory is exhaustive**: Every function and edge case listed.
4. **CI change is rightly mandatory**: Without Section 5, the FR perpetuates the problem it identifies.
5. **Single cohesive concern**: Test file split, new tests, and CI change are tightly coupled — splitting would create dependencies.

### Observations (non-blocking)

1. **Existing coverage is richer than implied.** 11 of 32 tests already cover `a2a_message.py` functions (agent card ×4, parse ×5, extract ×2). The "0% CI-validated coverage" is accurate, but the gap between existing tests and 85% may be smaller than the FR suggests. Effort may be lower than estimated.

2. **Per-module threshold enforcement is unspecified.** Acceptance criteria use manual `pytest --cov=...` commands. If these thresholds are meant to be CI-enforced (not just advisory), a mechanism should be added during implementation (e.g., `--cov-fail-under=85` in CI). The implementer should decide; this is a detail, not a scope issue.

3. **ARCHITECTURE.md traces REQ-YG-208 (`build_agent_card`) to `a2a_server.py`**, but the function lives in `a2a_message.py`. This is a pre-existing ARCHITECTURE.md inconsistency — not a defect in this FR. File separately if desired.

## Summary

Bring the three A2A modules (`a2a_message.py`, `a2a_server.py`, `cli/a2a_commands.py`) to ≥ 85% unit-test line coverage with per-module thresholds. These are network-facing protocol handlers introduced by FR-208 that currently show 0% CI-validated coverage, posing correctness and security risk.

## Value Statement

A2A protocol handlers become trustworthy production-grade code once every parse, validate, map, format, and dispatch path is exercised by unit tests — reducing the risk of silent regressions in a network-facing boundary.

## Problem

FR-208 introduced three modules totaling 660 lines of network-facing protocol code:

| Module | Lines | Functions | Current CI Coverage |
|--------|-------|-----------|---------------------|
| `yamlgraph/a2a_message.py` | 241 | 6 (`extract_text_from_parts`, `parse_a2a_message`, `_validate_required_vars`, `map_pipeline_error`, `build_agent_card`, `_detect_interrupt`) | 0% |
| `yamlgraph/a2a_server.py` | 330 | 7 (`_invoke_graph`, `__init__`, `execute`, `cancel`, `_resolve_graph`, `_format_result`, `create_a2a_app`) | 0% |
| `yamlgraph/cli/a2a_commands.py` | 89 | 4 (`cmd_a2a_dispatch`, `_resolve_patterns`, `_cmd_a2a_serve`, `_cmd_a2a_card`) | 0% |

Although 32 tests exist in `tests/unit/test_a2a_server.py`, all are gated by `pytest.importorskip("a2a")`. Standard CI runs without `pip install yamlgraph[a2a]`, so every test is skipped and coverage reads 0%.

**Risks of the current state:**

1. **Correctness**: Message parsing edge cases (malformed JSON, mixed `=` in values, multi-part concatenation) are untested in CI.
2. **Security**: `shlex.split()` on untrusted A2A input is never exercised by CI.
3. **Regression**: Any refactor to these modules has zero safety net in the standard test run.
4. **False confidence**: The 32 existing tests create an illusion of coverage that CI never validates.

## Proposed Solution

### 1. Per-module coverage thresholds

Each module is measured independently rather than relying on the global ≥ 92% metric:

- `yamlgraph/a2a_message.py` ≥ 85%
- `yamlgraph/a2a_server.py` ≥ 85%
- `yamlgraph/cli/a2a_commands.py` ≥ 85%

### 2. Guard all A2A tests with `pytest.importorskip("a2a")`

Existing tests already use `pytest.importorskip("a2a")` at module level. New tests must follow the same pattern — the `a2a-sdk` is an optional dependency and tests must skip gracefully when absent.

### 3. Test structure: one file per module

Split the monolithic `test_a2a_server.py` into per-module test files:

```
tests/unit/test_a2a_message.py      # extract, parse, validate, map_error, build_card, detect_interrupt
tests/unit/test_a2a_server.py       # executor, cancel, resolve, format, factory (retain, trim)
tests/unit/test_a2a_commands.py     # dispatch, resolve, serve, card CLI
```

### 4. Functions requiring new/expanded test coverage

**`a2a_message.py`** — extract/parse/validate/map/build:

- `extract_text_from_parts`: empty list, single TextPart, multiple TextParts, non-text parts only (ValueError)
- `parse_a2a_message`: JSON mode, key_value mode, single_input mode, fallback mode, resolution order priority, malformed JSON with `=`, missing required vars
- `_validate_required_vars`: all present, some missing, empty required list
- `map_pipeline_error`: each ErrorType variant, unknown type fallback, retryable flag propagation
- `build_agent_card`: single graph, multiple graphs, empty graphs list, custom host/port
- `_detect_interrupt`: present vs. absent `__interrupt__` key

**`a2a_server.py`** — executor/cancel/resolve/format/factory:

- `_invoke_graph`: mock `load_graph_config` + `compile_graph` + `invoke`, verify pass-through
- `YAMLGraphAgentExecutor.execute`: happy path (working → artifact → completed), error path (failed state), PipelineError mapping path, interrupt path (input-required)
- `YAMLGraphAgentExecutor.cancel`: cancels running task, emits canceled state
- `_resolve_graph`: single graph lookup, multi-graph lookup
- `_format_result`: string values, JSON-serializable values, internal keys filtered, empty result
- `create_a2a_app`: returns valid `A2AStarletteApplication`, wires executor + task_store + queue_manager

**`cli/a2a_commands.py`** — dispatch/resolve/serve/card:

- `cmd_a2a_dispatch`: routes "serve" subcmd, routes "card" subcmd, unknown subcmd exits 1
- `_resolve_patterns`: file path, directory path, missing path exits 1, no path (defaults)
- `_cmd_a2a_serve`: missing uvicorn exits 1, happy path calls `uvicorn.run`
- `_cmd_a2a_card`: no graphs found exits 1, prints valid JSON Agent Card

### 5. CI enforcement (MANDATORY)

CI workflow (`.github/workflows/workflow.yml`) must install `yamlgraph[a2a]` so A2A tests actually run in the standard test job. Without this change, every new test is skipped in CI and the FR perpetuates the exact "false confidence" problem it identifies. The CI change is minimal: add `[a2a]` to the existing `pip install -e ".[dev,digest,websearch]"` line.

> **Rationale:** Section 5 is mandatory per the *detection without enforcement* trap from the Knowledge Graph. Tests that CI skips are advisory, not enforcement.

## Acceptance Criteria

- [ ] `tests/unit/test_a2a_message.py` exists with tests covering `extract_text_from_parts`, `parse_a2a_message`, `_validate_required_vars`, `map_pipeline_error`, `build_agent_card`, `_detect_interrupt`
- [ ] `tests/unit/test_a2a_commands.py` exists with tests covering `cmd_a2a_dispatch`, `_resolve_patterns`, `_cmd_a2a_serve`, `_cmd_a2a_card`
- [ ] `tests/unit/test_a2a_server.py` retains executor/server tests; message-layer tests moved to `test_a2a_message.py`
- [ ] `pytest --cov=yamlgraph.a2a_message tests/unit/test_a2a_message.py` reports ≥ 85%
- [ ] `pytest --cov=yamlgraph.a2a_server tests/unit/test_a2a_server.py` reports ≥ 85%
- [ ] `pytest --cov=yamlgraph.cli.a2a_commands tests/unit/test_a2a_commands.py` reports ≥ 85%
- [ ] All A2A tests guarded with `pytest.importorskip("a2a")`
- [ ] All test functions tagged with `@pytest.mark.req("REQ-YG-xxx")` linking to FR-208 requirements (REQ-YG-206 through REQ-YG-213)
- [ ] No tests require a running A2A server or network access (pure unit tests with mocks)
- [ ] CI workflow installs `yamlgraph[a2a]` and A2A tests run (not skip) in the standard test job
- [ ] Existing 32 tests in `test_a2a_server.py` remain passing (no regressions)

## Implementation Approach

### Phase 1: Test file split and message layer (1 day)

1. Create `tests/unit/test_a2a_message.py` — move message-parsing and Agent Card tests from `test_a2a_server.py`
2. Add missing test cases for `extract_text_from_parts` edge cases
3. Add missing test cases for `parse_a2a_message` edge cases (malformed JSON, shlex edge cases)
4. Add `_validate_required_vars` direct tests
5. Add `map_pipeline_error` tests for all `ErrorType` variants
6. Verify `a2a_message.py` ≥ 85%

### Phase 2: Server and executor layer (1 day)

7. Expand `test_a2a_server.py` — cover `_resolve_graph` multi-graph case, `_format_result` edge cases
8. Add `_invoke_graph` unit test (mock `load_graph_config` + `compile_graph`)
9. Expand `execute` test for PipelineError path
10. Verify `a2a_server.py` ≥ 85%

### Phase 3: CLI commands layer (0.5 day)

11. Create `tests/unit/test_a2a_commands.py`
12. Test `cmd_a2a_dispatch` routing and unknown subcmd
13. Test `_resolve_patterns` for file, directory, missing, and default cases
14. Test `_cmd_a2a_serve` (mock uvicorn) and `_cmd_a2a_card` (mock discover_graphs)
15. Verify `cli/a2a_commands.py` ≥ 85%

### Phase 4: CI and cleanup (0.5 day)

16. Update `.github/workflows/workflow.yml` to install `yamlgraph[a2a]`
17. Run full `pytest tests/unit/` — no regressions
18. Verify per-module coverage thresholds met
19. Add `@pytest.mark.req` tags to all new tests

## Alternatives Considered

### 1. Raise global coverage threshold instead of per-module

Rejected — the global ≥ 92% metric is influenced by all modules. Adding tests to A2A modules alone cannot guarantee the global number moves, and other module changes could mask A2A regressions. Per-module thresholds give direct accountability.

### 2. Install `a2a-sdk` in CI and rely on existing 32 tests

Partially addresses the problem — existing tests would run in CI, but coverage gaps remain. The existing 32 tests do not cover all branches (e.g., `_format_result` edge cases, `_resolve_patterns` error paths, `cmd_a2a_dispatch` unknown subcmd). New tests are still needed to reach 85%.

### 3. Mock the A2A SDK entirely to avoid the optional dependency

Rejected — the tests already have `pytest.importorskip("a2a")` which is the correct pattern. Mocking the SDK types would reduce test fidelity (can't validate actual A2A type construction).

## Related

- **FR-208**: A2A Protocol Server — the original feature that introduced these modules
- **FR-209**: A2A Demo Streaming Response
- **REQ-YG-206 through REQ-YG-213**: Existing requirements for A2A functionality
- `yamlgraph/a2a_message.py` — message parsing, error mapping, Agent Card
- `yamlgraph/a2a_server.py` — executor, server factory
- `yamlgraph/cli/a2a_commands.py` — CLI dispatch
- `tests/unit/test_a2a_server.py` — existing test file (32 tests)
