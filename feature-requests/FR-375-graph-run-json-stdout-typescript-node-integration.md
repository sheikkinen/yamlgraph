# Feature Request: FR-375 `graph run --json` stdout mode + Node.js/TypeScript subprocess example

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-05-13

## Summary

Add a `--json` flag to `yamlgraph graph run` that emits the final graph state as JSON to stdout, and add a minimal `examples/demos/typescript-node/` demo showing Node.js/TypeScript integration through `child_process.execFile`.

## Value Statement

Node.js/TypeScript backend developers can call YAMLGraph directly without running MCP/A2A servers and without parsing human-formatted CLI output.

## Problem

Issue #375 requests a direct subprocess integration path:

1. `yamlgraph graph run <graph> --json` should produce machine-readable final state on stdout.
2. A minimal TypeScript demo should show end-to-end usage.

Current codebase behavior does not yet satisfy that contract:

1. `cmd_graph_run()` prints human-oriented output (`Running graph`, `RESULT`, tracing/tokens/timing summaries).
2. `--export-state` writes JSON to a file path, not stdout (`yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py`).
3. TypeScript integration currently demonstrates MCP (`examples/demos/mastra-integration/`), not direct CLI subprocess invocation.
4. CLI parser/docs currently expose no `--json` run mode (`yamlgraph/cli/__init__.py`, `reference/cli.md`).

## Research: Existing Patterns, Prior Art, and Gaps

1. **Reusable serialization already exists.**
   - `yamlgraph/storage/export.py::_serialize_state()` already defines state-to-JSON serialization behavior (including Pydantic objects) and should be reused.
2. **Inter-run state contracts already exist and must be preserved.**
   - `--import-state` / `--export-state` semantics are covered by CAP-120 and tests in `tests/unit/test_cli_inter_run_state_chaining.py`.
3. **TypeScript demo structure prior art exists.**
   - `examples/demos/mastra-integration/mastra-app/` already provides a suitable `package.json` + `tsconfig.json` + `src/index.ts` demo layout to mirror.
4. **Unspecified behavior was identified and now constrained.**
   - JSON-mode error path and interrupt handling were previously ambiguous; this FR fixes both contracts explicitly (see Constraints and AC-04/AC-05).
5. **Topic source file missing in this worktree snapshot.**
   - Requested source `.chaplain/processing/gh-375.md` is absent; planning source used was GitHub issue #375 plus in-repo artifacts.

## Objectives

1. Add machine-readable stdout mode for `graph run`.
2. Preserve existing default behavior when `--json` is not provided.
3. Provide one minimal Node.js/TypeScript subprocess integration demo.

## Constraints

1. **Single responsibility:** JSON stdout contract for `graph run` plus one demo.
2. **No default behavior drift:** non-JSON output/flow remains unchanged.
3. **Strict JSON stdout contract (success):** stdout contains only final-state JSON.
4. **Strict JSON failure contract:** on failure in `--json` mode, stdout is empty, error text is written to stderr, and exit code is non-zero.
5. **Interrupt safety:** `--json` mode is non-interactive; if `__interrupt__` is encountered, fail fast (non-zero) instead of calling `input()`.
6. **Serializer reuse required:** JSON mode must use existing `_serialize_state()` behavior.
7. **No new Python dependencies.**
8. **Demo gate alignment:** demo changes include runnable `demo-output.log`.

## Proposed Solution

### In Scope

1. Add `--json` flag to `graph run` parser in `yamlgraph/cli/__init__.py` (default `False`).
2. Update `cmd_graph_run()` in `yamlgraph/cli/graph_commands.py`:
   - when `--json` is enabled, suppress human success output on stdout;
   - serialize result via existing `_serialize_state()` contract and print JSON-only stdout on success;
   - in JSON mode failures, print errors to stderr only and exit non-zero;
   - in JSON mode, treat `__interrupt__` as unsupported and fail fast (no `input()` loop).
3. Preserve compatibility with existing run-path inputs and exports (`--var`, `--var-file`, `--import-state`, `--export-state`).
4. Add `examples/demos/typescript-node/`:
   - `package.json`
   - `tsconfig.json`
   - `src/index.ts`
   - `README.md`
   - `demo.sh`
   - `demo-output.log`
5. Update docs for discoverability and usage contracts:
   - `reference/cli.md`
   - `examples/README.md`
6. Add traceability artifacts required by project gates:
   - `capabilities/CAP-147-graph-run-json-stdout.yaml`
   - `ARCHITECTURE.md` capability row + REQ rows.

### Out of Scope

1. New Python embedding SDK.
2. MCP/A2A protocol changes.
3. Type generation for TypeScript clients from graph schemas.
4. Streaming/event JSON output mode.

## Requirement IDs (planned)

| REQ ID | Maps to |
| --- | --- |
| REQ-YG-348 | AC-02: `graph run` parser accepts `--json` and defaults to `False` |
| REQ-YG-349 | AC-03: JSON success path writes valid JSON-only stdout |
| REQ-YG-350 | AC-04: JSON failure path writes error to stderr only; stdout remains empty; exits non-zero |
| REQ-YG-351 | AC-05: JSON mode fails fast on interrupts (non-interactive; no stdin prompt loop) |
| REQ-YG-352 | AC-06: JSON payload uses existing full-state serialization contract (no truncation) |
| REQ-YG-353 | AC-07: JSON mode preserves existing run input/merge contracts and remains compatible with `--export-state` |
| REQ-YG-354 | AC-08: TypeScript subprocess demo assets exist and parse JSON output from `yamlgraph graph run --json` |
| REQ-YG-355 | AC-09: docs cover `--json` usage and when to prefer subprocess pattern vs MCP/A2A |

## Acceptance Criteria

- [x] **AC-01:** Capability/architecture traceability is added for this FR (`CAP-147`, `REQ-YG-348..355`).
- [x] **AC-02 (REQ-YG-348):** `yamlgraph graph run ... --json` parses successfully; default is `False` when omitted.
- [x] **AC-03 (REQ-YG-349):** On success with `--json`, stdout contains only valid JSON (no `Running graph`, `RESULT`, trace/token/timing summaries, or other human headers).
- [x] **AC-04 (REQ-YG-350):** On failure with `--json`, stdout is empty, error text is emitted on stderr, and process exits non-zero.
- [x] **AC-05 (REQ-YG-351):** If graph execution returns `__interrupt__` while `--json` is active, command fails fast (non-zero) without entering `input()` loop.
- [x] **AC-06 (REQ-YG-352):** JSON mode emits full final state (no 200-char truncation) and preserves `_serialize_state()` behavior for Pydantic-rich values.
- [x] **AC-07 (REQ-YG-353):** `--json` mode preserves run-path semantics with `--var`, `--var-file`, `--import-state`, and remains compatible with `--export-state`.
- [x] **AC-08 (REQ-YG-354):** `examples/demos/typescript-node/` includes runnable assets; `src/index.ts` uses `execFile` to run `yamlgraph graph run ... --json` and parses stdout JSON.
- [x] **AC-09 (REQ-YG-355):** `reference/cli.md` and `examples/README.md` document JSON mode usage and subprocess-vs-MCP/A2A guidance.

## Failing Acceptance Tests (RED plan)

Planned RED test modules:

- `tests/unit/test_fr375_graph_run_json_stdout_red.py`
- `tests/unit/test_fr375_typescript_node_demo_red.py`

Planned RED tests (must fail before implementation):

1. `test_ac01_registry_entries_for_cap147_and_reqyg348_355_exist`
2. `test_ac02_parser_accepts_json_flag_default_false`
3. `test_ac03_json_success_stdout_contains_only_valid_json`
4. `test_ac04_json_failure_writes_stderr_and_leaves_stdout_empty`
5. `test_ac05_json_mode_rejects_interrupt_without_input_prompt`
6. `test_ac06_json_mode_emits_full_untruncated_serialized_state`
7. `test_ac07_json_mode_preserves_import_var_merge_and_export_state_compatibility`
8. `test_ac08_typescript_demo_files_exist_and_execfile_uses_json_flag`
9. `test_ac09_docs_include_json_mode_and_typescript_demo_guidance`

Planned RED commands:

```bash
pytest tests/unit/test_fr375_graph_run_json_stdout_red.py -q --no-cov
pytest tests/unit/test_fr375_typescript_node_demo_red.py -q --no-cov
```

Each new test will use `@pytest.mark.req(...)` for REQ-YG-348..355 where applicable.

## Alternatives Considered

1. **Use only `--export-state` and read temp files in Node.**
   - Rejected: adds file lifecycle overhead and unnecessary I/O for request-response backend usage.
2. **Use MCP/A2A integration only.**
   - Rejected for this scope: solves broader integration protocols but adds infrastructure overhead versus direct subprocess calls.
3. **Add a Python SDK embedding path for Node.**
   - Rejected: larger surface area than required by issue scope.

## Related

- GitHub issue #375: <https://github.com/sheikkinen/yamlgraph/issues/375>
- `yamlgraph/cli/__init__.py`
- `yamlgraph/cli/graph_commands.py`
- `yamlgraph/cli/helpers.py`
- `yamlgraph/storage/export.py`
- `tests/unit/test_cli_inter_run_state_chaining.py`
- `reference/cli.md`
- `examples/README.md`
- `examples/demos/mastra-integration/README.md`
