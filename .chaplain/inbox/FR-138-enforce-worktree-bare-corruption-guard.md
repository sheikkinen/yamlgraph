# Feature Request: Enforce Worktree bare=true Corruption Guard

**Priority:** HIGH
**Type:** Bug
**Status:** Amend
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a git config integrity guard to `enforce_worktree.sh` that prevents and detects `bare = true` corruption in the main repo's `.git/config` after worktree operations.

## Value Statement

All developers using the enforce pipeline regain reliable git operations without manual `.git/config` intervention after worktree runs.

## Problem

After `enforce_worktree.sh` completes (success or failure), the main repo's `.git/config` sometimes has `bare = true` set, causing all subsequent git commands to fail with _"this operation must be run in a work tree"_. This requires a manual fix (`sed -i '' 's/bare = true/bare = false/' .git/config`) every time.

**Root cause hypothesis (ranked by likelihood):**

1. **`git worktree remove --force`** — When the worktree is the last one removed and the cleanup runs from inside the worktree directory (before `cd "$MAIN_DIR"`), git may misidentify the main repo as bare.
2. **`GIT_DIR` / `GIT_WORK_TREE` env pollution** — An LLM-generated command inside the enforce graph (`yamlgraph graph run`) may set these environment variables, leaking into the cleanup trap.
3. **Race condition** — When `watch.sh` spawns multiple `enforce_worktree.sh` instances via `nohup`, concurrent `git worktree add/remove` operations on the same `.git` directory may corrupt the config.

The current script has no protection against any of these scenarios.

## Proposed Solution

Three-layered defense: **snapshot**, **restore**, and **assert**.

> ⚠️ **Judge note:** This section claims three layers but defines four. See Judge Amendments below — resolve before implementation.

### Layer 1: Snapshot `bare` value before worktree creation

In `enforce_worktree.sh`, immediately before `git worktree add`:

```bash
# Snapshot git config integrity before worktree operations
BARE_BEFORE=$(git config --get core.bare 2>/dev/null || echo "false")
```

### Layer 2: Restore in cleanup trap

Extend the existing `cleanup()` function:

```bash
cleanup() {
    local exit_code=$?
    cd "$MAIN_DIR" 2>/dev/null || true
    log_info "Cleaning up worktree: $WORKTREE_DIR"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true
    # Also delete the branch if it was newly created and has no remote
    if ! git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
        git branch -D "$BRANCH" 2>/dev/null || true
    fi

    # Guard: restore core.bare if corrupted (FR-138)
    local bare_after
    bare_after=$(git config --get core.bare 2>/dev/null || echo "false")
    if [[ "$bare_after" == "true" ]]; then
        log_warn "Detected bare=true corruption in .git/config — restoring to bare=false"
        git config core.bare false
    fi

    exit $exit_code
}
```

### Layer 3: Post-run assertion

After the `yamlgraph graph run` call returns (but before the script exits normally), add a verification step:

```bash
# FR-138: Assert git config integrity after pipeline execution
cd "$MAIN_DIR"
if [[ "$(git config --get core.bare 2>/dev/null)" == "true" ]]; then
    log_error "FATAL: bare=true detected after pipeline run. Restoring."
    git config core.bare false
fi
```

### Layer 4 (defensive): Pin `GIT_DIR` in worktree scope

Before entering the worktree `cd`, unset any leaked env vars:

```bash
cd "$WORKTREE_DIR"
unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
log_info "Working in: $(pwd)"
```

## Acceptance Criteria

- [ ] After `enforce_worktree.sh` completes successfully, main repo `.git/config` has `bare = false`
- [ ] After `enforce_worktree.sh` fails mid-execution (trap fires), main repo `.git/config` has `bare = false`
- [ ] If `bare = true` is detected during cleanup, a warning is logged and the value is restored automatically
- [ ] `GIT_DIR` and `GIT_WORK_TREE` are unset before entering the worktree context
- [ ] Unit test in `tests/unit/test_enforce_worktree_bare_guard.sh` (or Python equivalent) verifies the guard detects and fixes corruption
- [ ] Existing worktree integration tests (`tests/integration/test_worktree_integration.py`) still pass
- [ ] Documentation: update `examples/enforce/README.md` with known-issue resolution note

## Alternatives Considered

1. **Fix only in cleanup trap** — Insufficient. The corruption can occur during `yamlgraph graph run` (between creation and cleanup), leaving a window where other processes see `bare = true`.
2. **Periodic background monitor** — Overcomplicated. A pre/post assertion is sufficient and deterministic.
3. **Lock file around git worktree operations** — Would address the concurrency hypothesis but adds complexity. Defer to a separate FR if concurrent spawns remain problematic after this fix.
4. **Move to `git clone --shared`** — Eliminates worktree mechanics entirely but loses the branch-based workflow. Too disruptive.

## Judge Amendments (2026-03-08)

**Verdict: AMEND** — Two issues must be resolved before authority is granted.

### Issue 1: Dead variable — `BARE_BEFORE` captured but never used

Layer 1 snapshots `BARE_BEFORE` but neither Layer 2 nor Layer 3 references it — both hardcode the restore target to `false`. This is dead code masquerading as a safety mechanism.

**Resolution (pick one):**
- **Option A (preferred): Remove Layer 1 entirely.** The script already requires a non-bare repo (it runs `git worktree add`), so `BARE_BEFORE` will always be `false`. The snapshot adds no value. Rename the remaining layers (2→1, 3→2, 4→3) and fix the summary to say "Three-layered defense" truthfully.
- **Option B:** Use `BARE_BEFORE` in the restore: `git config core.bare "$BARE_BEFORE"`. This is only meaningful if the repo could legitimately start as bare — it cannot in this workflow.

### Issue 2: Vague test specification in AC 5

"Unit test in `tests/unit/test_enforce_worktree_bare_guard.sh` (or Python equivalent)" is ambiguous. The project is pytest-centric.

**Resolution:** Specify a Python test using `subprocess` + a temporary git repo. Example shape: create a temp repo, manually set `bare=true` in its config, invoke the guard logic, assert `bare=false` afterward. Name it `tests/unit/test_enforce_worktree_bare_guard.py`.

---

## Related

- `scripts/enforce_worktree.sh` — Primary file to modify
- `yamlgraph/utils/worktree_helpers.py` — Python helpers (no changes expected)
- `.chaplain/watch.sh` — Spawns enforce_worktree.sh (concurrent risk)
- `feature-requests/FR-106-parallel-worktree-pipeline.md` — Parent feature (IMPLEMENTED)
- `tests/integration/test_worktree_integration.py` — Integration tests to verify
