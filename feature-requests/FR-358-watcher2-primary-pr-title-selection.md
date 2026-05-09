# Feature Request: FR-358 watcher2 PR title should use primary feat/fix commit

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-05-09

## Summary

Make watcher2 derive PR titles from the branch's primary implementation commit (prefer `feat`/`fix`) instead of the latest commit, so squash-merge commit history on `main` reflects the real change.

## Value Statement

Maintainers get accurate squash-merge commit subjects on `main`, preserving auditability and changelog signal for feature/fix work even when diary/format commits are appended later in the branch.

## Problem

Watcher2 currently sets PR title in `.chaplain/config/watcher-pipeline-v2.yaml` from:

```bash
PR_TITLE=$(git log -1 --format=%s)
```

When a branch has multiple commits (`feat` -> `chore(format)` -> `docs(diary)`), the final diary commit wins PR title. Because squash merge uses PR title as the merge commit message, `main` receives a docs/diary-flavored subject for feature work.

Issue evidence (GH-358 / PR #357):

1. Branch contained a primary feature commit (`feat(mcp): FR-355 ...`) plus later format + diary commits.
2. PR title was taken from the final diary commit.
3. Squash merge commit on `main` no longer represented the actual feature.

## Research: Existing Patterns, Evidence, and Gaps

1. **Current source of PR title is latest commit subject.**
   - `.chaplain/config/watcher-pipeline-v2.yaml` `done` action uses `git log -1 --format=%s`.
2. **A reusable PR helper exists but done path bypasses it.**
   - `.chaplain/lib/watcher/create_pr.sh` supports `--title`/existing-PR reuse, yet pipeline `done` currently shells `gh pr create` inline.
3. **Current deterministic gate is coupled to latest-commit title semantics.**
   - `.chaplain/actions/validate_gate_action.py` reads title from `git log -1 --format=%s`.
4. **Existing requirement and tests explicitly lock old behavior.**
   - `REQ-YG-318` (in `ARCHITECTURE.md` and `capabilities/CAP-140-watcher2-validate-split-fix-gate.yaml`) and
     `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py::test_ac09_done_pr_title_source_remains_latest_commit_subject`.
5. **Gap:** no branch-aware title-priority selection exists (feat/fix first, diary/format deprioritized).

## Objectives

1. Ensure watcher2 PR title reflects the branch's primary implementation commit.
2. Keep title selection deterministic for both new and existing PR update paths.
3. Preserve valid title fallback behavior for branches without `feat`/`fix` commits.
4. Keep validate-gate and done-title contracts aligned to avoid CI/local drift.

## Constraints

1. Scope is limited to watcher2 orchestration and its documented/tested contracts:
   - `.chaplain/config/watcher-pipeline-v2.yaml`
   - `.chaplain/actions/validate_gate_action.py`
   - `ARCHITECTURE.md`
   - `capabilities/CAP-140-watcher2-validate-split-fix-gate.yaml`
   - watcher2 acceptance tests under `tests/unit/`
2. No YAMLGraph runtime/provider/CLI feature work under `yamlgraph/`.
3. No new dependencies.
4. Single responsibility: PR title selection priority only.

## Proposed Solution

Implement a deterministic "primary PR title selector" for watcher2 branch commits:

1. Read branch commit subjects in chronological order (`origin/main..HEAD`, oldest first).
2. Select the first subject whose Conventional Commit type is `feat` or `fix`.
3. If none, select the first subject whose type is not `chore` or `docs`.
4. If still none (e.g., docs-only branch), fall back to the first subject.
5. Use that selected subject as `PR_TITLE` in `done` before `gh pr create` / PR reuse path.
6. Align validate-gate **diary-parity trigger** to use the same primary-title selector (not latest commit), and update REQ-YG-318/CAP-140 wording plus tests accordingly.

### In scope

1. Title-selection logic and wiring in watcher2 `done` path.
2. Diary-parity trigger parity in `validate_gate_action` using the same primary-title selector.
3. Requirement/acceptance test contract updates from "latest commit title" to "primary commit title policy".
4. Delete or replace `test_ac09_done_pr_title_source_remains_latest_commit_subject` in `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py` (it asserts the old `git log -1` behavior superseded by AC-01).

### Out of scope

1. Diary-gate policy redesign.
2. Branch naming, PR body templating, or merge strategy changes.
3. Generalized commit ranking framework beyond this priority rule.

## Acceptance Criteria

- [x] **AC-01:** watcher2 `done` action no longer derives PR title from `git log -1 --format=%s`.
- [x] **AC-02:** PR title selection prioritizes first `feat`/`fix` commit subject in branch history.
- [x] **AC-03:** If no `feat`/`fix` exists, selector falls back to first non-`chore`/non-`docs` subject.
- [x] **AC-04:** If only `docs`/`chore` commits exist, selector still returns a valid title (first commit fallback).
- [x] **AC-05:** In `validate_gate_action`, the **diary-parity trigger** (`diary_checked`) is derived from the primary commit title (feat/fix detection uses the same selector as `done`), not from the latest commit. The CC-format validation block (`commit_title` check) continues to validate the latest commit and is not in scope for this FR.
- [x] **AC-06:** `REQ-YG-318` and CAP-140 text are updated to reflect primary-title policy (replacing latest-commit policy).
- [x] **AC-07:** RED acceptance tests are present for AC-01..AC-06.
- [x] **AC-08:** `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py::test_ac09_done_pr_title_source_remains_latest_commit_subject` is deleted or replaced as superseded by AC-01 and AC-02 tests in this FR.

## Failing Acceptance Tests (RED plan)

Planned RED test module:

- `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py`

Planned RED tests:

1. `test_ac01_done_no_longer_uses_latest_commit_subject_for_pr_title`
2. `test_ac02_prefers_first_feat_or_fix_subject_when_later_diary_commit_exists`
3. `test_ac03_fallback_selects_first_non_docs_non_chore_subject`
4. `test_ac04_docs_only_branch_falls_back_to_first_subject`
5. `test_ac05_validate_gate_uses_same_primary_title_policy_as_done`
6. `test_ac06_req_yg_318_and_cap140_contract_text_updated_for_primary_title_policy`

RED command:

```bash
pytest tests/unit/test_fr358_watcher2_primary_pr_title_selection.py -q --no-cov
```

## Alternatives Considered

1. **Keep `git log -1 --format=%s` (status quo).**
   Rejected: diary/format tail commits continue to overwrite feature/fix PR titles.
2. **Always use first commit subject only.**
   Rejected: does not prioritize feat/fix when first commit is setup/chore.
3. **Require manual PR title override.**
   Rejected: leaks deterministic pipeline behavior into manual operator intervention.

## Related

- GitHub issue #358: <https://github.com/sheikkinen/yamlgraph/issues/358>
- Evidence PR: <https://github.com/sheikkinen/yamlgraph/pull/357>
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `.chaplain/actions/validate_gate_action.py`
- `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`
- `ARCHITECTURE.md`
- `capabilities/CAP-140-watcher2-validate-split-fix-gate.yaml`

## Topic Source Note

Requested source file `.chaplain/processing/gh-358.md` was not present in this worktree snapshot; canonical issue content from GitHub issue #358 was used.
