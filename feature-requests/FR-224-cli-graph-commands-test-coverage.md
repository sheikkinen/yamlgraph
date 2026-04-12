# Feature Request: CLI Graph Commands Test Coverage

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-12

## Summary

Bring `cli/graph_commands.py` (50%) and `cli/graph_validate.py` (50%) to ≥ 85% unit-test line coverage by extending `test_graph_commands.py` and creating `test_graph_validate.py`.

## Value Statement

Developers get confidence that the primary CLI surface (`graph run`, `graph info`, `graph validate`, `graph lint`, `graph codegen`) is tested against regressions, reducing bug escape through the most user-facing module.

## Problem

The two CLI modules that implement YAMLGraph's primary user interface are at ~50% coverage — the lowest of any CLI module. Uncovered paths include:

**`graph_commands.py` (222 stmts, 111 missed — 50%):**
- `_setup_timeout` / `_teardown_timeout` — signal-based timeout guard
- `_display_result` — truncation and full-output logic
- `_get_interrupt_message` — interrupt value extraction (str, dict, fallback)
- `_handle_export` — export config dispatch
- `_build_run_config` — data merge, recursion_limit, timeout, token tracking
- `_invoke_graph` — async path (`asyncio.run`)
- `cmd_graph_run` — var-file loading, timeout error, token usage summary, export flag
- `cmd_graph_info` — full happy-path display (nodes, edges, inputs)
- `cmd_graph_codegen` — stdout and file output, error paths
- `cmd_graph_dispatch` — dispatch routing and unknown command

**`graph_validate.py` (109 stmts, 55 missed — 50%):**
- `_validate_required_fields` — missing name, missing nodes, no edges warning
- `_validate_edges` — unknown from/to, conditional edge list
- `_validate_nodes` — agent without tools warning
- `_report_validation_result` — error/warning/clean output formatting
- `cmd_graph_validate` — error handling paths (GraphLoadError, generic Exception)
- `cmd_graph_lint` — multi-file iteration, error/warning counts, summary, exit code

These paths exercise the exact code users hit via `yamlgraph graph *` commands. Gaps here mean regressions in the primary interface go undetected.

## Proposed Solution

### Phase 1: `test_graph_validate.py` (new file)

Test each validation helper and both CLI commands with crafted YAML dicts:

```python
# tests/unit/test_graph_validate.py

class TestValidateRequiredFields:
    def test_missing_name_returns_error(self): ...
    def test_missing_nodes_returns_error(self): ...
    def test_no_edges_returns_warning(self): ...
    def test_valid_config_no_issues(self): ...

class TestValidateEdges:
    def test_unknown_from_node(self): ...
    def test_unknown_to_node(self): ...
    def test_conditional_edge_list_unknown_target(self): ...
    def test_valid_edges_no_errors(self): ...

class TestValidateNodes:
    def test_agent_without_tools_warning(self): ...
    def test_agent_with_tools_no_warning(self): ...

class TestReportValidationResult:
    def test_errors_prints_invalid_and_exits(self): ...
    def test_warnings_prints_valid_with_warnings(self): ...
    def test_clean_prints_valid(self): ...

class TestCmdGraphLint:
    def test_lint_valid_graph(self): ...
    def test_lint_missing_file(self): ...
    def test_lint_multiple_files(self): ...
    def test_lint_errors_exit_code_1(self): ...
    def test_lint_warnings_only_exit_code_0(self): ...
```

### Phase 2: Extend `test_graph_commands.py`

Add test classes for uncovered helpers and command paths:

```python
class TestDisplayResult:
    def test_truncates_long_values(self): ...
    def test_full_output_no_truncation(self): ...
    def test_skips_internal_keys(self): ...

class TestGetInterruptMessage:
    def test_string_value(self): ...
    def test_dict_with_message(self): ...
    def test_dict_with_question(self): ...
    def test_fallback_to_response(self): ...

class TestSetupTimeout:
    def test_none_returns_none(self): ...
    def test_sets_alarm_on_unix(self): ...
    def test_windows_skips_with_warning(self): ...

class TestTeardownTimeout:
    def test_none_context_noop(self): ...
    def test_cancels_alarm(self): ...

class TestBuildRunConfig:
    def test_merges_data_files(self): ...
    def test_cli_recursion_limit_overrides_yaml(self): ...
    def test_token_usage_callback_added(self): ...

class TestCmdGraphCodegen:
    def test_codegen_stdout(self): ...
    def test_codegen_to_file(self, tmp_path): ...
    def test_codegen_file_not_found(self): ...

class TestCmdGraphDispatch:
    def test_dispatches_run(self): ...
    def test_dispatches_info(self): ...
    def test_dispatches_validate(self): ...
    def test_dispatches_lint(self): ...
    def test_dispatches_codegen(self): ...
    def test_unknown_command_exits(self): ...

class TestCmdGraphInfo:
    def test_displays_nodes_and_edges(self): ...
    def test_displays_inputs(self): ...
    def test_generic_error_exits(self): ...
```

### Test strategy

- All tests are pure unit tests using `unittest.mock` (no LLM calls, no file I/O beyond tmp_path).
- `cmd_graph_run` tests mock `graph_loader.load_graph_config`, `compile_graph`, `get_checkpointer_for_graph`, and `utils.tracing.*`.
- `cmd_graph_lint` tests mock `yamlgraph.linter.lint_graph` to return crafted `LintResult` objects.
- Timeout tests mock `signal.signal`/`signal.alarm` and `platform.system`.
- Each test is tagged with the appropriate `@pytest.mark.req()` (REQ-YG-033 for graph commands, REQ-YG-036 for codegen).

### Coverage verification

Per-module coverage measured with:
```bash
pytest tests/unit/test_graph_commands.py tests/unit/test_graph_validate.py \
  --cov=yamlgraph/cli/graph_commands --cov=yamlgraph/cli/graph_validate \
  --cov-report=term-missing -q
```

Target: both modules ≥ 85% line coverage individually.

## Acceptance Criteria

- [ ] `yamlgraph/cli/graph_commands.py` ≥ 85% line coverage from unit tests
- [ ] `yamlgraph/cli/graph_validate.py` ≥ 85% line coverage from unit tests
- [ ] New `tests/unit/test_graph_validate.py` created with tests for all validation helpers and `cmd_graph_lint`
- [ ] `tests/unit/test_graph_commands.py` extended with tests for `_display_result`, `_get_interrupt_message`, `_setup_timeout`, `_teardown_timeout`, `_build_run_config`, `cmd_graph_codegen`, `cmd_graph_dispatch`, and `cmd_graph_info` happy path
- [ ] All new tests tagged with `@pytest.mark.req()` linking to REQ-YG-033, REQ-YG-036, or REQ-YG-047
- [ ] No integration tests — all tests use mocks for LLM calls, file I/O, signal handling
- [ ] Existing tests continue to pass (`pytest tests/unit/ -q`)
- [ ] `ruff check` passes on new test files

## Alternatives Considered

1. **Global coverage threshold only**: The project uses `--cov-fail-under=70` globally. This hides per-module gaps — a module at 50% can hide behind well-tested neighbours. Per-module targets give targeted improvement.

2. **Integration tests with real graphs**: Would test more realistically but requires API keys, is slow, and already partly covered in `tests/integration/`. Unit tests with mocks give fast, deterministic coverage of branching logic.

3. **Defer until next CLI change**: Risk compounds — each change to these modules without tests increases regression probability. The modules are stable enough to test now.

## Related

- `yamlgraph/cli/graph_commands.py` — target module (50% → ≥ 85%)
- `yamlgraph/cli/graph_validate.py` — target module (50% → ≥ 85%)
- `tests/unit/test_graph_commands.py` — existing test file to extend
- REQ-YG-033: Graph command execution and information
- REQ-YG-036: CLI schema export and access
- REQ-YG-047: LangSmith trace URL retrieval and sharing
