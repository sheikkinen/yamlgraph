# Feature Request: FR-433 Post-Edit Coverage for apply_patch

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 1 day (Phase 1: 0.5d, Phase 2: 0.5d)
**Requested:** 2026-05-21

**Judge Verdict:** APPROVE with phasing — Phase 1 (apply_patch coverage + multi-file aggregation) is the bug fix. Phase 2 (optional auto-ruff) is an independent enhancement. Self-judgement noted; verdict re-confirmed by external judge.

## Summary

Fix `post-edit-checks.sh` so edits made via `apply_patch` are inspected at post-edit time.

## Value Statement

Agents get immediate feedback (or auto-fix) for file-size and Ruff issues while editing, instead of discovering failures only when pre-commit runs during `git commit`.

## Problem

Observed event timeline from `.github/hooks/logs/audit.jsonl` shows:

1. `apply_patch` edits are logged by `pre-command-guard` as `pass/not-inspected`.
2. `post-edit-checks` entries in this session were only for `create_file`.
3. File-size (>450) and Ruff modifications surfaced later at pre-commit during commit.

Root cause in hook implementation:

- `post-edit-checks.sh` filters tool names to only `replace_string_in_file|create_file|multi_replace_string_in_file`.
- `apply_patch` exits early and is never analyzed.
- Ruff in post-edit is check-only (`ruff check --no-fix`, `ruff format --check`), so no early auto-fix exists.

This mismatch means the hook covers older edit tools but misses the primary code-edit tool used by the current agent.

## Proposed Solution

### Phase 1: apply_patch coverage + multi-file aggregation (bug fix)

**Depends on FR-429** routing refactor (line-60 early-exit → file-type dispatch).

#### 1a) Add `apply_patch` to tool routing

Extend tool routing in `post-edit-checks.sh`:

```bash
case "$TOOL_NAME" in
  replace_string_in_file|create_file|multi_replace_string_in_file|apply_patch) ;;
  *) exit 0 ;;
esac
```

For `apply_patch`, parse all touched file paths from the patch payload:

- Read `tool_input.input` text (raw string inside JSON, not nested JSON)
- Extract lines matching `*** Add File:`, `*** Update File:` (format reverse-engineered from audit log observations; not formally documented by VS Code)
- Build unique path list
- Run existing checks per file, **routed by file type**: `.py` → ruff/size/forbidden, `.yaml` → graph lint (FR-429), `.md` in `feature-requests/` → FSM check (FR-431)

Nonexistent files (deleted/renamed targets) continue to be skipped safely.

#### 1b) Aggregate multi-file feedback

### Phase 2: Optional auto-ruff (enhancement, implement after Phase 1)

Introduce opt-in env flag (default off) to avoid surprise write behavior:

- `POST_EDIT_AUTO_RUFF=1`

When enabled for `.py` files:

1. Run `ruff check --fix` first
2. Run `ruff format`
3. Re-run lint/check and report residual issues only
4. Audit-log when auto-fix changed file

When disabled, preserve current warning-only behavior.

This phase applies to **all** edit tools (not just `apply_patch`) and can be implemented independently.

## Acceptance Criteria

### Phase 1

- [x] `post-edit-checks` inspects `apply_patch` edits
- [x] All `*** Add File` / `*** Update File` paths in patch payload are analyzed
- [x] Per-file routing: `.py` → ruff/size, `.yaml` → graph lint (FR-429), `.md` → FR-431 checks
- [x] Multi-file patches return one combined `systemMessage` prefixed by file path
- [x] Python file-size warnings/errors emitted at post-edit time
- [x] Ruff findings emitted at post-edit time (warning only, no mutation)
- [x] Existing behavior for `create_file`, `replace_string_in_file`, `multi_replace_string_in_file` unchanged
- [x] Tests: single-file patch, multi-file patch, mixed `.py`+`.yaml` patch, file-size, ruff warning

### Phase 2

- [x] Optional `POST_EDIT_AUTO_RUFF=1` auto-fixes Ruff issues and logs that action
- [x] Default behavior remains non-mutating when `POST_EDIT_AUTO_RUFF` is unset
- [x] Auto-fix applies to all edit tools, not just `apply_patch`
- [x] Tests: auto-fix path enabled, auto-fix path disabled

## Implementation Notes

- Updated `.github/hooks/scripts/post-edit-checks.sh` tool routing to include `apply_patch`.
- Added patch payload parsing for `*** Add File:` and `*** Update File:` headers from `toolInput.input`.
- Implemented multi-file iteration and single aggregated `systemMessage` with `File: <path>` prefixes.
- Preserved existing per-file checks and legacy tool behavior while removing early exits that blocked aggregation.
- Added optional `POST_EDIT_AUTO_RUFF=1` path (`ruff check --fix`, `ruff format`) with `ruff-autofix-applied` audit entries when file content changed.
- Added FR-433 regression tests to `.github/hooks/tests/test_post_edit_checks.py`; current run: `32 passed, 0 failed`.

## Test Plan

Add/extend `.github/hooks/tests/test_post_edit_checks.py` with subprocess payloads:

1. `test_apply_patch_python_files_are_checked`
2. `test_apply_patch_multiple_files_aggregates_issues`
3. `test_apply_patch_reports_file_size`
4. `test_apply_patch_reports_ruff_without_autofix`
5. `test_apply_patch_autofix_ruff_when_enabled`
6. `test_apply_patch_non_python_yaml_unchanged`

Use a realistic patch payload including multiple `*** Update File:` sections.

## Alternatives Considered

- **Rely on pre-commit only**: Rejected — catches too late, increases commit thrash.
- **Support only apply_patch and drop legacy tool names**: Rejected — unnecessary compatibility break.
- **Always auto-fix Ruff**: Rejected — mutating behavior should be explicit and auditable.

## Dependencies

- **FR-429**: Routing refactor (line-60 early-exit → file-type dispatch). Phase 1 needs this to route `.py`/`.yaml`/`.md` files from a single `apply_patch` invocation.

## Related

- [post-edit-checks.sh](../.github/hooks/scripts/post-edit-checks.sh): current hook implementation
- [FR-429](FR-429-post-edit-yaml-checks.md): routing refactor + YAML checks (dependency)
- [FR-431](FR-431-fsm-reinvention-hook.md): FR markdown checks (routed by Phase 1)
- `.github/hooks/logs/audit.jsonl`: event evidence (`post-edit-checks` absent for `apply_patch`)
