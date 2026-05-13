# Watcher2 Sanity Check — FR-375 `graph run --json` stdout mode + TypeScript Node.js demo

**Date:** 2026-05-13
**FR:** FR-375
**Branch:** feat/watcher2-gh-375
**Reviewer:** watcher2 post-validate

## What Happened

FR-375 adds `--json` to `yamlgraph graph run`, making the CLI machine-readable for Node.js/TypeScript subprocess consumers. The diff covers: CLI parser flag, a new `graph_run_helpers.py` module (refactored from `graph_commands.py`), TypeScript demo under `examples/demos/typescript-node/`, capability/ARCHITECTURE traceability, docs, and 9 acceptance tests covering all ACs.

All 9 acceptance tests pass (`test_fr375_graph_run_json_stdout_red.py` + `test_fr375_typescript_node_demo_red.py`).

## Proportionality

+1230/-279 lines across 23 files. Scope matches FR: CLI flag, helper refactor, demo assets, traceability, docs. No speculative extensions found.

## Test Quality

Tests check behavioral contracts, not implementation trivia:
- AC-03: asserts `"Running graph" not in stdout` and `json.loads(stdout)` parses — stdout purity verified
- AC-04: asserts `stdout == ""` and `"boom" in stderr` on failure — correct boundary check
- AC-05: asserts `mock_input.assert_not_called()` on interrupt — non-interactive contract verified
- AC-06: 300-char string fully preserved, Pydantic model serialized to dict — no truncation confirmed
- AC-07: merge priority chain tested via `_fake_build_run_config` side effect — state semantics confirmed
- All tests carry `@pytest.mark.req` tags (REQ-YG-348..355)

## FR/Code Alignment

All 9 ACs checked `[x]` in FR and all have corresponding passing tests. Serializer reuse (`_serialize_state()`) confirmed in `_print_json_result`. Interrupt guard precedes the interactive loop — correct fail-fast without `input()`.

## Trap Identified

**`_handle_optional_exports` defined in both `graph_commands.py` and `graph_run_helpers.py`.**
The refactor moved most helpers to `graph_run_helpers.py` and aliased them, but `_handle_optional_exports` was re-implemented locally in `graph_commands.py` rather than aliased. The version in `graph_run_helpers.py` (lines ~250-271) is therefore dead code. This is a minor structural smell — not a behavioral defect, and not a blocker for the current gate — but contradicts the refactor's intent and should be cleaned up in a follow-up.

## What Worked

Normalizing at the stdout output boundary (routing every non-payload write through `error_stream`) rather than patching individual `print()` call sites. This is the "normalize at the boundary" law applied in the output direction and was correctly identified in the implementation's own diary entry.

## Seed

If `--json` and `--stream` flags coexist in a future FR, what structural contract should govern mixed-mode output — ndjson event stream vs SSE vs a structured envelope? And could the interrupt payload be emittable as a typed JSON event rather than an error exit, enabling non-interactive resume from a subprocess controller?
