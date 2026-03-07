# Feature Request: Integrate enforce_worktree.sh into watch.sh Loop

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Approved — Scope Frozen
**Effort:** 1 day
**Requested:** 2026-03-07

## Summary

Extend `.chaplain/watch.sh` to detect approved feature requests and automatically invoke `scripts/enforce_worktree.sh`, closing the gap between the Plan→Judge phase (FR-068) and the Enforce phase (FR-106) into a single autonomous pipeline.

## Value Statement

Maintainers get a fully autonomous Plan→Judge→Enforce pipeline, eliminating the manual step of running `enforce_worktree.sh` after a feature request is approved.

## Problem

Today the chaplain workflow has two disconnected stages:

1. **Plan→Judge** (automated via `watch.sh` + `examples/copilot/graph.yaml`): A topic file dropped in `.chaplain/inbox/` is planned, judged, and written to `.chaplain/drafts/`. The user manually reviews and moves the approved FR to `feature-requests/`.

2. **Enforce** (manual via `scripts/enforce_worktree.sh <fr_path>`): The user must remember to invoke the enforce script on the approved FR.

The handoff between stages 1 and 2 is manual and error-prone. An approved FR can sit unimplemented simply because nobody ran the enforce script.

## Proposed Solution

Add a second polling loop (or extend the existing one) in `watch.sh` that watches `feature-requests/` for newly committed FRs and triggers `enforce_worktree.sh`.

### Detection mechanism

Use `git diff --name-only HEAD~1 HEAD -- feature-requests/` to detect FRs that were committed since the last check. This avoids false triggers on existing FRs and aligns with the existing commit-based workflow.

Track the last-checked commit SHA in a state file (`.chaplain/.last-enforce-sha`) to avoid re-processing.

### Updated watch.sh flow

```bash
# Existing inbox loop (unchanged)
# ...

# New: Enforce loop — runs after inbox processing
LAST_SHA_FILE=".chaplain/.last-enforce-sha"
last_sha=$(cat "$LAST_SHA_FILE" 2>/dev/null || git rev-parse HEAD)
current_sha=$(git rev-parse HEAD)

if [[ "$last_sha" != "$current_sha" ]]; then
    new_frs=$(git diff --name-only "$last_sha" "$current_sha" -- feature-requests/ \
              | grep -E '^feature-requests/FR-[0-9]+-' \
              | grep -v TEMPLATE.md \
              | grep -v README.md)
    for fr in $new_frs; do
        if [[ -f "$fr" ]]; then
            echo "🚀 Enforcing: $fr"
            scripts/enforce_worktree.sh "$fr" &
        fi
    done
    echo "$current_sha" > "$LAST_SHA_FILE"
fi
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| Git-diff detection (not filesystem polling) | Only triggers on committed FRs — prevents accidental enforcement of drafts |
| Background `&` for enforce | Multiple FRs can be enforced in parallel (FR-106 worktrees are isolated) |
| SHA state file | Idempotent — restart-safe, won't re-enforce already-processed FRs |
| Filter pattern `FR-[0-9]+-` | Only matches numbered FRs, excludes TEMPLATE.md, README.md, draft-* files |
| Extend watch.sh (not new script) | Single polling daemon; avoids proliferating watcher scripts |

### What changes

| File | Change |
|------|--------|
| `.chaplain/watch.sh` | Add enforce detection block after inbox processing |
| `.chaplain/.last-enforce-sha` | New state file (git-ignored) |
| `.chaplain/.gitignore` | Add `.last-enforce-sha` entry |

### What does NOT change

- `scripts/enforce_worktree.sh` — Invoked as-is, no modifications
- `examples/copilot/graph.yaml` — Plan→Judge pipeline unchanged
- `examples/enforce/graph.yaml` — Enforce pipeline unchanged

## Acceptance Criteria

- [ ] `watch.sh` detects FRs added to `feature-requests/` since last checked commit
- [ ] Detection uses `git diff --name-only` between stored SHA and current HEAD
- [ ] Only files matching `FR-[0-9]+-*.md` trigger enforcement (excludes TEMPLATE, README, draft-*)
- [ ] `enforce_worktree.sh` is invoked in background for each detected FR
- [ ] SHA state file (`.chaplain/.last-enforce-sha`) persists across restarts
- [ ] `.last-enforce-sha` is covered by `.chaplain/.gitignore`
- [ ] Multiple FRs committed in a single push are each enforced independently
- [ ] Re-running watch.sh after restart does not re-enforce already-processed FRs
- [ ] Manual `enforce_worktree.sh` invocation still works independently
- [ ] Unit test: SHA state file read/write logic
- [ ] Integration test: end-to-end detection of new FR → enforce invocation (mocked)
- [ ] Tests tagged with `@pytest.mark.req("REQ-YG-114")`
- [ ] Documentation updated in README or `.chaplain/` comments

## Alternatives Considered

1. **Approval marker file (e.g., `FR-XXX.approved`)**: Adds filesystem state outside git. Fragile — files can be orphaned, no audit trail. Rejected.

2. **Watch `feature-requests/` via filesystem polling**: Would trigger on any file change (editor temp files, partial writes). Git-diff is more precise and semantically correct — only committed FRs are "approved."

3. **Separate watcher script**: Would require running two daemons. Extending watch.sh keeps a single process and shared polling cadence.

4. **Git hook (post-commit)**: Would couple enforcement to every commit, not just FR additions. Too broad — we only want to enforce when FRs land in `feature-requests/`.

## Related

- `scripts/enforce_worktree.sh` — The enforce script to be triggered
- `feature-requests/FR-106-parallel-worktree-pipeline.md` — Parallel worktree pipeline (prerequisite, completed)
- `feature-requests/068-chaplain-watch.md` — Original watch loop FR
- `feature-requests/FR-098-consolidate-watch-graph.md` — Watch consolidation
- `feature-requests/055-autonomous-chaplain.md` — Autonomous chaplain pipeline
- `.chaplain/watch.sh` — The script to be extended
- `yamlgraph/utils/worktree_helpers.py` — Branch derivation and worktree path utilities
