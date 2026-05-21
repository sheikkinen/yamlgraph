# Feature Request: FR-441 Pre-commit files patterns for scoped hook execution

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-21

## Summary

Add `files:` selectors to file-scoped local pre-commit hooks and remove unnecessary `always_run: true`, so commits only run hooks relevant to staged file types.

## Value Statement

Contributors get materially faster docs-only and diary-only commits while preserving current enforcement coverage for Python and YAML changes.

## Problem

`.pre-commit-config.yaml` currently marks many local hooks as `always_run: true`, including expensive Python scans and full unit tests. This makes docs-only commits run the same heavy stack as code commits.

Issue #429 reports this as the core pain point: markdown-only changes still trigger vulture, jscpd, radon, import-linter, and pytest.

Current prior art exists in this same config: `dependency-rationale` already uses a narrow `files:` selector, proving the pattern is compatible with repository conventions.

## Proposed Solution

Add `files:` patterns to the following local hooks and remove `always_run: true` from these hooks:

| Hook ID | `files:` pattern |
|---|---|
| `req-coverage-strict` | `(^yamlgraph/|^tests/|^ARCHITECTURE\\.md$|^capabilities/|^scripts/req_coverage\\.py$)` |
| `validate-capabilities` | `(^capabilities/|^scripts/validate_capabilities\\.py$)` |
| `validate-id-registry` | `(^capabilities/|^scripts/validate_id_registry\\.py$)` |
| `noqa-confession` | `(\\.py$|^docs/confessions\\.md$|^scripts/noqa_coverage\\.py$)` |
| `inline-llm-check` | `(\\.py$|^scripts/lint_inline_llm\\.py$)` |
| `radon-complexity` | `\\.py$` |
| `file-size-gate` | `\\.py$` |
| `forbid-terms` | `\\.py$` |
| `jscpd-dup` | `\\.py$` |
| `import-linter` | `(\\.py$|^\\.importlinter$)` |
| `vulture-dead-code` | `(\\.py$|^vulture_whitelist\\.py$)` |
| `hedging-check` | `\\.py$` |
| `changelog-release-sync` | `(^changelog/|^pyproject\\.toml$|^scripts/check_changelog_release_sync\\.py$|^scripts/release\\.sh$)` |
| `changelog-req-cross-check` | `(^changelog/|^capabilities/|^scripts/check_changelog_req\\.py$)` |
| `diary-reflection-check` | `^docs/diary/` |
| `diary-filename-check` | `^docs/diary/` |
| `pytest` | `(\\.py$|\\.yaml$|\\.yml$|^pyproject\\.toml$)` |

Hooks that remain `always_run: true` in this FR (verified from config):

1. `diary-rotate` (scheduled side effect; not file-triggered) — has `always_run: true`
2. `final-summary` (session-level summary behavior) — has `always_run: true`

Hooks that have no `files:` pattern and no `always_run: true` and must stay unchanged:

3. `demo-proof-check` (cross-cutting staged diff policy) — no `always_run:`, no `files:`; FR-441 must not add either
4. `gitignore-boundary-guard` (workspace boundary safety) — no `always_run:`, no `files:`; FR-441 must not add either

### Scope constraints

- No hook script logic changes in `scripts/` (configuration-only change)
- No commit-msg hook changes
- No enforcement removals; only invocation scoping by file relevance

## Failing Acceptance Tests (RED)

Create `tests/unit/test_fr441_precommit_files_patterns_red.py` first, and keep it RED until config changes land.

Planned tests:

1. `test_ac01_target_hooks_define_files_patterns`
   Parse `.pre-commit-config.yaml`; assert each hook in the table above has the expected `files` regex.
2. `test_ac02_target_hooks_do_not_use_always_run`
   Assert those same hooks do not have `always_run: true`.
3. `test_ac03_cross_cutting_hooks_not_modified_by_fr441`
   Assert `diary-rotate` and `final-summary` have `always_run: true`.
   Assert `demo-proof-check` and `gitignore-boundary-guard` have neither `always_run: true` nor a `files:` key (FR-441 must not add either).
4. `test_ac04_pytest_hook_pattern_covers_code_and_yaml`
   Assert `pytest` hook `files` regex includes `.py`, `.yaml`, `.yml`, and `pyproject.toml`.
5. `test_ac05_dependency_rationale_existing_scope_unchanged`
   Assert existing `dependency-rationale` `files` selector is unchanged by FR-441.

## Acceptance Criteria

- [x] All hook IDs listed in the solution table have `files:` selectors in `.pre-commit-config.yaml`
- [x] `always_run: true` is removed from those same hook entries
- [x] `diary-rotate` and `final-summary` retain `always_run: true`; `demo-proof-check` and `gitignore-boundary-guard` gain neither `always_run: true` nor `files:`
- [x] Commit-msg hooks are unchanged
- [x] RED acceptance tests are added first and fail before config edits
- [x] After implementation, RED tests turn GREEN without changing hook script semantics

## Alternatives Considered

- Keep all hooks `always_run: true`: rejected; preserves known commit latency pain with no safety gain for docs-only edits.
- Move heavy hooks to CI only: rejected; weakens local fast feedback and increases late failure.
- Add changed-file checks inside each script instead of pre-commit `files:`: rejected; duplicates dispatch logic and increases script complexity.

## Related

- GitHub issue: `#429` — FR-441 request and proposed patterns
- `.pre-commit-config.yaml` — target file for scoped dispatch
- `feature-requests/FR-219-dependency-rationale-audit.md` — prior art for `files:`-scoped local hook
- `feature-requests/FR-293-pytest-xdist-parallel-tests.md` — existing pytest hook performance focus
- `ARCHITECTURE.md` capability map entries touching pre-commit enforcement (Diary, Changelog, Demo gates)

## Judge Notes

**2026-05-21 — AMEND → APPROVE (corrections applied in-place)**

Two issues found and corrected before authority was granted:

1. **Factual error in "remains always_run" list.**
   The FR claimed all four cross-cutting hooks (`diary-rotate`, `demo-proof-check`, `gitignore-boundary-guard`, `final-summary`) have `always_run: true`. Verified against the live config: `demo-proof-check` (lines 189–194) and `gitignore-boundary-guard` (lines 180–185) have neither `always_run: true` nor a `files:` key. They run on any commit with staged files by default. The FR scope section and AC03 have been corrected to reflect this.

2. **AC03 non-deterministic assertion.**
   "Where applicable" made the test impossible to write without ambiguity. Replaced with two concrete assertions: `diary-rotate` and `final-summary` retain `always_run: true`; `demo-proof-check` and `gitignore-boundary-guard` must gain neither `always_run: true` nor `files:`.

**Post-correction verdict: APPROVE.** Scope is minimal and config-only. All 17 hook patterns are explicit. Tests AC01–AC05 are now fully deterministic. Prior art (`dependency-rationale`) confirms the pattern is repo-compatible.
