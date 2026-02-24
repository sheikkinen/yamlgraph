# Feature Request: Infrastructure Script Unit Tests

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 3 days
**Requested:** 2026-02-24

## Summary

Add unit tests for pre-commit hook scripts in `scripts/` that currently lack coverage. These scripts guard every commit but are themselves untested — a blind spot in the quality pipeline.

## Problem

Six Python scripts run as pre-commit hooks on every commit. Three have no tests at all, one has only partial coverage, and two are already covered. This creates a fragile foundation: a regression in any hook script could silently pass bad commits or block good ones.

**Current coverage inventory:**

| Script | Lines | Pre-commit? | Test Status |
|---|---|---|---|
| `diary_rotate.py` | 299 | ✅ | ❌ No tests |
| `noqa_coverage.py` | 228 | ✅ | ❌ No tests |
| `hedging_check.py` | 102 | ✅ | ❌ No tests |
| `absolution.py` | 27 | ✅ | ❌ No tests (trivial) |
| `req_coverage.py` | 597 | ✅ | ⚠️ Partial (AST extraction only, 162 lines) |
| `lint_inline_llm.py` | — | ✅ | ✅ Covered (235 lines) |

**Non-hook scripts excluded from scope:**

| Script | Reason |
|---|---|
| `_add_req_markers.py` | One-shot utility ("delete after use") |
| `reconsolidate.py` | Project-specific, depends on `examples/ocr_cleanup` |
| `generate_tts_fixtures.py` | Requires external API (ElevenLabs) |
| `diary_digest.sh` | Already has tests (`test_diary_digest.py`, 529 lines) |

## Proposed Solution

Add unit test files under `tests/unit/` for each untested script. Tests should use `tmp_path` fixtures and mock external dependencies (filesystem, git, subprocess). Each test file follows existing patterns (see `test_lint_inline_llm.py`, `test_req_coverage_ast.py`).

### Phase 1: `hedging_check.py` (smallest, pure AST — quick win)

**File:** `tests/unit/test_hedging_check.py`

Tests:
- `test_detects_if_not_x_reassign` — Pattern 1: `if not X: X = Y` detected
- `test_ignores_different_variable` — `if not X: Y = Z` not flagged
- `test_allowlist_suppresses` — Allowlisted `file:line` entries skipped
- `test_syntax_error_skipped` — Malformed Python files don't crash
- `test_no_findings_returns_zero` — Clean code exits 0
- `test_strict_mode_returns_one` — Findings + `--strict` exits 1
- `test_directory_not_found` — Missing directory exits 1

### Phase 2: `noqa_coverage.py` (medium, file parsing)

**File:** `tests/unit/test_noqa_coverage.py`

Tests:
- `test_find_noqa_single_code` — `# noqa: E402` → `("E402",)`
- `test_find_noqa_multiple_codes` — `# noqa: E402, F401` → both
- `test_find_noqa_blanket` — `# noqa` (no code) → `"ALL"`
- `test_parse_confessions_complete` — Full `### CONF-001` block parsed
- `test_parse_confessions_missing_fields` — Incomplete confessions ignored
- `test_undocumented_noqa_detected` — Code noqa not in confessions flagged
- `test_all_documented_passes` — All noqa in confessions → exit 0
- `test_strict_undocumented_fails` — Undocumented + `--strict` → exit 1

### Phase 3: `diary_rotate.py` (complex, file ops + subprocess)

**File:** `tests/unit/test_diary_rotate.py`

Tests for helpers (pure functions, `tmp_path`):
- `test_latest_entry_date_multiple` — Finds most recent `## YYYY-MM-DD:` header
- `test_latest_entry_date_none` — No headers → `None`
- `test_entry_count` — Counts `##` date headers correctly
- `test_one_line_summary_single_date` — `"1 entries from 2026-02-24"`
- `test_one_line_summary_range` — `"3 entries, 2026-02-20 to 2026-02-24"`
- `test_archive_path_no_conflict` — Returns `diary-YYYY-MM-DD.md`
- `test_archive_path_with_conflict` — Returns `diary-YYYY-MM-DD-1.md`
- `test_create_fresh_diary` — Writes header with Previous link

Tests for `main()` (mock `git_add`, filesystem):
- `test_no_diary_exits_zero` — Missing `docs/diary.md` → 0
- `test_no_dated_entries_exits_zero` — Diary without `##` headers → 0
- `test_rotation_when_date_changed` — Archives old diary, creates fresh one
- `test_no_rotation_same_day` — Same day entries → no rotation
- `test_check_flag_dry_run` — `--check` reports but doesn't rotate

Tests for import helpers (mock filesystem):
- `test_import_scheduled_entries` — Diary entry files imported and deleted
- `test_import_skips_already_present` — Duplicate date skipped
- `test_import_git_reports` — Git report files imported and renamed

### Phase 4: `req_coverage.py` (expand partial coverage)

**File:** `tests/unit/test_req_coverage.py` (new, alongside existing `test_req_coverage_ast.py`)

Tests:
- `test_extract_req_markers_single` — `@pytest.mark.req("REQ-YG-001")` extracted
- `test_extract_req_markers_multiple` — Multi-arg marker extracted
- `test_extract_class_level_markers` — Class decorator applies to methods
- `test_is_req_marker` — Positive/negative AST matching
- `test_module_to_path_file` — `yamlgraph.utils.llm_factory` → path
- `test_module_to_path_package` — `yamlgraph.cli` → `__init__.py`
- `test_load_req_descriptions` — Parses `ARCHITECTURE.md` table rows
- `test_main_summary_all_covered` — All reqs covered → exit 0
- `test_main_strict_uncovered_fails` — Missing reqs + `--strict` → exit 1

### Phase 5: `absolution.py` (trivial — optional)

**File:** `tests/unit/test_absolution.py`

Tests:
- `test_main_returns_zero` — Always exits 0
- `test_output_contains_absolution` — Prints "✓ Absolution granted"

## Acceptance Criteria

- [ ] `hedging_check.py` has ≥7 unit tests covering the implemented AST pattern (Pattern 1: `if not X: X = Y`), allowlist, strict mode, and error paths
- [ ] `noqa_coverage.py` has ≥8 unit tests covering parsing, scanning, matching, and strict mode
- [ ] `diary_rotate.py` has ≥14 unit tests covering all helpers, main flow, and import functions
- [ ] `req_coverage.py` has ≥9 unit tests expanding beyond current AST-only coverage
- [ ] `absolution.py` has ≥2 unit tests (optional — may skip if trivial adds noise)
- [ ] All tests use `tmp_path` and mocks — no real git operations or external dependencies
- [ ] All test functions tagged with `@pytest.mark.req("REQ-YG-063")` (Testing & Quality)
- [ ] `pytest tests/unit/ -q --no-cov` passes with new tests
- [ ] No changes to the scripts themselves (test-only PR)

## Alternatives Considered

1. **Integration tests with real git repo** — Heavier, slower, fragile. Pure unit tests with mocks are sufficient for logic coverage.
2. **Test only pre-commit hooks, skip others** — This is the chosen approach. Non-hook scripts are excluded due to external dependencies or one-shot nature.
3. **Snapshot testing (capture stdout)** — Considered for `main()` functions but too brittle. Assert on return codes and key outputs instead.

## Implementation Notes

- Import scripts via `sys.path.insert(0, scripts_dir)` pattern (see `test_req_coverage_ast.py:16-17`)
- For `diary_rotate.py` tests, mock `subprocess.run` (git add) and use `monkeypatch` for `date.today()`
- For `noqa_coverage.py` tests, create minimal confessions.md fixtures in `tmp_path`
- Phase order reflects increasing complexity — start with quick wins

## Related

- `tests/unit/test_req_coverage_ast.py` — Existing partial coverage for `req_coverage.py`
- `tests/unit/test_lint_inline_llm.py` — Reference pattern for script testing
- `tests/unit/test_diary_digest.py` — Reference pattern for diary-related testing
- `.pre-commit-config.yaml` — Defines all hook scripts
- `ARCHITECTURE.md` REQ-YG-063 — Testing & Quality requirement
