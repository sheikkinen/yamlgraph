# Feature Request: FR-406 Machine-Readable Lint Output (`graph lint --json`)

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-18

## Summary

Add `--json` output mode to `yamlgraph graph lint` so automation can consume lint diagnostics without parsing human-oriented emoji/text formatting.

## Value Statement

Agents and CI jobs get stable, parseable lint diagnostics from stdout, reducing fragile regex parsing and boundary ambiguity.

## Problem

`cmd_graph_lint` currently only prints human output (status icons, prose messages, summary line). This is good for developers but noisy for machine consumers.

Codebase evidence:

1. `yamlgraph/cli/graph_validate.py::cmd_graph_lint` prints formatted text and summary only.
2. `yamlgraph/linter/graph_linter.py` already exposes `LintResult` as a Pydantic model (`file`, `issues`, `valid`), so structured data already exists in memory.
3. Existing CLI precedent (`graph run --json`) routes machine payload to stdout and diagnostics to stderr (`yamlgraph/cli/graph_commands.py`), proving the pattern in this repository.

Without `graph lint --json`, any consumer must parse presentation text instead of reading a stable schema.

## Research

### Topic source

- Requested source file `.chaplain/processing/gh-406.md` is not present in this worktree.
- Canonical topic was recovered from GitHub issue #406:
  <https://github.com/sheikkinen/yamlgraph/issues/406>

### Prior art and current patterns

1. **Structured model already exists**
   - `yamlgraph/linter/graph_linter.py` defines `LintResult(BaseModel)` and `LintIssue` composition.
   - This lowers implementation risk and scope.

2. **CLI machine-mode precedent**
   - `yamlgraph graph run --json` already enforces stdout/stderr separation and parser flag defaults (`yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`).
   - Reusing this behavior keeps CLI ergonomics consistent.

3. **Current lint test surface**
   - `tests/unit/test_graph_validate.py` covers lint success/failure paths and exit codes but has no JSON-mode assertions.

### Architecture alignment

- REQ-YG-032: CLI parser setup (`yamlgraph/cli/__init__.py`)
- REQ-YG-033: graph command execution (`yamlgraph/cli/graph_validate.py`)
- REQ-YG-348–355: existing JSON CLI mode precedent (`graph run --json`)

Planned traceability addition during implementation:
- `capabilities/CAP-151-lint-json-output.yaml` with requirement `REQ-YG-406` (or next free REQ ID at implementation time)
- Corresponding capability and requirement rows in `ARCHITECTURE.md`

## Objectives

1. Add one machine-readable mode to `graph lint` only.
2. Preserve existing human output behavior when `--json` is omitted.
3. Preserve existing exit-code semantics.

## Constraints

1. Single responsibility: this FR covers `graph lint` only (not `graph validate`, not SARIF).
2. JSON mode must keep stdout parseable (no summary/prose mixed into stdout payload lines).
3. Errors/diagnostics in JSON mode must go to stderr.
4. No linter rule logic changes; output transport only.

## Proposed Solution

1. Add `--json` boolean flag to `graph lint` parser in `yamlgraph/cli/__init__.py`.
2. In `cmd_graph_lint`, branch by mode:
   - **human mode (default):** current behavior unchanged.
   - **json mode:** emit one `LintResult.model_dump_json()` line per input file (NDJSON).
3. Keep current linting and counting logic for exit-code behavior:
   - exit 1 when total errors > 0
   - exit 0 otherwise.
4. In JSON mode, print non-payload diagnostics (missing file, exceptions) to stderr only.

Example:

```bash
yamlgraph graph lint --json graphs/a.yaml graphs/b.yaml
```

stdout (NDJSON):

```json
{"file":"graphs/a.yaml","issues":[],"valid":true}
{"file":"graphs/b.yaml","issues":[{"severity":"error","code":"E501","message":"...","line":12,"fix":"..."}],"valid":false}
```

## Acceptance Criteria

- [x] **AC-01 Parser:** `yamlgraph graph lint --json <path>` is accepted; default is `False` when omitted.
- [x] **AC-02 Single file JSON:** JSON mode emits valid `LintResult` JSON to stdout for one file.
- [x] **AC-03 Multi-file NDJSON:** JSON mode emits one JSON object per input file (newline-delimited).
- [x] **AC-04 Stream separation:** JSON mode writes only payload JSON to stdout; diagnostics/errors go to stderr.
- [x] **AC-05 Exit codes unchanged:** lint errors still exit with code 1; warnings-only or clean runs exit 0.
- [x] **AC-06 Human mode unchanged:** behavior/output remains unchanged when `--json` is not passed.
- [x] **AC-07 Tests:** dedicated FR-406 RED/GREEN unit tests are added for parser, JSON payload shape, stream separation, and exit semantics.
- [x] **AC-08 Traceability:** capability + requirement registry updates are included (`CAP-151`, `REQ-YG-406` or next free REQ at implementation time).

## Implementation Notes

- Added `--json` to `graph lint` parser with default `False`.
- `cmd_graph_lint` now uses NDJSON payload output (`LintResult.model_dump_json()`) in JSON mode.
- JSON mode routes diagnostics/errors to stderr and suppresses human summary text on stdout.
- Exit semantics are preserved: non-zero on accumulated lint errors, zero otherwise.
- Added capability and requirement traceability entries: `CAP-151` / `REQ-YG-406`.

## Failing Acceptance Tests (RED)

RED test file prepared:

- `tests/unit/test_fr406_lint_json_output_red.py`

Planned RED tests:

1. `test_ac01_parser_accepts_lint_json_flag_default_false`
2. `test_ac02_json_single_file_emits_valid_lintresult_to_stdout`
3. `test_ac03_json_multi_file_emits_ndjson_one_object_per_file`
4. `test_ac04_json_mode_routes_diagnostics_to_stderr_only`
5. `test_ac05_exit_code_semantics_match_existing_lint_behavior`
6. `test_ac06_non_json_mode_output_is_unchanged`
7. `test_ac08_traceability_entries_for_cap151_and_reqyg406_exist`

RED command:

```bash
pytest tests/unit/test_fr406_lint_json_output_red.py -q --no-cov
```

Expected current RED failure reasons before implementation:

- parser rejects `graph lint --json`
- lint output contains human formatting instead of machine payload
- traceability entries for CAP-151/REQ-YG-406 are absent

## Alternatives Considered

1. **`--format json|human`**
   - Rejected for this FR: only one new mode is needed now; additional formats are YAGNI.

2. **SARIF output**
   - Rejected for this FR: heavier surface area and schema mapping; viable follow-up if IDE/security scanner integration is needed.

3. **Parse existing human output in consumers**
   - Rejected: brittle, locale/presentation-coupled, and contrary to boundary normalization doctrine.

## Related

- GitHub issue #406: <https://github.com/sheikkinen/yamlgraph/issues/406>
- `feature-requests/TEMPLATE.md`
- `yamlgraph/cli/__init__.py`
- `yamlgraph/cli/graph_validate.py`
- `yamlgraph/linter/graph_linter.py`
- `tests/unit/test_graph_validate.py`
- `tests/unit/test_fr375_graph_run_json_stdout_red.py` (JSON CLI precedent)
