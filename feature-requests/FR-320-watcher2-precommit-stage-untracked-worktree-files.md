# Feature Request: FR-320 watcher2 precommit stages untracked worktree files

**Priority:** HIGH
**Type:** Bug
**Status:** Implemented
**Effort:** 0.25 day
**Requested:** 2026-05-03

## Summary

Make watcher2 `precommit_check` stage untracked worktree files before running pre-commit so generated artifacts (for example diary files) are validated and included in the eventual PR diff.

## Value Statement

Watcher2 operators get deterministic precommit coverage for all generated artifacts, eliminating manual recovery when CI gates fail due to missing untracked files in the diff.

## Problem

Topic source `gh-312.md` reports repeated runs where `sanity_check` creates files but those files are not always staged before `precommit_check`, causing CI `diary-gate` failures downstream.

Current gap at boundary:

1. `.chaplain/actions/precommit_action.py` runs `pre-commit run --all-files` first, then stages only tracked modifications with `git add -u` on failure.
2. Untracked files created earlier in the pipeline are not guaranteed to be staged at precommit boundary.
3. `done` can still push/create PR without those untracked artifacts committed, producing gate failures and manual intervention.

Important context from in-repo research:

- FR-318 improved the `sanity_check` prompt to stage/commit diary files, but this remains prompt-level behavior and not a mechanical precommit invariant.
- FR-198 prior art already enforces `git add -A` around quality loops in watcher flow, showing a repository-approved pattern for complete staging.

## Objectives

1. Stage all changes (tracked + untracked) before `pre-commit run --all-files` in `PrecommitAction`.
2. Use full restaging in retry path so hook auto-fixes on newly tracked files are not dropped.
3. Keep scope limited to mechanical precommit boundary and targeted tests.

## Constraints

1. Scope limited to `.chaplain/actions/precommit_action.py` and directly coupled unit tests.
2. No FSM topology or transition changes in `.chaplain/config/watcher-pipeline-v2.yaml`.
3. No silent success fallback: staging failures must surface as `error`.
4. Preserve existing retry contract (`success`/`retry`/`error`, `max_attempts`, `precommit_output` capture).

## Proposed Solution

Update `PrecommitAction.execute()` to normalize index state at boundary:

1. Before running pre-commit, run `git add -A` in `cwd`.
2. If pre-stage fails, return `error` with explicit log (do not proceed to pre-commit).
3. Keep `pre-commit run --all-files` as gate command.
4. In retry path after pre-commit failure, replace `git add -u` with `git add -A` so new files and hook rewrites are staged consistently.

Rationale:

- `git add -A` captures new, modified, and deleted paths, while `-u` updates only tracked paths.
- Mechanical staging at `precommit_check` boundary protects against prompt drift and future artifact-producing steps.

## Acceptance Criteria

- [x] **AC-01:** `PrecommitAction` stages all changes via `git add -A` before invoking `pre-commit run --all-files`.
- [x] **AC-02:** If pre-stage fails, action emits `error` and does not run pre-commit.
- [x] **AC-03:** Retry restage path after pre-commit failure uses `git add -A` (not `git add -u`).
- [x] **AC-04:** Existing retry semantics remain: on pre-commit failure, action stores `precommit_output` and emits configured retry event unless attempt cap is exceeded.
- [x] **AC-05:** Existing success semantics remain unchanged when pre-commit passes.
- [x] **AC-06:** Acceptance tests are added in `tests/unit/test_fr320_watcher2_precommit_stage_untracked_worktree_files.py` and fail on current implementation (RED).

## Failing Acceptance Tests (RED plan)

Create `tests/unit/test_fr320_watcher2_precommit_stage_untracked_worktree_files.py`:

1. `test_ac01_stages_all_changes_before_precommit_run`
   - Monkeypatch subprocess calls and assert `git add -A` occurs before `pre-commit run --all-files`.
2. `test_ac02_stage_failure_returns_error_without_running_precommit`
   - Simulate failing `git add -A`; assert event is `error` and no pre-commit call occurs.
3. `test_ac03_retry_restage_uses_git_add_a_not_u`
   - Simulate pre-commit failure; assert retry path calls `git add -A` and never calls `git add -u`.
4. `test_ac04_ac05_retry_and_success_contracts_preserved`
   - Assert `precommit_output` capture and configured event behavior remains intact.

RED command:

```bash
pytest tests/unit/test_fr320_watcher2_precommit_stage_untracked_worktree_files.py -q --no-cov
```

## Research Findings

### In-repo prior art and evidence

1. **Issue signal still open:** GitHub issue #312 remains open with repeated evidence from PR #311, #307, #310.
2. **Current behavior source:** `.chaplain/actions/precommit_action.py` currently stages retry fixes with `git add -u` only.
3. **Pipeline boundary:** `.chaplain/config/watcher-pipeline-v2.yaml` routes `sanity_check -> precommit_check -> done`, so precommit is the last mechanical gate before push/PR.
4. **Partial mitigation already shipped:** FR-318 changed sanity-check prompt to stage+commit diary artifacts, but this does not guarantee future generated files outside that prompt contract.
5. **Repository-approved pattern:** FR-198 acceptance tests assert `git add -A` around quality loops.

### External evidence

1. `git add` documentation: `-A` stages new/modified/removed paths, while `-u` updates tracked paths only.
   Source: <https://git-scm.com/docs/git-add>

## Alternatives Considered

1. **Stage in sanity-check prompt only**
   Rejected: prompt-level instruction is not a mechanical gate and can drift.
2. **Stage in done/finalize step before push**
   Rejected: too late; precommit gate would still miss files.
3. **Keep `git add -u` and rely on FR-318 behavior**
   Rejected: does not cover non-diary untracked artifacts or future prompt regressions.
4. **Use `git add .` exactly as issue text suggests**
   Considered; `git add -A` chosen for explicit full-index semantics (including deletions) and consistency with prior watcher pattern.

## Related

- Topic source: `/Users/sheikki/Documents/src/yamlgraph/.chaplain/processing/gh-312.md`
- Issue: <https://github.com/sheikkinen/yamlgraph/issues/312>
- `.chaplain/actions/precommit_action.py`
- `.chaplain/config/watcher-pipeline-v2.yaml`
- `feature-requests/FR-318-watcher2-sanity-check-diary-commit-and-fr-derived-filename.md`
- `tests/unit/test_fr198_watcher2_finalize_optimization.py`
