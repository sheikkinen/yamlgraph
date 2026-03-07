# Feature Request: Spawn enforce_worktree.sh from watch.sh on New FR

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Rejected
**Effort:** 0.5 days
**Requested:** 2026-03-07

## Summary

After `watch.sh` processes an inbox topic through the Plan→Judge graph and produces an approved FR in `feature-requests/`, automatically spawn `scripts/enforce_worktree.sh` in the background — without blocking the inbox polling loop.

## Value Statement

The chaplain loop gains end-to-end autonomy: topic → FR → implementation branch → PR, with zero human intervention between watch.sh and enforce_worktree.sh.

## Problem

Today, `watch.sh` produces approved feature requests in `feature-requests/` but stops there. A human must manually invoke `scripts/enforce_worktree.sh <path>` to start implementation. This breaks the autonomous pipeline aspiration.

A previous attempt (FR-114) was merged then reverted the same day. The root cause was twofold:
1. Copilot nodes returning exit code 1 propagated through `set -euo pipefail` and killed the watch loop.
2. The implementation used SHA-tracking state files and Python helper functions — unnecessary complexity.

This retry is deliberately conservative: pure shell, no state files, no Python helpers, background-detached spawn.

## Proposed Solution

Add a post-graph hook to `watch.sh` that:

1. Snapshots `feature-requests/` file list before running the graph
2. After the graph completes, diffs the file list to detect any new FR file
3. If a new FR is found and its status is not `Rejected`, spawns `enforce_worktree.sh` in the background with `nohup` and redirects output to a log file
4. Continues the polling loop immediately (does not wait for enforce to finish)

```bash
# In watch.sh, around the graph invocation:

# Snapshot before
before=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)

yamlgraph graph run examples/copilot/graph.yaml \
    --var topic_file="$topic_file" \
    --var drafts_dir="$DRAFTS" \
    --var date="$(date +%Y-%m-%d)" \
    --var diary_prefix="Chaplain" \
    --full

# Detect new FR
after=$(find feature-requests -maxdepth 1 -name "*.md" -type f 2>/dev/null | sort)
new_fr=$(comm -13 <(echo "$before") <(echo "$after") | head -1)

if [[ -n "$new_fr" ]]; then
    if grep -q 'Status.*Rejected' "$new_fr" 2>/dev/null; then
        echo "⏭️  Skipping rejected FR: $new_fr"
    else
        echo "🚀 Spawning enforce pipeline for: $new_fr"
        mkdir -p tmp
        LOG="tmp/enforce-$(basename "$new_fr" .md).log"
        nohup scripts/enforce_worktree.sh "$new_fr" > "$LOG" 2>&1 &
        echo "   PID: $!  Log: $LOG"
    fi
fi
```

### Guard Rails

- **Isolation**: `enforce_worktree.sh` already runs in its own git worktree — a crash there cannot corrupt the main tree or the watch loop.
- **No exit code propagation**: `nohup ... &` detaches enforce from the watch process; its exit code is never checked by watch.sh. This directly addresses the FR-114 failure mode.
- **Idempotent**: If enforce fails (branch exists, worktree exists), it logs the error and exits — watch.sh is unaffected.
- **Log visibility**: Output goes to `tmp/enforce-FR-XXX-slug.log` for post-mortem.
- **mkdir -p tmp**: Ensures the log directory exists before writing (safe even if already present).

### Difference from FR-114

| Aspect | FR-114 (reverted) | FR-117 (this) |
|--------|-------------------|---------------|
| Detection | SHA-tracking via `.chaplain/.last-enforce-sha` | Ephemeral `find` + `comm` diff |
| Code | Python helpers in `worktree_helpers.py` | Pure shell, no new files |
| Error isolation | Exit code propagated through `set -e` | `nohup ... &` fully detached |
| Complexity | ~400 lines added (Python + tests + shell) | ~15 lines added to watch.sh |

## Acceptance Criteria

- [ ] `watch.sh` snapshots `feature-requests/` before graph execution and diffs after
- [ ] New FR files are detected via `comm -13` between before/after snapshots
- [ ] Rejected FRs (matching `Status.*Rejected` in content) are skipped with log message
- [ ] `enforce_worktree.sh` is spawned via `nohup ... &`, not blocking the poll loop
- [ ] Enforce output is redirected to `tmp/enforce-<slug>.log`
- [ ] `mkdir -p tmp` ensures the log directory exists
- [ ] A failing enforce process does not crash or affect the watch loop
- [ ] No state files, no Python helpers — detection is ephemeral per loop iteration
- [ ] Smoke-testable: drop a topic in inbox, observe FR creation, observe enforce spawn in logs

## Alternatives Considered

1. **Graph-internal spawning (via tool node)**: Adding an `enforce` tool to `examples/copilot/graph.yaml` that shells out. Rejected — mixes orchestration concerns into the LLM graph; a tool node failure would break the graph state.

2. **Filesystem watcher (`fswatch`/`inotifywait`)**: A separate process watching `feature-requests/` for new files. Rejected — adds a dependency and a second daemon to manage. The `find` diff in watch.sh is simpler and sufficient given the 5-second poll interval.

3. **Status file tracking (FR-114 approach)**: Writing processed FRs to a `.chaplain/.last-enforce-sha` ledger with Python helpers. Rejected — proved fragile when exit codes propagated; unnecessary complexity for a problem solvable with ephemeral shell state.

## Rejection Reason

**Duplicate of FR-116.** The work described in this FR was already implemented and merged in commit `4765fdc` ("feat: FR-116 implementation (#4)", 2026-03-07). The code in `.chaplain/watch.sh` already contains the `find`+`comm` snapshot-diff logic, rejected-FR skipping, and `nohup` background spawn — character-for-character identical to what this FR proposes. Tests exist in `tests/unit/test_watch_enforce_spawn.py` (314 lines) and a demo in `examples/demos/watch-enforce/demo_detect.sh`.

This FR was likely generated from a chaplain inbox topic that was unaware FR-116 had already landed. The FR references FR-114 (the reverted attempt) but omits FR-116 (the successful retry), confirming stale context.

## Related

- `scripts/enforce_worktree.sh` — The pipeline to spawn (FR-106)
- `.chaplain/watch.sh` — The integration target (FR-084, FR-098)
- `examples/copilot/graph.yaml` — The Plan→Judge graph
- FR-114 — Previous failed attempt (reverted; exit code propagation + complexity)
- FR-116 — **Successful implementation** (commit `4765fdc`, already merged)
- FR-106 — Parallel worktree pipeline (provides enforce_worktree.sh)
