# Feature Request: fix(watcher): worktree_setup.sh should clean stale branches on retry

**Priority:** HIGH
**Type:** Bug
**Status:** Draft
**Effort:** 1 day
**Requested:** 2026-05-05

## Summary

`worktree_setup.sh` fails with `git worktree add --new-branch` when a pipeline run is re-queued because the branch `feat/watcher2-gh-XXX` already exists locally and/or remotely from the previous failed run. The script must detect and clean up stale branches and worktrees before attempting a fresh setup.

## Value Statement

Pipeline operators get automatic recovery from re-queued runs without manual `git branch -D` / `git push origin --delete` intervention, eliminating a repetitive failure mode that blocks every retried issue dispatch.

## Problem

When a pipeline run fails and is re-queued, `worktree_setup.sh` calls `git worktree add --new-branch feat/watcher2-gh-XXX` which errors immediately if the branch already exists from the prior attempt. The pipeline transitions directly to `failed`, requiring a human to manually delete both the local branch and its remote tracking ref before the dispatcher can process the issue again.

Every re-queued issue hits this path. gh-304 failed three consecutive times solely due to this condition. The manual remediation steps (`git branch -D feat/watcher2-gh-XXX && git push origin --delete feat/watcher2-gh-XXX`) are undocumented and error-prone.

## Proposed Solution

Add a pre-flight cleanup step inside `worktree_setup.sh` that runs before `git worktree add`:

1. **Detect** a worktree registered for the target branch: `git worktree list --porcelain | grep <slug>`
2. **Remove stale worktree** (if found): `git worktree remove --force <path>`
3. **Delete local branch** (if exists): `git branch -D <branch>` (no-op if absent)
4. **Optionally delete remote branch** (if `WATCHER_CLEANUP_REMOTE=true`): `git push origin --delete <branch>` — guarded by an env flag so behaviour is opt-in for repos that protect remote branches.
5. Proceed with the existing `git worktree add --new-branch <branch>` call.

```bash
# worktree_setup.sh — stale-branch cleanup (new section before worktree add)
BRANCH="feat/watcher2-gh-${ISSUE_NUMBER}"
WORKTREE_PATH="${WORKTREE_ROOT}/${BRANCH}"

# 1. Remove stale worktree entry
if git worktree list --porcelain | grep -q "branch refs/heads/${BRANCH}"; then
  echo "[watcher] removing stale worktree for ${BRANCH}"
  git worktree remove --force "${WORKTREE_PATH}" || true
fi

# 2. Delete local branch
if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  echo "[watcher] deleting stale local branch ${BRANCH}"
  git branch -D "${BRANCH}"
fi

# 3. Optionally delete remote branch
if [[ "${WATCHER_CLEANUP_REMOTE:-false}" == "true" ]]; then
  if git ls-remote --exit-code origin "${BRANCH}" > /dev/null 2>&1; then
    echo "[watcher] deleting stale remote branch ${BRANCH}"
    git push origin --delete "${BRANCH}" || true
  fi
fi
```

## Acceptance Criteria

- [ ] `worktree_setup.sh` successfully completes when the target branch already exists locally
- [ ] `worktree_setup.sh` successfully completes when the target branch has a stale registered worktree
- [ ] Remote branch deletion is gated behind `WATCHER_CLEANUP_REMOTE=true` env var (default: `false`)
- [ ] Cleanup steps are no-ops (not errors) when no stale state exists
- [ ] Existing unit / integration tests for `worktree_setup.sh` continue to pass
- [ ] New test case: re-queue scenario where branch + worktree pre-exist
- [ ] Documentation updated in `docs/watcher.md` (or equivalent) describing retry behaviour and the `WATCHER_CLEANUP_REMOTE` flag

## Alternatives Considered

- **`--force` on `git worktree add`**: Not directly supported; `--force` allows adding a checked-out branch but does not handle an existing-but-absent worktree directory, making it unreliable.
- **Rename branch on retry** (e.g., append `-retry-N` suffix): Leaves orphaned remote branches and complicates PR linkage; rejected in favour of clean replacement.
- **Fail fast with actionable error message only**: Reduces noise but still requires manual intervention; unacceptable for an automated pipeline.

## Related

- gh-304 — failed 3 consecutive times due to this bug
- #233 — branch name collision with previously merged PRs (related upstream cause)
