# Feature Request: Enforce Worktree bare=true Corruption Guard

**ID:** FR-139
**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-08

## Summary

Add a three-layered git config integrity guard to `scripts/enforce_worktree.sh` that detects and restores `bare = true` corruption in the main repo's `.git/config` after worktree operations.

## Value Statement

All developers using the enforce pipeline regain reliable git operations without manual `.git/config` intervention after worktree runs.

## Problem

After `enforce_worktree.sh` completes (success or failure), the main repo's `.git/config` sometimes has `bare = true` set, causing all subsequent git commands to fail with _"this operation must be run in a work tree"_. This requires a manual fix (`scripts/fix_bare.sh` or `sed`) every time.

**Root cause hypothesis (ranked by likelihood):**

1. **`GIT_DIR` / `GIT_WORK_TREE` env pollution** — An LLM-generated command inside the enforce graph (`yamlgraph graph run`) may set these environment variables, leaking into the cleanup trap and causing git to misidentify the repo as bare.
2. **`git worktree remove --force`** — When the worktree is removed while the shell's CWD is still inside it, git may misidentify the main repo as bare.
3. **Race condition** — When `watch.sh` spawns multiple `enforce_worktree.sh` instances via `nohup`, concurrent `git worktree add/remove` operations on the same `.git` directory may corrupt the config.

The current script has **no protection** against any of these scenarios. Only a reactive manual script (`scripts/fix_bare.sh`) exists.

## Proposed Solution

Three-layered defense: **sanitize**, **restore**, and **assert**.

### Layer 1: Sanitize environment before worktree context

Before entering the worktree `cd`, unset any env vars that could confuse git's repo detection:

```bash
cd "$WORKTREE_DIR"
unset GIT_DIR GIT_WORK_TREE 2>/dev/null || true
log_info "Working in: $(pwd)"
```

This prevents env pollution from the calling shell or previous commands from leaking into the worktree or cleanup contexts.

### Layer 2: Restore in cleanup trap

Extend the existing `cleanup()` function to detect and fix corruption:

```bash
cleanup() {
    local exit_code=$?
    cd "$MAIN_DIR" 2>/dev/null || true
    log_info "Cleaning up worktree: $WORKTREE_DIR"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || true

    if ! git ls-remote --heads origin "$BRANCH" | grep -q "$BRANCH"; then
        git branch -D "$BRANCH" 2>/dev/null || true
    fi

    # FR-139: Guard against bare=true corruption
    local bare_after
    bare_after=$(git config --get core.bare 2>/dev/null || echo "false")
    if [[ "$bare_after" == "true" ]]; then
        log_warn "Detected bare=true corruption in .git/config — restoring to bare=false"
        git config core.bare false
    fi

    exit $exit_code
}
```

This fires on **both** success and failure paths (via `trap cleanup EXIT`), guaranteeing the main repo is left in a usable state.

### Layer 3: Post-run assertion

After the `yamlgraph graph run` call returns (before the script exits normally), verify config integrity while still in the main context:

```bash
yamlgraph graph run examples/enforce/graph.yaml ...

# FR-139: Assert git config integrity after pipeline execution
cd "$MAIN_DIR"
if [[ "$(git config --get core.bare 2>/dev/null)" == "true" ]]; then
    log_error "bare=true detected after pipeline run — restoring"
    git config core.bare false
fi
```

This catches mid-run corruption (between worktree creation and cleanup) that could affect other concurrent processes.

## Acceptance Criteria

- [ ] After `enforce_worktree.sh` completes successfully, main repo `.git/config` has `bare = false`
- [ ] After `enforce_worktree.sh` fails mid-execution (trap fires), main repo `.git/config` has `bare = false`
- [ ] If `bare = true` is detected during cleanup, a warning is logged and the value is restored automatically
- [ ] `GIT_DIR` and `GIT_WORK_TREE` are unset before entering the worktree context
- [ ] Python test in `tests/unit/test_enforce_worktree_bare_guard.py` verifies the guard: creates a temp git repo, sets `bare=true` in its config, invokes the guard logic via subprocess, and asserts `bare=false` afterward
- [ ] Existing worktree integration tests (`tests/integration/test_worktree_integration.py`) still pass
- [ ] `scripts/fix_bare.sh` remains as a standalone emergency tool (no changes)

## Alternatives Considered

1. **Fix only in cleanup trap** — Insufficient. Corruption can occur during `yamlgraph graph run` (between creation and cleanup), leaving a window where other processes see `bare = true`. Rejected.
2. **Snapshot `bare` value before worktree creation** — The script requires a non-bare repo to run (`git worktree add` fails on bare repos), so the snapshot would always be `false`. This is dead code masquerading as safety. Rejected.
3. **Periodic background monitor** — Overcomplicated. Pre/post assertion is sufficient and deterministic. Rejected.
4. **Lock file around git worktree operations** — Would address the concurrency hypothesis but adds complexity. Defer to a separate FR if concurrent spawns remain problematic after this fix.
5. **Move to `git clone --shared`** — Eliminates worktree mechanics entirely but loses the branch-based workflow. Too disruptive. Rejected.

## Related

- `scripts/enforce_worktree.sh` — Primary file to modify
- `scripts/fix_bare.sh` — Existing manual recovery (unchanged)
- `yamlgraph/utils/worktree_helpers.py` — Python helpers (no changes expected)
- `.chaplain/watch.sh` — Spawns enforce_worktree.sh (concurrent risk)
- `feature-requests/FR-106-parallel-worktree-pipeline.md` — Parent feature (IMPLEMENTED)
- `tests/integration/test_worktree_integration.py` — Integration tests to verify

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Evaluation:**

1. **Scope: Clear and minimal.** Three surgical additions to one file (`scripts/enforce_worktree.sh`): an `unset`, a cleanup guard, and a post-run assertion. No framework changes. The defense-in-depth layering (sanitize → restore → assert) is sound — each layer covers a distinct failure window. No speculative extensibility.

2. **No contradictions.** One minor note: the Layer 1 code snippet shows `unset` after `cd "$WORKTREE_DIR"`, while the text says "Before entering the worktree context." These are consistent — "context" means before issuing git commands in the worktree, not before `cd`. The implementation should place the `unset` between the existing `cd "$WORKTREE_DIR"` (line 107) and the log line (line 108), matching the snippet exactly.

3. **Acceptance criteria: Measurable.** All 7 items are binary pass/fail. The test AC is specific: temp git repo, force `bare=true`, invoke guard via subprocess, assert `bare=false`. One refinement: the test should also verify the warning log output (`"Detected bare=true corruption"`) to confirm the guard fired vs the value being false already.

4. **Feasibility: High.** `git config --get core.bare` + `git config core.bare false` are well-understood operations. `unset GIT_DIR GIT_WORK_TREE` is zero-risk. 1-day estimate is realistic including the test and verification against existing integration tests.

5. **Architecture alignment: Good.** Changes stay in the Presentation layer (`scripts/`). The root cause hypotheses are honestly ranked. The decision to defer lock-file concurrency to a separate FR is disciplined — solve the deterministic guard first, investigate the race later.

**Notes for implementation:**
- Place the `unset` between the existing `cd "$WORKTREE_DIR"` (line 107) and `log_info "Working in: $(pwd)"` (line 108).
- In the cleanup function, add the bare guard after `git branch -D` (line 85) and before `exit $exit_code` (line 87).
- The post-run assertion goes between `yamlgraph graph run` (line 113-116) and the success log (line 118). Use `cd "$MAIN_DIR"` first since CWD may still be in the worktree.
- Tag the test with `@pytest.mark.req("REQ-YG-UTIL")` for requirement traceability.
