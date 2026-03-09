# Feature Request: Sequential Enforcement Mode

**Priority:** HIGH
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-09

## Summary

Replace parallel `nohup ... &` enforcement spawning in `.chaplain/watch.sh` with a sequential queue that waits for each enforcement pipeline to complete before starting the next.

## Value Statement

The Chaplain pipeline eliminates manual merge-conflict resolution by serializing enforcement, so each PR lands on a clean `main` before the next begins.

## Problem

When `watch.sh` processes multiple inbox items in rapid succession, it spawns concurrent `enforce_worktree.sh` and `bugfix_worktree.sh` processes via `nohup ... &`. Each pipeline creates a worktree branched from the same `main` HEAD and modifies shared files:

- **ARCHITECTURE.md** — capability/requirement counts incremented by each FR
- **CHANGELOG.md** — both PRs append to the same `## [Unreleased]` section
- **scripts/req_coverage.py** — capability maps extended by each FR

The result: every second PR conflicts. Session PRs #31–43 required multiple rebase cycles. Manual conflict resolution is error-prone and wastes human time on a pipeline designed to be autonomous.

Root cause: parallel spawning assumes independent worktrees produce non-overlapping diffs. In practice, the shared bookkeeping files violate that assumption on nearly every enforcement run.

## Proposed Solution

Replace the `nohup ... &` fire-and-forget pattern with a **foreground wait** in the watch loop. After spawning an enforcement pipeline, `watch.sh` blocks until the child process exits before polling for the next inbox item.

```bash
# Current (parallel):
nohup scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 &
echo "   PID: $!"

# Proposed (sequential):
echo "🚀 Enforcing: $new_fr (sequential, log: $LOG)"
scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1
EXIT_CODE=$?
echo "   Completed: exit $EXIT_CODE"
```

Same change applies to the `bugfix_worktree.sh` branch (FR-173 route).

### Behavior changes

| Aspect | Before | After |
|--------|--------|-------|
| Enforcement concurrency | Parallel (N pipelines) | Sequential (1 at a time) |
| Inbox processing | Immediate spawn per FR | Queued — next FR waits |
| Merge conflicts on shared files | Frequent | Eliminated (each PR merges to updated `main`) |
| Total wall-clock time | ~T (parallel) | ~N×T (sequential) |
| watch.sh availability | Always polling | Blocked during enforcement |
| Error isolation | Background PID, check logs | Foreground exit code, inline |

### Error handling

On non-zero exit from the enforcement script, log the failure and continue to the next inbox item. Do not abort the watch loop:

```bash
if [[ $EXIT_CODE -ne 0 ]]; then
    echo "⚠️  Enforcement failed (exit $EXIT_CODE) for: $new_fr — see $LOG"
fi
```

## Acceptance Criteria

- [ ] `watch.sh` runs enforcement pipelines sequentially (foreground, not `nohup ... &`)
- [ ] `bugfix_worktree.sh` route is also sequential (same treatment as enforce)
- [ ] Non-zero exit from enforcement does not crash the watch loop
- [ ] Exit code and log path are printed after each enforcement completes
- [ ] Existing `set -euo pipefail` does not cause watch loop to abort on enforcement failure
- [ ] No changes to `enforce_worktree.sh` or `bugfix_worktree.sh` internals
- [ ] Tests added (shellcheck lint on watch.sh; integration test confirming sequential execution order)
- [ ] Documentation updated (CHANGELOG.md, this FR status)

## Alternatives Considered

1. **File-lock gating**: Use `flock` to serialize only the PR-submission phase. More concurrent but adds complexity; the shared-file conflict window spans the entire implementation phase, not just submission.

2. **Rebase-before-push retry loop**: Let pipelines run in parallel but auto-rebase on conflict. Fragile — semantic conflicts (duplicate CHANGELOG entries, double-incremented counts) are not auto-resolvable.

3. **Split shared files into per-FR fragments**: E.g., `changelog.d/` directory with per-PR files merged at release time. Eliminates structural conflicts but requires tooling changes across the project. Orthogonal improvement; can be pursued later.

## Related

- `.chaplain/watch.sh` — primary change target
- `scripts/enforce_worktree.sh` — called sequentially (no internal changes)
- `scripts/bugfix_worktree.sh` — called sequentially (no internal changes)
- FR-116: New FR detection via ephemeral diff
- FR-173: Bug-type FR routing to bugfix pipeline
