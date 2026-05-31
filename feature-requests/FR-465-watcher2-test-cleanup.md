# Feature Request: Delete retired watcher2 tests

**Priority:** HIGH
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-05-31
**Depends-on:** FR-466 (CAP retirement support)

## Summary

Delete 10 permanently-skipped watcher2 test files (84 skipped tests) and mark 4 retired CAP files with `status: retired`. Identified by the 2026-05-29 audit (`docs/2026-05-29-audit/12-pytest-analysis.md`).

## Value Statement

The test suite drops 84 false skips (60% of all skips), making the skip count an honest signal again — every remaining skip has a real reason.

## Problem

The watcher2 pipeline was retired in FR-317. Ten test files still exist with `pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")`. They contribute 84 of 139 total skips, drowning real skips in noise.

**Files to delete (10):**

| File | Tests | REQs |
|------|-------|------|
| `test_fr191_diary_filename_normalization.py` | 11 | REQ-YG-188 |
| `test_fr198_watcher2_finalize_optimization.py` | 9 | REQ-YG-286 |
| `test_fr279_watcher2_ci_resilience.py` | 5 | REQ-YG-294, 298–301 |
| `test_fr280_watcher2_red_verification_timestamp_fix.py` | 12 | REQ-YG-263 |
| `test_fr281_watcher2_ruff_unsafe_fixes.py` | 10 | REQ-YG-287 |
| `test_fr283_watcher2_changelog_auto_generation.py` | 9 | REQ-YG-308 |
| `test_fr284_watcher2_ci_remediation_crash_fix.py` | 7 | REQ-YG-307 |
| `test_fr286_watcher2_merged_branch_collision_guard.py` | 8 | REQ-YG-276 |
| `test_fr287_watcher2_deduplication_gate.py` | 9 | REQ-YG-276 |
| `test_fr288_watcher2_hook_preflight_gate.py` | 9 | REQ-YG-276 |

**Orphaned REQ IDs** (no other test coverage after deletion): REQ-YG-286, REQ-YG-298, REQ-YG-299, REQ-YG-300, REQ-YG-301, REQ-YG-307, REQ-YG-308. These are in 4 retired CAP files that must be marked `status: retired` (requires FR-466).

**Scope guard:** 18 other watcher/FSM test files (test_fr289 through test_fr423) are NOT skipped, pass, and test active `.chaplain/` infrastructure. These are **not** in scope.

## Proposed Solution

1. `git rm` the 10 skipped watcher2 test files
2. Add `status: retired` to 4 CAP files: CAP-130, CAP-132, CAP-133, CAP-134 (uses FR-466 machinery)
3. Run `python scripts/req_coverage.py --strict` — must pass (retired REQs excluded)
4. Run full test suite — skip count drops from 139 to ~55

## Acceptance Criteria

- [ ] 10 module-skipped watcher2 test files deleted
- [ ] 4 retired CAP files marked `status: retired` (CAP-130, CAP-132, CAP-133, CAP-134)
- [ ] `req_coverage.py --strict` passes
- [ ] Full pytest passes with skip count ≤ 60
- [ ] No active test file deleted (18 non-skipped watcher/FSM files untouched)

## Alternatives Considered

- **Archive to `tests/archived/`** — adds complexity for no value; git history preserves everything.
- **Keep and ignore** — 84 false skips erode trust in the skip count as a signal.
- **Delete CAP files instead of retiring** — loses historical record; retirement is the proper lifecycle.

## Judgement

**Verdict: APPROVED (revised scope).**

### Watcher2 deletion — APPROVED as-is

Clean scope. 10 files, all with `pytestmark = pytest.mark.skip(reason="Legacy watcher2 runtime retired (FR-317)")`. 84 skipped tests. Git history preserves content. No ambiguity.

The explicit scope guard ("18 non-skipped watcher/FSM files are NOT in scope") is correct and verified — those files test active `.chaplain/` infrastructure and pass.

### FR-392 consolidation — REMOVED from scope

Judgement found the FR-392 pairs are **not duplicates** — they have different REQ tags (319 vs 347), different edge cases, and different assertions. Merging them is cosmetic refactoring on passing tests, not dead code removal. If it bothers someone later, it's a separate FR.

### Orphaned REQs — depends on FR-466

`req_coverage.py` has no concept of "retired." Adding `status: retired` to CAP YAML requires FR-466 to teach the script to filter retired REQs. This is a clean 2-FR dependency chain, not scope creep.

## Related

- FR-317: Watcher2 pipeline retirement
- FR-466: CAP retirement support in req_coverage.py (pre-req)
- `docs/2026-05-29-audit/12-pytest-analysis.md`: Audit finding (P1 recommendation)
