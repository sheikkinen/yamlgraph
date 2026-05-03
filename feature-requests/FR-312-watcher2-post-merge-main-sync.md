# Feature Request: FR-312 watcher2 post-merge main sync with stash-pull-rebase-pop

**Priority:** HIGH
**Type:** Bug
**Status:** Draft
**Effort:** 0.5 days
**Requested:** 2026-05-03

## Summary

Harden watcher2 post-merge cleanup so `main` is synchronized even when local unstaged changes exist, by performing conditional stash → pull --rebase → stash pop.

## Value Statement

Watcher2 operators keep local uncommitted edits safe while preventing `main` drift that causes downstream worktree-cycle failures.

## Problem

Topic `gh-277.md` requests deterministic post-merge reconciliation:

1. `git stash` (if dirty)
2. `git pull --rebase`
3. `git stash pop` (if stashed)

Current behavior does not satisfy this boundary:

- `.chaplain/lib/watcher/worktree_teardown.sh` runs `git pull --ff-only --quiet` and only logs a warning on failure.
- `.chaplain/lib/watcher/preflight.sh` also runs a best-effort `git pull --ff-only --quiet` and continues on failure.
- `.chaplain/lib/watcher/post_merge.sh` currently handles issue close + FR-token inbox consumption, but has no main-sync reconciliation.

When local unstaged changes exist in the main worktree, `git pull --ff-only` can fail, watcher2 continues, and the next cycle may start from a stale local `main`.

## Objectives

1. Ensure post-merge always attempts to sync local `main` to `origin/main`.
2. Preserve local uncommitted work instead of blocking or discarding it.
3. Keep scope limited to watcher2 shell orchestration boundaries.

## Constraints

- Scope is limited to watcher2 shell/docs/tests (`.chaplain/lib/watcher/post_merge.sh`, `.chaplain/README.md`, and a new unit test file).
- Do not change YAMLGraph runtime, node types, or CLI behavior.
- Do not use destructive reconciliation (`git reset --hard`, checkout discard patterns).
- Keep existing post-merge responsibilities intact (issue close + FR-token cleanup).
- No new dependencies.

## Proposed Solution

Implement a `sync_main_after_merge` path inside `.chaplain/lib/watcher/post_merge.sh` and call it from `post_merge()` after existing issue-close/token-cleanup logic.

### 1. Conditional stash at the boundary

- Detect dirty state via `git status --porcelain`.
- If dirty, run:
  - `git stash push --include-untracked -m "watcher2-post-merge-<timestamp>"`
- Track whether stash happened to gate later pop.

### 2. Rebase pull on main

- Ensure execution from main worktree branch (`main`).
- Run:
  - `git pull --rebase --quiet origin main`

### 3. Conditional stash pop restoration

- If a stash entry was created in step 1, run:
  - `git stash pop`
- Log reconciliation outcome explicitly.
- If pop fails/conflicts, surface the error (no silent success-shaped fallback).

### 4. Documentation update

Update `.chaplain/README.md` post-merge section to document the stash/pull-rebase/pop reconciliation and why it exists.

## Acceptance Criteria

- [ ] **AC-01:** `post_merge.sh` detects dirty working tree state before pulling.
- [ ] **AC-02:** When dirty, `post_merge.sh` stashes tracked + untracked changes with a watcher2 post-merge message.
- [ ] **AC-03:** `post_merge.sh` executes `git pull --rebase` against `origin main`.
- [ ] **AC-04:** `git stash pop` is attempted only when stash was created in AC-02.
- [ ] **AC-05:** Clean working tree path still performs pull/rebase and does not create/pop stash.
- [ ] **AC-06:** Stash/pop/pull failures are surfaced via logs and non-silent control flow (no hidden ignore path).
- [ ] **AC-07:** Existing post-merge behaviors remain: issue close for `gh-*.md` and FR-token inbox consumption.
- [ ] **AC-08:** Failing acceptance tests are added in `tests/unit/test_fr312_watcher2_post_merge_main_sync.py`.
- [ ] **AC-09:** `.chaplain/README.md` documents the new post-merge reconciliation contract.

## Failing Acceptance Tests (RED plan)

Create `tests/unit/test_fr312_watcher2_post_merge_main_sync.py` with `@pytest.mark.req("REQ-YG-276")` coverage for AC-01..AC-09.

Planned RED tests:

1. `test_ac01_ac02_detects_dirty_state_and_stashes_include_untracked`
   Assert `post_merge.sh` contains dirty-tree detection and `git stash push --include-untracked` with post-merge message.
2. `test_ac03_uses_pull_rebase_on_origin_main`
   Assert `git pull --rebase` path is present and references `origin main`.
3. `test_ac04_ac05_pop_is_conditional_on_prior_stash`
   Assert stash-pop branch is gated by an explicit stash-created flag and clean path does not pop.
4. `test_ac06_no_silent_ignore_on_sync_failures`
   Assert sync path does not end in unconditional success when pull/pop fails.
5. `test_ac07_existing_post_merge_behaviors_still_present`
   Assert issue close logic and FR-token inbox consumption helpers remain.
6. `test_ac09_readme_documents_post_merge_reconciliation`
   Assert `.chaplain/README.md` mentions stash/pull-rebase/pop in post-merge behavior.

RED command (expected to fail before implementation):

```bash
pytest tests/unit/test_fr312_watcher2_post_merge_main_sync.py -q --no-cov
```

## Alternatives Considered

1. **Keep current best-effort `git pull --ff-only` in preflight/teardown only**
   Rejected: this is current behavior; dirty trees still cause pull failures and local-main drift.
2. **Fail pipeline whenever main is dirty**
   Rejected: safe but blocks legitimate local parallel work and does not preserve that work.
3. **Force-clean main (`reset --hard`) before pull**
   Rejected: violates local-change safety and can destroy uncommitted work.
4. **Move reconciliation into worktree setup instead of post-merge**
   Rejected: too late in the cycle and does not enforce immediate post-merge boundary normalization.

## Related

- Topic source: `.chaplain/processing/gh-277.md` (root repository queue)
- `.chaplain/lib/watcher/post_merge.sh`
- `.chaplain/lib/watcher/worktree_teardown.sh`
- `.chaplain/lib/watcher/preflight.sh`
- `.chaplain/watcher2.sh`
- `feature-requests/FR-289-watcher2-post-merge-inbox-consumption.md`

## Research Brief

### Existing Abstractions and Prior Art (in-repo)

- `worktree_teardown.sh` already tries to sync main after teardown, but with `git pull --ff-only --quiet` and warn-only failure handling.
- `preflight.sh` repeats the same best-effort `--ff-only` pull and continues when it fails.
- `post_merge.sh` is the lifecycle boundary where merge-success cleanup already runs (issue close + FR-token cleanup), making it the right place for deterministic post-merge reconciliation.
- `reference/release-checklist.md` documents the same manual conflict-safe pattern (`git stash` → `git pull` → `git stash pop`) as operational guidance.

### External Evidence

- `git stash` is explicitly intended to save dirty working directory/index state and restore it later (`git stash pop`).
  Source: <https://git-scm.com/docs/git-stash>
- `git pull --rebase` is a first-class integration mode of `git pull` for integrating upstream via rebase.
  Source: <https://git-scm.com/docs/git-pull>
- GitHub guidance warns `pull` integrates remote changes and local work should be committed/stashed beforehand to avoid conflicts.
  Source: <https://docs.github.com/en/get-started/using-git/getting-changes-from-a-remote-repository>

### Classification Signal

- Abstraction level: **integration**
- Recommended approach: **build**
- Key risk: stash-pop conflicts after rebase; must be explicit and visible, not silently ignored.
