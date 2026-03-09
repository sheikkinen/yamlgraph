# Diary Entry: The Watch-Enforce-Merge Dance

**Date:** 2026-03-09
**Author:** Merger Agent
**Context:** Extended PR management session (PRs #31-43)

## The Pain Points

### 1. Terminal Context Loss (pushd/popd trap)

When a worktree is removed while the shell's cwd is inside it:
```
fatal: Unable to read current working directory: No such file or directory
```

**Root cause:** `gh pr merge --delete-branch` tries to switch to main, but the worktree directory no longer exists. The shell is orphaned.

**Current workaround:** `cd ~ && cd /path/to/repo` — escape to known-good location.

**Better fix:** Enforce script should `cd` back to repo root before cleanup. Or: never `pushd` into worktrees from the main session.

### 2. Venv Corruption (FR-174)

Editable installs (`pip install -e .`) create `.pth` and `.egg-link` files pointing to absolute paths. When worktrees are removed:
- Stale entries cause `ModuleNotFoundError` despite package being "installed"
- Symlinked venvs inherit corruption from main venv

**Implemented fix:** FR-174 added `validate_venv_health()` and `clean_stale_pth_entries()`.

**Remaining gap:** The fix runs at worktree creation, not after worktree deletion. Should also run in main venv after worktree cleanup.

### 3. Enforcement Stalls (FR-173)

The Copilot CLI hung mid-execution. The worktree had 95% of the work done but no commits. Recovery required:
1. Manual inspection of worktree state
2. Running tests to assess completeness
3. Completing the final 5% manually
4. Rebasing, fixing conflicts, creating PR

**Insight:** Stalled automation often produces recoverable partial work. Inventory before discarding.

### 4. The Rebase Dance

With parallel enforcement (`nohup ... &`), two PRs can be created simultaneously. But they both branch from the same base commit. When PR #41 merges:
- PR #42 becomes DIRTY/CONFLICTING
- Manual rebase required
- Common conflicts: ARCHITECTURE.md counts, CHANGELOG.md entries, req_coverage.py capability maps

**The dance:**
```
PR #41 created → PR #42 created →
merge #41 → #42 now conflicts →
fetch origin → git checkout #42-branch → git rebase main →
resolve conflicts → force push → merge #42
```

## Sequential vs Parallel Enforcement

### Current: Parallel (nohup &)
**Pros:**
- Fast throughput when FRs are independent
- Multiple features in flight

**Cons:**
- Merge conflict resolution is manual and error-prone
- Capability counts in ARCHITECTURE.md cause collision every time
- CHANGELOG.md always conflicts (both add to same section)

### Alternative: Sequential Queue
**Pros:**
- Each PR merges cleanly (based on latest main)
- No conflict resolution needed
- Deterministic ordering

**Cons:**
- Slower (enforcement takes 5-30 minutes each)
- Queue stalls block everything

### Hybrid Proposal

```yaml
# .chaplain/config.yaml
enforcement:
  mode: sequential  # or parallel, hybrid

  # For hybrid mode:
  parallel_limit: 2  # max concurrent enforcements
  sequential_files:    # files that trigger sequential mode
    - ARCHITECTURE.md
    - CHANGELOG.md
    - scripts/req_coverage.py
```

If an FR touches "sequential_files", wait for queue to drain before starting.

## Improvement Ideas

### 1. Auto-Rebase on Conflict Detection

When `gh pr view` shows `CONFLICTING`:
```bash
# Auto-rebase script
if gh pr view $PR --json mergeStateStatus | jq -r '.mergeStateStatus' | grep -q DIRTY; then
    git fetch origin
    git checkout $BRANCH
    git rebase origin/main || {
        # If conflicts, attempt auto-resolution for known patterns
        resolve_capability_counts
        resolve_changelog_entries
        git add -A && git rebase --continue
    }
    git push --force-with-lease
fi
```

### 2. Central Capability Counter

Instead of hardcoding counts in ARCHITECTURE.md:
```python
# scripts/count_capabilities.py
actual_caps = len(grep_capability_rows("ARCHITECTURE.md"))
actual_reqs = len(grep_requirement_rows("ARCHITECTURE.md"))
# Update the summary line automatically
```

Run as pre-commit hook. Eliminates conflict source entirely.

### 3. Worktree Session Isolation

Never `pushd` into worktrees from interactive sessions:
```bash
# Instead of:
pushd tmp/worktrees/feat/xxx && git status && popd

# Use:
git -C tmp/worktrees/feat/xxx status
# Or spawn subshell:
(cd tmp/worktrees/feat/xxx && git status)
```

### 4. Checkpoint Commits in Enforce Pipeline

Modify copilot nodes to commit incrementally:
```yaml
nodes:
  implement:
    type: copilot
    checkpoint_interval: 300  # commit every 5 minutes
```

If Copilot stalls, partial work is preserved in git history.

### 5. Post-Merge Cleanup Hook

After merge, run venv health check:
```bash
# In gh pr merge wrapper
gh pr merge $PR --squash --admin --delete-branch
python -c "from yamlgraph.utils.worktree_helpers import clean_stale_pth_entries; clean_stale_pth_entries()"
```

## Seed

What's the minimal queue discipline that eliminates merge conflicts without sacrificing parallelism?

Consider: conflict prediction based on which files an FR is likely to touch (parsed from FR description → expected modules). FRs with disjoint file sets run in parallel; overlapping FRs serialize.
